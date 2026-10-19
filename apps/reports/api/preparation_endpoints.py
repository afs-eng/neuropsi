from django.http import HttpResponse
from ninja import Router, Schema
from pydantic import Field

from apps.api.auth import bearer_auth
from apps.evaluations.models import Evaluation
from apps.reports.models import Report
from apps.reports.services.report_preparation_service import PreparationConflict, ReportPreparationService

router = Router(tags=["report-preparations"], auth=bearer_auth)


class PreparationIn(Schema):
    report_id: int | None = Field(default=None, gt=0)


class MessageOut(Schema):
    message: str


@router.get("/evaluations/{evaluation_id}", response={200: dict, 404: MessageOut})
def preparation_status(request, evaluation_id: int, response: HttpResponse, report_id: int | None = None):
    response["Cache-Control"] = "private, no-store"
    try:
        return ReportPreparationService.status(user=request.auth, evaluation_id=evaluation_id, report_id=report_id)
    except (Evaluation.DoesNotExist, Report.DoesNotExist):
        return 404, {"message": "Avaliação ou laudo inexistente."}


@router.post("/evaluations/{evaluation_id}", response={200: dict, 201: dict, 403: MessageOut, 404: MessageOut, 409: MessageOut})
def prepare_report(request, evaluation_id: int, payload: PreparationIn, response: HttpResponse):
    response["Cache-Control"] = "private, no-store"
    try:
        # Conferir escopo antes da flag para não revelar dados de outras contas.
        ReportPreparationService.evaluation(request.auth, evaluation_id)
        preparation, checked, created = ReportPreparationService.start(
            user=request.auth, evaluation_id=evaluation_id, report_id=payload.report_id,
        )
    except (Evaluation.DoesNotExist, Report.DoesNotExist):
        return 404, {"message": "Avaliação ou laudo inexistente."}
    except PermissionError as exc:
        return 403, {"message": str(exc)}
    except PreparationConflict as exc:
        return 409, {"message": str(exc)}
    return (201 if created else 200), {
        "preparation": ReportPreparationService.serialize(preparation, checked["source_sha256"]),
        "created": created, "ready_for_execution": False,
        "message": "Fontes registradas. Nenhuma execução de IA foi agendada.",
    }
