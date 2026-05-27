from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path

from django.template import Context
from django.template import engines

from apps.tests.services.playwright_pdf_service import generate_pdf_from_html
from .paths import TABELAS_CD


class WISC4PdfService:
    TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tests" / "pdf" / "wisc_4_relatorio_preview.html"

    SUBTEST_ORDER = ["CB", "SM", "DG", "CN", "CD", "VC", "SNL", "RM", "CO", "PS"]
    SUPPLEMENTAL_ORDER = ["CF", "CA", "IN", "AR", "RP"]
    INDEX_ORDER = ["icv", "iop", "imt", "ivp"]
    INDEX_ABBREVIATIONS = {"icv": "ICV", "iop": "IOP", "imt": "IMO", "ivp": "IVP"}
    INDEX_TEXT_LABELS = {
        "icv": "compreensão verbal",
        "iop": "organização perceptual",
        "imt": "memória operacional",
        "ivp": "velocidade de processamento",
    }
    PROFILE_COLUMNS = ["SM", "VC", "CO", "IN", "RP", "CB", "CN", "RM", "CF", "DG", "SNL", "AR", "CD", "PS", "CA"]
    END_PROFILE_COLUMNS = {"RP", "CF", "AR", "CA"}
    CONVERSION_ROWS = [
        ("CB", "Cubos", "iop", False),
        ("SM", "Semelhanças", "icv", False),
        ("DG", "Dígitos", "imt", False),
        ("CN", "Conceitos Figurativos", "iop", False),
        ("CD", "Código", "ivp", False),
        ("VC", "Vocabulário", "icv", False),
        ("SNL", "Seq. de Núm. e Letras", "imt", False),
        ("RM", "Raciocínio Matricial", "iop", False),
        ("CO", "Compreensão", "icv", False),
        ("PS", "Procurar Símbolos", "ivp", False),
        ("CF", "Completar Figuras", "iop", True),
        ("CA", "Cancelamento", "ivp", True),
        ("IN", "Informação", "icv", True),
        ("AR", "Aritmética", "imt", True),
        ("RP", "Raciocínio com Palavras", "icv", True),
    ]

    @classmethod
    def generate_pdf_bytes(cls, application) -> bytes:
        context = cls._build_context(application)
        template_source = cls.TEMPLATE_PATH.read_text(encoding="utf-8")
        template = engines["django"].from_string(template_source)
        html = template.render(Context(context).flatten())
        return generate_pdf_from_html(html)

    @classmethod
    def _build_context(cls, application) -> dict:
        evaluation = getattr(application, "evaluation", None)
        patient = getattr(evaluation, "patient", None)
        classified = application.classified_payload or {}
        computed = application.computed_payload or {}
        qit = classified.get("qit_data") or {}
        gai = classified.get("gai_data") or {}
        cpi = classified.get("cpi_data") or {}
        process_scores = classified.get("process_scores") or {}
        interpretation_text = application.interpretation_text or ""
        interpretation_paragraphs = cls._interpretation_paragraphs(interpretation_text)
        subtest_rows = cls._subtest_rows(classified.get("subtestes") or [])
        index_rows = cls._index_rows(classified.get("indices") or [])
        qit_row = cls._composite_row("qit", "QI Total", "QIT", qit, highlight=True)
        gai_row = cls._composite_row("gai", "Habilidade Geral", "GAI", gai)
        cpi_row = cls._composite_row("cpi", "Proficiência Cognitiva", "CPI", cpi)
        composite_rows = [*index_rows]
        composite_rows.extend(row for row in [qit_row, gai_row, cpi_row] if row)

        return {
            "codigo_avaliado": cls._application_code(application),
            "codigo_relatorio": cls._report_code(application),
            "data_relatorio": cls._format_date(date.today()),
            "data_aplicacao": cls._format_date(getattr(application, "applied_on", None)),
            "nome": getattr(patient, "full_name", None) or "Não informado",
            "sexo": cls._sex_label(getattr(patient, "sex", None)),
            "idade": cls._age_label(patient, getattr(application, "applied_on", None)),
            "escolaridade": cls._schooling_label(patient),
            "profissional": cls._professional_label(getattr(evaluation, "examiner", None)),
            "tabela_normativa": "WISC-IV / Brasil / Faixa etária correspondente",
            "aplicacao": "Válida",
            "referencia_normativa": "WISC-IV, tabelas normativas por idade cronológica",
            "intervalo_confianca_label": f"IC {classified.get('confidence_level') or 95}%",
            "qit_score": cls._format_number(qit.get("escore_composto")),
            "qit_classification": qit.get("classificacao") or "Não classificado",
            "qit_percentile": cls._format_number(qit.get("percentil"), decimals=1),
            "qit_interval": cls._interval(qit.get("intervalo_confianca")),
            "conversion_rows": cls._conversion_rows(subtest_rows, computed),
            "conversion_sums": cls._conversion_sums(index_rows, qit),
            "profile_columns": cls._profile_columns(subtest_rows, computed),
            "profile_score_rows": cls._profile_score_rows(subtest_rows, computed),
            "composite_table_rows": [row for row in [*index_rows, qit_row, gai_row, cpi_row] if row],
            "composite_profile_values": cls._composite_profile_values(index_rows, qit),
            "composite_profile_rows": cls._composite_profile_rows(index_rows, qit),
            "analysis_discrepancy_rows": cls._analysis_discrepancy_rows(
                index_rows,
                subtest_rows,
                cls._age_years(patient, getattr(application, "applied_on", None)),
                cls._float(qit.get("escore_composto")),
                classified.get("confidence_level") or 95,
            ),
            "facility_rows": cls._facility_rows(
                index_rows,
                subtest_rows,
                cls._age_years(patient, getattr(application, "applied_on", None)),
                classified.get("confidence_level") or 95,
            ),
            "facility_summary_rows": cls._facility_summary_rows(subtest_rows),
            "process_scaled_rows": cls._process_scaled_rows(process_scores),
            "sequence_frequency_rows": cls._sequence_frequency_rows(process_scores),
            "raw_process_discrepancy_rows": cls._raw_process_discrepancy_rows(process_scores),
            "process_discrepancy_rows": cls._process_discrepancy_rows(process_scores),
            "subtest_rows": subtest_rows,
            "supplemental_rows": cls._supplemental_rows(computed),
            "index_rows": index_rows,
            "composite_rows": composite_rows,
            "subtest_bars": cls._subtest_bars(subtest_rows),
            "composite_bars": cls._composite_bars(composite_rows),
            "difference_rows": cls._difference_rows(classified.get("diferencas_significativas") or []),
            "strengths": classified.get("pontos_fortes") or [],
            "weaknesses": classified.get("pontos_fragilizados") or [],
            "clinical_paragraphs": interpretation_paragraphs,
            "clinical_box_text": cls._clinical_box_text(getattr(patient, "full_name", None), qit, index_rows),
            "synthesis_text": cls._synthesis_text(getattr(patient, "full_name", None), qit, index_rows, interpretation_paragraphs),
        }

    @classmethod
    def _score_lookup(cls, subtest_rows: list[dict], computed: dict) -> dict:
        lookup = {row["code"]: row for row in subtest_rows}
        for item in computed.values():
            if not isinstance(item, dict):
                continue
            code = (item.get("codigo") or "").upper()
            if not code or code in lookup:
                continue
            pp = item.get("escore_padrao")
            lookup[code] = {
                "name": item.get("subteste") or code,
                "code": code,
                "raw_score": cls._format_number(item.get("escore_bruto")),
                "scaled_score": cls._format_number(pp),
                "scaled_score_raw": cls._float(pp),
                "classification": item.get("classificacao") or "Não classificado",
            }
        return lookup

    @classmethod
    def _conversion_rows(cls, subtest_rows: list[dict], computed: dict) -> list[dict]:
        lookup = cls._score_lookup(subtest_rows, computed)
        rows = []
        for code, name, index_code, optional in cls.CONVERSION_ROWS:
            item = lookup.get(code, {})
            scaled = item.get("scaled_score") or ""
            row = {
                "label": f"({name}) ({code})" if optional else f"{name} ({code})",
                "raw_score": item.get("raw_score") or "",
                "scaled_score": scaled,
                "icv": cls._conversion_cell("icv", index_code, scaled, optional),
                "iop": cls._conversion_cell("iop", index_code, scaled, optional),
                "imo": cls._conversion_cell("imt", index_code, scaled, optional),
                "ivp": cls._conversion_cell("ivp", index_code, scaled, optional),
                "qit": cls._conversion_qit_cell(scaled, optional),
            }
            rows.append(row)
        return rows

    @staticmethod
    def _conversion_cell(column: str, index_code: str, value: str, optional: bool) -> dict:
        if column != index_code:
            return {"value": "", "class": "fill"}
        if optional:
            return {"value": f"({value})" if value else "", "class": "optional"}
        return {"value": value, "class": "value-cell"}

    @staticmethod
    def _conversion_qit_cell(value: str, optional: bool) -> dict:
        if optional:
            return {"value": f"({value})" if value else "", "class": "optional"}
        return {"value": value, "class": "value-cell"}

    @classmethod
    def _conversion_sums(cls, index_rows: list[dict], qit: dict) -> dict:
        by_code = {row["code"]: row for row in index_rows}
        return {
            "ICV": (by_code.get("icv") or {}).get("scaled_sum") or "",
            "IOP": (by_code.get("iop") or {}).get("scaled_sum") or "",
            "IMO": (by_code.get("imt") or {}).get("scaled_sum") or "",
            "IVP": (by_code.get("ivp") or {}).get("scaled_sum") or "",
            "QIT": cls._format_number(qit.get("soma_ponderados")),
        }

    @classmethod
    def _profile_columns(cls, subtest_rows: list[dict], computed: dict) -> list[dict]:
        lookup = cls._score_lookup(subtest_rows, computed)
        return [
            {
                "code": code,
                "value": (lookup.get(code) or {}).get("scaled_score") or "",
                "end": code in cls.END_PROFILE_COLUMNS,
            }
            for code in cls.PROFILE_COLUMNS
        ]

    @classmethod
    def _profile_score_rows(cls, subtest_rows: list[dict], computed: dict) -> list[dict]:
        lookup = cls._score_lookup(subtest_rows, computed)
        rows = []
        for score in range(19, 0, -1):
            rows.append(
                {
                    "score": score,
                    "average": score in {9, 10},
                    "cells": [
                        {
                            "dot": int((lookup.get(code) or {}).get("scaled_score_raw") or 0) == score,
                            "end": code in cls.END_PROFILE_COLUMNS,
                            "average": score in {9, 10},
                        }
                        for code in cls.PROFILE_COLUMNS
                    ],
                }
            )
        return rows

    @classmethod
    def _composite_profile_values(cls, index_rows: list[dict], qit: dict) -> list[dict]:
        by_code = {row["code"]: row for row in index_rows}
        return [
            {"code": "ICV", "value": (by_code.get("icv") or {}).get("score") or ""},
            {"code": "IOP", "value": (by_code.get("iop") or {}).get("score") or ""},
            {"code": "IMO", "value": (by_code.get("imt") or {}).get("score") or ""},
            {"code": "IVP", "value": (by_code.get("ivp") or {}).get("score") or ""},
            {"code": "QIT", "value": cls._format_number(qit.get("escore_composto"))},
        ]

    @classmethod
    def _composite_profile_rows(cls, index_rows: list[dict], qit: dict) -> list[dict]:
        scores = [
            cls._float((next((row for row in index_rows if row["code"] == code), {}) or {}).get("score_raw"))
            for code in cls.INDEX_ORDER
        ]
        scores.append(cls._float(qit.get("escore_composto")))
        rows = []
        for score in range(160, 39, -10):
            rows.append(
                {
                    "score": score,
                    "average": score == 100,
                    "cells": [
                        {"dot": value is not None and round(value / 10) * 10 == score, "average": score == 100}
                        for value in scores
                    ],
                }
            )
        return rows

    @classmethod
    def _analysis_discrepancy_rows(
        cls,
        index_rows: list[dict],
        subtest_rows: list[dict],
        age_years: int | None,
        qit_score: float | None,
        confidence_level: int | str,
    ) -> list[dict]:
        by_code = {row["code"]: row for row in index_rows}
        pairs = [("icv", "iop"), ("icv", "imt"), ("icv", "ivp"), ("iop", "imt"), ("iop", "ivp"), ("imt", "ivp")]
        rows = []
        significance = cls._significance_level(confidence_level)
        for first, second in pairs:
            first_row = by_code.get(first) or {}
            second_row = by_code.get(second) or {}
            first_score = cls._float(first_row.get("score_raw"))
            second_score = cls._float(second_row.get("score_raw"))
            signed_difference = first_score - second_score if first_score is not None and second_score is not None else None
            difference = abs(signed_difference) if signed_difference is not None else None
            critical = cls._lookup_index_critical(first, second, age_years, significance)
            significant = difference is not None and critical is not None and difference >= critical
            rows.append(
                {
                    "label": f"{cls.INDEX_ABBREVIATIONS[first]} - {cls.INDEX_ABBREVIATIONS[second]}",
                    "first": cls.INDEX_ABBREVIATIONS[first],
                    "second": cls.INDEX_ABBREVIATIONS[second],
                    "difference": cls._format_number(difference),
                    "critical": cls._format_number(critical, decimals=2),
                    "significant": "Sim" if significant else "Não" if difference is not None else "",
                    "frequency": cls._format_number(
                        cls._lookup_index_frequency(first, second, signed_difference, qit_score) if significant else None,
                        decimals=1,
                    ),
                }
            )
        subtests_by_code = {row["code"]: row for row in subtest_rows}
        rows.extend(
            cls._subtest_discrepancy_row("Dígitos - Seq. de Núm. e Letras", "DG", "SNL", subtests_by_code),
        )
        rows.extend(
            cls._subtest_discrepancy_row("Código - Procurar Símbolos", "CD", "PS", subtests_by_code),
        )
        rows.extend(
            cls._subtest_discrepancy_row("Semelhanças - Conceitos Figurativos", "SM", "CN", subtests_by_code),
        )
        return rows

    @classmethod
    def _facility_rows(
        cls,
        index_rows: list[dict],
        subtest_rows: list[dict],
        age_years: int | None,
        confidence_level: int | str,
    ) -> list[dict]:
        rows = []
        by_code = {row["code"]: row for row in subtest_rows}
        general_values = [row["scaled_score_raw"] for row in subtest_rows if row.get("scaled_score_raw") is not None]
        general_average = sum(general_values) / len(general_values) if general_values else None
        verbal_average = cls._mean_for_codes(by_code, ["SM", "VC", "CO"])
        perceptual_average = cls._mean_for_codes(by_code, ["CB", "CN", "RM"])
        significance = cls._significance_level(confidence_level)
        icv_iop_significant = cls._is_icv_iop_significant(index_rows, age_years, significance)

        for row in subtest_rows:
            value = row.get("scaled_score_raw")
            average = cls._facility_average_for_code(
                row.get("code"),
                general_average,
                verbal_average,
                perceptual_average,
                icv_iop_significant,
            )
            diff = value - average if value is not None and average is not None else None
            critical = cls._lookup_facility_critical(row.get("code"), significance, icv_iop_significant)
            label = "—"
            if diff is not None and critical is not None and abs(diff) >= critical:
                if diff > 0:
                    label = "Facilidade"
                elif diff < 0:
                    label = "Dificuldade"
            rows.append(
                {
                    "name": row["name"],
                    "score": row["scaled_score"],
                    "average": cls._format_number(average, decimals=1),
                    "difference": cls._format_number(diff, decimals=1),
                    "critical": cls._format_number(critical, decimals=2),
                    "label": label,
                    "frequency": cls._lookup_facility_frequency_label(row.get("code"), diff, icv_iop_significant) if label != "—" else "—",
                }
            )
        return rows

    @classmethod
    def _subtest_discrepancy_row(cls, label: str, first_code: str, second_code: str, subtests_by_code: dict) -> list[dict]:
        first_row = subtests_by_code.get(first_code) or {}
        second_row = subtests_by_code.get(second_code) or {}
        first_score = cls._float(first_row.get("scaled_score_raw"))
        second_score = cls._float(second_row.get("scaled_score_raw"))
        signed_difference = first_score - second_score if first_score is not None and second_score is not None else None
        difference = abs(signed_difference) if signed_difference is not None else None
        critical = cls._lookup_subtest_pair_critical(first_code, second_code)
        significant = difference is not None and critical is not None and difference >= critical
        return [
            {
                "label": label,
                "first": first_code,
                "second": second_code,
                "difference": cls._format_number(difference),
                "critical": cls._format_number(critical, decimals=2),
                "significant": "Sim" if significant else "Não" if difference is not None else "",
                "frequency": cls._format_number(
                    cls._lookup_subtest_pair_frequency(first_code, second_code, signed_difference) if significant else None,
                    decimals=1,
                ),
            }
        ]

    @classmethod
    def _facility_summary_rows(cls, subtest_rows: list[dict]) -> list[dict]:
        groups = [
            ("10 Subtestes", cls.SUBTEST_ORDER, "÷ 10"),
            ("3 Subtestes Compreensão Verbal", ["SM", "VC", "CO"], "÷ 3"),
            ("3 Subtestes Organização Perceptual", ["CB", "CN", "RM"], "÷ 3"),
        ]
        by_code = {row["code"]: row for row in subtest_rows}
        summaries = []
        for label, codes, divisor in groups:
            values = [(by_code.get(code) or {}).get("scaled_score_raw") for code in codes]
            values = [value for value in values if value is not None]
            total = sum(values) if values else None
            summaries.append(
                {
                    "label": label,
                    "sum": cls._format_number(total),
                    "divisor": divisor,
                    "average": cls._format_number(total / len(values), decimals=1) if values else "",
                }
            )
        return summaries

    @classmethod
    def _process_scaled_rows(cls, process_scores: dict) -> list[dict]:
        return [
            {
                "name": row.get("name") or "—",
                "raw_score": cls._format_number(row.get("raw_score")),
                "scaled_score": cls._format_number(row.get("scaled_score")),
            }
            for row in process_scores.get("scaled_rows", [])
        ]

    @classmethod
    def _sequence_frequency_rows(cls, process_scores: dict) -> list[dict]:
        return [
            {
                "name": row.get("name") or "—",
                "raw_score": cls._format_number(row.get("raw_score")),
                "frequency": cls._format_number(row.get("frequency"), decimals=1),
            }
            for row in process_scores.get("sequence_frequency_rows", [])
        ]

    @classmethod
    def _raw_process_discrepancy_rows(cls, process_scores: dict) -> list[dict]:
        return [
            {
                "label": row.get("label") or "—",
                "first": cls._format_number(row.get("first")),
                "second": cls._format_number(row.get("second")),
                "difference": cls._format_number(row.get("difference")),
                "frequency": cls._format_number(row.get("frequency"), decimals=1),
            }
            for row in process_scores.get("raw_discrepancy_rows", [])
        ]

    @classmethod
    def _process_discrepancy_rows(cls, process_scores: dict) -> list[dict]:
        rows = []
        for row in process_scores.get("process_discrepancy_rows", []):
            significant = row.get("significant")
            if significant is True:
                significant_label = "Sim"
            elif significant is False:
                significant_label = "Não"
            else:
                significant_label = ""
            rows.append(
                {
                    "label": row.get("label") or "—",
                    "first": cls._format_number(row.get("first")),
                    "second": cls._format_number(row.get("second")),
                    "difference": cls._format_number(row.get("difference")),
                    "critical": cls._format_number(row.get("critical"), decimals=2),
                    "significant": significant_label,
                    "frequency": cls._format_number(row.get("frequency"), decimals=1),
                }
            )
        return rows

    @classmethod
    def _subtest_rows(cls, subtests: list[dict]) -> list[dict]:
        order = {code: index for index, code in enumerate(cls.SUBTEST_ORDER)}
        rows = []
        for item in sorted(subtests, key=lambda value: order.get(value.get("codigo"), 999)):
            pp = item.get("escore_padrao")
            rows.append(
                {
                    "name": item.get("subteste") or "—",
                    "code": item.get("codigo") or "—",
                    "raw_score": cls._format_number(item.get("escore_bruto")),
                    "scaled_score": cls._format_number(pp),
                    "scaled_score_raw": cls._float(pp),
                    "percentile": cls._format_number(item.get("percentil"), decimals=1),
                    "confidence_interval": cls._interval(item.get("intervalo_confianca_95")),
                    "classification": item.get("classificacao") or "Não classificado",
                    "badge_class": cls._badge_class(item.get("classificacao")),
                }
            )
        return rows

    @classmethod
    def _supplemental_rows(cls, computed: dict) -> list[dict]:
        by_code = {
            (item.get("codigo") or "").upper(): item
            for item in computed.values()
            if isinstance(item, dict)
        }
        rows = []
        for code in cls.SUPPLEMENTAL_ORDER:
            item = by_code.get(code)
            if not item or item.get("escore_bruto") is None:
                continue
            rows.append(
                {
                    "name": item.get("subteste") or code,
                    "code": code,
                    "raw_score": cls._format_number(item.get("escore_bruto")),
                    "scaled_score": cls._format_number(item.get("escore_padrao")),
                    "classification": item.get("classificacao") or "Não classificado",
                }
            )
        return rows

    @classmethod
    def _index_rows(cls, indices: list[dict]) -> list[dict]:
        by_code = {item.get("indice"): item for item in indices}
        rows = []
        for code in cls.INDEX_ORDER:
            item = by_code.get(code) or {}
            abbreviation = cls.INDEX_ABBREVIATIONS[code]
            rows.append(
                {
                    "code": code,
                    "name": item.get("nome") or abbreviation,
                    "abbreviation": abbreviation,
                    "scaled_sum": cls._format_number(item.get("soma_ponderados")),
                    "score": cls._format_number(item.get("escore_composto")),
                    "score_raw": cls._float(item.get("escore_composto")),
                    "percentile": cls._format_number(item.get("percentil"), decimals=1),
                    "confidence_interval": cls._interval(item.get("intervalo_confianca")),
                    "classification": item.get("classificacao") or "Não classificado",
                    "badge_class": cls._badge_class(item.get("classificacao")),
                }
            )
        return rows

    @classmethod
    def _composite_row(cls, code: str, name: str, abbreviation: str, data: dict, highlight: bool = False) -> dict | None:
        if not data:
            return None
        return {
            "code": code,
            "name": name,
            "abbreviation": abbreviation,
            "scaled_sum": cls._format_number(data.get("soma_ponderados")),
            "score": cls._format_number(data.get("escore_composto")),
            "score_raw": cls._float(data.get("escore_composto")),
            "percentile": cls._format_number(data.get("percentil"), decimals=1),
            "confidence_interval": cls._interval(data.get("intervalo_confianca")),
            "classification": data.get("classificacao") or "Não classificado",
            "badge_class": cls._badge_class(data.get("classificacao")),
            "highlight": highlight,
        }

    @classmethod
    def _subtest_bars(cls, rows: list[dict]) -> list[dict]:
        return [
            {
                "label": row["code"],
                "value": row["scaled_score"],
                "height": cls._chart_height(row["scaled_score_raw"], minimum=1, maximum=19),
                "is_low": row["scaled_score_raw"] and row["scaled_score_raw"] < 8,
            }
            for row in rows
        ]

    @classmethod
    def _composite_bars(cls, rows: list[dict]) -> list[dict]:
        return [
            {
                "label": row["abbreviation"],
                "value": row["score"],
                "height": cls._chart_height(row["score_raw"], minimum=40, maximum=160),
                "is_qit": row["code"] == "qit",
            }
            for row in rows
            if row.get("score_raw") is not None
        ]

    @staticmethod
    def _difference_rows(differences: list[str]) -> list[dict]:
        return [{"description": item} for item in differences]

    @staticmethod
    def _interpretation_paragraphs(text: str) -> list[str]:
        paragraphs = []
        for paragraph in re.split(r"\n\s*\n", text or ""):
            cleaned = re.sub(r"\s+", " ", paragraph).strip()
            if cleaned and cleaned.lower() != "interpretação e observações clínicas":
                paragraphs.append(cleaned)
        return paragraphs

    @classmethod
    def _clinical_box_text(cls, patient_name: str | None, qit: dict, indices: list[dict]) -> str:
        qit_class = qit.get("classificacao") or "não classificado"
        first_name = cls._first_name(patient_name)
        top_rows, low_row, spread = cls._profile_highlights(indices)

        parts = [
            f"o WISC-IV indicou QI Total na faixa {qit_class}, com {cls._strength_summary(top_rows, spread)}.",
            f"{first_name} apresentou funcionamento cognitivo global {cls._global_resources_summary(qit_class)}, com {cls._weakness_summary(low_row, spread)}.",
            "Os achados devem ser interpretados de forma integrada às observações clínicas, dados escolares, comportamentais e demais instrumentos, sem inferências diagnósticas isoladas.",
        ]
        return " ".join(parts)

    @classmethod
    def _synthesis_text(cls, patient_name: str | None, qit: dict, indices: list[dict], paragraphs: list[str]) -> str:
        qit_class = qit.get("classificacao") or "não classificado"
        first_name = cls._first_name(patient_name)
        top_rows, low_row, spread = cls._profile_highlights(indices)
        profile_label = "globalmente preservado, porém heterogêneo" if spread >= 15 else "globalmente preservado e relativamente homogêneo"

        parts = [
            f"Em análise clínica, {first_name} apresentou funcionamento cognitivo global na faixa {qit_class}, com recursos {cls._global_resources_summary(qit_class, plural=True)} nos principais domínios avaliados.",
            f"Foram observados {cls._strength_summary(top_rows, spread)}, em contraste com {cls._weakness_summary(low_row, spread)}.",
            f"O perfil deve ser compreendido como {profile_label}, exigindo integração com dados clínicos, escolares, comportamentais e demais instrumentos da avaliação.",
        ]
        return " ".join(parts)

    @classmethod
    def _profile_highlights(cls, indices: list[dict]) -> tuple[list[dict], dict | None, float]:
        rows = [row for row in indices if row.get("code") in cls.INDEX_ORDER and row.get("score_raw") is not None]
        if not rows:
            return [], None, 0
        ordered = sorted(rows, key=lambda row: row["score_raw"], reverse=True)
        spread = ordered[0]["score_raw"] - ordered[-1]["score_raw"]
        return ordered[:2], ordered[-1], spread

    @classmethod
    def _strength_summary(cls, top_rows: list[dict], spread: float) -> str:
        if spread < 15 or not top_rows:
            return "recursos cognitivos globalmente preservados"
        return f"melhores desempenhos relativos em {cls._join([cls.INDEX_TEXT_LABELS[row['code']] for row in top_rows])}"

    @classmethod
    def _weakness_summary(cls, low_row: dict | None, spread: float) -> str:
        if not low_row or spread < 15:
            return "ausência de fragilidades relativas clinicamente relevantes entre os índices disponíveis"
        classification = low_row.get("classification") or "não classificado"
        label = cls.INDEX_TEXT_LABELS.get(low_row.get("code"), low_row.get("name", "esse índice"))
        if low_row.get("code") == "ivp" and not cls._is_low(classification):
            return "fragilidade relativa em velocidade de processamento, embora preservada normativamente"
        if cls._is_low(classification):
            return f"maior vulnerabilidade em {label}"
        return f"menor eficiência relativa em {label}"

    @staticmethod
    def _global_resources_summary(classification: str, plural: bool = False) -> str:
        if classification in {"Muito Superior", "Superior", "Média Superior"}:
            return "preservados e acima da média" if plural else "preservado e acima da média"
        if classification == "Média":
            return "preservados" if plural else "preservado"
        return "mais vulneráveis" if plural else "com maior vulnerabilidade"

    @staticmethod
    def _first_name(name: str | None) -> str:
        if not name:
            return "Paciente"
        return str(name).strip().split(" ", 1)[0] or "Paciente"

    @staticmethod
    def _age_years(patient, reference_date) -> int | None:
        birth_date = getattr(patient, "birth_date", None)
        if not birth_date or not reference_date:
            return None
        years = reference_date.year - birth_date.year
        if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
            years -= 1
        return years

    @staticmethod
    def _parse_csv_float(value) -> float | None:
        if value in (None, "", ".", "-", "0,/"):
            return None
        cleaned = str(value).strip().replace(",", ".")
        cleaned = cleaned.replace(" ", "")
        try:
            return float(cleaned)
        except ValueError:
            return None

    @classmethod
    def _csv_rows(cls, filename: str) -> list[dict]:
        with (TABELAS_CD / filename).open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    @staticmethod
    def _csv_matrix(filename: str) -> list[list[str]]:
        with (TABELAS_CD / filename).open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.reader(handle))

    @staticmethod
    def _significance_level(confidence_level: int | str) -> str:
        return "0.15" if str(confidence_level) == "90" else "0.05"

    @staticmethod
    def _age_band_label(age_years: int | None) -> str:
        if age_years is None:
            return "Todas as Idades"
        bounded_years = max(6, min(16, age_years))
        return f"{bounded_years}:0–{bounded_years}:11"

    @classmethod
    def _lookup_index_critical(cls, first: str, second: str, age_years: int | None, significance: str) -> float | None:
        column = f"{cls.INDEX_ABBREVIATIONS[first]}-{cls.INDEX_ABBREVIATIONS[second]}"
        age_band = cls._age_band_label(age_years)
        fallback = None
        target_significance = cls._parse_csv_float(significance)
        for row in cls._csv_rows("Tabela_B1.csv"):
            value = cls._parse_csv_float(row.get(column))
            if value is None:
                continue
            row_significance = cls._parse_csv_float(row.get("Significância"))
            if row_significance == target_significance and row.get("Faixa Etária") == age_band:
                return value
            if row_significance == target_significance and row.get("Faixa Etária") == "Todas as Idades":
                fallback = value
        return fallback

    @staticmethod
    def _b2_filename(qit_score: float | None) -> str:
        if qit_score is None:
            return "tabela_B2_amostra_geral.csv"
        if qit_score <= 79:
            return "tabela_B2_QI_79.csv"
        if qit_score <= 89:
            return "tabela_B2_QI_80-89.csv"
        if qit_score <= 109:
            return "tabela_B2_QI_109.csv"
        if qit_score <= 119:
            return "tabela_B2_QI_119.csv"
        return "tabela_B2_QI_120.csv"

    @classmethod
    def _lookup_index_frequency(cls, first: str, second: str, signed_difference: float | None, qit_score: float | None) -> float | None:
        if signed_difference is None:
            return None
        direction = ">" if signed_difference >= 0 else "<"
        column = f"{cls.INDEX_ABBREVIATIONS[first]}{direction}{cls.INDEX_ABBREVIATIONS[second]} {'(+)' if direction == '>' else '(-)'}"
        target = abs(signed_difference)
        for row in cls._csv_rows(cls._b2_filename(qit_score)):
            key = cls._parse_csv_float(row.get("Tamanho da") or row.get("Discrepancia") or row.get("Tamanho da Discrepância"))
            value = cls._parse_csv_float(row.get(column))
            if key is None or value is None:
                continue
            if abs(key - target) < 0.001:
                return value
        return None

    @classmethod
    def _lookup_subtest_pair_critical(cls, first_code: str, second_code: str) -> float | None:
        second_column = cls._subtest_csv_code(second_code)
        for row in cls._csv_rows("tabela_B3.csv"):
            if row.get("Unnamed: 0") == first_code:
                value = cls._parse_csv_float(row.get(second_column))
                if value is not None:
                    return value
            if row.get("Unnamed: 0") == second_code:
                value = cls._parse_csv_float(row.get(cls._subtest_csv_code(first_code)))
                if value is not None:
                    return value
        return None

    @classmethod
    def _lookup_subtest_pair_frequency(cls, first_code: str, second_code: str, signed_difference: float | None) -> float | None:
        if signed_difference is None:
            return None
        column = f"{first_code}{'>' if signed_difference >= 0 else '<'}{second_code} {'(+)' if signed_difference >= 0 else '(-)'}"
        target = abs(signed_difference)
        for row in cls._csv_rows("tabela_B4.csv"):
            key = cls._parse_csv_float(row.get("Tamanho da Discrepância"))
            value = cls._parse_csv_float(row.get(column))
            if key is None or value is None:
                continue
            if abs(key - target) < 0.001:
                return value
        return None

    @classmethod
    def _mean_for_codes(cls, by_code: dict, codes: list[str]) -> float | None:
        values = [(by_code.get(code) or {}).get("scaled_score_raw") for code in codes]
        values = [value for value in values if value is not None]
        if not values:
            return None
        return sum(values) / len(values)

    @classmethod
    def _is_icv_iop_significant(cls, index_rows: list[dict], age_years: int | None, significance: str) -> bool:
        by_code = {row["code"]: row for row in index_rows}
        icv = cls._float((by_code.get("icv") or {}).get("score_raw"))
        iop = cls._float((by_code.get("iop") or {}).get("score_raw"))
        if icv is None or iop is None:
            return False
        critical = cls._lookup_index_critical("icv", "iop", age_years, significance)
        if critical is None:
            return False
        return abs(icv - iop) >= critical

    @staticmethod
    def _facility_average_for_code(
        code: str | None,
        general_average: float | None,
        verbal_average: float | None,
        perceptual_average: float | None,
        icv_iop_significant: bool,
    ) -> float | None:
        if not icv_iop_significant:
            return general_average
        if code in {"SM", "VC", "CO"}:
            return verbal_average
        if code in {"CB", "CN", "RM"}:
            return perceptual_average
        return general_average

    @classmethod
    def _lookup_facility_critical(cls, code: str | None, significance: str, icv_iop_significant: bool) -> float | None:
        if not code:
            return None
        thresholds = cls._lookup_b5_thresholds(code, icv_iop_significant)
        if not thresholds:
            return None
        return thresholds.get(significance)

    @classmethod
    def _lookup_facility_frequency_label(cls, code: str | None, difference: float | None, icv_iop_significant: bool) -> str:
        if not code or difference is None:
            return "—"
        thresholds = cls._lookup_b5_thresholds(code, icv_iop_significant)
        if not thresholds:
            return "—"
        diff = abs(difference)
        one = thresholds.get("1%")
        two = thresholds.get("2%")
        five = thresholds.get("5%")
        ten = thresholds.get("10%")
        twenty_five = thresholds.get("25%")
        if one is None or two is None or five is None or ten is None or twenty_five is None:
            return "—"
        if diff > one:
            return "< 1%"
        if cls._float_equals(diff, one):
            return "1%"
        if diff > two:
            return "> 1% e < 2%"
        if cls._float_equals(diff, two):
            return "2%"
        if diff > five:
            return "> 2% e < 5%"
        if cls._float_equals(diff, five):
            return "5%"
        if diff > ten:
            return "> 5% e < 10%"
        if cls._float_equals(diff, ten):
            return "10%"
        if diff > twenty_five:
            return "> 10% e < 25%"
        if cls._float_equals(diff, twenty_five):
            return "25%"
        return "> 25%"

    @classmethod
    def _lookup_b5_thresholds(cls, code: str, icv_iop_significant: bool) -> dict[str, float] | None:
        matrix = cls._csv_matrix("tabela_B5_1.csv" if icv_iop_significant and code in {"SM", "VC", "CO", "CB", "CN", "RM"} else "tabela_B5_2.csv")
        for row in matrix[1:]:
            if not row or row[0] != code:
                continue
            if len(row) >= 15 and icv_iop_significant and code in {"SM", "VC", "CO", "CB", "CN", "RM"}:
                offset = 1 if cls._parse_csv_float(row[1]) is not None else 8
                return {
                    "0.15": cls._parse_csv_float(row[offset]),
                    "0.05": cls._parse_csv_float(row[offset + 1]),
                    "1%": cls._parse_csv_float(row[offset + 2]),
                    "2%": cls._parse_csv_float(row[offset + 3]),
                    "5%": cls._parse_csv_float(row[offset + 4]),
                    "10%": cls._parse_csv_float(row[offset + 5]),
                    "25%": cls._parse_csv_float(row[offset + 6]),
                }
            if len(row) >= 8:
                return {
                    "0.15": cls._parse_csv_float(row[1]),
                    "0.05": cls._parse_csv_float(row[2]),
                    "1%": cls._parse_csv_float(row[3]),
                    "2%": cls._parse_csv_float(row[4]),
                    "5%": cls._parse_csv_float(row[5]),
                    "10%": cls._parse_csv_float(row[6]),
                    "25%": cls._parse_csv_float(row[7]),
                }
        return None

    @staticmethod
    def _float_equals(first: float, second: float, tolerance: float = 0.001) -> bool:
        return abs(first - second) < tolerance

    @staticmethod
    def _subtest_csv_code(code: str) -> str:
        return {"PS": "OS", "RP": "PR"}.get(code, code)

    @staticmethod
    def _application_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"AVL-{base_id:03d}" if isinstance(base_id, int) else f"AVL-{base_id}"

    @staticmethod
    def _report_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"RPT-WISC4-{base_id:03d}" if isinstance(base_id, int) else f"RPT-WISC4-{base_id}"

    @staticmethod
    def _format_date(value) -> str:
        if not value:
            return "—"
        if hasattr(value, "strftime"):
            return value.strftime("%d/%m/%Y")
        return str(value)

    @classmethod
    def _age_label(cls, patient, reference_date) -> str:
        birth_date = getattr(patient, "birth_date", None)
        if birth_date and reference_date:
            years = reference_date.year - birth_date.year
            months = reference_date.month - birth_date.month
            if reference_date.day < birth_date.day:
                months -= 1
            if months < 0:
                years -= 1
                months += 12
            return f"{years} anos e {months} meses"
        age = getattr(patient, "age", None)
        return f"{age} anos" if age is not None else "Não informado"

    @staticmethod
    def _sex_label(value: str | None) -> str:
        labels = {"M": "Masculino", "F": "Feminino", "male": "Masculino", "female": "Feminino"}
        return labels.get(value, value or "Não informado")

    @staticmethod
    def _schooling_label(patient) -> str:
        value = getattr(patient, "schooling", None) or getattr(patient, "grade_year", None)
        labels = {
            "preschool": "Educação infantil",
            "elementary": "Ensino fundamental",
            "elementary_incomplete": "Ensino fundamental incompleto",
            "elementary_complete": "Ensino fundamental completo",
            "middle": "Ensino médio",
            "middle_incomplete": "Ensino médio incompleto",
            "middle_complete": "Ensino médio completo",
        }
        if not value:
            return "Não informado"
        return labels.get(str(value), str(value).replace("_", " ").strip().title())

    @staticmethod
    def _professional_label(examiner) -> str:
        if not examiner:
            return "Não informado"
        get_full_name = getattr(examiner, "get_full_name", None)
        if callable(get_full_name):
            name = get_full_name()
            if name:
                return name
        return getattr(examiner, "full_name", None) or getattr(examiner, "name", None) or getattr(examiner, "username", None) or "Não informado"

    @staticmethod
    def _interval(value) -> str:
        if not value:
            return "—"
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return f"{value[0]}-{value[1]}"
        return str(value)

    @staticmethod
    def _format_number(value, decimals: int = 0) -> str:
        if value is None or value == "":
            return "—"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        text = f"{number:.{decimals}f}".replace(".", ",")
        if decimals > 0:
            text = text.rstrip("0").rstrip(",")
        return text

    @staticmethod
    def _float(value) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _chart_height(value: float | None, minimum: int, maximum: int) -> str:
        if value is None:
            return "0"
        normalized = ((max(minimum, min(maximum, value)) - minimum) / (maximum - minimum)) * 100
        return str(max(6, min(100, int(round(normalized)))))

    @staticmethod
    def _badge_class(classification: str | None) -> str:
        if classification in {"Muito Superior", "Superior", "Média Superior"}:
            return "high"
        if classification == "Média":
            return "average"
        if classification in {"Não classificado", None}:
            return "neutral"
        return "low"

    @staticmethod
    def _is_low(classification: str | None) -> bool:
        return classification in {"Extremamente Baixo", "Inferior", "Limítrofe", "Média Inferior", "Dificuldade Grave", "Dificuldade Moderada", "Dificuldade Leve"}

    @staticmethod
    def _join(items: list[str]) -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        return ", ".join(items[:-1]) + " e " + items[-1]
