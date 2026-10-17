from django.http import HttpResponse
from ninja import Router, Schema
from pydantic import Field

from apps.api.auth import bearer_auth
from apps.common.clinical_access import owned_reports
from apps.reports.models import Report, SpecialistRun
from apps.reports.services.specialist_run_service import SpecialistRunService

router = Router(tags=["report-specialists"], auth=bearer_auth)


class RunRequestIn(Schema):
    application_ids: list[int] | None = Field(default=None, min_length=1, max_length=30)


class MessageOut(Schema):
    message: str


def serialize_run(run):
    current = SpecialistRunService.is_current(run)
    return {
        "id": run.pk,
        "application_id": run.application_id,
        "instrument_code": run.instrument_code,
        "specialist_version": run.specialist_version,
        "source_sha256": run.source_sha256,
        "model": run.model_name,
        "status": run.status if current else SpecialistRun.Status.STALE,
        "is_current": current,
        "requires_professional_review": True,
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
    ).order_by("-created_at", "-id")[:100]
    return [serialize_run(run) for run in runs]
