from dataclasses import dataclass, field
from typing import Any, Optional, Protocol
from datetime import date


class BaseTestModule:
    code: str = ""
    name: str = ""

    def validate(self, context: "TestContext") -> list[str]:
        return []

    def compute(self, context: "TestContext") -> dict[str, Any]:
        return {}

    def classify(self, computed_data: dict[str, Any]) -> dict[str, Any]:
        return {}

    def interpret(self, context: "TestContext", merged_data: dict[str, Any]) -> str:
        return ""

    def build_report_payload(
        self, context: "TestContext", merged_data: dict[str, Any]
    ) -> dict[str, Any]:
        interpretation = self.interpret(context, merged_data)
        summary = interpretation.split(". ")[0].strip() if interpretation else ""
        return {
            "results": [],
            "summary_for_report": summary,
            "technical_notes": [],
            "clinical_flags": [],
            "chart_payload": {},
        }


@dataclass
class TestContext:
    patient_name: str
    evaluation_id: int
    instrument_code: str
    patient_age: int = 0
    patient_education: Optional[int] = None
    raw_scores: dict[str, Any] = field(default_factory=dict)
    reviewed_scores: dict[str, Any] = field(default_factory=dict)
    computed_scores: dict[str, Any] = field(default_factory=dict)
    classification: dict[str, Any] = field(default_factory=dict)


@dataclass
class RawScoreInput:
    raw_score: Optional[float] = None
    raw_responses: Optional[list] = None
    raw_times: Optional[dict] = None
    raw_answers: Optional[dict] = None


@dataclass
class ComputedScore:
    score: float
    age_group: str
    education_group: Optional[str] = None
    percentile: Optional[float] = None
    grade_equivalent: Optional[str] = None
    supplementary_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class ClassificationResult:
    classification: str
    level: str
    description: str
    severity: Optional[str] = None


@dataclass
class InterpretationResult:
    text: str
    recommendations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class InstrumentConfig:
    code: str
    name: str
    version: str
    age_range_min: int
    age_range_max: int
    requires_education: bool = False
    categories: list[str] = field(default_factory=list)


class TestCalculator(Protocol):
    def calculate(
        self, raw_data: dict, age: int, education: Optional[int] = None
    ) -> ComputedScore: ...


class TestClassifier(Protocol):
    def classify(self, computed: ComputedScore) -> ClassificationResult: ...


class TestInterpreter(Protocol):
    def interpret(
        self, computed: ComputedScore, classification: ClassificationResult
    ) -> InterpretationResult: ...


class AgeGroup:
    @staticmethod
    def calculate(age: int, instrument_code: str) -> str:
        if instrument_code == "wisc4":
            if age < 7:
                return "6-6"
            elif age < 9:
                return "7-8"
            elif age < 11:
                return "9-10"
            elif age < 13:
                return "11-12"
            elif age < 15:
                return "13-14"
            else:
                return "15-16"
        elif instrument_code == "bpa2":
            if age < 20:
                return "18-19"
            elif age < 30:
                return "20-29"
            elif age < 40:
                return "30-39"
            elif age < 50:
                return "40-49"
            elif age < 60:
                return "50-59"
            else:
                return "60+"
        elif instrument_code == "fdt":
            if age < 10:
                return "5-9"
            elif age < 20:
                return "10-19"
            elif age < 40:
                return "20-39"
            elif age < 60:
                return "40-59"
            else:
                return "60+"
        return f"{age}"


class EducationGroup:
    @staticmethod
    def calculate(education_years: int, instrument_code: str) -> str:
        if instrument_code in ["wisc4", "ebaped_ij", "epq_j"]:
            if education_years <= 4:
                return "1-4"
            elif education_years <= 8:
                return "5-8"
            elif education_years <= 11:
                return "9-11"
            else:
                return "12+"
        return "default"
