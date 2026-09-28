from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"


class PatientIntake(BaseModel):
    age: int = Field(ge=0, le=120)
    sex: str
    symptoms: List[str]
    duration_days: int = Field(ge=0, le=90)
    severity: Severity
    progression: str
    consent: bool

    @field_validator("symptoms")
    @classmethod
    def symptoms_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one symptom is required")
        return v

    @field_validator("consent")
    @classmethod
    def consent_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Consent is required to proceed")
        return v