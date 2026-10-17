from ninja import Router, Query
from ninja.errors import HttpError
from django.db.models.deletion import ProtectedError

from apps.api.auth import bearer_auth
from apps.accounts.models import UserRole
from apps.patients.selectors import (
    get_patient_by_id,
    get_patients,
    search_patients,
)
from apps.patients.services import create_patient, update_patient, delete_patient

from .schemas import PatientOut, PatientCreateIn, PatientUpdateIn, MessageOut


router = Router(tags=["patients"])


def can_view_patients(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
        UserRole.REVIEWER,
        UserRole.READONLY,
    }


def can_edit_patients(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
    }


def can_access_patient(user, patient) -> bool:
    return patient.created_by_id == user.pk



def serialize_patient(patient):
    return {
        "id": patient.id,
        "full_name": patient.full_name,
        "birth_date": patient.birth_date,
        "sex": patient.sex or None,
        "schooling": patient.schooling or None,
        "school_name": patient.school_name or None,
        "grade_year": patient.grade_year or None,
        "mother_name": patient.mother_name or None,
        "father_name": patient.father_name or None,
        "phone": patient.phone or None,
        "email": patient.email or None,
        "city": patient.city or None,
        "state": patient.state or None,
        "notes": patient.notes or None,
        "responsible_name": patient.responsible_name or None,
        "responsible_phone": patient.responsible_phone or None,
    }


@router.get("/", response=list[PatientOut], auth=bearer_auth)
def list_patients(request, q: str | None = Query(default=None)):
    user = request.auth

    if not can_view_patients(user):
        raise HttpError(403, "Você não tem permissão para visualizar pacientes.")

    patients = (
        search_patients(q, user=user) if q else get_patients(user=user)
    )
    return [serialize_patient(patient) for patient in patients]



@router.get(
    "/{patient_id}",
    response={200: PatientOut, 404: MessageOut},
    auth=bearer_auth,
)
def get_patient_endpoint(request, patient_id: int):
    user = request.auth

    if not can_view_patients(user):
        raise HttpError(403, "Você não tem permissão para visualizar pacientes.")

    patient = get_patient_by_id(patient_id, user=user)
    if not patient:
        return 404, {"message": "Paciente não encontrado."}

    if not can_access_patient(user, patient):
        raise HttpError(
            403, "Você não tem permissão para acessar os dados deste paciente."
        )

    return 200, serialize_patient(patient)



@router.post(
    "/",
    response={201: PatientOut, 403: MessageOut},
    auth=bearer_auth,
)
def create_patient_endpoint(request, payload: PatientCreateIn):
    user = request.auth

    if not can_edit_patients(user):
        return 403, {"message": "Você não tem permissão para criar pacientes."}

    patient = create_patient(**payload.dict(), created_by=user)
    return 201, serialize_patient(patient)



@router.patch(
    "/{patient_id}",
    response={200: PatientOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def update_patient_endpoint(request, patient_id: int, payload: PatientUpdateIn):
    user = request.auth

    if not can_edit_patients(user):
        return 403, {"message": "Você não tem permissão para editar pacientes."}

    patient = get_patient_by_id(patient_id, user=user)
    if not patient:
        return 404, {"message": "Paciente não encontrado."}

    if not can_access_patient(user, patient):
        raise HttpError(
            403, "Você não tem permissão para editar os dados deste paciente."
        )

    patient = update_patient(patient, **payload.dict(exclude_unset=True))
    return 200, serialize_patient(patient)


@router.delete(
    "/{patient_id}",
    response={200: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def delete_patient_endpoint(request, patient_id: int) -> tuple[int, dict]:
    user = request.auth

    if not can_edit_patients(user):
        return 403, {"message": "Você não tem permissão para excluir pacientes."}

    patient = get_patient_by_id(patient_id, user=user)
    if not patient:
        return 404, {"message": "Paciente não encontrado."}

    if not can_access_patient(user, patient):
        return 403, {"message": "Você não tem permissão para excluir este paciente."}

    try:
        delete_patient(patient)
    except ProtectedError:
        return 403, {"message": "O paciente possui laudo aprovado preservado e não pode ser excluído por este fluxo."}
    return 200, {"message": "Paciente excluído com sucesso."}
