from __future__ import annotations

from datetime import date

from apps.tests.base import TestContext
from apps.tests.registry import get_test_module


class TestReportPayloadService:
    @staticmethod
    def _patient_age(application) -> int:
        patient = getattr(getattr(application, "evaluation", None), "patient", None)
        birth_date = getattr(patient, "birth_date", None)
        if not birth_date:
            return 0
        reference_date = application.applied_on or getattr(application.evaluation, "start_date", None) or getattr(application.evaluation, "end_date", None) or date.today()
        years = reference_date.year - birth_date.year
        if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
            years -= 1
        return max(years, 0)

    @classmethod
    def build_for_application(cls, application) -> dict:
        module = get_test_module(application.instrument.code)
        merged_payload = {
            **(application.computed_payload or {}),
            **(application.classified_payload or {}),
        }
        context = TestContext(
            patient_name=application.evaluation.patient.full_name,
            evaluation_id=application.evaluation_id,
            instrument_code=application.instrument.code,
            patient_age=cls._patient_age(application),
            raw_scores=application.raw_payload or {},
            reviewed_scores=application.reviewed_payload or {},
            computed_scores=application.computed_payload or {},
            classification=application.classified_payload or {},
        )

        report_payload = {}
        if module and hasattr(module, "build_report_payload"):
            try:
                report_payload = module.build_report_payload(context, merged_payload) or {}
            except TypeError:
                try:
                    report_payload = module.build_report_payload(merged_payload) or {}
                except Exception:
                    report_payload = {}
            except Exception:
                report_payload = {}

        summary = (report_payload.get("summary_for_report") or "").strip()
        interpretation = (application.interpretation_text or "").strip()
        if not summary and interpretation:
            summary = interpretation.split(". ")[0].strip()

        return {
            "test_code": application.instrument.code,
            "test_name": application.instrument.name,
            "domain": application.instrument.category or "geral",
            "application_id": application.id,
            "status": application.status,
            "applied_on": application.applied_on.isoformat() if application.applied_on else None,
            "raw_payload": application.raw_payload or {},
            "computed_payload": application.computed_payload or {},
            "classified_payload": application.classified_payload or {},
            "interpretation": interpretation,
            "summary_for_report": summary,
            "results": report_payload.get("results") or cls._fallback_results(application),
            "clinical_flags": report_payload.get("clinical_flags") or [],
            "chart_payload": report_payload.get("chart_payload") or {},
            "technical_notes": report_payload.get("technical_notes") or [],
        }

    @staticmethod
    def _fallback_results(application) -> list[dict]:
        classified = application.classified_payload or {}
        computed = application.computed_payload or {}
        payload = classified or computed
        rows: list[dict] = []

        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(value, dict):
                    item = {"scale": key}
                    for field in (
                        "raw_score",
                        "escore_bruto",
                        "score",
                        "valor",
                        "percentile",
                        "percentil",
                        "classification",
                        "classificacao",
                    ):
                        if field in value and value[field] not in (None, ""):
                            item[field] = value[field]
                    if len(item) > 1:
                        rows.append(item)
                elif isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                    for nested in value[:12]:
                        label = (
                            nested.get("nome")
                            or nested.get("name")
                            or nested.get("subteste")
                            or nested.get("indice")
                            or key
                        )
                        item = {"scale": label}
                        for field in (
                            "raw_score",
                            "escore_bruto",
                            "escore_padrao",
                            "escore_composto",
                            "percentile",
                            "percentil",
                            "classification",
                            "classificacao",
                        ):
                            if field in nested and nested[field] not in (None, ""):
                                item[field] = nested[field]
                        if len(item) > 1:
                            rows.append(item)

        return rows
