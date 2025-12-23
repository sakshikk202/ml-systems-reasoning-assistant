import os
import json
import streamlit as st
from typing import Optional, Dict, Any, List

from db import fetch_scenarios, insert_diagnosis_run, fetch_recent_runs
from llm import hf_chat

st.set_page_config(
    page_title="ML Systems Reasoning Assistant",
    layout="centered",
)

st.title("ML Systems Reasoning Assistant")
st.caption("Diagnose why ML systems fail in production — with checks, causes, and actions.")

RUNBOOKS_BY_TITLE: Dict[str, str] = {}


@st.cache_data(ttl=30)
def load_scenarios():
    return fetch_scenarios()


def build_stub_diagnosis(prompt: str) -> Dict[str, Any]:
    return {
        "severity": "Medium",
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
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _normalize_severity(val: Optional[str]) -> str:
    if not val:
        return "Medium"
    v = val.strip().lower()
    if v in ("low", "l"):
        return "Low"
    if v in ("high", "h", "sev1", "sev-1", "critical", "p0", "p1"):
        return "High"
    if v in ("medium", "med", "m", "sev2", "sev-2", "p2"):
        return "Medium"
    return "Medium"


def build_llm_diagnosis(prompt: str, scenario_title: Optional[str] = None) -> Dict[str, Any]:
    system = (
        "You are an ML systems reliability engineer. "
        "Return concise, production-grade guidance in STRICT JSON with keys: "
        "severity (Low|Medium|High), summary, checks, causes, actions."
    )

    user = (
        f"Scenario: {scenario_title or 'Custom'}\n"
        f"Issue: {prompt}\n"
    )

    text = hf_chat(user, system=system)

    try:
        obj = json.loads(_clean_llm_json(text))
        return {
            "severity": _normalize_severity(obj.get("severity")),
            "summary": obj.get("summary", "").strip(),
            "checks": obj.get("checks", []),
            "causes": obj.get("causes", []),
            "actions": obj.get("actions", []),
        }
    except Exception:
        return {
            "severity": "Medium",
            "summary": text.strip(),
            "checks": [],
            "causes": [],
            "actions": [],
        }


def get_runbook_url(selected: Optional[Dict[str, Any]]) -> Optional[str]:
    if not selected:
        return None
    for k in ("runbook_url", "runbook", "url"):
        if selected.get(k):
            return selected[k]
    return None


def _list_or_empty(val: Any) -> List[str]:
    return val if isinstance(val, list) else []


def render_severity(severity: str):
    if severity == "High":
        st.error("Severity: High")
    elif severity == "Low":
        st.info("Severity: Low")
    else:
        st.warning("Severity: Medium")


def render_diagnosis(diagnosis: Dict[str, Any], runbook_url: Optional[str]):
    render_severity(diagnosis.get("severity", "Medium"))
    if runbook_url:
        st.markdown(f"Runbook: {runbook_url}")

    st.subheader("Diagnosis")
    st.write(diagnosis.get("summary", ""))

    for section, items in {
        "Checks to Run": diagnosis.get("checks"),
        "Likely Causes": diagnosis.get("causes"),
        "Recommended Actions": diagnosis.get("actions"),
    }.items():
        if items:
            st.markdown(f"### {section}")
            for i in items:
                st.markdown(f"- {i}")


# ---------------- UI ----------------

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Mode")  # ✅ ONLY CHANGE

    scenarios = load_scenarios()
    scenario_titles = ["(Custom)"] + [s["title"] for s in scenarios]

    pick = st.selectbox("Pick a scenario", scenario_titles)
    selected = next((s for s in scenarios if s["title"] == pick), None) if pick != "(Custom)" else None

    st.selectbox("Mode", ["Custom"], index=0)

with col2:
    st.subheader("Prompt")
    prompt = st.text_area(
        "Problem description",
        value=selected.get("description", "") if selected else "",
        height=140,
    )

st.divider()

if st.button("Run Diagnosis", disabled=not prompt.strip()):
    diagnosis = build_llm_diagnosis(prompt, selected.get("title") if selected else None)
    insert_diagnosis_run(
        scenario_id=selected.get("id") if selected else None,
        prompt=prompt,
        diagnosis=diagnosis,
    )
    render_diagnosis(diagnosis, get_runbook_url(selected))