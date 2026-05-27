from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class TestAIInterpretationDraft:
    clinical_paragraphs: list[str]
    clinical_box_text: str
    summary_for_report: str
    metadata: dict[str, object] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class TestAIInterpretationHandler(Protocol):
    instrument_code: str
    prompt_name: str
    skill_path: str

    def build_payload(self, application) -> dict:
        ...

    def validate_response(self, response: dict, payload: dict) -> list[str]:
        ...

    def normalize_response(self, response: dict, payload: dict) -> TestAIInterpretationDraft:
        ...
