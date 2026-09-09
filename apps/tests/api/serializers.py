from apps.tests.age_rules import get_instrument_age_rule
from apps.tests.services import TestReportPayloadService


INSTRUMENT_DESCRIPTIONS = {
    "bfp": "Avalia traços de personalidade nos cinco grandes fatores e suas facetas.",
    "wasi": "Estimativa abreviada de inteligencia verbal, de execucao e global por quatro subtestes.",
    "scared": "Triagem de sintomas de ansiedade em crianças e adolescentes.",
    "ravlt": "Avalia aprendizagem verbal, evocação e memória episódica.",
    "srs2": "Mensura responsividade social e traços associados ao espectro autista.",
    "ssrs": "Avalia habilidades sociais, problemas de comportamento e competencia academica por informante.",
    "bai": "Inventário de sintomas de ansiedade com foco em intensidade e gravidade.",
    "cars2_hf": "Escala clínica para perfil autista em alto funcionamento, com foco em reciprocidade social, comunicação e flexibilidade.",
    "mchat": "Triagem precoce para sinais compatíveis com TEA em crianças de 18 a 24 meses.",
}


def serialize_instrument(instrument):
    age_rule = get_instrument_age_rule(instrument.code) or {}
    return {
        "id": instrument.id,
        "code": instrument.code,
        "name": instrument.name,
        "category": instrument.category,
        "version": instrument.version,
        "description": INSTRUMENT_DESCRIPTIONS.get(instrument.code, ""),
        "is_active": instrument.is_active,
        "min_age": age_rule.get("min_age"),
        "max_age": age_rule.get("max_age"),
        "age_message": age_rule.get("message", ""),
    }


def serialize_test_application(application):
    patient = application.evaluation.patient if application.evaluation else None
    return {
        "id": application.id,
        "evaluation_id": application.evaluation_id,
        "patient_name": patient.full_name if patient else None,
        "patient_sex": patient.sex if patient else None,
        "patient_schooling": patient.schooling if patient else None,
        "instrument_id": application.instrument_id,
        "instrument_code": application.instrument.code,
        "instrument_name": application.instrument.name,
        "applied_on": application.applied_on,
        "raw_payload": application.raw_payload or {},
        "computed_payload": application.computed_payload or {},
        "classified_payload": application.classified_payload or {},
        "reviewed_payload": application.reviewed_payload or {},
        "interpretation_text": application.interpretation_text or "",
        "report_payload": TestReportPayloadService.build_for_application(application),
        "is_validated": application.is_validated,
        "status": application.status,
        "status_display": application.get_status_display(),
    }
