from datetime import date as date_cls
from ninja import Router, Query
from ninja.errors import HttpError

from apps.api.auth import bearer_auth
from apps.accounts.models import User, UserRole
from apps.patients.models import Patient
from apps.evaluations.models import Evaluation, EvaluationStatus, EvaluationPriority
from apps.evaluations.selectors import (
    get_evaluation_by_id,
    get_evaluations,
    get_evaluations_by_patient,
    get_progress_entry_by_id,
    get_progress_entries_by_evaluation,
)
from apps.evaluations.services import (
    create_evaluation,
    update_evaluation,
    delete_evaluation,
    create_progress_entry,
    update_progress_entry,
    delete_progress_entry,
)
from apps.anamnesis.services import get_current_response_summary
from apps.documents.selectors import get_relevant_documents_by_evaluation
from apps.tests.selectors import get_validated_test_applications_by_evaluation
from apps.tests.services import TestReportPayloadService

from .schemas import (
    EvaluationOut,
    EvaluationCreateIn,
    EvaluationUpdateIn,
    EvaluationDetailOut,
    ProgressEntryOut,
    ProgressEntryCreateIn,
    ProgressEntryUpdateIn,
    TestApplicationOut,
    DocumentOut,
    MessageOut,
)


router = Router(tags=["evaluations"])


def can_view_evaluations(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
        UserRole.REVIEWER,
        UserRole.READONLY,
    }


def can_edit_evaluations(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
    }


def can_access_evaluation(user, evaluation) -> bool:
    if user.is_superuser or user.role in ["admin", "reviewer"]:
        return True
    return evaluation.examiner == user


