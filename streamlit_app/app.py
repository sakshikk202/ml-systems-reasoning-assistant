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
        "severity (Low|Medium|High), summary, checks, causes, actions. "
        "checks/causes/actions must be short bullet strings."
    )

    user = (
        f"Scenario: {scenario_title or 'Custom'}\n"
        f"Issue: {prompt}\n\n"
        "Return ONLY valid JSON like:\n"
        "{\n"
        '  "severity": "Low|Medium|High",\n'
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
            "severity": _normalize_severity(obj.get("severity")),
            "summary": (obj.get("summary") or "").strip() or "No summary returned.",
            "checks": obj.get("checks") or [],
            "causes": obj.get("causes") or [],
            "actions": obj.get("actions") or [],
        }
    except Exception:
        return {
            "severity": "Medium",
            "summary": (text or "").strip(),
            "checks": [],
            "causes": [],
            "actions": [],
        }


def get_runbook_url(selected: Optional[Dict[str, Any]]) -> Optional[str]:
    if not selected:
        return None

    for key in ("runbook_url", "runbook", "runbookLink", "runbook_link", "url"):
        if selected.get(key):
            return str(selected.get(key))

    title = selected.get("title")
    if title and title in RUNBOOKS_BY_TITLE:
        return RUNBOOKS_BY_TITLE[title]

    return None


def _list_or_empty(val: Any) -> List[str]:
    if isinstance(val, list):
        return [str(x) for x in val if str(x).strip()]
    return []


def render_severity(severity: str) -> None:
    sev = _normalize_severity(severity)
    if sev == "High":
        st.error("Severity: High")
    elif sev == "Low":
        st.info("Severity: Low")
    else:
        st.warning("Severity: Medium")


def render_diagnosis(diagnosis: Dict[str, Any], runbook_url: Optional[str]) -> None:
    render_severity(diagnosis.get("severity", "Medium"))

    if runbook_url:
        st.markdown(f"Runbook: {runbook_url}")

    st.subheader("Diagnosis")

    st.markdown("### Summary")
    st.write((diagnosis.get("summary") or "").strip())

    checks = _list_or_empty(diagnosis.get("checks"))
    causes = _list_or_empty(diagnosis.get("causes"))
    actions = _list_or_empty(diagnosis.get("actions"))

    if checks:
        st.markdown("### Checks to Run")
        for c in checks:
            st.markdown(f"- {c}")

    if causes:
        st.markdown("### Likely Causes")
        for c in causes:
            st.markdown(f"- {c}")

    if actions:
        st.markdown("### Recommended Actions")
        for a in actions:
            st.markdown(f"- {a}")


# ---------------- UI ----------------

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    # ✅ remove the big "Scenario" heading
    # st.subheader("Scenario")

    try:
        scenarios = load_scenarios()
    except Exception as e:
        st.error(f"Failed to load scenarios: {e}")
        scenarios = []

    # ✅ Scenario dropdown should NOT show "(Custom)" anymore
    scenario_titles = [s["title"] for s in scenarios]

    if scenario_titles:
        pick = st.selectbox(
            "Pick a scenario",
            scenario_titles,
            index=0,
            key="scenario_pick",
        )
        selected: Optional[Dict[str, Any]] = next((s for s in scenarios if s["title"] == pick), None)
    else:
        st.selectbox("Pick a scenario", ["No scenarios available"], index=0, disabled=True)
        selected = None

    # ✅ Custom stays as a separate dropdown below (still independent)
    st.selectbox(
        "Mode",
        ["Custom"],
        index=0,
        key="mode_custom_only",
        help="Free-form problem description",
    )

with col2:
    st.subheader("Prompt")
    default_prompt = selected.get("description", "") if selected else ""
    prompt = st.text_area(
        "Problem description",
        value=default_prompt,
        height=140,
        placeholder="Offline metrics look good → production performance degraded. What are you seeing in prod?",
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
            scenario_title = selected.get("title") if selected else None
            scenario_id = selected.get("id") if selected else None
            runbook_url = get_runbook_url(selected)

            if os.getenv("HF_TOKEN"):
                try:
                    diagnosis = build_llm_diagnosis(issue, scenario_title)
                except Exception as llm_err:
                    st.warning(f"HF failed, using stub: {llm_err}")
                    diagnosis = build_stub_diagnosis(issue)
            else:
                diagnosis = build_stub_diagnosis(issue)

            saved = insert_diagnosis_run(
                scenario_id=scenario_id,
                prompt=issue,
                diagnosis=diagnosis,
            )

            st.success(f"Saved run: {saved['id']} @ {saved['created_at']}")
            render_diagnosis(diagnosis=diagnosis, runbook_url=runbook_url)

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
                st.write(f"Scenario ID: {str(r.get('scenario_id')) if r.get('scenario_id') is not None else ''}")
                st.write("Input:")
                st.write(r.get("input", ""))

                d = r.get("diagnosis") or {}
                st.divider()
                render_severity(d.get("severity", "Medium"))

                st.markdown("### Summary")
                st.write((d.get("summary") or "").strip())

                checks = _list_or_empty(d.get("checks"))
                causes = _list_or_empty(d.get("causes"))
                actions = _list_or_empty(d.get("actions"))

                if checks:
                    st.markdown("### Checks to Run")
                    for c in checks:
                        st.markdown(f"- {c}")

                if causes:
                    st.markdown("### Likely Causes")
                    for c in causes:
                        st.markdown(f"- {c}")

                if actions:
                    st.markdown("### Recommended Actions")
                    for a in actions:
                        st.markdown(f"- {a}")

except Exception as e:
    st.error(f"Failed to load history: {e}")