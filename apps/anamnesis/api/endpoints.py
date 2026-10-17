from django.conf import settings
from ninja import Query, Router
from ninja.errors import HttpError

from apps.accounts.models import UserRole
from apps.api.auth import bearer_auth
from apps.common.clinical_access import owned_evaluations, owned_patients
from apps.common.security import rate_limit
from apps.evaluations.models import Evaluation
from apps.patients.models import Patient

from apps.anamnesis.selectors import (
    get_active_templates,
    get_internal_responses_by_evaluation,
    get_current_anamnesis_response_by_evaluation,
    get_invite_by_id,
    get_invite_by_token,
    get_response_by_id,
    get_responses_by_evaluation,
    get_template_by_id,
    get_invites_by_evaluation,
)
from apps.anamnesis.services import (
    build_public_url,
    cancel_invite,
    create_invite,
    create_internal_response,
    invite_access_state,
    review_response,
    save_draft_response,
    send_invite,
    submit_internal_response,
    sync_default_templates,
    submit_response,
    touch_invite_open,
    update_response_draft,
)
from apps.audit.services import AuditService

from .schemas import (
    AnamnesisInviteCreateIn,
    AnamnesisInviteOut,
    AnamnesisResponseCreateIn,
    AnamnesisResponseOut,
    AnamnesisResponseReviewIn,
    AnamnesisResponseSubmitIn,
    AnamnesisResponseUpdateIn,
    AnamnesisTemplateOut,
    MessageOut,
    PublicAnamnesisDraftIn,
    PublicAnamnesisOut,
    PublicAnamnesisSubmitIn,
)


router = Router(tags=["anamnesis"])
public_router = Router(tags=["public-anamnesis"])


def can_view(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
        UserRole.REVIEWER,
        UserRole.READONLY,
    }


def can_edit(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
        UserRole.REVIEWER,
    }


def frontend_base_url() -> str:
    return getattr(settings, "FRONTEND_BASE_URL", "http://localhost:3000")


def serialize_invite(invite) -> dict:
    return {
        "id": invite.id,
        "evaluation_id": invite.evaluation_id,
        "patient_id": invite.patient_id,
        "template_id": invite.template_id,
        "template_name": invite.template.name,
        "template_target_type": invite.template.target_type,
        "recipient_name": invite.recipient_name,
        "recipient_email": invite.recipient_email or "",
        "recipient_phone": invite.recipient_phone or "",
        "channel": invite.channel,
        "token": invite.token,
        "public_url": build_public_url(invite.token, frontend_base_url()),
        "status": invite.status,
        "sent_at": invite.sent_at.isoformat() if invite.sent_at else None,
        "opened_at": invite.opened_at.isoformat() if invite.opened_at else None,
        "last_activity_at": invite.last_activity_at.isoformat()
        if invite.last_activity_at
        else None,
        "completed_at": invite.completed_at.isoformat()
        if invite.completed_at
        else None,
        "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
        "created_by_name": invite.created_by.display_name
        if invite.created_by
        else None,
        "created_at": invite.created_at.isoformat() if invite.created_at else None,
        "message": invite.message or "",
        "delivery_payload": invite.delivery_payload or {},
    }


def serialize_response(response) -> dict:
    return {
        "id": response.id,
        "invite_id": response.invite_id,
        "evaluation_id": response.evaluation_id,
        "patient_id": response.patient_id,
        "template_id": response.template_id,
        "template_name": response.template.name,
        "response_type": response.response_type,
        "source": response.source,
        "answers_payload": response.answers_payload or {},
        "summary_payload": response.summary_payload or {},
        "status": response.status,
        "submitted_by_name": response.submitted_by_name or "",
        "submitted_by_relation": response.submitted_by_relation or "",
        "submitted_at": response.submitted_at.isoformat()
        if response.submitted_at
        else None,
        "reviewed_by_name": response.reviewed_by.display_name
        if response.reviewed_by
        else None,
        "created_by_name": response.created_by.display_name
        if response.created_by
        else None,
        "reviewed_at": response.reviewed_at.isoformat()
        if response.reviewed_at
        else None,
        "created_at": response.created_at.isoformat() if response.created_at else None,
        "updated_at": response.updated_at.isoformat() if response.updated_at else None,
    }


