from django.http import HttpResponse
from django.conf import settings
from ninja import Router, Schema
from pydantic import Field

from apps.api.auth import bearer_auth
from apps.common.clinical_access import owned_reports
from apps.reports.models import Report, SpecialistRun
from apps.reports.services.specialist_run_service import SpecialistRunService
from apps.reports.services.specialist_review_service import SpecialistReviewService
from apps.reports.services.report_approval_service import ReportApprovalService
from apps.reports.services.specialist_instructions import INSTRUMENT_INSTRUCTIONS
from apps.reports.models import ReportStatus, SpecialistReview
from apps.tests.models import TestApplication

router = Router(tags=["report-specialists"], auth=bearer_auth)


class RunRequestIn(Schema):
    application_ids: list[int] | None = Field(default=None, min_length=1, max_length=30)


class MessageOut(Schema):
    message: str


class ReviewRequestIn(Schema):
    decision: str = Field(pattern="^(approved|rejected)$")
    notes: str = Field(default="", max_length=2000)
    source_sha256: str = Field(pattern="^[a-f0-9]{64}$")
    output_sha256: str = Field(pattern="^[a-f0-9]{64}$")


def serialize_review(review):
    return {
        "id": review.pk, "decision": review.decision, "notes": review.notes,
        "reviewed_by": review.reviewed_by_id, "created_at": review.created_at.isoformat(),
        "source_sha256": review.source_sha256, "output_sha256": review.output_sha256,
    }


def serialize_run(run):
    current = SpecialistRunService.is_current(run)
    output_sha256 = SpecialistReviewService.output_fingerprint(run)
    reviews = list(run.reviews.all())
    latest = reviews[0] if reviews else None
    review_current = bool(current and run.status == SpecialistRun.Status.NEEDS_REVIEW and latest and latest.source_sha256 == run.source_sha256 and latest.output_sha256 == output_sha256)
    return {
        "id": run.pk,
        "application_id": run.application_id,
        "instrument_code": run.instrument_code,
        "specialist_version": run.specialist_version,
        "source_sha256": run.source_sha256,
        "model": run.model_name,
        "provider": run.provider_name,
        "status": run.status if current else SpecialistRun.Status.STALE,
        "is_current": current,
        "requires_professional_review": not (review_current and latest.decision == SpecialistReview.Decision.APPROVED),
        "review_is_current": review_current,
        "reviews": [serialize_review(review) for review in reviews],
        "output_sha256": output_sha256,
        "output": run.output_payload,
        "evidence": run.input_payload.get("facts", {}),
        "usage": run.usage_payload,
        "error_code": run.error_code,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.post("/{report_id}/specialist-runs", response={202: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut})
def enqueue_specialists(request, report_id: int, payload: RunRequestIn):
    # Falhar fechado, inclusive para admins de outro proprietário.
    if not owned_reports(Report.objects.all(), request.auth).filter(pk=report_id).exists():
        return 404, {"message": "Laudo inexistente."}
    try:
        runs, skipped = SpecialistRunService.enqueue(
            user=request.auth, report_id=report_id, application_ids=payload.application_ids,
        )
    except Report.DoesNotExist:
        return 404, {"message": "Laudo inexistente."}
    except PermissionError as exc:
        return 403, {"message": str(exc)}
    except ValueError as exc:
        return 400, {"message": str(exc)}
    return 202, {
        "run_ids": [run.pk for run in runs],
        "skipped": skipped,
        "message": "Execuções persistidas. Um worker separado deve processar a fila.",
    }


@router.get("/{report_id}/specialist-runs", response={200: list[dict], 404: MessageOut})
def list_specialist_runs(request, report_id: int, response: HttpResponse):
    response["Cache-Control"] = "private, no-store"
    if not owned_reports(Report.objects.all(), request.auth).filter(pk=report_id).exists():
        return 404, {"message": "Laudo inexistente."}
    runs = SpecialistRun.objects.filter(report_id=report_id, report__author=request.auth).select_related(
        "report", "application__evaluation__patient", "application__instrument",
    ).prefetch_related("reviews").order_by("-created_at", "-id")[:100]
    return [serialize_run(run) for run in runs]


@router.get("/{report_id}/specialist-status", response={200: dict, 404: MessageOut})
def specialist_status(request, report_id: int, response: HttpResponse):
    response["Cache-Control"] = "private, no-store"
    report = owned_reports(Report.objects.all(), request.auth).filter(pk=report_id).first()
    if not report:
        return 404, {"message": "Laudo inexistente."}
    reason = ""
    try:
        SpecialistRunService.configuration()
        configured = True
    except ValueError as exc:
        configured = False
        reason = str(exc)
    applications = list(TestApplication.objects.filter(evaluation_id=report.evaluation_id, is_validated=True).select_related("instrument").order_by("id"))
    allowlist = set(settings.SPECIALIST_AI_INSTRUMENTS) & set(INSTRUMENT_INSTRUCTIONS)
    editable = report.status in {ReportStatus.DRAFT, ReportStatus.IN_REVIEW}
    return {
        "experimental": True, "configured": configured, "configuration_message": reason,
        "model": settings.SPECIALIST_AI_MODEL, "legacy_unchanged": True,
        "provider": SpecialistRunService.provider_name(),
        "can_request": configured and editable and request.auth.role in SpecialistRunService.CLINICAL_ROLES and any(app.instrument.code in allowlist for app in applications),
        "can_review": editable and ReportApprovalService.can_approve(request.auth),
        "worker_status": "not_monitored", "automatic_integration": False,
        "applications": [{
            "id": app.pk, "instrument_code": app.instrument.code, "instrument_name": app.instrument.name,
            "respondent": str((app.raw_payload or {}).get("respondent_name") or (app.raw_payload or {}).get("informant") or ""),
            "enabled": app.instrument.code in allowlist,
            "supported": app.instrument.code in INSTRUMENT_INSTRUCTIONS,
        } for app in applications],
    }


@router.post("/{report_id}/specialist-runs/{run_id}/reviews", response={201: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut})
def review_specialist_run(request, report_id: int, run_id: int, payload: ReviewRequestIn):
    if not owned_reports(Report.objects.all(), request.auth).filter(pk=report_id).exists():
        return 404, {"message": "Laudo inexistente."}
    try:
        review = SpecialistReviewService.review(user=request.auth, report_id=report_id, run_id=run_id, **payload.model_dump())
    except (Report.DoesNotExist, SpecialistRun.DoesNotExist):
        return 404, {"message": "Execução inexistente."}
    except PermissionError as exc:
        return 403, {"message": str(exc)}
    except ValueError as exc:
        return 400, {"message": str(exc)}
    return 201, serialize_review(review)
