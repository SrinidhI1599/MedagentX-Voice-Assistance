def check_red_flags(patient):
    symptoms = " ".join(patient.symptoms).lower()

    # Chest pain
    if "chest pain" in symptoms:
        return {
            "flag": "CHEST_PAIN",
            "severity": "CRITICAL",
            "action": "CALL_EMERGENCY",
            "message": "Patient reports chest pain - requires immediate emergency evaluation"
        }

    # Severe breathing difficulty
    if "severe breathing" in symptoms or "struggling to breathe" in symptoms:
        return {
            "flag": "SEVERE_BREATHING",
            "severity": "CRITICAL",
            "action": "CALL_EMERGENCY",
            "message": "Patient has severe breathing difficulty - requires immediate medical attention"
        }

    # Unconsciousness
    if "unconscious" in symptoms or "loss of consciousness" in symptoms:
        return {
            "flag": "UNCONSCIOUS",
            "severity": "CRITICAL",
            "action": "CALL_EMERGENCY",
            "message": "Patient is unconscious - requires immediate emergency intervention"
        }

    # Severe bleeding
    if "severe bleeding" in symptoms:
        return {
            "flag": "SEVERE_BLEEDING",
            "severity": "CRITICAL",
            "action": "CALL_EMERGENCY",
            "message": "Patient has severe bleeding - requires immediate emergency care"
        }

    # Severe allergic reaction
    if "anaphylaxis" in symptoms or "severe allergic" in symptoms:
        return {
            "flag": "ANAPHYLAXIS",
            "severity": "CRITICAL",
            "action": "CALL_EMERGENCY",
            "message": "Patient shows signs of a severe allergic reaction"
        }

    # Stroke symptoms
    stroke_keywords = [
        "facial drooping",
        "arm weakness",
        "speech difficulty",
        "sudden confusion"
    ]

    matches = [keyword for keyword in stroke_keywords if keyword in symptoms]

    if matches:
        return {
            "flag": "STROKE_SYMPTOMS",
            "severity": "CRITICAL",
            "action": "CALL_EMERGENCY",
            "message": "Patient shows possible stroke symptoms"
        }

    # Severe abdominal pain
    if "severe abdominal pain" in symptoms:
        return {
            "flag": "SEVERE_ABDOMINAL_PAIN",
            "severity": "HIGH",
            "action": "CALL_EMERGENCY",
            "message": "Patient has severe abdominal pain"
        }

    # Poisoning / overdose
    if "poisoning" in symptoms or "overdose" in symptoms:
        return {
            "flag": "POISONING_OVERDOSE",
            "severity": "CRITICAL",
            "action": "CALL_EMERGENCY",
            "message": "Possible poisoning or overdose requires immediate medical attention"
        }

    return None