@router.get("/templates", response=list[AnamnesisTemplateOut], auth=bearer_auth)
def list_templates(request):
    if not can_view(request.auth):
        raise HttpError(
            403, "Você não tem permissão para visualizar templates de anamnese."
        )
    sync_default_templates()
    return list(
        get_active_templates().values(
            "id",
            "code",
            "name",
            "target_type",
            "version",
            "schema_payload",
            "is_active",
        )
    )


@router.get(
    "/templates/{template_id}",
    response={200: AnamnesisTemplateOut, 404: MessageOut},
    auth=bearer_auth,
)
def get_template_endpoint(request, template_id: int):
    if not can_view(request.auth):
        raise HttpError(
            403, "Você não tem permissão para visualizar templates de anamnese."
        )
    sync_default_templates()
    template = get_template_by_id(template_id)
    if not template:
        return 404, {"message": "Template de anamnese não encontrado."}
    return 200, {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "target_type": template.target_type,
        "version": template.version,
        "schema_payload": template.schema_payload or {},
        "is_active": template.is_active,
    }


@router.post(
    "/invites",
    response={
        201: AnamnesisInviteOut,
        400: MessageOut,
        403: MessageOut,
        404: MessageOut,
    },
    auth=bearer_auth,
)
def create_invite_endpoint(request, payload: AnamnesisInviteCreateIn):
    if not can_edit(request.auth):
        return 403, {
            "message": "Você não tem permissão para criar convites de anamnese."
        }
    evaluation = (
        owned_evaluations(Evaluation.objects.all(), request.auth).filter(id=payload.evaluation_id)
        .select_related("patient")
        .first()
    )
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}
    patient = owned_patients(Patient.objects.all(), request.auth).filter(id=payload.patient_id).first()
    if not patient or patient.id != evaluation.patient_id:
        return 400, {"message": "Paciente inválido para a avaliação informada."}
    template = get_template_by_id(payload.template_id)
    if not template:
        return 404, {"message": "Template de anamnese não encontrado."}
    invite = create_invite(
        evaluation=evaluation,
        patient=patient,
        template=template,
        created_by=request.auth,
        recipient_name=payload.recipient_name,
        recipient_email=payload.recipient_email or "",
        recipient_phone=payload.recipient_phone or "",
        channel=payload.channel,
        message=payload.message or "",
        expires_at=payload.expires_at,
    )
    return 201, serialize_invite(invite)


@router.get("/invites", response=list[AnamnesisInviteOut], auth=bearer_auth)
def list_invites_endpoint(request, evaluation_id: int = Query(...)):
    if not can_view(request.auth):
        raise HttpError(
            403, "Você não tem permissão para visualizar convites de anamnese."
        )
    return [serialize_invite(item) for item in get_invites_by_evaluation(evaluation_id, user=request.auth)]


@router.get(
    "/invites/{invite_id}",
    response={200: AnamnesisInviteOut, 404: MessageOut},
    auth=bearer_auth,
)
def get_invite_endpoint(request, invite_id: int):
    if not can_view(request.auth):
        raise HttpError(
            403, "Você não tem permissão para visualizar convites de anamnese."
        )
    invite = get_invite_by_id(invite_id, user=request.auth)
    if not invite:
        return 404, {"message": "Convite não encontrado."}
    return 200, serialize_invite(invite)


