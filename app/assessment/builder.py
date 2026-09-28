class AssessmentBuilder:

    def build(self, patient_data: dict, llm_output: dict, risk_result: dict) -> dict:
        return {
            "age": patient_data["age"],
            "sex": patient_data["sex"],
            "symptoms": patient_data["symptoms"],
            "duration_days": patient_data["duration_days"],
            "severity": patient_data["severity"],
            "progression": patient_data["progression"],
            "patient_summary": llm_output.get("patient_summary"),
            "possible_conditions": llm_output.get("possible_conditions", []),
            "evidence": llm_output.get("evidence", []),
            "risk_level": risk_result["risk_level"],
            "urgency": risk_result["urgency"],
            "disclaimer": (
                "This tool does not provide medical diagnoses "
                "and is not a substitute for professional medical advice."
            )
        }