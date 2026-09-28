"""
pdf_report.py
-------------
Generates a downloadable PDF summary of the patient assessment.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fpdf import FPDF


# Helvetica (a built-in PDF core font) only supports Latin-1, so map common
# "smart" Unicode punctuation to ASCII equivalents before writing text.
_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u2022": "-", "\u00b7": "-", "\u25cf": "-",
    "\u2026": "...",
    "\u00a0": " ", "\u2009": " ", "\u200b": "",
    "\u2265": ">=", "\u2264": "<=", "\u00d7": "x",
    "\u2192": "->", "\u2190": "<-",
    "\u00b0": " deg",
}


def safe(value: Any) -> str:
    """Convert any value to text that Helvetica can render."""
    text = "" if value is None else str(value)
    for bad, good in _REPLACEMENTS.items():
        text = text.replace(bad, good)
    # Anything still outside Latin-1 becomes '?' instead of crashing
    return text.encode("latin-1", "replace").decode("latin-1")


def build_assessment_pdf(patient_data: Dict[str, Any], result: Dict[str, Any]) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    def reset_x():
        pdf.set_x(pdf.l_margin)

    def title(text: str, size: int = 16):
        reset_x()
        pdf.set_font("Helvetica", "B", size)
        pdf.cell(0, 10, safe(text))
        pdf.ln(10)
        reset_x()

    def section(text: str):
        reset_x()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, safe(text))
        pdf.ln(10)
        reset_x()
        pdf.set_font("Helvetica", "", 11)

    def line(label: str, value: Any):
        reset_x()
        pdf.multi_cell(0, 7, safe(f"{label}: {value}"))
        reset_x()

    def paragraph(text: str):
        reset_x()
        pdf.multi_cell(0, 7, safe(text))
        reset_x()

    def bold_line(text: str):
        reset_x()
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(0, 7, safe(text))
        reset_x()
        pdf.set_font("Helvetica", "", 11)

    title("MedAgentX - Patient Assessment Summary")

    pdf.set_font("Helvetica", "", 10)
    line("Generated", datetime.now().strftime("%Y-%m-%d %H:%M"))
    pdf.ln(4)

    section("Patient Details")
    line("Age", patient_data.get("age"))
    line("Sex", patient_data.get("sex"))
    line("Duration (days)", patient_data.get("duration_days"))
    line("Severity", patient_data.get("severity"))
    line("Progression", patient_data.get("progression"))
    line("Reported symptoms", ", ".join(patient_data.get("symptoms", [])))
    if patient_data.get("history"):
        line("Medical history", patient_data["history"])
    pdf.ln(3)

    if result.get("status") == "URGENT":
        section("Urgent Safety Alert")
        line("Flag", result.get("flag"))
        line("Severity", result.get("severity"))
        line("Action", result.get("action"))
        line("Message", result.get("message"))
    else:
        assessment = result.get("assessment", {})
        risk = result.get("risk", {})

        section("Assessment Summary")
        paragraph(assessment.get("patient_summary", ""))
        pdf.ln(2)

        section("Possible Conditions")
        for cond in assessment.get("possible_conditions", []):
            bold_line(cond.get("condition", ""))
            paragraph(cond.get("explanation", ""))
            pdf.ln(1)

        section("Evidence")
        for ev in assessment.get("evidence", []):
            bold_line(f"Source: {ev.get('source', '')}")
            paragraph(ev.get("explanation", ""))
            pdf.ln(1)

        section("Risk Assessment")
        line("Risk level", risk.get("risk_level"))
        line("Urgency", risk.get("urgency"))

        if assessment.get("disclaimer"):
            pdf.ln(3)
            reset_x()
            pdf.set_font("Helvetica", "I", 9)
            paragraph(assessment["disclaimer"])

    return bytes(pdf.output())