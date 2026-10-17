import logging
import threading

from ninja import Router
from ninja.errors import HttpError
from django.http import HttpResponse
from django.db import close_old_connections, transaction
from django.utils.text import slugify

from apps.ai.services.ai_healthcheck_service import AIHealthcheckService
from apps.accounts.models import UserRole
from apps.api.auth import bearer_auth
from apps.common.clinical_access import owned_evaluations, owned_reports
from apps.reports.services.report_approval_service import ReportApprovalService
from apps.reports.services.clinical_consistency_audit_service import ClinicalConsistencyAuditService
from apps.evaluations.models import Evaluation
from apps.reports.models import Report, ReportSection, ReportStatus
from apps.reports.selectors import (
    get_report_by_id,
    get_reports_by_evaluation,
    get_reports_by_patient,
    list_reports,
)
from apps.reports.services.report_export_service import ReportExportService
from apps.reports.services.report_context_service import ReportContextService
from apps.reports.services.report_generation_service import ReportGenerationService
from apps.reports.services.report_section_service import ReportSectionService
from apps.reports.services.section_regeneration_service import SectionRegenerationService
from apps.reports.services.report_validation_service import ReportValidationService
from apps.reports.services.report_version_service import ReportVersionService

from .schemas import (
    HtmlOut,
    MessageOut,
    ReportCreateIn,
    ReportDetailOut,
    ReportOut,
    ReportSectionOut,
    ReportSectionUpdateIn,
    ReportUpdateIn,
)

router = Router(tags=["reports"])
logger = logging.getLogger(__name__)


def can_edit_reports(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
    }


