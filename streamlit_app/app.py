import os
import streamlit as st
from db import fetch_scenarios, insert_diagnosis_run, fetch_recent_runs

st.set_page_config(page_title="ML Systems Reasoning Assistant", layout="centered")

st.title("ML Systems Reasoning Assistant")
st.caption("Diagnose why ML systems fail in production — with checks, causes, and actions.")

# ---- Load scenarios
@st.cache_data(ttl=30)
def load_scenarios():
    return fetch_scenarios()

def build_stub_diagnosis(prompt: str):
    # Same spirit as your Next.js stub response
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

run = st.button("Run Diagnosis", type="primary", disabled=(not prompt.strip()))

if run:
    try:
        diagnosis = build_stub_diagnosis(prompt.strip())
        saved = insert_diagnosis_run(
            scenario_id=selected["id"] if selected else None,
            prompt=prompt.strip(),
            diagnosis=diagnosis,
        )
        st.success(f"Saved run: {saved['id']} @ {saved['created_at']}")
        st.subheader("Diagnosis Output")
        st.json({"ok": True, "scenarioId": selected["id"] if selected else None, "input": prompt.strip(), "diagnosis": diagnosis})
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
                st.write("**Scenario ID:**", r["scenario_id"])
                st.write("**Input:**")
                st.write(r["input"])
                st.write("**Diagnosis:**")
                st.json(r["diagnosis"])
except Exception as e:
    st.error(f"Failed to load history: {e}")