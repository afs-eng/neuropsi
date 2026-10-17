import re

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

ReviewText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=1500)]


class SupportedFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    statement: str = Field(min_length=10, max_length=2000)
    evidence_ids: list[str] = Field(min_length=1, max_length=30)

    @field_validator("statement")
    @classmethod
    def nonempty_statement(cls, value):
        if not value.strip():
            raise ValueError("Achado sem texto.")
        return value


class SpecialistOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    findings: list[SupportedFinding] = Field(min_length=1, max_length=15)
    limitations: list[ReviewText] = Field(min_length=1, max_length=10)
    review_questions: list[ReviewText] = Field(default_factory=list, max_length=10)


def validate_evidence(output: SpecialistOutput, facts: dict, instrument_code: str = "") -> None:
    for finding in output.findings:
        if any(evidence_id not in facts for evidence_id in finding.evidence_ids):
            raise ValueError("O especialista citou evidência inexistente.")
        evidence_text = " ".join(str(facts[key]) for key in finding.evidence_ids)
        allowed_numbers = set(re.findall(r"-?\d+(?:[.,]\d+)?", evidence_text.replace(",", ".")))
        statement = finding.statement
        for code, label in (("bpa2", "BPA-2"), ("srs2", "SRS-2")):
            if instrument_code == code:
                statement = re.sub(re.escape(label), "instrumento", statement, flags=re.IGNORECASE)
        stated_numbers = set(re.findall(r"-?\d+(?:[.,]\d+)?", statement.replace(",", ".")))
        if not stated_numbers.issubset(allowed_numbers):
            raise ValueError("O achado contém número sem suporte nas evidências citadas.")
