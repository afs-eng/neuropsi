import hashlib
import json

from .specialist_registry import get_specialist


class SpecialistPlanningService:
    @staticmethod
    def build_plan(context: dict) -> dict:
        applications = []
        for test in context.get("validated_tests") or []:
            if test.get("is_validated") is not True:
                continue
            code = test.get("instrument_code") or ""
            specialist = get_specialist(code)
            source = {
                key: test.get(key)
                for key in (
                    "id", "instrument_code", "applied_on", "computed_payload",
                    "classified_payload", "structured_results", "report_payload",
                    "raw_payload", "respondent_name",
                )
            }
            # O paciente/avaliação integra a chave para impedir reuso entre casos.
            source["patient"] = context.get("patient") or {}
            source["evaluation"] = context.get("evaluation") or {}
            fingerprint = hashlib.sha256(
                json.dumps(source, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
            ).hexdigest()
            applications.append({
                "application_id": test.get("id"),
                "instrument_code": code,
                "specialist": specialist.name if specialist else None,
                "specialist_version": specialist.version if specialist else None,
                "source_sha256": fingerprint,
                "status": "requires_clinical_configuration" if specialist else "unsupported",
            })
        return {"mode": "planning_only", "applications": applications, "execution_enabled": False}
