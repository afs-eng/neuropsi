from __future__ import annotations

from django.utils import timezone

from apps.ai.services.ai_healthcheck_service import AIHealthcheckService
from apps.reports.builders.snapshot_builder import build_report_snapshot
from apps.reports.models import Report, ReportStatus
from apps.reports.services.report_pipeline_service import ReportPipelineService
from apps.reports.services.report_section_service import ReportSectionService
from apps.reports.services.report_version_service import ReportVersionService
from .section_workflow_service import SectionWorkflowService
from .report_ai_service import ReportAIService
from .section_registry import get_section_config, list_section_configs


class SectionRegenerationService:
    @staticmethod
    def _validated_codes(context: dict) -> set[str]:
        return {
            item.get("instrument_code")
            for item in (context.get("validated_tests") or [])
            if item.get("instrument_code")
        }

    @classmethod
    def _enabled_test_section_keys(cls, context: dict) -> list[str]:
        validated_codes = cls._validated_codes(context)
        enabled_keys: list[str] = []
        for section_key, config in list_section_configs():
            if config.get("kind") != "test":
                continue
            required_codes = set(config.get("required_any_codes") or ())
            if required_codes and not (required_codes & validated_codes):
                continue
            enabled_keys.append(section_key)
        return enabled_keys

    @classmethod
    def _regenerate_section_in_place(
        cls,
        report: Report,
        section_key: str,
        context: dict,
        *,
        ensure_ai_available: bool = True,
    ):
        section = report.sections.filter(key=section_key).first()
        if not section or section.is_locked:
            return None

        config = get_section_config(section_key)
        title = section.title or config["title"]
        order = section.order if section.order is not None else config.get("order", 0)

        result = ReportPipelineService._generate_single_section(report, section_key, context)
        ReportPipelineService._save_section_result(
            report,
            section_key,
            title,
            order,
            result,
        )

        cls.mark_dependents_stale(report, section_key)
        regenerated = report.sections.filter(key=section_key).first()
        generation_metadata = regenerated.generation_metadata or {}
        generation_metadata = {
            **generation_metadata,
            "generated_at": timezone.now().isoformat(),
            "stale": False,
            "stale_dependencies": [],
        }
        regenerated.generation_metadata = generation_metadata
        regenerated.save(update_fields=["generation_metadata", "updated_at"])
        return regenerated

    @classmethod
    def regenerate_section(
        cls, report: Report, section_key: str, context: dict | None = None, user=None
    ):
        context = context or build_report_snapshot(report.evaluation)
        report.context_payload = context
        report.save(update_fields=["context_payload", "updated_at"])

        regenerated = cls._regenerate_section_in_place(report, section_key, context)
        if not regenerated:
            return None
        generation_metadata = regenerated.generation_metadata or {}

        report.ai_metadata = {
            **(report.ai_metadata or {}),
            "last_generation": generation_metadata,
            "stale_sections": [
                item.key
                for item in report.sections.all()
                if (item.generation_metadata or {}).get("stale")
            ],
        }
        report.save(update_fields=["ai_metadata", "updated_at"])
        ReportSectionService._rebuild_report_text(report)
        ReportVersionService.create_version(report, user=user)
        return regenerated

    @classmethod
    def regenerate_test_sections(
        cls,
        report: Report,
        context: dict | None = None,
        user=None,
        scope: str | None = None,
    ) -> list[str]:
        context = context or build_report_snapshot(report.evaluation)
        report.status = ReportStatus.GENERATING
        report.context_payload = context
        report.save(update_fields=["status", "context_payload", "updated_at"])

        section_keys = cls._enabled_test_section_keys(context)
        enabled_key_set = set(section_keys)
        existing_test_sections = [
            section
            for section in report.sections.all()
            if get_section_config(section.key).get("kind") == "test"
        ]
        for section in existing_test_sections:
            if section.key in enabled_key_set:
                continue
            if section.is_locked:
                continue
            section.delete()

        existing_keys = {section.key for section in report.sections.all()}
        for section_key in section_keys:
            if section_key in existing_keys:
                continue
            config = get_section_config(section_key)
            report.sections.create(
                key=section_key,
                title=config["title"],
                order=config.get("order", 0),
            )

        regenerated_keys: list[str] = []
        for section_key in section_keys:
            regenerated = cls._regenerate_section_in_place(
                report,
                section_key,
                context,
                ensure_ai_available=False,
            )
            if regenerated:
                regenerated_keys.append(section_key)

        report.ai_metadata = {
            **(report.ai_metadata or {}),
            **({"generation_scope": scope} if scope else {}),
            "last_test_regeneration": {
                "regenerated_sections": regenerated_keys,
                "regenerated_at": timezone.now().isoformat(),
            },
            "stale_sections": [
                item.key
                for item in report.sections.all()
                if (item.generation_metadata or {}).get("stale")
            ],
        }
        report.status = ReportStatus.IN_REVIEW
        report.generated_at = timezone.now()
        report.save(
            update_fields=[
                "context_payload",
                "ai_metadata",
                "status",
                "generated_at",
                "updated_at",
            ]
        )
        ReportSectionService._rebuild_report_text(report)
        ReportVersionService.create_version(report, user=user)
        return regenerated_keys

    @classmethod
    def mark_dependents_stale(cls, report: Report, section_key: str) -> list[str]:
        stale_keys: list[str] = []
        queue: list[tuple[str, str]] = [
            (dependent_key, section_key)
            for dependent_key in SectionWorkflowService.get_dependents(section_key)
        ]
        visited: set[str] = set()

        while queue:
            dependent_key, stale_source = queue.pop(0)
            if dependent_key in visited:
                continue
            visited.add(dependent_key)
            section = report.sections.filter(key=dependent_key).first()
            if not section or section.is_locked:
                continue
            metadata = section.generation_metadata or {}
            stale_dependencies = sorted(
                set((metadata.get("stale_dependencies") or []) + [stale_source])
            )
            section.generation_metadata = {
                **metadata,
                "stale": True,
                "stale_dependencies": stale_dependencies,
                "stale_marked_at": timezone.now().isoformat(),
            }
            section.save(update_fields=["generation_metadata", "updated_at"])
            stale_keys.append(dependent_key)
            queue.extend(
                (child_key, dependent_key)
                for child_key in SectionWorkflowService.get_dependents(dependent_key)
            )
        return stale_keys

    @classmethod
    def regenerate_with_dependents(
        cls, report: Report, section_key: str, context: dict | None = None, user=None
    ) -> dict:
        context = context or build_report_snapshot(report.evaluation)
        report.context_payload = context
        regeneration_order = [section_key, *cls._collect_dependents(section_key)]
        existing_keys = {item.key for item in report.sections.all()}
        generated_set = existing_keys - set(regeneration_order)
        regenerated_keys: list[str] = []
        failed_sections: list[dict] = []

        for item_key in regeneration_order:
            section = report.sections.filter(key=item_key).first()
            if not section or section.is_locked:
                failed_sections.append(
                    {
                        "section_key": item_key,
                        "reason": "Seção inexistente ou bloqueada.",
                    }
                )
                continue
            if not SectionWorkflowService.can_generate(item_key, generated_set):
                failed_sections.append(
                    {
                        "section_key": item_key,
                        "reason": "Dependências não disponíveis para regeneração.",
                    }
                )
                continue

            result = ReportPipelineService._generate_single_section(report, item_key, context)
            ReportPipelineService._save_section_result(
                report,
                item_key,
                section.title,
                section.order,
                result,
            )
            current = report.sections.filter(key=item_key).first()
            metadata = current.generation_metadata or {}
            current.generation_metadata = {
                **metadata,
                "generated_at": timezone.now().isoformat(),
                "stale": False,
                "stale_dependencies": [],
            }
            current.save(update_fields=["generation_metadata", "updated_at"])
            regenerated_keys.append(item_key)
            generated_set.add(item_key)

        report.ai_metadata = {
            **(report.ai_metadata or {}),
            "last_regeneration": {
                "section_key": section_key,
                "regenerated_sections": regenerated_keys,
                "failed_sections": failed_sections,
                "regenerated_at": timezone.now().isoformat(),
            },
            "stale_sections": [
                item.key
                for item in report.sections.all()
                if (item.generation_metadata or {}).get("stale")
            ],
        }
        report.save(update_fields=["context_payload", "ai_metadata", "updated_at"])
        ReportSectionService._rebuild_report_text(report)
        ReportVersionService.create_version(report, user=user)
        return {
            "regenerated_sections": regenerated_keys,
            "failed_sections": failed_sections,
        }

    @classmethod
    def _collect_dependents(cls, section_key: str) -> list[str]:
        queue = list(SectionWorkflowService.get_dependents(section_key))
        visited: list[str] = []
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.append(current)
            queue.extend(SectionWorkflowService.get_dependents(current))
        return visited