def serialize_version(version) -> dict:
    return {
        "id": version.id,
        "version_number": version.version_number,
        "content": version.content,
        "created_by": version.created_by.display_name
        if version.created_by
        else "Sistema",
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


def serialize_section(section) -> dict:
    return {
        "id": section.id,
        "key": section.key,
        "title": section.title,
        "order": section.order,
        "source_payload": {},
        "generated_text": section.content_generated or "",
        "edited_text": section.content_edited or "",
        "generation_metadata": section.generation_metadata or {},
        "warnings_payload": section.warnings_payload or [],
        "is_locked": section.is_locked,
        "updated_at": section.updated_at.isoformat() if section.updated_at else None,
    }


def serialize_report(report, include_sections=False, include_versions=False) -> dict:
    data = {
        "id": report.id,
        "evaluation_id": report.evaluation_id,
        "evaluation_code": report.evaluation.code if report.evaluation else "",
        "evaluation_title": report.evaluation.title if report.evaluation else "",
        "patient_id": report.patient_id,
        "patient_name": report.patient.full_name if report.patient else "",
        "author_id": report.author_id,
        "author_name": report.author.display_name if report.author else "Sistema",
        "title": report.title,
        "interested_party": report.interested_party or "",
        "purpose": report.purpose or "",
        "status": report.status,
        "snapshot_payload": report.context_payload or {},
        "context_payload": report.context_payload or {},
        "generated_text": report.generated_text or "",
        "edited_text": report.edited_text or "",
        "final_text": report.final_text or "",
        "ai_metadata": report.ai_metadata or {},
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        "generated_at": report.generated_at.isoformat()
        if report.generated_at
        else None,
    }
    if report.status in {ReportStatus.FINALIZED, ReportStatus.SENT}:
        from apps.reports.services.professional_identity_service import ProfessionalIdentityService

        context = report.context_payload or {}
        data["patient_name"] = (context.get("patient") or {}).get("full_name") or data["patient_name"]
        data["evaluation_code"] = (context.get("evaluation") or {}).get("code") or data["evaluation_code"]
        data["evaluation_title"] = (context.get("evaluation") or {}).get("title", data["evaluation_title"])
        data["author_name"] = ProfessionalIdentityService.author_label(report)
    if include_sections:
        data["sections"] = [serialize_section(s) for s in report.sections.all()]
    if include_versions:
        data["versions"] = [serialize_version(v) for v in report.versions.all()]
    return data


def _get_report_or_404(report_id: int, user, *, editable=False, lock=False):
    report = (
        owned_reports(Report.objects.select_for_update(), user).filter(pk=report_id).first()
        if lock else get_report_by_id(report_id, user=user)
    )
    if not report:
        return None, (404, {"message": "Laudo inexistente."})
    if editable and report.status in {ReportStatus.FINALIZED, ReportStatus.SENT}:
        raise HttpError(403, "Laudo aprovado não pode ser alterado. Crie uma nova revisão.")
    return report, None


def _reserve_report_generation(report_id, user):
    with transaction.atomic():
        report, error = _get_report_or_404(report_id, user, editable=True, lock=True)
        if error:
            return report, error
        if report.status == ReportStatus.GENERATING:
            raise HttpError(403, "O laudo já está em geração.")
        report.status = ReportStatus.GENERATING
        report.save(update_fields=["status", "updated_at"])
        return report, None


def _generate_report_async(report_id: int, user_id: int | None):
    close_old_connections()
    try:
        report = (
            Report.objects.select_related("evaluation", "patient")
            .filter(id=report_id)
            .first()
        )
        if not report:
            logger.error("Laudo %s nao encontrado para geracao assincrona", report_id)
            return
        user = (
            request_user_model().objects.filter(id=user_id).first() if user_id else None
        )
        ReportGenerationService.generate_full_report(report, user=user)
    except Exception:
        logger.exception("Erro na geracao assincrona do laudo %s", report_id)
        Report.objects.filter(id=report_id).update(status=ReportStatus.DRAFT)
    finally:
        close_old_connections()


def _regenerate_test_sections_async(
    report_id: int, user_id: int | None, scope: str | None = None
):
    close_old_connections()
    try:
        report = (
            Report.objects.select_related("evaluation", "patient")
            .prefetch_related("sections", "versions")
            .filter(id=report_id)
            .first()
        )
        if not report:
            logger.error("Laudo %s nao encontrado para regeneracao assincrona", report_id)
            return
        user = (
            request_user_model().objects.filter(id=user_id).first() if user_id else None
        )
        SectionRegenerationService.regenerate_test_sections(
            report, user=user, scope=scope
        )
    except Exception:
        logger.exception("Erro na regeneracao assincrona de testes do laudo %s", report_id)
        Report.objects.filter(id=report_id).update(status=ReportStatus.IN_REVIEW)
    finally:
        close_old_connections()


def request_user_model():
    from django.contrib.auth import get_user_model

    return get_user_model()


@router.get(
    "/{report_id}/specialist-plan",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def specialist_plan(request, report_id: int):
    from apps.reports.services.specialist_planning_service import SpecialistPlanningService

    report = owned_reports(Report.objects.all(), request.auth).filter(pk=report_id).first()
    if report is None:
        return 404, {"message": "Laudo inexistente."}
    # Planejar não sincroniza nem modifica o snapshot clínico existente.
    return SpecialistPlanningService.build_plan(report.context_payload or {})


@router.get("/", response=list[ReportOut], auth=bearer_auth)
def list_reports_endpoint(
    request, evaluation_id: int | None = None, patient_id: int | None = None
):
    if evaluation_id:
        reports = get_reports_by_evaluation(evaluation_id, user=request.auth)
    elif patient_id:
        reports = get_reports_by_patient(patient_id, user=request.auth)
    else:
        reports = list_reports(user=request.auth)
    return [serialize_report(item) for item in reports]


@router.get(
    "/by-evaluation/{evaluation_id}", response=list[ReportOut], auth=bearer_auth
)
def get_reports_by_evaluation_endpoint(request, evaluation_id: int):
    return [serialize_report(item) for item in get_reports_by_evaluation(evaluation_id, user=request.auth)]


@router.post(
    "/", response={201: ReportOut, 400: MessageOut, 403: MessageOut}, auth=bearer_auth
)
def create_report(request, payload: ReportCreateIn):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}

    evaluation = (
        owned_evaluations(Evaluation.objects.select_related("patient"), request.auth)
        .filter(id=payload.evaluation_id)
        .first()
    )
    if not evaluation:
        return 400, {"message": "Avaliação não encontrada."}

    report = Report.objects.create(
        evaluation=evaluation,
        patient=evaluation.patient,
        author=request.auth,
        title=payload.title or "Laudo Neuropsicológico",
        interested_party=payload.interested_party or evaluation.patient.full_name,
        purpose=payload.purpose
        or evaluation.evaluation_purpose
        or evaluation.referral_reason,
    )
    return 201, serialize_report(report)


def _generate_report_for_evaluation(evaluation_id: int, user):
    evaluation = (
        owned_evaluations(Evaluation.objects.select_related("patient"), user).filter(id=evaluation_id).first()
    )
    if not evaluation:
        return None, (400, {"message": "Avaliação não encontrada."})

    try:
        ReportValidationService.validate_for_generation(evaluation)
    except Exception as exc:
        return None, (400, {"message": str(exc)})

    report = Report.objects.create(
        evaluation=evaluation,
        patient=evaluation.patient,
        author=user,
        interested_party=evaluation.patient.full_name,
        purpose=evaluation.evaluation_purpose or evaluation.referral_reason,
        status=ReportStatus.GENERATING,
    )
    thread = threading.Thread(
        target=_generate_report_async,
        args=(report.id, getattr(user, "id", None)),
        daemon=True,
    )
    thread.start()
    return report, None


def _generate_test_report_for_evaluation(evaluation_id: int, user):
    evaluation = (
        owned_evaluations(Evaluation.objects.select_related("patient"), user).filter(id=evaluation_id).first()
    )
    if not evaluation:
        return None, (400, {"message": "Avaliação não encontrada."})

    try:
        ReportValidationService.validate_for_generation(evaluation)
    except Exception as exc:
        return None, (400, {"message": str(exc)})

    report = Report.objects.create(
        evaluation=evaluation,
        patient=evaluation.patient,
        author=user,
        interested_party=evaluation.patient.full_name,
        purpose=evaluation.evaluation_purpose or evaluation.referral_reason,
        status=ReportStatus.GENERATING,
        ai_metadata={"generation_scope": "tests_only"},
    )
    thread = threading.Thread(
        target=_regenerate_test_sections_async,
        args=(report.id, getattr(user, "id", None), "tests_only"),
        daemon=True,
    )
    thread.start()
    return report, None


@router.post(
    "/generate-ia/{evaluation_id}",
    response={201: ReportOut, 400: MessageOut, 403: MessageOut},
    auth=bearer_auth,
)
def generate_ia(request, evaluation_id: int):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}

    report, error = _generate_report_for_evaluation(evaluation_id, request.auth)
    if error:
        return error
    return 201, serialize_report(report)