@router.post(
    "/invites/{invite_id}/send-email",
    response={200: AnamnesisInviteOut, 400: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def send_invite_email_endpoint(request, invite_id: int):
    if not can_edit(request.auth):
        raise HttpError(403, "Você não tem permissão para enviar convites.")
    invite = get_invite_by_id(invite_id, user=request.auth)
    if not invite:
        return 404, {"message": "Convite não encontrado."}
    if not invite.recipient_email:
        return 400, {"message": "Este convite não possui e-mail cadastrado."}
    invite.channel = "email"
    try:
        send_invite(invite, frontend_base_url())
    except Exception as exc:
        return 400, {"message": f"Erro ao enviar e-mail: {exc}"}
    return 200, serialize_invite(invite)


@router.post(
    "/invites/{invite_id}/send-whatsapp",
    response={200: AnamnesisInviteOut, 400: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def send_invite_whatsapp_endpoint(request, invite_id: int):
    if not can_edit(request.auth):
        raise HttpError(403, "Você não tem permissão para enviar convites.")
    invite = get_invite_by_id(invite_id, user=request.auth)
    if not invite:
        return 404, {"message": "Convite não encontrado."}
    if not invite.recipient_phone:
        return 400, {"message": "Este convite não possui telefone cadastrado."}
    invite.channel = "whatsapp"
    try:
        send_invite(invite, frontend_base_url())
    except Exception as exc:
        return 400, {"message": f"Erro ao enviar WhatsApp: {exc}"}
    return 200, serialize_invite(invite)


@router.post(
    "/invites/{invite_id}/resend",
    response={200: AnamnesisInviteOut, 404: MessageOut},
    auth=bearer_auth,
)
def resend_invite_endpoint(request, invite_id: int):
    if not can_edit(request.auth):
        raise HttpError(403, "Você não tem permissão para reenviar convites.")
    invite = get_invite_by_id(invite_id, user=request.auth)
    if not invite:
        return 404, {"message": "Convite não encontrado."}
    send_invite(invite, frontend_base_url())
    return 200, serialize_invite(invite)


@router.post(
    "/invites/{invite_id}/cancel",
    response={200: AnamnesisInviteOut, 404: MessageOut},
    auth=bearer_auth,
)
def cancel_invite_endpoint(request, invite_id: int):
    if not can_edit(request.auth):
        raise HttpError(403, "Você não tem permissão para cancelar convites.")
    invite = get_invite_by_id(invite_id, user=request.auth)
    if not invite:
        return 404, {"message": "Convite não encontrado."}
    return 200, serialize_invite(cancel_invite(invite))


@router.get("/responses", response=list[AnamnesisResponseOut], auth=bearer_auth)
def list_responses_endpoint(request, evaluation_id: int = Query(...)):
    if not can_view(request.auth):
        raise HttpError(
            403, "Você não tem permissão para visualizar respostas de anamnese."
        )
    return [
        serialize_response(item) for item in get_responses_by_evaluation(evaluation_id, user=request.auth)
    ]


@router.get(
    "/responses/current/{evaluation_id}",
    response={200: AnamnesisResponseOut, 404: MessageOut},
    auth=bearer_auth,
)
def get_current_response_endpoint(request, evaluation_id: int):
    if not can_view(request.auth):
        raise HttpError(
            403, "Você não tem permissão para visualizar respostas de anamnese."
        )
    if not owned_evaluations(Evaluation.objects.all(), request.auth).filter(pk=evaluation_id).exists():
        return 404, {"message": "Avaliação não encontrada."}
    response = get_current_anamnesis_response_by_evaluation(evaluation_id)
    if not response:
        return 404, {
            "message": "Nenhuma resposta vigente encontrada para esta avaliação."
        }
    return 200, serialize_response(response)


@router.post(
    "/responses",
    response={
        201: AnamnesisResponseOut,
        400: MessageOut,
        403: MessageOut,
        404: MessageOut,
    },
    auth=bearer_auth,
)
def create_response_endpoint(request, payload: AnamnesisResponseCreateIn):
    if not can_edit(request.auth):
        raise HttpError(403, "Você não tem permissão para criar anamneses internas.")
    evaluation = (
        owned_evaluations(Evaluation.objects.all(), request.auth).filter(id=payload.evaluation_id)
        .select_related("patient")
        .first()
    )
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}
    patient = owned_patients(Patient.objects.all(), request.auth).filter(id=payload.patient_id).first()
    if not patient or patient.id != evaluation.patient_id:
        return 400, {"message": "Paciente inválido para a avaliação informada."}
    template = get_template_by_id(payload.template_id)
    if not template:
        return 404, {"message": "Template de anamnese não encontrado."}
    response = create_internal_response(
        evaluation=evaluation,
        patient=patient,
        template=template,
        created_by=request.auth,
    )
    response = update_response_draft(
        response,
        answers_payload=payload.answers_payload,
        submitted_by_name=payload.submitted_by_name or response.submitted_by_name,
        submitted_by_relation=payload.submitted_by_relation
        or response.submitted_by_relation,
        summary_payload=payload.summary_payload,
    )
    AuditService.track_create(
        request,
        "anamnesis_response",
        str(response.id),
        {"evaluation_id": evaluation.id, "template_id": template.id},
    )
    return 201, serialize_response(response)


@router.get(
    "/responses/{response_id}",
    response={200: AnamnesisResponseOut, 404: MessageOut},
    auth=bearer_auth,
)
def get_response_endpoint(request, response_id: int):
    if not can_view(request.auth):
        raise HttpError(
            403, "Você não tem permissão para visualizar respostas de anamnese."
        )
    response = get_response_by_id(response_id, user=request.auth)
    if not response:
        return 404, {"message": "Resposta não encontrada."}
    return 200, serialize_response(response)


@router.patch(
    "/responses/{response_id}",
    response={200: AnamnesisResponseOut, 404: MessageOut},
    auth=bearer_auth,
)
def update_response_endpoint(
    request, response_id: int, payload: AnamnesisResponseUpdateIn
):
    if not can_edit(request.auth):
        raise HttpError(403, "Você não tem permissão para editar anamneses.")
    response = get_response_by_id(response_id, user=request.auth)
    if not response:
        return 404, {"message": "Resposta não encontrada."}
    response = update_response_draft(
        response,
        answers_payload=payload.answers_payload
        if payload.answers_payload is not None
        else response.answers_payload,
        submitted_by_name=payload.submitted_by_name or response.submitted_by_name,
        submitted_by_relation=payload.submitted_by_relation
        or response.submitted_by_relation,
        summary_payload=payload.summary_payload
        if payload.summary_payload is not None
        else response.summary_payload,
    )
    AuditService.track_update(
        request,
        "anamnesis_response",
        str(response.id),
        {},
        {
            "submitted_by_name": response.submitted_by_name,
            "submitted_by_relation": response.submitted_by_relation,
        },
    )
    return 200, serialize_response(response)


@router.post(
    "/responses/{response_id}/submit",
    response={200: AnamnesisResponseOut, 404: MessageOut},
    auth=bearer_auth,
)
def submit_internal_response_endpoint(
    request, response_id: int, payload: AnamnesisResponseSubmitIn
):
    if not can_edit(request.auth):
        raise HttpError(403, "Você não tem permissão para enviar anamneses.")
    response = get_response_by_id(response_id, user=request.auth)
    if not response:
        return 404, {"message": "Resposta não encontrada."}
    response = submit_internal_response(
        response,
        answers_payload=payload.answers_payload
        if payload.answers_payload is not None
        else response.answers_payload,
        submitted_by_name=payload.submitted_by_name or response.submitted_by_name,
        submitted_by_relation=payload.submitted_by_relation
        or response.submitted_by_relation,
        summary_payload=payload.summary_payload
        if payload.summary_payload is not None
        else response.summary_payload,
    )
    AuditService.log(
        request,
        "submit",
        "anamnesis_response",
        resource_id=str(response.id),
        metadata={"evaluation_id": response.evaluation_id, "source": response.source},
    )
    return 200, serialize_response(response)


@router.patch(
    "/responses/{response_id}/review",
    response={200: AnamnesisResponseOut, 404: MessageOut},
    auth=bearer_auth,
)
def review_response_endpoint(
    request, response_id: int, payload: AnamnesisResponseReviewIn
):
    if not can_edit(request.auth):
        raise HttpError(
            403, "Você não tem permissão para revisar respostas de anamnese."
        )
    response = get_response_by_id(response_id, user=request.auth)
    if not response:
        return 404, {"message": "Resposta não encontrada."}
    response = review_response(
        response,
        reviewed_by=request.auth,
        answers_payload=payload.answers_payload,
        summary_payload=payload.summary_payload,
        status=payload.status or "reviewed",
    )
    AuditService.log(
        request,
        "review",
        "anamnesis_response",
        resource_id=str(response.id),
        metadata={"evaluation_id": response.evaluation_id, "status": response.status},
    )
    return 200, serialize_response(response)


@public_router.get("/{token}", response={200: PublicAnamnesisOut, 404: MessageOut})
def public_get_anamnesis(request, token: str):
    rate_limit(request, "public-anamnesis-get", limit=30, window_seconds=300)

    invite = get_invite_by_token(token)
    if not invite:
        return 404, {"message": "Convite inválido ou não encontrado."}
    access_state = invite_access_state(invite)
    if access_state == "active":
        touch_invite_open(invite)
    response = getattr(invite, "response", None)
    return 200, {
        "invite_id": invite.id,
        "status": invite.status,
        "patient_name": invite.patient.full_name,
        "template_name": invite.template.name,
        "target_type": invite.template.target_type,
        "schema_payload": invite.template.schema_payload or {},
        "answers_payload": response.answers_payload if response else {},
        "submitted_by_name": response.submitted_by_name if response else "",
        "submitted_by_relation": response.submitted_by_relation if response else "",
        "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
        "access_state": access_state,
        "message": invite.message or "",
    }


@public_router.post(
    "/{token}/save-draft",
    response={200: PublicAnamnesisOut, 400: MessageOut, 404: MessageOut},
)
def public_save_draft(request, token: str, payload: PublicAnamnesisDraftIn):
    rate_limit(request, "public-anamnesis-save", limit=20, window_seconds=300)

    invite = get_invite_by_token(token)
    if not invite:
        return 404, {"message": "Convite inválido ou não encontrado."}
    access_state = invite_access_state(invite)
    if access_state != "active":
        return 400, {"message": f"Este convite está {access_state}."}
    response = save_draft_response(
        invite,
        answers_payload=payload.answers_payload,
        submitted_by_name=payload.submitted_by_name or "",
        submitted_by_relation=payload.submitted_by_relation or "",
    )
    AuditService.log(
        request,
        "save_draft",
        "public_anamnesis",
        resource_id=str(invite.id),
        metadata={"status": invite.status},
    )
    return public_get_anamnesis(request, token)


@public_router.post(
    "/{token}/submit",
    response={200: PublicAnamnesisOut, 400: MessageOut, 404: MessageOut},
)
def public_submit(request, token: str, payload: PublicAnamnesisSubmitIn):
    rate_limit(request, "public-anamnesis-submit", limit=10, window_seconds=300)

    invite = get_invite_by_token(token)
    if not invite:
        return 404, {"message": "Convite inválido ou não encontrado."}
    access_state = invite_access_state(invite)
    if access_state != "active":
        return 400, {"message": f"Este convite está {access_state}."}
    submit_response(
        invite,
        answers_payload=payload.answers_payload,
        submitted_by_name=payload.submitted_by_name,
        submitted_by_relation=payload.submitted_by_relation,
    )
    AuditService.log(
        request,
        "submit",
        "public_anamnesis",
        resource_id=str(invite.id),
        metadata={"status": invite.status},
    )
    return public_get_anamnesis(request, token)
