from __future__ import annotations

from django.utils import timezone

from apps.evaluations.models import EvaluationStatus
from apps.reports.models import Report, ReportSection, ReportStatus
from apps.reports.services.clinical_consistency_audit_service import (
    ClinicalConsistencyAuditService,
)
from apps.reports.services.report_generation_service import ReportGenerationService
from apps.reports.services.report_review_service import ReportReviewService
from apps.reports.services.report_section_service import ReportSectionService
from apps.reports.services.report_version_service import ReportVersionService
from .section_registry import get_section_config
from .section_workflow_service import SectionWorkflowService


class ReportPipelineService:
    @classmethod
    def generate_full_report(cls, report: Report, context: dict, user=None) -> dict:
        report.status = ReportStatus.GENERATING
        report.context_payload = context

        if not report.interested_party:
            report.interested_party = (context.get("patient") or {}).get("full_name") or ""
        if not report.purpose:
            evaluation = context.get("evaluation") or {}
            report.purpose = (
                evaluation.get("evaluation_purpose")
                or evaluation.get("referral_reason")
                or "Auxílio diagnóstico e planejamento clínico."
            )

        report.save(
            update_fields=[
                "status",
                "context_payload",
                "interested_party",
                "purpose",
                "updated_at",
            ]
        )

        generation_order = SectionWorkflowService.get_generation_order(context)
        result = cls.generate_sections(report, context, generation_order)
        audit_result = cls._run_final_audit(report, context)
        flagged_sections = sorted(
            {
                item.get("section_key")
                for item in (audit_result.get("alerts") or [])
                if item.get("section_key")
            }
        )

        report.generated_text = report.edited_text
        report.status = ReportStatus.IN_REVIEW
        report.generated_at = timezone.now()
        report.ai_metadata = {
            **(report.ai_metadata or {}),
            "generation_scope": "full",
            "mode": "hybrid"
            if result["ai_sections"] and result["fallback_sections"]
            else ("ai" if result["ai_sections"] else "deterministic"),
            "ai_sections": result["ai_sections"],
            "fallback_sections": result["fallback_sections"],
            "pipeline": {
                "generated_sections": result["generated_sections"],
                "failed_sections": result["failed_sections"],
                "flagged_sections": flagged_sections,
                "generation_order": generation_order,
                "generated_at": report.generated_at.isoformat(),
            },
            "audit": audit_result,
        }
        report.ai_metadata["review"] = ReportReviewService.review(report)
        report.save(
            update_fields=[
                "generated_text",
                "edited_text",
                "status",
                "generated_at",
                "ai_metadata",
                "updated_at",
            ]
        )

        if getattr(report, "evaluation", None):
            report.evaluation.status = EvaluationStatus.WRITING_REPORT
            report.evaluation.save(update_fields=["status"])

        ReportVersionService.create_version(report, user=user)
        result["flagged_sections"] = flagged_sections
        result["audit"] = audit_result
        return result

    @classmethod
    def generate_sections(
        cls, report: Report, context: dict, section_keys: list[str]
    ) -> dict:
        generated_sections: list[str] = []
        failed_sections: list[dict] = []
        ai_sections: list[str] = []
        fallback_sections: list[str] = []
        generated_set: set[str] = set()

        active_titles = {}
        for index, section_key in enumerate(section_keys, start=1):
            config = get_section_config(section_key)
            clean_title = config["title"].split(". ", 1)[1] if ". " in config["title"] else config["title"]
            active_titles[section_key] = f"{index}. {clean_title}"

        report.sections.exclude(key__in=section_keys).delete()

        for order, section_key in enumerate(section_keys):
            if not SectionWorkflowService.can_generate(section_key, generated_set):
                failed_sections.append(
                    {
                        "section_key": section_key,
                        "reason": "Dependências ainda não geradas.",
                    }
                )
                continue

            try:
                result = cls._generate_single_section(report, section_key, context)
                provider = (result.get("metadata") or {}).get("provider")
                if provider in {"ollama", "openai", "anthropic"}:
                    ai_sections.append(section_key)
                else:
                    fallback_sections.append(section_key)
                cls._save_section_result(
                    report,
                    section_key,
                    active_titles[section_key],
                    order,
                    result,
                )
                generated_sections.append(section_key)
                generated_set.add(section_key)
            except Exception as exc:
                failed_sections.append(
                    {
                        "section_key": section_key,
                        "reason": str(exc),
                    }
                )

        ReportSectionService._rebuild_report_text(report)
        return {
            "generated_sections": generated_sections,
            "failed_sections": failed_sections,
            "ai_sections": ai_sections,
            "fallback_sections": fallback_sections,
        }

    @classmethod
    def _run_final_audit(cls, report: Report, context: dict) -> dict:
        try:
            return ClinicalConsistencyAuditService.audit_report(report, context)
        except Exception as exc:
            return {
                "status": "error",
                "alerts": [
                    {
                        "severity": "medium",
                        "section_key": "geral",
                        "issue": f"Falha ao executar auditoria clínica automatizada: {exc}",
                        "suggestion": "Revisar o laudo manualmente ou tentar novamente a auditoria.",
                    }
                ],
                "metadata": {},
            }

    @classmethod
    def _generate_single_section(cls, report: Report, section_key: str, context: dict) -> dict:
        content, metadata, warnings = ReportGenerationService._generate_section_payload(
            report, section_key, context
        )
        return {
            "content": content,
            "warnings": warnings,
            "metadata": metadata,
        }

    @classmethod
    def _save_section_result(
        cls,
        report: Report,
        section_key: str,
        title: str,
        order: int,
        result: dict,
    ) -> None:
        content = result.get("content") or ""
        metadata = result.get("metadata") or {}
        warnings = result.get("warnings") or []
        section, created = ReportSection.objects.get_or_create(
            report=report,
            key=section_key,
            defaults={
                "title": title,
                "order": order,
            },
        )

        previous_generated = section.content_generated
        previous_edited = section.content_edited

        section.title = title
        section.order = order
        section.content_generated = content
        section.generation_metadata = metadata
        section.warnings_payload = warnings
        if created or previous_edited == previous_generated:
            section.content_edited = content

        section.save(
            update_fields=[
                "title",
                "order",
                "content_generated",
                "content_edited",
                "generation_metadata",
                "warnings_payload",
                "updated_at",
            ]
        )
