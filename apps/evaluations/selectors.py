from typing import Optional

from django.db.models import QuerySet

from .models import Evaluation, EvaluationProgressEntry
from apps.common.clinical_access import owned_evaluations, owned_evaluation_children


def get_evaluations(user=None) -> QuerySet[Evaluation]:
    queryset = Evaluation.objects.with_details().all().order_by("-created_at")
    if user is not None:
        queryset = owned_evaluations(queryset, user)
    return queryset



def get_evaluation_by_id(evaluation_id: int, user=None) -> Optional[Evaluation]:
    queryset = Evaluation.objects.with_details().filter(id=evaluation_id)
    return (owned_evaluations(queryset, user) if user is not None else queryset).first()


def get_evaluations_by_patient(patient_id: int, user=None) -> QuerySet[Evaluation]:
    queryset = (
        Evaluation.objects.with_details()
        .filter(patient_id=patient_id)
        .order_by("-created_at")
    )
    if user is not None:
        queryset = owned_evaluations(queryset, user)
    return queryset



def get_progress_entry_by_id(entry_id: int, user=None) -> Optional[EvaluationProgressEntry]:
    queryset = EvaluationProgressEntry.objects.with_details().filter(id=entry_id)
    return (owned_evaluation_children(queryset, user) if user is not None else queryset).first()


def get_progress_entries_by_evaluation(
    evaluation_id: int,
) -> QuerySet[EvaluationProgressEntry]:
    return (
        EvaluationProgressEntry.objects.with_details()
        .filter(evaluation_id=evaluation_id)
        .order_by("-entry_date", "-created_at")
    )
