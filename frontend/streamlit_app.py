"""
Patient intake form component.

Collects basic demographic and self-reported symptom/history data
via a Streamlit form (or the voice assistant) and sends it to the
FastAPI backend. After a PDF summary is downloaded, the whole session
automatically resets so the next patient starts with a clean form.
"""

from typing import Any, Dict, Tuple

# pyrefly: ignore [missing-import]
import httpx
# pyrefly: ignore [missing-import]
import streamlit as st

from constants import COMMON_SYMPTOMS
from voice_assistant import render_voice_intake, reset_voice_intake
from pdf_report import build_assessment_pdf


# ----------------------------------------------------------------------
# Reset handling
#
# `form_run_id` is bumped every time we reset. It's suffixed onto every
# widget key in render_patient_form(), so Streamlit treats them as brand
# new widgets with default values -- this is what actually clears a
# st.form's fields, since clear_on_submit alone won't do it here (we
# need the fields to survive across the result-rendering run, then
# clear only once the user has downloaded the PDF).
# ----------------------------------------------------------------------

if "form_run_id" not in st.session_state:
    st.session_state.form_run_id = 0

if "last_result" not in st.session_state:
    st.session_state.last_result = None
    st.session_state.last_patient_data = None


def reset_everything() -> None:
    """Called as the download button's on_click: clears the manual
    form, the voice assistant state, and the stored assessment, then
    bumps form_run_id so widgets rebuild fresh on the next run."""
    reset_voice_intake()
    st.session_state.last_result = None
    st.session_state.last_patient_data = None
    st.session_state.form_run_id += 1


