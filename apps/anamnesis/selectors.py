from typing import Optional

from django.db.models import QuerySet

from .models import AnamnesisInvite, AnamnesisResponse, AnamnesisTemplate
from apps.common.clinical_access import owned_evaluation_children


def get_active_templates() -> QuerySet[AnamnesisTemplate]:
    return AnamnesisTemplate.objects.filter(is_active=True).order_by("name", "-version")


def get_template_by_id(template_id: int) -> Optional[AnamnesisTemplate]:
    return AnamnesisTemplate.objects.filter(id=template_id, is_active=True).first()


def get_invites_by_evaluation(evaluation_id: int, user=None) -> QuerySet[AnamnesisInvite]:
    queryset = AnamnesisInvite.objects.with_details().filter(evaluation_id=evaluation_id)
    return owned_evaluation_children(queryset, user) if user is not None else queryset


def get_invite_by_id(invite_id: int, user=None) -> Optional[AnamnesisInvite]:
    queryset = AnamnesisInvite.objects.with_details().filter(id=invite_id)
    return (owned_evaluation_children(queryset, user) if user is not None else queryset).first()


def get_invite_by_token(token: str) -> Optional[AnamnesisInvite]:
    return AnamnesisInvite.objects.with_details().filter(token=token).first()


def get_responses_by_evaluation(evaluation_id: int, user=None) -> QuerySet[AnamnesisResponse]:
    queryset = AnamnesisResponse.objects.with_details().filter(evaluation_id=evaluation_id)
    return owned_evaluation_children(queryset, user) if user is not None else queryset


def get_response_by_id(response_id: int, user=None) -> Optional[AnamnesisResponse]:
    queryset = AnamnesisResponse.objects.with_details().filter(id=response_id)
    return (owned_evaluation_children(queryset, user) if user is not None else queryset).first()


def get_internal_responses_by_evaluation(
    evaluation_id: int,
) -> QuerySet[AnamnesisResponse]:
    return (
        AnamnesisResponse.objects.with_details()
        .filter(evaluation_id=evaluation_id, source="internal")
        .order_by("-updated_at")
    )


def get_active_invites_by_evaluation(evaluation_id: int) -> QuerySet[AnamnesisInvite]:
    return (
        AnamnesisInvite.objects.with_details()
        .filter(
            evaluation_id=evaluation_id,
            status__in=["pending", "sent", "opened", "in_progress"],
        )
        .order_by("-created_at")
    )


def get_current_anamnesis_response_by_evaluation(
    evaluation_id: int,
) -> Optional[AnamnesisResponse]:
    reviewed = (
        AnamnesisResponse.objects.with_details()
        .filter(evaluation_id=evaluation_id, status="reviewed")
        .order_by("-reviewed_at", "-updated_at")
        .first()
    )
    if reviewed:
        return reviewed

    submitted = (
        AnamnesisResponse.objects.with_details()
        .filter(evaluation_id=evaluation_id, status="submitted")
        .order_by("-submitted_at", "-updated_at")
        .first()
    )
    if submitted:
        return submitted

    return (
        AnamnesisResponse.objects.with_details()
        .filter(evaluation_id=evaluation_id)
        .order_by("-updated_at")
        .first()
    )
