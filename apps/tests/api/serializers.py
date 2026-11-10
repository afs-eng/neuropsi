from apps.tests.age_rules import get_instrument_age_rule
from apps.tests.services import TestReportPayloadService


INSTRUMENT_DESCRIPTIONS = {
    "vineland3": "Comportamento adaptativo: Entrevista, Pais/Cuidadores e Professores extensivos. Correção quantitativa por normas americanas; requer revisão clínica.",
    "thcp": "Avalia habilidades percepto-motoras, linguagem, pensamento quantitativo, memória e atenção na pré-alfabetização (4–7 anos).",
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
    raw_payload = application.raw_payload or {}
    normative_results = None
    clinical_review = None
    if application.instrument.code == "vineland3":
        from apps.tests.vineland3.domain_scoring import results_for_application
        from apps.tests.vineland3.domain_protocol import build_item_summary
        from apps.tests.vineland3.domain_totals import is_domain_application

        if is_domain_application(application):
            raw_payload = {**raw_payload,
                           "birth_date": patient.birth_date.isoformat() if patient and patient.birth_date else None,
                           "reference_date": application.applied_on.isoformat() if application.applied_on else None}
        try:
            normative_results = results_for_application(application)
            if normative_results is not None and raw_payload.get("entry_mode") == "items":
                raw_payload = {**raw_payload, "item_summary": build_item_summary(raw_payload.get("item_responses")),
                               "scoring_enabled": normative_results["normative_scoring"],
                               "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
                               "reference_date": application.applied_on.isoformat() if application.applied_on else None}
        except ValueError as error:
            normative_results = {"error": str(error)}
        if is_domain_application(application):
            from apps.tests.vineland3.review import review_state

            clinical_review = review_state(application)
    status = application.status
    status_display = application.get_status_display()
    if clinical_review is not None and not clinical_review["validated"] and status == "reviewed":
        status, status_display = "completed", "Aplicação concluída — revisão pendente"
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
        "raw_payload": raw_payload,
        "normative_results": normative_results,
        "clinical_review": clinical_review,
        "computed_payload": application.computed_payload or {},
        "classified_payload": application.classified_payload or {},
        "reviewed_payload": application.reviewed_payload or {},
        "interpretation_text": application.interpretation_text or "",
        "report_payload": TestReportPayloadService.build_for_application(application),
        "is_validated": clinical_review["validated"] if clinical_review is not None else application.is_validated,
        "status": status,
        "status_display": status_display,
    }
