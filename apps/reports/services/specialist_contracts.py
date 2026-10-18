import re

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from .bpa2_specialist import BPA2_SECTIONS, validate_bpa2_findings

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


class BPA2Finding(SupportedFinding):
    section: Literal["introducao", "ac", "ad", "aa", "ag", "analise_clinica"]


class BPA2SpecialistOutput(SpecialistOutput):
    findings: list[BPA2Finding] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def ordered_sections(self):
        if tuple(finding.section for finding in self.findings) != BPA2_SECTIONS:
            raise ValueError("BPA-2 exige introdução, AC, AD, AA, AG e análise clínica, nessa ordem.")
        return self


def specialist_output_model(instrument_code: str):
    return BPA2SpecialistOutput if instrument_code == "bpa2" else SpecialistOutput


def validate_evidence(output: SpecialistOutput, facts: dict, instrument_code: str = "") -> None:
    if instrument_code == "bpa2":
        output = BPA2SpecialistOutput.model_validate(output.model_dump())
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
    if instrument_code == "bpa2":
        validate_bpa2_findings(output, facts)
