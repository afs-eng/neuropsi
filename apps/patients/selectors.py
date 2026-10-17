from django.db.models import Q

from .models import Patient
from apps.common.clinical_access import owned_patients


def get_patients(user=None):
    queryset = Patient.objects.all().order_by("full_name")
    if user is not None:
        queryset = owned_patients(queryset, user)
    return queryset



def get_patient_by_id(patient_id: int, user=None):
    queryset = Patient.objects.filter(id=patient_id)
    return (owned_patients(queryset, user) if user is not None else queryset).first()


def search_patients(query: str, user=None):
    queryset = Patient.objects.filter(
        Q(full_name__icontains=query)
        | Q(mother_name__icontains=query)
        | Q(father_name__icontains=query)
        | Q(email__icontains=query)
        | Q(phone__icontains=query)
    )
    if user is not None:
        queryset = owned_patients(queryset, user)
    return queryset.order_by("full_name")
