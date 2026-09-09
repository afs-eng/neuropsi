from __future__ import annotations

from apps.tests.etdah_pais.config import FACTOR_NAMES
from apps.tests.etdah_pais.interpreters import generate_report
from apps.tests.services.etdah_pdf_base import ETDAHPdfBase


class ETDAHPAISPdfService(ETDAHPdfBase):
    instrument_code = "etdah_pais"
    report_prefix = "ETDAHPAIS"
    title = "E-TDAH-PAIS"
    subtitle = "Escala de Transtorno de Déficit de Atenção e Hiperatividade"
    version_label = "Versão para Pais"
    row_order = ["fator_1", "fator_2", "fator_3", "fator_4", "escore_geral"]
    row_labels = FACTOR_NAMES
    intro_paragraphs = [
        "A E-TDAH-PAIS investiga manifestações comportamentais relacionadas à regulação emocional, hiperatividade/impulsividade, comportamento adaptativo e atenção a partir da percepção dos responsáveis.",
        "Os resultados auxiliam a compreensão do funcionamento da criança ou adolescente no contexto familiar e cotidiano, devendo ser integrados à anamnese, observação clínica e demais instrumentos aplicados.",
        "Este documento apresenta uma síntese para impressão, com tabela de resultados, gráfico de percentis e interpretação clínica descritiva.",
    ]
    definition_text = "Percentis mais elevados na E-TDAH-PAIS indicam maior presença de manifestações comportamentais no domínio avaliado. A interpretação deve considerar idade, sexo, contexto informante e convergência com outras fontes clínicas."

    @classmethod
    def _interpretation_text(cls, application, computed: dict, classified: dict) -> str:
        if application.interpretation_text:
            return application.interpretation_text
        raw_scores = classified.get("raw_scores") or computed.get("raw_scores") or {}
        age = classified.get("age") or computed.get("age") or (application.raw_payload or {}).get("age") or 10
        sex = classified.get("sex") or computed.get("sex") or (application.raw_payload or {}).get("sex") or "M"
        return generate_report(raw_scores, int(age), str(sex), patient_name=application.evaluation.patient.full_name)

    @classmethod
    def _normative_label(cls, classified: dict, computed: dict, patient, applied_on) -> str:
        age = classified.get("age") or computed.get("age")
        sex = classified.get("sex") or computed.get("sex")
        sex_label = cls._sex_label(str(sex)) if sex else cls._sex_label(getattr(patient, "sex", None))
        return f"Idade {age or cls._age_label(patient, applied_on)} / {sex_label}"

    @classmethod
    def _reference_label(cls, classified: dict, computed: dict) -> str:
        age = classified.get("age") or computed.get("age") or "-"
        sex = classified.get("sex") or computed.get("sex") or "-"
        return f"Percentis normativos - {age} anos / sexo {sex} - Brasil"
