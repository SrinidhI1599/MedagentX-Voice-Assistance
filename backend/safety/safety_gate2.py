def _system_generated_text(assessment: dict) -> str:
    """
    Text that the system itself wrote (patient_summary, condition labels,
    disclaimer). Deliberately EXCLUDES 'evidence', since that field holds
    verbatim excerpts from third-party medical reference sources, which
    routinely contain ordinary phrasing like 'if you have symptoms of...'
    that would otherwise false-trigger the checks below.
    """
    parts = [
        str(assessment.get("patient_summary", "")),
        str(assessment.get("disclaimer", "")),
    ]

    for condition in assessment.get("possible_conditions", []):
        if isinstance(condition, dict):
            parts.append(str(condition.get("condition", "")))
            parts.append(str(condition.get("explanation", "")))
        else:
            parts.append(str(condition))

    return " ".join(parts).lower()


def safety_gate2(assessment, risk_result):

    system_text = _system_generated_text(assessment)

    if "you have" in system_text:
        return {"safe": False}

    if "disclaimer" not in assessment:
        return {"safe": False}

    if risk_result["risk_level"] == "HIGH" and "low risk" in system_text:
        return {"safe": False}

    return {
        "safe": True,
        "assessment": assessment,
        "risk": risk_result
    }