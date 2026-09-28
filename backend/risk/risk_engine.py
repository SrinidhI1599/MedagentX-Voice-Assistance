def get_risk_level(patient) -> str:
    """
    Deterministic risk classification: LOW / MODERATE / HIGH
    
    Rules:
    - HIGH: Severe + Worsening OR Severe + >=7 days
    - MODERATE: Moderate + Worsening OR Moderate + >=7 days
    - LOW: Everything else
    """
    
    severity = patient.severity.value if hasattr(patient.severity, 'value') else patient.severity
    progression = patient.progression
    duration_days = patient.duration_days
    
    # High risk
    if severity == "Severe" and progression == "Worsening":
        return "HIGH"
    if severity == "Severe" and duration_days >= 7:
        return "HIGH"
    
    # Moderate risk
    if severity == "Moderate" and progression == "Worsening":
        return "MODERATE"
    if severity == "Moderate" and duration_days >= 7:
        return "MODERATE"
    
    # Low risk
    return "LOW"


def risk_engine(patient, llm_output: dict) -> dict:
    """
    Risk engine wrapper - returns detailed risk assessment.
    """
    risk_level = get_risk_level(patient)
    
    urgency_map = {"HIGH": "urgent", "MODERATE": "priority", "LOW": "routine"}
    
    return {
        "risk_level": risk_level,
        "urgency": urgency_map[risk_level]
    }