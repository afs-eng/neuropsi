import hashlib
import json

from django.db import transaction

from apps.common.clinical_access import owned_reports
from apps.reports.models import Report, ReportStatus, SpecialistReview, SpecialistRun
from apps.reports.services.report_approval_service import ReportApprovalService
from apps.reports.services.specialist_contracts import specialist_output_model, validate_evidence
from apps.reports.services.specialist_run_service import SpecialistRunService


class SpecialistReviewService:
    @staticmethod
    def output_fingerprint(run) -> str:
        data = json.dumps(run.output_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()

    @classmethod
    def review(cls, *, user, report_id, run_id, decision, notes, source_sha256, output_sha256):
        if not ReportApprovalService.can_approve(user):
            raise PermissionError("A revisão exige o profissional responsável com CRP cadastrado.")
        if decision not in SpecialistReview.Decision.values:
            raise ValueError("Decisão de revisão inválida.")
        notes = notes.strip()
        if len(notes) > 2000 or (decision == SpecialistReview.Decision.REJECTED and len(notes) < 3):
            raise ValueError("Informe um motivo para rejeitar (até 2.000 caracteres).")
        with transaction.atomic():
            report = owned_reports(Report.objects.select_for_update(), user).get(pk=report_id)
            if report.status not in {ReportStatus.DRAFT, ReportStatus.IN_REVIEW}:
                raise ValueError("A revisão dos especialistas exige um laudo em revisão.")
            run = SpecialistRun.objects.select_for_update().select_related(
                "application__evaluation__patient", "application__instrument", "report",
            ).get(pk=run_id, report=report)
            if run.status != SpecialistRun.Status.NEEDS_REVIEW or not SpecialistRunService.is_current(run):
                raise ValueError("O rascunho não está pronto ou seus dados foram alterados.")
            current_output = cls.output_fingerprint(run)
            if source_sha256 != run.source_sha256 or output_sha256 != current_output:
                raise ValueError("O rascunho mudou. Atualize o painel antes de revisar.")
            if decision == SpecialistReview.Decision.APPROVED:
                try:
                    output = specialist_output_model(run.instrument_code).model_validate(run.output_payload)
                    validate_evidence(output, run.input_payload.get("facts", {}), run.instrument_code)
                except ValueError:
                    raise ValueError("O rascunho não passou na validação de evidências.") from None
            return SpecialistReview.objects.create(
                run=run, reviewed_by=user, decision=decision, notes=notes,
                source_sha256=run.source_sha256, output_sha256=current_output,
            )
