from typing import Optional

from django.db.models import QuerySet

from .models import Report, ReportSection
from apps.common.clinical_access import owned_reports


def list_reports(user=None) -> QuerySet[Report]:
    queryset = Report.objects.with_details().order_by("-updated_at")
    return owned_reports(queryset, user) if user is not None else queryset


def get_reports_by_evaluation(evaluation_id: int, user=None) -> QuerySet[Report]:
    return list_reports(user=user).filter(evaluation_id=evaluation_id)


def get_reports_by_patient(patient_id: int, user=None) -> QuerySet[Report]:
    return list_reports(user=user).filter(patient_id=patient_id)


def get_report_by_id(report_id: int, user=None) -> Optional[Report]:
    return list_reports(user=user).filter(id=report_id).first()


def get_report_section_by_id(section_id: int, user=None) -> Optional[ReportSection]:
    queryset = ReportSection.objects.select_related("report").filter(id=section_id)
    if user is not None:
        queryset = queryset.filter(report__in=list_reports(user=user))
    return queryset.first()
