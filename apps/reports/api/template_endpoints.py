from django.http import HttpResponse
from ninja import File, Router, Schema
from ninja.files import UploadedFile

from apps.api.auth import bearer_auth
from apps.reports.api.endpoints import can_edit_reports
from apps.reports.models import ReportTemplate, ReportTemplateVersion
from apps.reports.services.report_template_service import ReportTemplateService

router = Router(tags=["report-templates"], auth=bearer_auth)


class TemplateCreateIn(Schema):
    name: str
    instrument_code: str = ""


class MessageOut(Schema):
    message: str


def serialize_version(version):
    return {
        "id": version.pk,
        "version_number": version.version_number,
        "sha256": version.sha256,
        "original_filename": version.original_filename,
        "validation": version.validation_payload,
        "created_at": version.created_at.isoformat(),
    }


@router.get("/", response=list[dict])
def list_templates(request):
    return [
        {
            "id": template.pk,
            "name": template.name,
            "instrument_code": template.instrument_code,
            "versions": [serialize_version(v) for v in template.versions.all()],
        }
        for template in ReportTemplate.objects.filter(owner=request.auth).prefetch_related("versions")
    ]


@router.post("/", response={201: dict, 400: MessageOut, 403: MessageOut})
def create_template(request, payload: TemplateCreateIn):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}
    name = payload.name.strip()
    code = payload.instrument_code.strip().lower()
    if not name or len(name) > 255 or len(code) > 50:
        return 400, {"message": "Informe nome e código do instrumento válidos."}
    template = ReportTemplate.objects.create(owner=request.auth, name=name, instrument_code=code)
    return 201, {"id": template.pk, "name": template.name, "instrument_code": code}


@router.post("/{template_id}/versions", response={201: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut})
def upload_version(request, template_id: int, file: UploadedFile = File(...)):
    if not can_edit_reports(request.auth):
        return 403, {"message": "Permissão negada."}
    if not ReportTemplate.objects.filter(pk=template_id, owner=request.auth).exists():
        return 404, {"message": "Modelo inexistente."}
    try:
        version = ReportTemplateService.add_version(
            owner=request.auth,
            template_id=template_id,
            filename=file.name,
            data=file.read(ReportTemplateService.MAX_UPLOAD_BYTES + 1),
        )
    except ReportTemplate.DoesNotExist:
        return 404, {"message": "Modelo inexistente."}
    except ValueError as exc:
        return 400, {"message": str(exc)}
    return 201, serialize_version(version)


@router.get("/{template_id}/versions/{version_id}/download", response={404: MessageOut})
def download_version(request, template_id: int, version_id: int):
    version = ReportTemplateVersion.objects.filter(
        pk=version_id, template_id=template_id, template__owner=request.auth
    ).first()
    if version is None:
        return 404, {"message": "Versão inexistente."}
    response = HttpResponse(
        bytes(version.document),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="modelo-{template_id}-v{version.version_number}.docx"'
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
