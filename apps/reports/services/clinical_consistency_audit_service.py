from __future__ import annotations

import json
import logging
import re

import requests

from apps.ai.services.text_generation_service import TextGenerationService
from .section_context_service import SectionContextService

logger = logging.getLogger(__name__)


class ClinicalConsistencyAuditService:
    PROMPT_NAME = "reports/consistency_audit_prompt.txt"
    ERROR_MESSAGES = {
        "empty_response": "O provedor de IA retornou uma resposta vazia para a auditoria.",
        "invalid_json": "A IA não retornou um JSON válido para a auditoria.",
        "invalid_schema": "A resposta da IA não seguiu o formato obrigatório da auditoria.",
        "truncated_response": "A resposta da auditoria foi interrompida pelo limite de tokens. A análise não foi concluída.",
        "provider_refusal": "O provedor de IA bloqueou a resposta da auditoria.",
        "provider_timeout": "O provedor de IA excedeu o tempo de resposta da auditoria.",
        "provider_rate_limit": "O provedor de IA informou limite de uso ou indisponibilidade de capacidade.",
        "provider_auth": "O provedor de IA recusou as credenciais ou informou falta de créditos/permissão.",
        "provider_error": "Não foi possível executar a auditoria no provedor de IA configurado.",
        "internal_error": "Não foi possível processar a auditoria. Consulte o diagnóstico técnico nos logs do backend.",
    }

    @classmethod
    def audit_report(cls, report, context: dict) -> dict:
        from .report_approval_service import ReportApprovalService

        source_sha256 = ReportApprovalService.fingerprint(report)
        payload = cls._build_audit_payload(report, context)
        try:
            result = cls._call_ai(payload)
        except Exception as exc:
            normalized = cls._invalid_result(cls._provider_error_code(exc))
            normalized["source_sha256"] = source_sha256
            cls._log_failure(normalized)
            return normalized
        if not isinstance(result, dict):
            result = {}
        finish_reason = str(result.get("finish_reason") or "").lower()
        if finish_reason in {"length", "max_tokens"}:
            normalized = cls._invalid_result("truncated_response")
        elif finish_reason in {"content_filter", "refusal"}:
            normalized = cls._invalid_result("provider_refusal")
        else:
            normalized = cls._normalize_audit_result(result.get("content") or "")
        normalized["metadata"] = {
            "provider": result.get("provider"),
            "model": result.get("model"),
            "finish_reason": result.get("finish_reason"),
            "usage": result.get("usage") or {},
            "warnings": result.get("warnings") or [],
            "prompt_name": cls.PROMPT_NAME,
        }
        normalized["status"] = normalized.get("status") or ("flagged" if normalized["alerts"] else "ok")
        normalized["source_sha256"] = source_sha256
        if normalized["status"] == "error":
            cls._log_failure(normalized)
        return normalized

    @staticmethod
    def _provider_error_code(exc: Exception) -> str:
        cause = exc
        visited = set()
        while cause is not None and id(cause) not in visited:
            visited.add(id(cause))
            if isinstance(cause, requests.Timeout):
                return "provider_timeout"
            status = getattr(getattr(cause, "response", None), "status_code", None)
            if status == 429:
                return "provider_rate_limit"
            if status in {401, 402, 403}:
                return "provider_auth"
            # O serviço legado encapsula alguns erros HTTP em ValueError.
            message = str(cause).lower()
            if any(token in message for token in ("rate limit", "rate-limit", "http 429", "capacity")):
                return "provider_rate_limit"
            if any(token in message for token in ("http 401", "http 402", "http 403", "invalid api key", "insufficient credits")):
                return "provider_auth"
            cause = cause.__cause__
        return "provider_error"

    @staticmethod
    def _log_failure(result: dict):
        metadata = result.get("metadata") or {}
        # Não registrar prompts, textos clínicos, resposta bruta ou mensagens de exceção.
        logger.warning(
            "clinical_audit_failed code=%s provider=%s model=%s finish_reason=%s",
            result.get("error_code"), metadata.get("provider"),
            metadata.get("model"), metadata.get("finish_reason"),
        )

    @classmethod
    def _build_audit_payload(cls, report, context: dict) -> dict:
        return SectionContextService.build_for_audit(report, context)

    @classmethod
    def _call_ai(cls, payload: dict) -> dict:
        return TextGenerationService.generate_from_prompt(
            prompt_name=cls.PROMPT_NAME,
            user_prompt=(
                "Audite a coerencia do laudo com base apenas nos dados abaixo. "
                "Retorne somente JSON valido.\n\n"
                f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
            ),
            timeout=1200,
            temperature=0.1,
            max_tokens=1400,
        )

    @classmethod
    def _normalize_audit_result(cls, content: str) -> dict:
        payload = cls._parse_json(content)
        if payload.get("status") == "error":
            error_code = payload.get("error_code")
            return cls._invalid_result(error_code if isinstance(error_code, str) and error_code in cls.ERROR_MESSAGES else "invalid_schema")
        alerts = payload.get("alerts")
        if not isinstance(alerts, list):
            return cls._invalid_result("invalid_schema")
        normalized_alerts = []
        for item in alerts:
            if not isinstance(item, dict):
                return cls._invalid_result("invalid_schema")
            severity = str(item.get("severity") or "").lower()
            if severity not in {"high", "medium", "low"}:
                return cls._invalid_result("invalid_schema")
            if not isinstance(item.get("issue"), str) or not item["issue"].strip():
                return cls._invalid_result("invalid_schema")
            normalized_alerts.append(
                {
                    "severity": severity,
                    "section_key": str(item.get("section_key") or "geral"),
                    "issue": str(item.get("issue") or "").strip(),
                    "suggestion": str(item.get("suggestion") or "").strip(),
                }
            )
        return {"alerts": [item for item in normalized_alerts if item["issue"]]}

    @staticmethod
    def _parse_json(content: str) -> dict:
        text = str(content or "").strip()
        if not text:
            return ClinicalConsistencyAuditService._invalid_result("empty_response")
        try:
            payload = json.loads(text)
            return payload if isinstance(payload, dict) else ClinicalConsistencyAuditService._invalid_result("invalid_schema")
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return ClinicalConsistencyAuditService._invalid_result("invalid_json")
            try:
                payload = json.loads(match.group(0))
                return payload if isinstance(payload, dict) else ClinicalConsistencyAuditService._invalid_result("invalid_schema")
            except json.JSONDecodeError:
                return ClinicalConsistencyAuditService._invalid_result("invalid_json")

    @staticmethod
    def _invalid_result(error_code: str = "internal_error") -> dict:
        return {
            "status": "error",
            "error_code": error_code,
            "alerts": [{
                "severity": "high", "section_key": "geral",
                "issue": ClinicalConsistencyAuditService.ERROR_MESSAGES[error_code],
                "suggestion": "Execute novamente a auditoria antes de aprovar o laudo.",
            }],
        }