@router.post(
    "/generate-from-evaluation/{evaluation_id}",
    response={201: ReportOut, 400: MessageOut, 403: MessageOut},
    auth=bearer_auth,
)
def generate_from_evaluation(request, evaluation_id: int):
    mode = (request.GET.get("mode") or "full").strip().lower()
    if mode == "full":
        return generate_ia(request, evaluation_id)
    if mode == "tests_only":
        if not can_edit_reports(request.auth):
            return 403, {"message": "Permissão negada."}
        report, error = _generate_test_report_for_evaluation(evaluation_id, request.auth)
        if error:
            return error
        return 201, serialize_report(report)
    return 400, {"message": "Modo de geração inválido."}


@router.post(
    "/{report_id}/build",
    response={200: ReportDetailOut, 404: MessageOut, 403: MessageOut},
    auth=bearer_auth,
)
def build_report(request, report_id: int):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}

    report, error = _reserve_report_generation(report_id, request.auth)
    if error:
        return error

    try:
        ReportGenerationService.generate_full_report(report, user=request.auth)
    except ValueError as exc:
        Report.objects.filter(pk=report.pk, status=ReportStatus.GENERATING).update(status=ReportStatus.IN_REVIEW)
        return 400, {"message": str(exc)}
    report.refresh_from_db()
    return 200, serialize_report(report, include_sections=True, include_versions=True)


@router.post(
    "/{report_id}/regenerate",
    response={200: ReportDetailOut, 404: MessageOut, 403: MessageOut},
    auth=bearer_auth,
)
def regenerate_report(request, report_id: int):
    return build_report(request, report_id)


