from __future__ import annotations

import json
import re

from apps.ai.services.text_generation_service import TextGenerationService
from .section_context_service import SectionContextService


class ClinicalConsistencyAuditService:
    PROMPT_NAME = "reports/consistency_audit_prompt.txt"

    @classmethod
    def audit_report(cls, report, context: dict) -> dict:
        from .report_approval_service import ReportApprovalService

        source_sha256 = ReportApprovalService.fingerprint(report)
        payload = cls._build_audit_payload(report, context)
        result = cls._call_ai(payload)
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
        return normalized

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
            return payload
        alerts = payload.get("alerts")
        if not isinstance(alerts, list):
            return cls._invalid_result()
        normalized_alerts = []
        for item in alerts:
            if not isinstance(item, dict):
                return cls._invalid_result()
            severity = str(item.get("severity") or "").lower()
            if severity not in {"high", "medium", "low"}:
                return cls._invalid_result()
            if not isinstance(item.get("issue"), str) or not item["issue"].strip():
                return cls._invalid_result()
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
            return ClinicalConsistencyAuditService._invalid_result()
        try:
            payload = json.loads(text)
            return payload if isinstance(payload, dict) else ClinicalConsistencyAuditService._invalid_result()
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return ClinicalConsistencyAuditService._invalid_result()
            try:
                payload = json.loads(match.group(0))
                return payload if isinstance(payload, dict) else ClinicalConsistencyAuditService._invalid_result()
            except json.JSONDecodeError:
                return ClinicalConsistencyAuditService._invalid_result()

    @staticmethod
    def _invalid_result() -> dict:
        return {
            "status": "error",
            "alerts": [{
                "severity": "high", "section_key": "geral",
                "issue": "A auditoria retornou dados vazios ou inválidos.",
                "suggestion": "Execute novamente a auditoria antes de aprovar o laudo.",
            }],
        }