def render_patient_form() -> Tuple[Dict[str, Any], bool]:
    """Render the patient intake form."""

    st.subheader("Patient Intake")
    run_id = st.session_state.form_run_id

    with st.form(f"patient_intake_form_{run_id}", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input(
                "Age",
                min_value=0,
                max_value=120,
                value=30,
                step=1,
                key=f"age_{run_id}",
            )

        with col2:
            sex = st.selectbox(
                "Sex assigned at birth",
                ["Female", "Male", "Intersex", "Prefer not to say"],
                key=f"sex_{run_id}",
            )

        symptoms = st.multiselect(
            "Reported symptoms",
            COMMON_SYMPTOMS,
            key=f"symptoms_{run_id}",
        )

        other_symptom = ""

        if "Other" in symptoms:
            other_symptom = st.text_input(
                "Please describe the other symptom",
                key=f"other_symptom_{run_id}",
            )

        duration_days = st.slider(
            "Duration of symptoms (days)",
            0,
            90,
            3,
            key=f"duration_days_{run_id}",
        )

        severity = st.select_slider(
            "Self-rated severity",
            options=["Mild", "Moderate", "Severe"],
            value="Mild",
            key=f"severity_{run_id}",
        )
        progression = st.selectbox(
            "Symptom progression",
            ["Improving", "Stable", "Worsening"],
            key=f"progression_{run_id}",
        )

        history = st.text_area(
            "Relevant medical history (conditions, medications, allergies)",
            placeholder="e.g. Type 2 diabetes, taking metformin, no known allergies",
            key=f"history_{run_id}",
        )

        consent = st.checkbox(
            "I understand this tool does not provide medical diagnoses "
            "and is intended to help organize information for a clinician.",
            key=f"consent_{run_id}",
        )

        submitted = st.form_submit_button(
            "Generate Assessment",
            use_container_width=True,
        )

    patient_data: Dict[str, Any] = {
        "age": age,
        "sex": sex,
        "symptoms": [
            s for s in symptoms if s != "Other"
        ] + ([other_symptom] if other_symptom else []),
        "duration_days": duration_days,
        "severity": severity,
        "progression": progression,
        "history": history.strip(),
        "consent": consent,
    }

    if submitted and not consent:
        st.warning(
            "Please confirm the acknowledgement above before continuing."
        )
        submitted = False

    if submitted and not patient_data["symptoms"]:
        st.warning("Please select at least one symptom.")
        submitted = False

    return patient_data, submitted


st.title("MedAgentX")
mode = st.radio("Choose intake method", ["Manual Form", "Voice Assistant"], horizontal=True)

patient_data: Dict[str, Any] = {}
submitted = False

if mode == "Manual Form":
    patient_data, submitted = render_patient_form()
else:
    completed_data = render_voice_intake()
    if completed_data is not None:
        patient_data, submitted = completed_data, True
        if st.button("🔁 Restart voice intake"):
            reset_voice_intake()
            st.rerun()

if submitted:
    try:
        response = httpx.post(
            "http://localhost:8000/intake",
            json=patient_data,
            timeout=300.0,
        )
        response.raise_for_status()
        result = response.json()

        # Stash so the assessment + PDF button survive reruns caused
        # by other widgets (e.g. the download button itself) without
        # needing to hit the backend again.
        st.session_state.last_result = result
        st.session_state.last_patient_data = patient_data

    except httpx.ConnectError:
        st.error("Could not connect to the backend. Please make sure FastAPI is running on port 8000.")
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json()
        except Exception:
            detail = exc.response.text
        st.error(f"Backend rejected the request ({exc.response.status_code}):")
        st.json(detail)
        st.write("Data that was sent:")
        st.json(patient_data)
    except Exception as exc:
        st.error(f"Error generating assessment: {exc}")

# ----------------------------------------------------------------------
# Render the last assessment (if any) + PDF download / auto-reset
# ----------------------------------------------------------------------

if st.session_state.last_result is not None:
    result = st.session_state.last_result
    patient_data = st.session_state.last_patient_data

    if result.get("status") == "URGENT":
        st.error("⚠️URGENT MEDICAL ATTENTION REQUIRED")
        st.subheader("Safety Alert")
        st.write(f"**Flag:** {result.get('flag')}")
        st.write(f"**Severity:** {result.get('severity')}")
        st.write(f"**Action:** {result.get('action')}")
        st.warning(result.get("message"))
        if result.get("disclaimer"):
            st.info(result["disclaimer"])
    else:
        assessment = result.get("assessment", {})
        risk = result.get("risk", {})

        st.divider()
        st.title("MedAgentX — Patient Assessment")

        st.subheader("Patient Summary")
        st.write(assessment.get("patient_summary", "No summary available."))

        st.subheader("Symptoms")
        for symptom in assessment.get("symptoms", []):
            st.write(f"- {symptom}")

        st.subheader("Clinical Information")
        st.write(f"**Age:** {assessment.get('age')}")
        st.write(f"**Sex:** {assessment.get('sex')}")
        st.write(f"**Duration:** {assessment.get('duration_days')} days")
        st.write(f"**Severity:** {assessment.get('severity')}")
        st.write(f"**Progression:** {assessment.get('progression')}")

        st.subheader("Possible Conditions")
        for condition in assessment.get("possible_conditions", []):
            st.write(f"**{condition.get('condition')}**")
            st.write(condition.get("explanation"))

        st.subheader("Evidence")
        for evidence in assessment.get("evidence", []):
            st.write(f"**Source:** {evidence.get('source')}")
            st.write(evidence.get("explanation"))

        st.subheader("Risk Assessment")
        st.write(f"**Risk Level:** {risk.get('risk_level')}")
        st.write(f"**Urgency:** {risk.get('urgency')}")

        if "disclaimer" in assessment:
            st.warning(assessment["disclaimer"])

    pdf_bytes = build_assessment_pdf(patient_data, result)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📄 Download PDF Summary",
            data=pdf_bytes,
            file_name="medagentx_assessment_summary.pdf",
            mime="application/pdf",
        )
    with col2:
        if st.button("🔄 Start New Assessment"):
            reset_everything()
            st.rerun()