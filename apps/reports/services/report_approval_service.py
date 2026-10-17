import hashlib
import json
from copy import deepcopy

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.common.clinical_access import owned_reports
from apps.reports.models import Report, ReportApprovalSnapshot, ReportSection, ReportStatus
from apps.reports.services.report_review_service import ReportReviewService
from apps.reports.services.report_version_service import ReportVersionService
from apps.reports.services.report_context_service import ReportContextService
from apps.reports.services.professional_identity_service import ProfessionalIdentityService


class ReportApprovalService:
    @staticmethod
    def fingerprint(report) -> str:
        payload = {
            "context": report.context_payload,
            "title": report.title,
            "purpose": report.purpose,
            "interested_party": report.interested_party,
            "professional_label": ProfessionalIdentityService.author_label(report),
            "sections": list(report.sections.order_by("order", "id").values(
                "key", "title", "content_edited", "content_generated", "warnings_payload",
            )),
        }
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode()).hexdigest()

    @staticmethod
    def can_approve(user) -> bool:
        return user.role in {UserRole.NEUROPSYCHOLOGIST, UserRole.ADMIN} and bool((user.crp or "").strip())

    @classmethod
    def finalize(cls, *, report_id: int, user):
        if not cls.can_approve(user):
            raise PermissionError("Aprovação exige profissional responsável com CRP cadastrado.")
        with transaction.atomic():
            report = owned_reports(Report.objects.select_for_update(), user).get(pk=report_id)
            if report.status not in {ReportStatus.DRAFT, ReportStatus.IN_REVIEW}:
                raise ValueError("O laudo precisa estar em revisão antes da aprovação.")
            if ReportContextService.build_context(report.evaluation) != report.context_payload:
                raise ValueError("Os dados clínicos mudaram. Atualize e audite o laudo novamente.")
            review = ReportReviewService.review(report)
            if review["status"] != "ok":
                raise ValueError("Resolva as pendências da revisão antes de aprovar o laudo.")
            audit = (report.ai_metadata or {}).get("audit")
            if not isinstance(audit, dict) or audit.get("status") not in {"ok", "flagged"}:
                raise ValueError("Execute uma auditoria clínica válida antes da aprovação.")
            alerts = audit.get("alerts")
            if not isinstance(alerts, list) or any(
                not isinstance(item, dict) or item.get("severity") not in {"low", "medium"}
                for item in alerts
            ):
                raise ValueError("A auditoria contém pendências críticas ou inválidas.")
            fingerprint = cls.fingerprint(report)
            if audit.get("source_sha256") != fingerprint:
                raise ValueError("O laudo mudou após a auditoria. Execute-a novamente.")
            if (report.ai_metadata or {}).get("pipeline", {}).get("failed_sections"):
                raise ValueError("Há seções cuja geração falhou. Corrija-as antes de aprovar.")
            report.final_text = "\n\n".join(
                f"## {section.title}\n{section.content_edited or section.content_generated}"
                for section in report.sections.order_by("order", "id")
            )
            professional_label = ProfessionalIdentityService.author_label(report)
            from apps.reports.services.report_export_service import ReportExportService

            template_path = ReportExportService._select_template_path(report, report.context_payload)
            try:
                template_sha256 = hashlib.sha256(template_path.read_bytes()).hexdigest()
                document = ReportExportService.generate_docx_bytes(report)
                html = ReportExportService.generate_html(report)
            except Exception as exc:
                raise ValueError("Não foi possível preservar a exportação aprovada. Verifique o DOCX antes de tentar novamente.") from exc
            current = owned_reports(Report.objects.select_related("evaluation__patient", "evaluation__examiner", "author"), user).get(pk=report_id)
            if cls.fingerprint(current) != fingerprint or ReportContextService.build_context(current.evaluation) != current.context_payload:
                raise ValueError("Os dados mudaram durante a aprovação. Revise e audite novamente.")
            if hashlib.sha256(template_path.read_bytes()).hexdigest() != template_sha256:
                raise ValueError("O modelo DOCX mudou durante a aprovação. Tente novamente.")
            ReportApprovalSnapshot.objects.create(
                report=report, approved_by=user, source_sha256=fingerprint,
                payload={
                    "context": deepcopy(report.context_payload),
                    "professional_label": professional_label,
                    "final_text": report.final_text,
                    "audit": deepcopy(audit),
                    "sections": list(report.sections.order_by("order", "id").values(
                        "key", "title", "order", "content_edited", "content_generated",
                    )),
                },
                template_name=template_path.name, template_sha256=template_sha256,
                document=document, document_sha256=hashlib.sha256(document).hexdigest(), html=html,
            )
            report.status = ReportStatus.FINALIZED
            report.ai_metadata = {
                **(report.ai_metadata or {}), "review": review,
                "finalization": {
                    "status": "approved", "approved_by": user.pk,
                    "approved_at": timezone.now().isoformat(), "source_sha256": fingerprint,
                    "professional_label": professional_label,
                    "warnings": alerts,
                },
            }
            report.save(update_fields=["final_text", "status", "ai_metadata", "updated_at"])
            ReportVersionService.create_version(report, user=user)
            return report

    @classmethod
    def create_revision(cls, *, report_id: int, user):
        if not cls.can_approve(user):
            raise PermissionError("Uma nova revisão exige o profissional responsável com CRP.")
        with transaction.atomic():
            original = owned_reports(Report.objects.select_for_update(), user).get(pk=report_id)
            if original.status not in {ReportStatus.FINALIZED, ReportStatus.SENT}:
                raise ValueError("Somente laudos aprovados podem originar uma nova revisão.")
            revised = Report.objects.create(
                evaluation=original.evaluation, patient=original.patient, author=user,
                title=original.title, interested_party=original.interested_party, purpose=original.purpose,
                status=ReportStatus.IN_REVIEW,
                context_payload=ReportContextService.build_context(original.evaluation),
                generated_text=original.generated_text, edited_text=original.edited_text,
                ai_metadata={"revision_of": original.pk},
            )
            ReportSection.objects.bulk_create([
                ReportSection(
                    report=revised, key=section.key, title=section.title, order=section.order,
                    content_generated=section.content_generated, content_edited=section.content_edited,
                    generation_metadata=deepcopy(section.generation_metadata),
                    warnings_payload=deepcopy(section.warnings_payload), is_locked=section.is_locked,
                )
                for section in original.sections.all()
            ])
            ReportVersionService.create_version(revised, user=user)
            return revised
