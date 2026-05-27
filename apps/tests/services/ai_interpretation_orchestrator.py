from __future__ import annotations

import json

from django.conf import settings

from apps.ai.services.prompt_registry_service import PromptRegistryService
from apps.ai.services.text_generation_service import TextGenerationService
from apps.tests.services.ai_interpretation_registry import TestAIInterpretationRegistry
from apps.tests.services.ai_interpretation_types import TestAIInterpretationDraft


class TestAIInterpretationOrchestrator:
    @classmethod
    def generate_for_application(cls, application, fallback: TestAIInterpretationDraft) -> TestAIInterpretationDraft:
        instrument_code = getattr(getattr(application, "instrument", None), "code", "")
        handler = TestAIInterpretationRegistry.get_handler(instrument_code)
        if not handler:
            return cls._with_fallback_metadata(fallback, reason="handler_unavailable")
        if not getattr(settings, "TEST_INTERPRETATION_AI_ENABLED", False):
            return cls._with_fallback_metadata(fallback, reason="feature_disabled")
        if not cls._provider_configured():
            return cls._with_fallback_metadata(fallback, reason="provider_unavailable")

        payload = handler.build_payload(application)
        skill_text = PromptRegistryService.read(handler.skill_path)
        try:
            result = TextGenerationService.generate_from_prompt(
                prompt_name=handler.prompt_name,
                user_prompt=cls._build_user_prompt(payload, fallback, skill_text),
                temperature=0.1,
                timeout=120,
                max_tokens=2200,
                feature="test_interpretation_agent",
                instrument=instrument_code,
            )
            response_payload = cls._parse_json_response(result.get("content") or "")
            errors = handler.validate_response(response_payload, payload)
            if errors:
                draft = cls._with_fallback_metadata(fallback, reason="validation_failed")
                draft.warnings.extend(errors)
                return draft

            draft = handler.normalize_response(response_payload, payload)
            draft.metadata.update(
                {
                    "generation_path": "ai",
                    "provider": result.get("provider"),
                    "model": result.get("model"),
                    "prompt_name": handler.prompt_name,
                    "skill_path": handler.skill_path,
                }
            )
            draft.warnings.extend(result.get("warnings") or [])
            return draft
        except Exception as exc:
            draft = cls._with_fallback_metadata(fallback, reason="generation_error")
            draft.warnings.append(str(exc))
            return draft

    @staticmethod
    def _with_fallback_metadata(fallback: TestAIInterpretationDraft, reason: str) -> TestAIInterpretationDraft:
        metadata = dict(fallback.metadata)
        metadata.update({"generation_path": "fallback", "fallback_reason": reason})
        return TestAIInterpretationDraft(
            clinical_paragraphs=list(fallback.clinical_paragraphs),
            clinical_box_text=fallback.clinical_box_text,
            summary_for_report=fallback.summary_for_report,
            metadata=metadata,
            warnings=list(fallback.warnings),
        )

    @staticmethod
    def _provider_configured() -> bool:
        provider = (getattr(settings, "AI_PROVIDER", "") or "").lower()
        if provider == "openai":
            return bool(getattr(settings, "OPENAI_API_KEY", ""))
        if provider == "anthropic":
            return bool(getattr(settings, "ANTHROPIC_API_KEY", ""))
        if provider == "ollama":
            return bool(getattr(settings, "OLLAMA_BASE_URL", ""))
        return False

    @staticmethod
    def _parse_json_response(content: str) -> dict:
        text = (content or "").strip()
        if text.startswith("```"):
            parts = text.split("```")
            text = next((part for part in parts if part.strip() and not part.strip().startswith("json")), text)
            text = text.removeprefix("json").strip()
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("A IA nao retornou um objeto JSON valido.")
        return payload

    @staticmethod
    def _build_user_prompt(payload: dict, fallback: TestAIInterpretationDraft, skill_text: str) -> str:
        contract = {
            "clinical_paragraphs": ["paragrafo_1", "paragrafo_2", "paragrafo_3", "paragrafo_4", "paragrafo_5"],
            "clinical_box_text": "texto do box clinico",
            "summary_for_report": "sintese para o laudo",
            "inconsistency_alerts": ["alerta opcional de incoerencia"],
        }
        return (
            "Use a skill clinica abaixo como fonte normativa principal do instrumento. "
            "Nao recalcule escores, nao invente classificacoes e nao contradiga os fatos estruturados. "
            "Retorne somente JSON valido, sem markdown, sem comentarios e sem texto extra.\n\n"
            f"Skill do instrumento:\n{skill_text}\n\n"
            "Contrato exato de saida JSON:\n"
            f"{json.dumps(contract, ensure_ascii=False, indent=2)}\n\n"
            "Fallback deterministico atual para referencia de estilo e seguranca:\n"
            f"{json.dumps({'clinical_paragraphs': fallback.clinical_paragraphs, 'clinical_box_text': fallback.clinical_box_text, 'summary_for_report': fallback.summary_for_report}, ensure_ascii=False, indent=2)}\n\n"
            "Fatos estruturados do caso:\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )
