from __future__ import annotations

from apps.tests.etdah_ad.config import FACTOR_NAMES
from apps.tests.etdah_ad.interpreters import generate_report
from apps.tests.services.etdah_pdf_base import ETDAHPdfBase


class ETDAHADPdfService(ETDAHPdfBase):
    instrument_code = "etdah_ad"
    report_prefix = "ETDAHAD"
    title = "E-TDAH-AD"
    subtitle = "Escala de Transtorno de Déficit de Atenção e Hiperatividade"
    version_label = "Versão Adolescentes e Adultos"
    row_order = ["D", "I", "AE", "AAMA", "H"]
    row_labels = FACTOR_NAMES
    intro_paragraphs = [
        "A E-TDAH-AD investiga manifestações comportamentais e emocionais associadas à atenção, impulsividade, autorregulação, motivação e hiperatividade a partir do autorrelato.",
        "Os resultados descrevem indicadores quantitativos do funcionamento autorregulatório e devem ser interpretados em conjunto com entrevista clínica, observação comportamental e demais instrumentos do processo avaliativo.",
        "Este documento apresenta uma síntese para impressão, com tabela de resultados, gráfico de percentis e interpretação clínica descritiva.",
    ]
    definition_text = "Percentis mais elevados na E-TDAH-AD indicam maior presença de manifestações autorreferidas relacionadas aos domínios avaliados. Elevações devem ser compreendidas clinicamente e não constituem, isoladamente, definição diagnóstica."

    @classmethod
    def _interpretation_text(cls, application, computed: dict, classified: dict) -> str:
        if application.interpretation_text:
            return application.interpretation_text
        raw_scores = classified.get("raw_scores") or computed.get("raw_scores") or {}
        schooling = classified.get("schooling") or computed.get("schooling") or (application.raw_payload or {}).get("schooling") or "elementary"
        return generate_report(raw_scores, schooling, patient_name=application.evaluation.patient.full_name)

    @classmethod
    def _reference_label(cls, classified: dict, computed: dict) -> str:
        schooling = classified.get("schooling") or computed.get("schooling") or "elementary"
        labels = {"fundamental": "Ensino fundamental", "medio": "Ensino médio", "superior": "Ensino superior", "elementary": "Ensino fundamental", "middle": "Ensino médio", "higher": "Ensino superior"}
        return f"Percentis normativos - {labels.get(str(schooling), str(schooling))} - Brasil"
