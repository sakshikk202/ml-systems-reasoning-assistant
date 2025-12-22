import os
import json
import streamlit as st
from typing import Optional

from db import fetch_scenarios, insert_diagnosis_run, fetch_recent_runs
from llm import hf_chat


st.set_page_config(
    page_title="ML Systems Reasoning Assistant",
    layout="centered",
)

st.title("ML Systems Reasoning Assistant")
st.caption("Diagnose why ML systems fail in production — with checks, causes, and actions.")


@st.cache_data(ttl=30)
def load_scenarios():
    return fetch_scenarios()


def build_stub_diagnosis(prompt: str) -> dict:
    return {
        "summary": "API wired correctly (stub).",
        "checks": [
            "Validate feature pipeline health",
            "Check null-rate by feature and slice",
            "Confirm training-serving schema parity",
        ],
        "causes": [
            "Upstream feature outage / partial nulls",
            "Schema change or parsing regression",
        ],
        "actions": [
            "Add feature-null SLO + alerting",
            "Fail fast or fallback defaults on nulls",
            "Rollback upstream change or hotfix parser",
        ],
    }


def _clean_llm_json(text: str) -> str:
    text = text.strip()

    # Remove fenced code block if model wraps JSON in ```...```
    if text.startswith("```"):
        lines = text.splitlines()
        # drop first fence line
        lines = lines[1:]
        # drop last fence line if present
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return text


def build_llm_diagnosis(prompt: str, scenario_title: Optional[str] = None) -> dict:
    system = (
        "You are an ML systems reliability engineer. "
        "Return concise, production-grade guidance in JSON with keys: "
        "summary, checks, causes, actions. "
        "checks/causes/actions must be short bullet strings."
    )

    user = (
        f"Scenario: {scenario_title or 'Custom'}\n"
        f"Issue: {prompt}\n\n"
        "Return ONLY valid JSON like:\n"
        "{\n"
        '  "summary": "...",\n'
        '  "checks": ["..."],\n'
        '  "causes": ["..."],\n'
        '  "actions": ["..."]\n'
        "}\n"
    )

    text = hf_chat(user, system=system)

    try:
        cleaned = _clean_llm_json(text)
        obj = json.loads(cleaned)
        return {
            "summary": (obj.get("summary") or "").strip() or "No summary returned.",
            "checks": obj.get("checks") or [],
            "causes": obj.get("causes") or [],
            "actions": obj.get("actions") or [],
        }
    except Exception:
        return {
            "summary": text.strip(),
            "checks": [],
            "causes": [],
            "actions": [],
        }


st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Scenario")
    try:
        scenarios = load_scenarios()
    except Exception as e:
        st.error(f"Failed to load scenarios: {e}")
        scenarios = []

    scenario_titles = ["(Custom)"] + [s["title"] for s in scenarios]
    pick = st.selectbox("Pick a scenario", scenario_titles, index=0)

    selected = None
    if pick != "(Custom)":
        selected = next((s for s in scenarios if s["title"] == pick), None)

with col2:
    st.subheader("Prompt")
    default_prompt = selected["description"] if selected else ""
    prompt = st.text_area(
        "Describe the issue",
        value=default_prompt,
        height=140,
        placeholder="Offline metrics good → production bad. What are you seeing in prod?",
    )

st.divider()

run = st.button(
    "Run Diagnosis",
    type="primary",
    disabled=not prompt.strip(),
)

if run:
    with st.spinner("Running diagnosis..."):
        try:
            issue = prompt.strip()
            scenario_title = selected["title"] if selected else None

            if os.getenv("HF_TOKEN"):
                try:
                    diagnosis = build_llm_diagnosis(issue, scenario_title)
                except Exception as llm_err:
                    st.warning(f"HF failed, using stub: {llm_err}")
                    diagnosis = build_stub_diagnosis(issue)
            else:
                diagnosis = build_stub_diagnosis(issue)

            saved = insert_diagnosis_run(
                scenario_id=selected["id"] if selected else None,
                prompt=issue,
                diagnosis=diagnosis,
            )

            st.success(f"Saved run: {saved['id']} @ {saved['created_at']}")
            st.subheader("Diagnosis Output")
            st.json(
                {
                    "ok": True,
                    "scenarioId": selected["id"] if selected else None,
                    "input": issue,
                    "diagnosis": diagnosis,
                }
            )
        except Exception as e:
            st.error(f"Run failed: {e}")

st.divider()
st.subheader("History (latest 30)")

try:
    runs = fetch_recent_runs(30)
    if not runs:
        st.info("No diagnosis runs yet.")
    else:
        for r in runs:
            with st.expander(f"{r['created_at']} — {r['id']}"):
                st.write("Scenario ID:", r["scenario_id"])
                st.write("Input:")
                st.write(r["input"])
                st.write("Diagnosis:")
                st.json(r["diagnosis"])
except Exception as e:
    st.error(f"Failed to load history: {e}")