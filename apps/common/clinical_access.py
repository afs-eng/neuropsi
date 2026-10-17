"""Escopo individual explícito, sem acesso clínico global por papel administrativo."""

from django.db.models import F, Q


def owned_patients(queryset, user):
    if not user or not getattr(user, "pk", None):
        return queryset.none()
    return queryset.filter(created_by_id=user.pk)


def owned_evaluations(queryset, user):
    if not user or not getattr(user, "pk", None):
        return queryset.none()
    return queryset.filter(patient__created_by_id=user.pk).filter(
        Q(examiner_id=user.pk) | Q(examiner__isnull=True)
    )


def owned_evaluation_children(queryset, user):
    from apps.evaluations.models import Evaluation

    queryset = queryset.filter(evaluation__in=owned_evaluations(Evaluation.objects.all(), user))
    if hasattr(queryset.model, "patient_id"):
        queryset = queryset.filter(patient_id=F("evaluation__patient_id"))
    return queryset


def owned_reports(queryset, user):
    if not user or not getattr(user, "pk", None):
        return queryset.none()
    return owned_evaluation_children(queryset, user).filter(
        author_id=user.pk, patient_id=F("evaluation__patient_id")
    )