def serialize_evaluation(evaluation, include_details=False):
    patient = evaluation.patient
    examiner = evaluation.examiner

    data = {
        "id": evaluation.id,
        "code": f"AV-{evaluation.id:04d}",
        "title": evaluation.title or "",
        "patient_id": patient.id,
        "patient_name": patient.full_name,
        "patient_birth_date": patient.birth_date,
        "patient_sex": patient.sex,
        "patient_responsible_name": patient.responsible_name,
        "examiner_id": examiner.id if examiner else None,
        "examiner_name": examiner.display_name if examiner else None,
        "referral_reason": evaluation.referral_reason or "",
        "evaluation_purpose": evaluation.evaluation_purpose or "",
        "clinical_hypothesis": evaluation.clinical_hypothesis or "",
        "start_date": evaluation.start_date,
        "end_date": evaluation.end_date,
        "status": evaluation.status,
        "status_display": evaluation.get_status_display(),
        "priority": evaluation.priority,
        "priority_display": evaluation.get_priority_display(),
        "is_archived": evaluation.is_archived,
        "general_notes": evaluation.general_notes or "",
        "created_at": evaluation.created_at.isoformat()
        if evaluation.created_at
        else None,
        "updated_at": evaluation.updated_at.isoformat()
        if evaluation.updated_at
        else None,
    }

    if include_details:
        from apps.tests.models import TestApplication
        from apps.documents.models import EvaluationDocument

        tests = TestApplication.objects.filter(evaluation=evaluation).select_related(
            "instrument"
        )
        data["tests"] = [
            {
                "id": t.id,
                "instrument_name": t.instrument.name,
                "instrument_code": t.instrument.code,
                "applied_on": t.applied_on,
                "is_validated": t.is_validated,
                "status": t.status,
                "status_display": t.get_status_display(),
                "report_payload": TestReportPayloadService.build_for_application(t),
            }
            for t in tests
        ]
        documents = EvaluationDocument.objects.filter(evaluation=evaluation)
        data["documents"] = [
            {
                "id": d.id,
                "name": d.title,
                "file_type": d.document_type,
                "uploaded_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in documents
        ]
        data["progress_entries"] = [
            serialize_progress_entry(item)
            for item in get_progress_entries_by_evaluation(evaluation.id)
        ]
        current_anamnesis = get_current_response_summary(evaluation.id)
        data["current_anamnesis"] = current_anamnesis
        has_relevant_documents = get_relevant_documents_by_evaluation(
            evaluation.id
        ).exists()
        has_progress_entries_for_report = any(
            item["include_in_report"] for item in data["progress_entries"]
        )
        has_validated_tests = get_validated_test_applications_by_evaluation(
            evaluation.id
        ).exists()
        anamnesis_completed = bool(
            current_anamnesis
            and current_anamnesis["status"] in {"submitted", "reviewed"}
        )
        anamnesis_reviewed = bool(
            current_anamnesis and current_anamnesis["status"] == "reviewed"
        )
        data["clinical_checklist"] = {
            "anamnesis_completed": anamnesis_completed,
            "anamnesis_reviewed": anamnesis_reviewed,
            "has_relevant_documents": has_relevant_documents,
            "has_progress_entries_for_report": has_progress_entries_for_report,
            "has_validated_tests": has_validated_tests,
            "ready_for_report": anamnesis_completed
            and has_progress_entries_for_report
            and has_validated_tests,
        }

    return data


def serialize_progress_entry(entry):
    return {
        "id": entry.id,
        "evaluation_id": entry.evaluation_id,
        "patient_id": entry.patient_id,
        "professional_id": entry.professional_id,
        "professional_name": entry.professional.display_name,
        "entry_type": entry.entry_type,
        "entry_type_display": entry.get_entry_type_display(),
        "entry_date": entry.entry_date,
        "start_time": entry.start_time,
        "end_time": entry.end_time,
        "objective": entry.objective or "",
        "tests_applied": entry.tests_applied or "",
        "observed_behavior": entry.observed_behavior or "",
        "clinical_notes": entry.clinical_notes or "",
        "next_steps": entry.next_steps or "",
        "include_in_report": entry.include_in_report,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }


@router.get("/", response=list[EvaluationOut], auth=bearer_auth)
def list_evaluations(
    request, patient_id: int | None = Query(default=None)
) -> list[dict]:
    user = request.auth

    if not can_view_evaluations(user):
        raise HttpError(403, "Você não tem permissão para visualizar avaliações.")

    evaluations = (
        get_evaluations_by_patient(patient_id, user=user)
        if patient_id
        else get_evaluations(user=user)
    )
    return [serialize_evaluation(evaluation) for evaluation in evaluations]


@router.get(
    "/{evaluation_id}",
    response={200: EvaluationDetailOut, 404: MessageOut},
    auth=bearer_auth,
)
def get_evaluation_endpoint(request, evaluation_id: int) -> tuple[int, dict]:
    user = request.auth

    if not can_view_evaluations(user):
        raise HttpError(403, "Você não tem permissão para visualizar avaliações.")

    evaluation = get_evaluation_by_id(evaluation_id)
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    if not can_access_evaluation(user, evaluation):
        raise HttpError(403, "Você não tem permissão para visualizar esta avaliação.")

    return 200, serialize_evaluation(evaluation, include_details=True)


@router.post(
    "/",
    response={201: EvaluationOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def create_evaluation_endpoint(
    request, payload: EvaluationCreateIn
) -> tuple[int, dict]:
    user = request.auth

    if not can_edit_evaluations(user):
        return 403, {"message": "Você não tem permissão para criar avaliações."}

    patient = Patient.objects.filter(id=payload.patient_id).first()
    if not patient:
        return 404, {"message": "Paciente não encontrado."}

    examiner = user
    if payload.examiner_id:
        examiner = User.objects.filter(id=payload.examiner_id, is_active=True).first()

    evaluation = create_evaluation(
        patient=patient,
        examiner=examiner,
        title=payload.title or "",
        referral_reason=payload.referral_reason or "",
        evaluation_purpose=payload.evaluation_purpose or "",
        clinical_hypothesis=payload.clinical_hypothesis or "",
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status or EvaluationStatus.DRAFT,
        priority=payload.priority or EvaluationPriority.MEDIUM,
        general_notes=payload.general_notes or "",
    )

    return 201, serialize_evaluation(evaluation)


@router.patch(
    "/{evaluation_id}",
    response={200: EvaluationOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def update_evaluation_endpoint(
    request, evaluation_id: int, payload: EvaluationUpdateIn
) -> tuple[int, dict]:
    user = request.auth

    if not can_edit_evaluations(user):
        return 403, {"message": "Você não tem permissão para editar avaliações."}

    evaluation = get_evaluation_by_id(evaluation_id)
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    if not can_access_evaluation(user, evaluation):
        raise HttpError(403, "Você não tem permissão para editar esta avaliação.")

    data = payload.dict(exclude_unset=True)

    if "patient_id" in data:
        patient = Patient.objects.filter(id=data["patient_id"]).first()
        if not patient:
            return 404, {"message": "Paciente não encontrado."}
        data["patient"] = patient
        del data["patient_id"]

    if "examiner_id" in data:
        examiner = None
        if data["examiner_id"]:
            examiner = User.objects.filter(
                id=data["examiner_id"], is_active=True
            ).first()
        data["examiner"] = examiner
        del data["examiner_id"]

    evaluation = update_evaluation(evaluation, **data)
    return 200, serialize_evaluation(evaluation)


@router.delete(
    "/{evaluation_id}",
    response={200: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def delete_evaluation_endpoint(request, evaluation_id: int) -> tuple[int, dict]:
    user = request.auth

    if not can_edit_evaluations(user):
        return 403, {"message": "Você não tem permissão para excluir avaliações."}

    evaluation = get_evaluation_by_id(evaluation_id)
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    if not can_access_evaluation(user, evaluation):
        return 403, {"message": "Você não tem permissão para excluir esta avaliação."}

    delete_evaluation(evaluation)
    return 200, {"message": "Avaliação excluída com sucesso."}


@router.post(
    "/progress-entries",
    response={201: ProgressEntryOut, 403: MessageOut, 404: MessageOut, 400: MessageOut},
    auth=bearer_auth,
)
def create_progress_entry_endpoint(
    request, payload: ProgressEntryCreateIn
) -> tuple[int, dict]:
    if not can_edit_evaluations(request.auth):
        return 403, {"message": "Você não tem permissão para criar evoluções."}

    evaluation = (
        Evaluation.objects.filter(id=payload.evaluation_id)
        .select_related("patient")
        .first()
    )
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}
    if evaluation.patient_id != payload.patient_id:
        return 400, {"message": "Paciente não corresponde à avaliação informada."}

    professional = request.auth
    if payload.professional_id:
        professional = User.objects.filter(
            id=payload.professional_id, is_active=True
        ).first()
        if not professional:
            return 404, {"message": "Profissional não encontrado."}

    entry = create_progress_entry(
        evaluation=evaluation,
        patient=evaluation.patient,
        professional=professional,
        entry_type=payload.entry_type,
        entry_date=payload.entry_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        objective=payload.objective or "",
        tests_applied=payload.tests_applied or "",
        observed_behavior=payload.observed_behavior or "",
        clinical_notes=payload.clinical_notes or "",
        next_steps=payload.next_steps or "",
        include_in_report=payload.include_in_report,
    )
    return 201, serialize_progress_entry(entry)


@router.get(
    "/{evaluation_id}/progress-entries",
    response=list[ProgressEntryOut],
    auth=bearer_auth,
)
def list_progress_entries_endpoint(request, evaluation_id: int) -> list[dict]:
    if not can_view_evaluations(request.auth):
        raise HttpError(403, "Você não tem permissão para visualizar evoluções.")
    evaluation = Evaluation.objects.filter(id=evaluation_id).first()
    if not evaluation or not can_access_evaluation(request.auth, evaluation):
        raise HttpError(403, "Você não tem permissão para acessar esta avaliação.")
    return [
        serialize_progress_entry(item)
        for item in get_progress_entries_by_evaluation(evaluation_id)
    ]


@router.patch(
    "/progress-entries/{entry_id}",
    response={200: ProgressEntryOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def update_progress_entry_endpoint(
    request, entry_id: int, payload: ProgressEntryUpdateIn
) -> tuple[int, dict]:
    if not can_edit_evaluations(request.auth):
        return 403, {"message": "Você não tem permissão para editar evoluções."}

    entry = get_progress_entry_by_id(entry_id)
    if not entry:
        return 404, {"message": "Evolução não encontrada."}

    data = payload.dict(exclude_unset=True)
    if "professional_id" in data:
        professional = (
            request.auth
            if not data["professional_id"]
            else User.objects.filter(id=data["professional_id"], is_active=True).first()
        )
        if not professional:
            return 404, {"message": "Profissional não encontrado."}
        data["professional"] = professional
        del data["professional_id"]

    updated = update_progress_entry(entry, **data)
    return 200, serialize_progress_entry(updated)


@router.delete(
    "/progress-entries/{entry_id}",
    response={200: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def delete_progress_entry_endpoint(request, entry_id: int) -> tuple[int, dict]:
    if not can_edit_evaluations(request.auth):
        return 403, {"message": "Você não tem permissão para excluir evoluções."}

    entry = get_progress_entry_by_id(entry_id)
    if not entry:
        return 404, {"message": "Evolução não encontrada."}

    delete_progress_entry(entry)
    return 200, {"message": "Evolução excluída com sucesso."}
