from datetime import date, time
from typing import Optional

from ninja import Schema


class EvaluationOut(Schema):
    id: int
    code: str
    title: str
    patient_id: int
    patient_name: str
    patient_birth_date: Optional[date] = None
    patient_sex: Optional[str] = None
    patient_responsible_name: Optional[str] = None
    examiner_id: Optional[int] = None
    examiner_name: Optional[str] = None
    referral_reason: str
    evaluation_purpose: str
    clinical_hypothesis: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    status_display: str
    priority: str
    priority_display: str
    is_archived: bool
    general_notes: str
    created_at: str
    updated_at: str


class EvaluationCreateIn(Schema):
    patient_id: int
    title: Optional[str] = ""
    examiner_id: Optional[int] = None
    referral_reason: Optional[str] = ""
    evaluation_purpose: Optional[str] = ""
    clinical_hypothesis: Optional[str] = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = "draft"
    priority: Optional[str] = "medium"
    general_notes: Optional[str] = ""


class EvaluationUpdateIn(Schema):
    title: Optional[str] = None
    patient_id: Optional[int] = None
    examiner_id: Optional[int] = None
    referral_reason: Optional[str] = None
    evaluation_purpose: Optional[str] = None
    clinical_hypothesis: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    is_archived: Optional[bool] = None
    general_notes: Optional[str] = None


class TestApplicationOut(Schema):
    id: int
    instrument_name: str
    instrument_code: str
    applied_on: Optional[date] = None
    is_validated: bool
    status: str
    status_display: Optional[str] = None
    report_payload: dict = {}


class DocumentOut(Schema):
    id: int
    name: str
    file_type: str
    uploaded_at: str


class CurrentAnamnesisOut(Schema):
    response_id: int
    status: str
    source: str
    response_type: str
    template_name: str
    submitted_by_name: str
    submitted_by_relation: str
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    summary_payload: dict = {}


class ClinicalChecklistOut(Schema):
    anamnesis_completed: bool
    anamnesis_reviewed: bool
    has_relevant_documents: bool
    has_progress_entries_for_report: bool
    has_validated_tests: bool
    ready_for_report: bool


class ProgressEntryOut(Schema):
    id: int
    evaluation_id: int
    patient_id: int
    professional_id: int
    professional_name: str
    entry_type: str
    entry_type_display: str
    entry_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    objective: str
    tests_applied: str
    observed_behavior: str
    clinical_notes: str
    next_steps: str
    include_in_report: bool
    created_at: str
    updated_at: str


class ProgressEntryCreateIn(Schema):
    evaluation_id: int
    patient_id: int
    professional_id: Optional[int] = None
    entry_type: str = "other"
    entry_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    objective: Optional[str] = ""
    tests_applied: Optional[str] = ""
    observed_behavior: Optional[str] = ""
    clinical_notes: Optional[str] = ""
    next_steps: Optional[str] = ""
    include_in_report: bool = True


class ProgressEntryUpdateIn(Schema):
    professional_id: Optional[int] = None
    entry_type: Optional[str] = None
    entry_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    objective: Optional[str] = None
    tests_applied: Optional[str] = None
    observed_behavior: Optional[str] = None
    clinical_notes: Optional[str] = None
    next_steps: Optional[str] = None
    include_in_report: Optional[bool] = None


class EvaluationDetailOut(EvaluationOut):
    tests: list[TestApplicationOut] = []
    documents: list[DocumentOut] = []
    progress_entries: list[ProgressEntryOut] = []
    current_anamnesis: Optional[CurrentAnamnesisOut] = None
    clinical_checklist: ClinicalChecklistOut


class MessageOut(Schema):
    message: str
