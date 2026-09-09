from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from django.template import Context
from django.template import engines

from apps.tests.services.playwright_pdf_service import generate_pdf_from_html


class ETDAHPdfBase:
    TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "etdah_ad" / "templates" / "tests" / "pdf" / "etdah_report.html"
    instrument_code = ""
    report_prefix = "ETDAH"
    title = "E-TDAH"
    subtitle = "Escala de Transtorno de Déficit de Atenção e Hiperatividade"
    version_label = ""
    row_order: list[str] = []
    row_labels: dict[str, str] = {}
    intro_paragraphs: list[str] = []
    definition_text = ""

    @classmethod
    def generate_pdf_bytes(cls, application) -> bytes:
        context = cls._build_context(application)
        template_source = cls.TEMPLATE_PATH.read_text(encoding="utf-8")
        template = engines["django"].from_string(template_source)
        html = template.render(Context(context).flatten())
        return generate_pdf_from_html(html)

    @classmethod
    def _build_context(cls, application) -> dict:
        patient = application.evaluation.patient
        evaluation = application.evaluation
        classified = application.classified_payload or {}
        computed = application.computed_payload or {}
        results = classified.get("results") or computed.get("results") or {}
        rows = cls._result_rows(results)
        interpretation = cls._interpretation_text(application, computed, classified)
        paragraphs = cls._paragraphs(interpretation)

        return {
            "codigo_avaliado": cls._application_code(application),
            "codigo_relatorio": cls._report_code(application),
            "data_aplicacao": cls._format_date(application.applied_on),
            "nome": patient.full_name or "Não informado",
            "sexo": cls._sex_label(getattr(patient, "sex", None)),
            "idade": cls._age_label(patient, application.applied_on),
            "escolaridade": cls._schooling_label(patient),
            "profissional": cls._professional_label(getattr(evaluation, "examiner", None)),
            "tabela_normativa": cls._normative_label(classified, computed, patient, application.applied_on),
            "referencia_normativa": cls._reference_label(classified, computed),
            "aplicacao": "Válida",
            "title": cls.title,
            "subtitle": cls.subtitle,
            "version_label": cls.version_label,
            "rows": rows,
            "chart_bars": cls._chart_bars(rows),
            "intro_paragraphs": cls.intro_paragraphs,
            "definition_text": cls.definition_text,
            "clinical_paragraphs_html": [cls._emphasize_terms(paragraph) for paragraph in paragraphs],
            "clinical_box_text_html": cls._emphasize_terms(cls._clinical_box_text(rows)),
            "synthesis_text_html": cls._emphasize_terms(cls._synthesis_text(patient.full_name, rows)),
        }

    @classmethod
    def _result_rows(cls, results: dict) -> list[dict]:
        rows = []
        for code in cls.row_order:
            item = results.get(code) or {}
            percentile_text = cls._first_present(item.get("percentile_text"), item.get("percentile"), item.get("percentile_guilmette"), "-")
            classification = item.get("classification") or "Não classificado"
            rows.append(
                {
                    "code": code,
                    "label": cls.row_labels.get(code) or item.get("name") or code,
                    "short_label": cls._short_label(code),
                    "points": cls._format_number(cls._first_present(item.get("raw_score"), item.get("score"))),
                    "mean": cls._format_number(item.get("mean")),
                    "percentile": cls._format_percentile(percentile_text),
                    "percentile_raw": cls._percentile_number(percentile_text),
                    "classification": classification,
                    "badge_class": cls._badge_class(classification),
                }
            )
        return rows

    @classmethod
    def _chart_bars(cls, rows: list[dict]) -> list[dict]:
        return [
            {
                "label": row["short_label"],
                "value": row["percentile"],
                "height": cls._chart_height(row["percentile_raw"]),
            }
            for row in rows
        ]

    @classmethod
    def _clinical_box_text(cls, rows: list[dict]) -> str:
        elevated = [row["label"].split(" - ", 1)[0] for row in rows if cls._is_elevated(row["classification"])]
        if elevated:
            return f"Em análise clínica, observaram-se elevações em {cls._join(elevated)}, indicando necessidade de integração com anamnese, observação clínica e demais instrumentos aplicados."
        return f"Em análise clínica, os resultados da {cls.title} não indicam elevações clinicamente significativas nos fatores apresentados."

    @classmethod
    def _synthesis_text(cls, full_name: str | None, rows: list[dict]) -> str:
        name = cls._short_name(full_name)
        classifications = ", ".join(f"{row['short_label']} {row['classification']}" for row in rows)
        return f"A {cls.title} apresentou o seguinte perfil para {name}: {classifications}. Os achados devem ser compreendidos como indicadores comportamentais e integrados aos demais dados do processo avaliativo."

    @classmethod
    def _interpretation_text(cls, application, computed: dict, classified: dict) -> str:
        return application.interpretation_text or ""

    @staticmethod
    def _paragraphs(text: str) -> list[str]:
        return [part.strip() for part in re.split(r"\n\s*\n", str(text or "")) if part.strip()]

    @classmethod
    def _normative_label(cls, classified: dict, computed: dict, patient, applied_on) -> str:
        return cls._reference_label(classified, computed)

    @classmethod
    def _reference_label(cls, classified: dict, computed: dict) -> str:
        return "Percentis normativos - E-TDAH"

    @classmethod
    def _report_code(cls, application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"RPT-{cls.report_prefix}-{int(base_id):03d}" if str(base_id).isdigit() else f"RPT-{cls.report_prefix}-{base_id}"

    @staticmethod
    def _application_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"AVL-{int(base_id):03d}" if str(base_id).isdigit() else f"AVL-{base_id}"

    @staticmethod
    def _format_date(value) -> str:
        if not value:
            return "-"
        return value.strftime("%d/%m/%Y") if hasattr(value, "strftime") else str(value)

    @staticmethod
    def _sex_label(value: str | None) -> str:
        if value == "M":
            return "Masculino"
        if value == "F":
            return "Feminino"
        return value or "Não informado"

    @classmethod
    def _age_label(cls, patient, applied_on) -> str:
        age = getattr(patient, "age", None)
        birth_date = getattr(patient, "birth_date", None)
        if age is None and birth_date:
            reference = applied_on or date.today()
            age = reference.year - birth_date.year
            if (reference.month, reference.day) < (birth_date.month, birth_date.day):
                age -= 1
        return f"{age} anos" if age is not None else "Não informado"

    @staticmethod
    def _schooling_label(patient) -> str:
        value = getattr(patient, "schooling", None) or getattr(patient, "grade_year", None)
        labels = {
            "elementary": "Ensino fundamental",
            "elementary_complete": "Ensino fundamental completo",
            "middle": "Ensino médio",
            "middle_complete": "Ensino médio completo",
            "higher": "Ensino superior",
            "higher_complete": "Ensino superior completo",
        }
        if not value:
            return "Não informado"
        normalized = str(value).strip().lower()
        return labels.get(normalized, str(value).replace("_", " ").strip().capitalize())

    @staticmethod
    def _professional_label(examiner) -> str:
        if examiner and hasattr(examiner, "get_full_name"):
            name = examiner.get_full_name()
            if name:
                return name
        return "Jacqueline O. Caires - CRP09/6017"

    @staticmethod
    def _format_number(value) -> str:
        if value is None or value == "":
            return "-"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if number.is_integer():
            return str(int(number))
        return f"{number:.1f}".replace(".", ",")

    @staticmethod
    def _first_present(*values):
        for value in values:
            if value is not None and value != "":
                return value
        return None

    @staticmethod
    def _format_percentile(value) -> str:
        text = str(value or "-").replace("Percentil ", "").replace("percentil ", "").strip()
        return text or "-"

    @staticmethod
    def _percentile_number(value) -> float:
        match = re.search(r"\d+(?:[\.,]\d+)?", str(value or ""))
        if not match:
            return 0.0
        return float(match.group(0).replace(",", "."))

    @staticmethod
    def _chart_height(value: int | float) -> str:
        return str(max(0, min(100, int(float(value or 0)))))

    @staticmethod
    def _badge_class(classification: str) -> str:
        if classification in {"Superior", "Muito Superior"}:
            return "superior"
        if classification == "Média Superior":
            return "media-superior"
        if classification == "Média":
            return "media"
        return "inferior"

    @staticmethod
    def _is_elevated(classification: str) -> bool:
        return classification in {"Média Superior", "Superior", "Muito Superior"}

    @staticmethod
    def _short_name(full_name: str | None) -> str:
        token = (full_name or "Paciente").strip().split(" ", 1)[0]
        return token[:1].upper() + token[1:] if token else "Paciente"

    @staticmethod
    def _short_label(code: str) -> str:
        return code.replace("fator_", "F").replace("escore_geral", "EG").upper()

    @staticmethod
    def _join(items: list[str]) -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} e {items[1]}"
        return f"{', '.join(items[:-1])} e {items[-1]}"

    @classmethod
    def _emphasize_terms(cls, text: str) -> str:
        html = str(text or "")
        terms = [cls.title, "Em análise clínica", "Escore Geral"]
        for row_label in cls.row_labels.values():
            terms.append(row_label.split(" - ", 1)[0])
        for term in terms:
            if term:
                html = html.replace(term, f"<strong>{term}</strong>")
        return html
