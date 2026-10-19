import re

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, create_model, field_validator, model_validator

from .bpa2_specialist import BPA2_SECTIONS, validate_bpa2_findings
from .specialist_errors import SpecialistValidationError
from .self_report_specialists import SELF_REPORT_VERSIONS, self_report_reading_guide, validate_self_report_findings

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


class SelfReportFinding(SupportedFinding):
    scale_codes: list[str] = Field(min_length=1, max_length=22)


class SelfReportSpecialistOutput(SpecialistOutput):
    findings: list[SelfReportFinding] = Field(min_length=2, max_length=5)


def specialist_output_model(instrument_code: str):
    if instrument_code in SELF_REPORT_VERSIONS:
        return SelfReportSpecialistOutput
    return BPA2SpecialistOutput if instrument_code == "bpa2" else SpecialistOutput


def bpa2_generation_model(facts: dict):
    """Restringe o schema nativo aos IDs da aplicação, sem cache entre pacientes.

    O enum orienta a geração; provedores que ignoram o schema ainda passam pelo
    validate_evidence. Nunca converter referências desconhecidas em IDs válidos.
    """
    if not facts:
        raise ValueError("BPA-2 sem evidências para geração.")
    finding = create_model(
        "BPA2GroundedFinding", __base__=BPA2Finding,
        evidence_ids=(list[str], Field(
            min_length=1, max_length=30,
            description=(
                "Copie IDs exatos de facts; não cite caminhos do reading_guide nem nomes de componentes. "
                "Para esta section, inclua TODOS os required_ids de section_evidence_requirements "
                "e UM score_one_of quando não vazio. Na analise_clinica, cite as quatro modalidades."
            ),
            json_schema_extra={"items": {"type": "string", "enum": sorted(facts)}},
        )),
    )
    return create_model(
        "BPA2GroundedOutput", __base__=BPA2SpecialistOutput,
        findings=(list[finding], Field(min_length=6, max_length=6)),
    )


def self_report_generation_model(instrument_code: str, facts: dict):
    dimensions = self_report_reading_guide(instrument_code, facts)["dimensions"]
    finding = create_model(
        "SelfReportGroundedFinding", __base__=SelfReportFinding,
        evidence_ids=(list[str], Field(
            min_length=1, max_length=30,
            description="Copie apenas IDs exatos de facts, incluindo as classificações das dimensões abordadas.",
            json_schema_extra={"items": {"type": "string", "enum": sorted(facts)}},
        )),
        scale_codes=(list[str], Field(
            min_length=1, max_length=len(dimensions),
            json_schema_extra={"items": {"type": "string", "enum": sorted(dimensions)}},
        )),
    )
    return create_model(
        "SelfReportGroundedOutput", __base__=SelfReportSpecialistOutput,
        findings=(list[finding], Field(min_length=2, max_length=5)),
    )


def validate_evidence(output: SpecialistOutput, facts: dict, instrument_code: str = "") -> None:
    if instrument_code == "bpa2":
        output = BPA2SpecialistOutput.model_validate(output.model_dump())
    for finding in output.findings:
        if any(evidence_id not in facts for evidence_id in finding.evidence_ids):
            raise SpecialistValidationError("evidence_not_found", "O especialista citou evidência inexistente.")
        evidence_text = " ".join(str(facts[key]) for key in finding.evidence_ids)
        allowed_numbers = set(re.findall(r"-?\d+(?:[.,]\d+)?", evidence_text.replace(",", ".")))
        statement = finding.statement
        for code, label in (("bpa2", "BPA-2"), ("srs2", "SRS-2")):
            if instrument_code == code:
                statement = re.sub(re.escape(label), "instrumento", statement, flags=re.IGNORECASE)
        stated_numbers = set(re.findall(r"-?\d+(?:[.,]\d+)?", statement.replace(",", ".")))
        if not stated_numbers.issubset(allowed_numbers):
            raise SpecialistValidationError("ungrounded_number", "O achado contém número sem suporte nas evidências citadas.")
    if instrument_code == "bpa2":
        validate_bpa2_findings(output, facts)
    elif instrument_code in SELF_REPORT_VERSIONS:
        validate_self_report_findings(SelfReportSpecialistOutput.model_validate(output.model_dump()), facts, instrument_code)
