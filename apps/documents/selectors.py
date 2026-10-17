from typing import Optional

from django.db.models import QuerySet

from .models import EvaluationDocument
from apps.common.clinical_access import owned_evaluation_children


def get_document_by_id(document_id: int, user=None) -> Optional[EvaluationDocument]:
    queryset = EvaluationDocument.objects.with_details().filter(id=document_id)
    return (owned_evaluation_children(queryset, user) if user is not None else queryset).first()


def get_documents_by_evaluation(evaluation_id: int, user=None) -> QuerySet[EvaluationDocument]:
    queryset = (
        EvaluationDocument.objects.with_details()
        .filter(evaluation_id=evaluation_id)
        .order_by("-created_at")
    )
    return owned_evaluation_children(queryset, user) if user is not None else queryset


def get_relevant_documents_by_evaluation(
    evaluation_id: int,
) -> QuerySet[EvaluationDocument]:
    return (
        EvaluationDocument.objects.with_details()
        .filter(evaluation_id=evaluation_id, is_relevant_for_report=True)
        .order_by("document_date", "created_at")
    )
