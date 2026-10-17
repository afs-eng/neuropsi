from apps.reports.builders.snapshot_builder import build_report_snapshot
from apps.reports.models import Report, ReportStatus
from django.db import transaction


class ReportContextService:
    @staticmethod
    def build_context(evaluation) -> dict:
        return build_report_snapshot(evaluation)

    @classmethod
    def sync_report_context(cls, report, persist: bool = True) -> dict:
        if report is None:
            return {}
        if getattr(report, "status", None) in {ReportStatus.FINALIZED, ReportStatus.SENT}:
            return dict(report.context_payload or {})
        if getattr(report, "evaluation", None) is None:
            return dict(report.context_payload or {})
        latest_context = cls.build_context(report.evaluation)
        if persist and isinstance(report, Report) and report.pk:
            with transaction.atomic():
                current = Report.objects.select_for_update().get(pk=report.pk)
                if current.status in {ReportStatus.FINALIZED, ReportStatus.SENT}:
                    report.status = current.status
                    report.context_payload = current.context_payload
                    return dict(current.context_payload or {})
                if latest_context != (current.context_payload or {}):
                    current.context_payload = latest_context
                    current.save(update_fields=["context_payload", "updated_at"])
                report.context_payload = latest_context
                return latest_context
        if latest_context != (report.context_payload or {}):
            report.context_payload = latest_context
            if persist:
                report.save(update_fields=["context_payload", "updated_at"])
        return latest_context
