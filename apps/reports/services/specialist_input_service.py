import hashlib
import json
from datetime import date

from .bpa2_specialist import bpa2_reading_guide
from .self_report_specialists import SELF_REPORT_VERSIONS, self_report_reading_guide, self_report_sources
from .fdt_specialist import fdt_reading_guide
from .wais3_specialist_input import WAIS3_INPUT_VERSION, wais3_specialist_sources


class SpecialistInputService:
    VERSION = "1"
    MAX_FACTS = 600
    OMIT_KEYS = {
        "clinical_interpretation", "interpretation_text", "interpretation", "interpretacao",
        "full_name", "patient_name", "respondent_name", "nome_paciente", "nome_avaliado",
        "birth_date", "data_nascimento", "date_of_birth", "cpf", "email", "phone", "address", "signature", "anamnese",
        "raw_payload", "items", "itens", "responses", "respostas", "answers",
        "notes", "observations", "observacoes", "clinical_summary", "endereco",
    }
    FORM_KEYS = ("form", "version", "respondent_type", "respondent_role")

    @classmethod
    def fingerprint(cls, application) -> str:
        patient = application.evaluation.patient
        source = {
            "input_version": WAIS3_INPUT_VERSION if application.instrument.code == "wais3" else cls.VERSION,
            "application_id": application.pk,
            "evaluation_id": application.evaluation_id,
            "patient_id": patient.pk,
            "birth_date": str(patient.birth_date),
            "sex": patient.sex,
            "schooling": patient.schooling,
            "instrument_code": application.instrument.code,
            "applied_on": str(application.applied_on),
            "start_date": str(application.evaluation.start_date),
            "validated": application.is_validated,
            "raw": application.raw_payload,
            "computed": application.computed_payload,
            "classified": application.classified_payload,
            "reviewed": application.reviewed_payload,
        }
        return hashlib.sha256(json.dumps(source, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    @classmethod
    def build(cls, application) -> dict:
        patient = application.evaluation.patient
        names = [patient.full_name, patient.mother_name, patient.father_name, patient.responsible_name]
        raw = application.raw_payload or {}
        names.append(raw.get("respondent_name"))
        protected = [name.strip().casefold() for name in names if isinstance(name, str) and name.strip()]
        facts = {}

        def visit(value, path):
            if isinstance(value, dict):
                for key, child in value.items():
                    if str(key).casefold() in cls.OMIT_KEYS:
                        continue
                    if str(key).casefold() in {"summary", "resumo"} and isinstance(child, str):
                        continue
                    escaped = str(key).replace("~", "~0").replace("/", "~1")
                    visit(child, f"{path}/{escaped}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, f"{path}/{index}")
            elif isinstance(value, (int, float, bool)) or (
                isinstance(value, str) and value.strip() and len(value) <= 160
                and not any(name in value.casefold() for name in protected)
            ):
                if any(name in path.casefold() for name in protected):
                    return
                facts[path] = value
                if len(facts) > cls.MAX_FACTS:
                    raise ValueError("Resultados excedem o limite de fatos por aplicação.")

        sources = (application.computed_payload or {}, application.classified_payload or {})
        code = getattr(getattr(application, "instrument", None), "code", "")
        if code in SELF_REPORT_VERSIONS:
            sources = self_report_sources(code, *sources)
        elif code == "wais3":
            sources = wais3_specialist_sources(*sources)
        for key, source in zip(("computed_payload", "classified_payload"), sources):
            visit(source, f"/{key}")
        if not facts:
            raise ValueError("Aplicação sem resultados calculados/classificados utilizáveis.")
        visit({key: raw[key] for key in cls.FORM_KEYS if key in raw}, "/application")
        reference = application.applied_on or application.evaluation.start_date
        if isinstance(reference, date) and patient.birth_date:
            birth = patient.birth_date
            months = (reference.year - birth.year) * 12 + reference.month - birth.month
            months -= reference.day < birth.day
            if months >= 0:
                facts["/application/age_months"] = months
        payload = {"instrument_code": application.instrument.code, "facts": facts}
        if application.instrument.code == "bpa2":
            payload["reading_guide"] = bpa2_reading_guide(facts)
        elif code in SELF_REPORT_VERSIONS:
            payload["reading_guide"] = self_report_reading_guide(code, facts)
        elif code == "fdt":
            payload["reading_guide"] = fdt_reading_guide(facts)
        if len(json.dumps(payload, ensure_ascii=False).encode()) > 60000:
            raise ValueError("Resultados excedem o tamanho permitido para o especialista.")
        return payload