@router.post(
    "/{report_id}/regenerate-tests",
    response={200: ReportDetailOut, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def regenerate_test_sections(request, report_id: int):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}
    report, error = _reserve_report_generation(report_id, request.auth)
    if error:
        return error
    try:
        report.status = ReportStatus.GENERATING
        report.save(update_fields=["status", "updated_at"])
        thread = threading.Thread(
            target=_regenerate_test_sections_async,
            args=(report.id, getattr(request.auth, "id", None), None),
            daemon=True,
        )
        thread.start()
    except ValueError as exc:
        report.status = ReportStatus.IN_REVIEW
        report.save(update_fields=["status", "updated_at"])
        return 400, {"message": str(exc)}
    report.refresh_from_db()
    return 200, serialize_report(report, include_sections=True, include_versions=True)


@router.post(
    "/{report_id}/regenerate-section/{section_key}",
    response={200: ReportSectionOut, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def regenerate_section(request, report_id: int, section_key: str):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}
    report, error = _reserve_report_generation(report_id, request.auth)
    if error:
        return error
    try:
        section = ReportSectionService.regenerate_section(
            report, section_key, user=request.auth
        )
    except ValueError as exc:
        return 400, {"message": str(exc)}
    finally:
        Report.objects.filter(pk=report.pk, status=ReportStatus.GENERATING).update(status=ReportStatus.IN_REVIEW)
    if not section:
        return 404, {"message": "Seção inexistente ou bloqueada."}
    return 200, serialize_section(section)


@router.post(
    "/{report_id}/finalize",
    response={200: ReportOut, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def finalize_report(request, report_id: int):
    try:
        report = ReportApprovalService.finalize(report_id=report_id, user=request.auth)
    except PermissionError as exc:
        return 403, {"message": str(exc)}
    except Report.DoesNotExist:
        return 404, {"message": "Laudo não encontrado."}
    except ValueError as exc:
        return 400, {"message": str(exc)}
    return 200, serialize_report(report, include_sections=True, include_versions=True)


@router.post(
    "/{report_id}/revisions",
    response={201: ReportDetailOut, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def create_report_revision(request, report_id: int):
    try:
        report = ReportApprovalService.create_revision(report_id=report_id, user=request.auth)
    except Report.DoesNotExist:
        return 404, {"message": "Laudo não encontrado."}
    except PermissionError as exc:
        return 403, {"message": str(exc)}
    except ValueError as exc:
        return 400, {"message": str(exc)}
    return 201, serialize_report(report, include_sections=True, include_versions=True)


@router.post(
    "/{report_id}/audit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def audit_report(request, report_id: int):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}
    report, error = _get_report_or_404(report_id, request.auth)
    if error:
        return error
    if report.status not in {ReportStatus.DRAFT, ReportStatus.IN_REVIEW}:
        return 400, {"message": "A auditoria exige um laudo em revisão."}
    ReportContextService.sync_report_context(report)
    source_sha256 = ReportApprovalService.fingerprint(report)
    try:
        result = ClinicalConsistencyAuditService.audit_report(report, report.context_payload or {})
    except Exception:
        result = {**ClinicalConsistencyAuditService._invalid_result(), "source_sha256": source_sha256}
    with transaction.atomic():
        report = owned_reports(Report.objects.select_for_update(), request.auth).filter(pk=report_id).first()
        if not report:
            return 404, {"message": "Laudo não encontrado."}
        if report.status not in {ReportStatus.DRAFT, ReportStatus.IN_REVIEW} or result.get("source_sha256") != ReportApprovalService.fingerprint(report):
            return 400, {"message": "O laudo mudou durante a análise. Execute a auditoria novamente."}
        report.ai_metadata = {**(report.ai_metadata or {}), "audit": result}
        report.save(update_fields=["ai_metadata", "updated_at"])
    return 200, result


@router.post(
    "/{report_id}/export-html",
    response={200: HtmlOut, 404: MessageOut},
    auth=bearer_auth,
)
def export_report_html(request, report_id: int):
    report, error = _get_report_or_404(report_id, request.auth)
    if error:
        return error
    return 200, {"html": ReportExportService.generate_html(report)}


@router.post(
    "/{report_id}/export-docx",
    response={200: None, 404: MessageOut, 500: MessageOut},
    auth=bearer_auth,
)
def export_report_docx(request, report_id: int):
    report, error = _get_report_or_404(report_id, request.auth)
    if error:
        return error
    try:
        payload = ReportExportService.generate_docx_bytes(report)
    except Exception as exc:
        logger.exception("Erro ao exportar DOCX do laudo %s", report_id)
        return 500, {"message": f"Erro ao exportar DOCX: {exc}"}
    patient_name = (report.context_payload.get("patient") or {}).get("full_name") or (report.patient.full_name if report.patient else f"report-{report.id}")
    filename = f"Laudo-{slugify(patient_name)}.docx"
    response = HttpResponse(
        payload,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Cache-Control"] = "private, no-store"
    return response


@router.get(
    "/{report_id}", response={200: ReportDetailOut, 404: MessageOut}, auth=bearer_auth
)
def get_report(request, report_id: int):
    report, error = _get_report_or_404(report_id, request.auth)
    if error:
        return error
    ReportContextService.sync_report_context(report)
    return 200, serialize_report(report, include_sections=True, include_versions=True)


@router.put(
    "/{report_id}",
    response={200: ReportOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
@transaction.atomic
def update_report(request, report_id: int, payload: ReportUpdateIn):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}

    report, error = _get_report_or_404(report_id, request.auth, editable=True, lock=True)
    if error:
        return error

    if payload.title is not None:
        report.title = payload.title
    if payload.interested_party is not None:
        report.interested_party = payload.interested_party
    if payload.purpose is not None:
        report.purpose = payload.purpose
    if payload.status is not None:
        if payload.status != report.status and payload.status in {ReportStatus.FINALIZED, ReportStatus.SENT}:
            return 403, {"message": "Use o fluxo de aprovação clínica para finalizar o laudo."}
        report.status = payload.status
    if payload.final_text is not None:
        return 403, {"message": "Texto final só pode ser definido pela aprovação clínica."}
    report.save()
    ReportVersionService.create_version(report, user=request.auth)
    return 200, serialize_report(report)


@router.delete(
    "/{report_id}",
    response={200: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def delete_report(request, report_id: int):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}

    report, error = _get_report_or_404(report_id, request.auth, editable=True)
    if error:
        return error

    report.delete()
    return 200, {"message": "Laudo excluído com sucesso."}


@router.patch(
    "/sections/{section_id}",
    response={200: ReportSectionOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
@transaction.atomic
def update_section(request, section_id: int, payload: ReportSectionUpdateIn):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}

    section = (
        ReportSection.objects.select_related("report").filter(
            id=section_id, report__in=owned_reports(Report.objects.all(), request.auth)
        ).first()
    )
    if not section:
        return 404, {"message": "Seção inexistente."}
    section.report = Report.objects.select_for_update().get(pk=section.report_id)
    if section.report.status in {ReportStatus.FINALIZED, ReportStatus.SENT}:
        return 403, {"message": "Laudo aprovado não pode ser alterado."}
    if section.report.status == ReportStatus.GENERATING:
        return 403, {"message": "Aguarde a geração antes de editar as seções."}
    if section.is_locked:
        return 403, {"message": "Seção bloqueada para edição."}

    if payload.edited_text is not None:
        ReportSectionService.update_manual_content(section, payload.edited_text)
    if payload.is_locked is not None:
        section.is_locked = payload.is_locked
        section.save(update_fields=["is_locked", "updated_at"])

    ReportVersionService.create_version(section.report, user=request.auth)
    return 200, serialize_section(section)


@router.patch(
    "/{report_id}/sections/{section_key}",
    response={200: ReportSectionOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def update_section_by_key(
    request, report_id: int, section_key: str, payload: ReportSectionUpdateIn
):
    report, error = _get_report_or_404(report_id, request.auth)
    if error:
        return error
    section = report.sections.filter(key=section_key).first()
    if not section:
        return 404, {"message": "Seção inexistente."}
    return update_section(request, section.id, payload)
