import base64

from django.core.files.base import ContentFile
from django.http import FileResponse
from ninja import Router
from ninja.errors import HttpError

from apps.accounts.models import UserRole
from apps.api.auth import bearer_auth
from apps.common.clinical_access import owned_evaluations, owned_patients
from apps.evaluations.models import Evaluation
from apps.patients.models import Patient

from apps.documents.selectors import get_document_by_id, get_documents_by_evaluation
from apps.documents.services import create_document, delete_document, update_document

from .schemas import DocumentOut, DocumentUpdateIn, DocumentUploadIn, MessageOut


router = Router(tags=["documents"])


def can_view_documents(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
        UserRole.REVIEWER,
        UserRole.READONLY,
    }


def can_edit_documents(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
    }


def serialize_document(document) -> dict:
    return {
        "id": document.id,
        "evaluation_id": document.evaluation_id,
        "patient_id": document.patient_id,
        "title": document.title,
        "file_name": document.file.name.split("/")[-1] if document.file else "",
        "file_url": f"/api/documents/download/{document.pk}" if document.file else "",
        "document_type": document.document_type,
        "document_type_display": document.get_document_type_display(),
        "source": document.source or "",
        "document_date": document.document_date,
        "notes": document.notes or "",
        "is_relevant_for_report": document.is_relevant_for_report,
        "created_at": document.created_at.isoformat() if document.created_at else None,
    }


@router.get("list", response=list[DocumentOut], auth=bearer_auth)
def list_documents(request, evaluation_id: int) -> list[dict]:
    if not can_view_documents(request.auth):
        raise HttpError(403, "Você não tem permissão para visualizar documentos.")
    return [
        serialize_document(item) for item in get_documents_by_evaluation(evaluation_id, user=request.auth)
    ]


@router.get(
    "get/{document_id}", response={200: DocumentOut, 404: MessageOut}, auth=bearer_auth
)
def get_document_endpoint(request, document_id: int) -> tuple[int, dict]:
    if not can_view_documents(request.auth):
        raise HttpError(403, "Você não tem permissão para visualizar documentos.")

    document = get_document_by_id(document_id, user=request.auth)
    if not document:
        return 404, {"message": "Documento não encontrado."}
    return 200, serialize_document(document)


@router.get("download/{document_id}", auth=bearer_auth)
def download_document(request, document_id: int):
    if not can_view_documents(request.auth):
        raise HttpError(403, "Permissão negada.")
    document = get_document_by_id(document_id, user=request.auth)
    if not document or not document.file:
        raise HttpError(404, "Documento não encontrado.")
    try:
        stream = document.file.open("rb")
    except FileNotFoundError:
        raise HttpError(404, "Arquivo não encontrado.") from None
    response = FileResponse(stream, as_attachment=True, filename=document.file.name.split("/")[-1])
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@router.post(
    "add",
    response={201: DocumentOut, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def upload_document_endpoint(request, payload: DocumentUploadIn) -> tuple[int, dict]:
    if not can_edit_documents(request.auth):
        return 403, {"message": "Você não tem permissão para enviar documentos."}

    evaluation = (
        owned_evaluations(Evaluation.objects.all(), request.auth).filter(id=payload.evaluation_id)
        .select_related("patient")
        .first()
    )
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    patient = owned_patients(Patient.objects.all(), request.auth).filter(id=payload.patient_id).first()
    if not patient:
        return 404, {"message": "Paciente não encontrado."}

    if evaluation.patient_id != patient.id:
        return 400, {"message": "Paciente não corresponde à avaliação informada."}

    try:
        file_content = base64.b64decode(payload.file_content)
    except Exception:
        return 400, {"message": "Arquivo inválido."}

    file_obj = ContentFile(file_content, name=payload.file_name)

    document = create_document(
        evaluation=evaluation,
        patient=patient,
        title=payload.title,
        file=file_obj,
        document_type=payload.document_type,
        source=payload.source,
        document_date=payload.document_date,
        notes=payload.notes,
        is_relevant_for_report=payload.is_relevant_for_report,
    )
    return 201, serialize_document(document)


@router.patch(
    "update/{document_id}",
    response={200: DocumentOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def update_document_endpoint(
    request, document_id: int, payload: DocumentUpdateIn
) -> tuple[int, dict]:
    if not can_edit_documents(request.auth):
        return 403, {"message": "Você não tem permissão para editar documentos."}

    document = get_document_by_id(document_id, user=request.auth)
    if not document:
        return 404, {"message": "Documento não encontrado."}

    updated = update_document(document, **payload.dict(exclude_unset=True))
    return 200, serialize_document(updated)


@router.delete(
    "delete/{document_id}",
    response={200: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def delete_document_endpoint(request, document_id: int) -> tuple[int, dict]:
    if not can_edit_documents(request.auth):
        return 403, {"message": "Você não tem permissão para excluir documentos."}

    document = get_document_by_id(document_id, user=request.auth)
    if not document:
        return 404, {"message": "Documento não encontrado."}

    delete_document(document)
    return 200, {"message": "Documento excluído com sucesso."}
