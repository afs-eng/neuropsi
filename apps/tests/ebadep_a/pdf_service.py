from __future__ import annotations

from datetime import date
from pathlib import Path

from django.template import Context, engines

from apps.tests.services.playwright_pdf_service import generate_pdf_from_html

from .config import ITEM_LABELS
from .interpreters import get_report_interpretation


class EBADEPAPdfService:
    TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tests" / "pdf" / "ebadep_a_report.html"

    @classmethod
    def generate_pdf_bytes(cls, application) -> bytes:
        html_source = cls._render_html(application)
        return generate_pdf_from_html(html_source)

    @classmethod
    def _render_html(cls, application) -> str:
        template_source = cls.TEMPLATE_PATH.read_text(encoding="utf-8")
        template = engines["django"].from_string(template_source)
        return template.render(Context(cls._build_context(application)).flatten())

    @classmethod
    def _build_context(cls, application) -> dict:
        evaluation = getattr(application, "evaluation", None)
        patient = getattr(evaluation, "patient", None)
        raw_payload = getattr(application, "raw_payload", None) or {}
        computed = getattr(application, "computed_payload", None) or {}
        classified = getattr(application, "classified_payload", None) or {}

        score = classified.get("escore_total", computed.get("escore_total", "—"))
        percentile = classified.get("percentil", "—")
        classification = classified.get("classificacao") or "Não classificado"
        patient_name = getattr(patient, "full_name", None) or "Não informado"
        interpretation_text = get_report_interpretation(classification, patient_name)

        return {
            "application": application,
            "application_code": cls._application_code(application),
            "report_code": cls._report_code(application),
            "page_count": 4,
            "patient_name": patient_name,
            "patient_cpf": getattr(patient, "cpf", None) or "—",
            "patient_sex": cls._sex_label(getattr(patient, "sex", None)),
            "patient_age": cls._age_label(patient, raw_payload, getattr(application, "applied_on", None)),
            "patient_schooling": cls._schooling_label(getattr(patient, "schooling", None)),
            "patient_state": getattr(patient, "state", None) or "—",
            "patient_email": getattr(patient, "email", None) or "—",
            "professional": cls._professional_label(getattr(evaluation, "examiner", None)),
            "applied_on": cls._format_date(getattr(application, "applied_on", None)),
            "normative_table": "Percentis - 2012 - Tabela Geral",
            "score": score,
            "percentile": percentile,
            "classification": classification,
            "classification_level": cls._classification_level(classification),
            "interpretation_text": interpretation_text,
            "clinical_alert": cls._clinical_alert(classification),
            "synthesis": classified.get("sintese") or "não classificado",
            "critical_items": cls._critical_items(classified),
            "response_rows": cls._response_rows(classified, raw_payload),
        }

    @staticmethod
    def _application_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"AVL-{int(base_id):03d}" if isinstance(base_id, int) else f"AVL-{base_id}"

    @staticmethod
    def _report_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"RPT-EBADEPA-{int(base_id):03d}" if isinstance(base_id, int) else f"RPT-EBADEPA-{base_id}"

    @staticmethod
    def _sex_label(value: str | None) -> str:
        if value == "M":
            return "Masculino"
        if value == "F":
            return "Feminino"
        return value or "Não informado"

    @staticmethod
    def _schooling_label(value: str | None) -> str:
        labels = {
            "preschool": "Ensino pré-escolar",
            "elementary": "Ensino fundamental",
            "elementary_incomplete": "Ensino fundamental incompleto",
            "elementary_complete": "Ensino fundamental completo",
            "middle": "Ensino médio",
            "middle_incomplete": "Ensino médio incompleto",
            "middle_complete": "Ensino médio completo",
            "higher_incomplete": "Ensino superior incompleto",
            "higher": "Ensino superior",
            "higher_complete": "Ensino superior completo",
            "postgraduate": "Pós-graduação",
        }
        if not value:
            return "Não informado"
        return labels.get(str(value), str(value).replace("_", " ").strip().title())

    @staticmethod
    def _professional_label(examiner) -> str:
        if examiner:
            name = getattr(examiner, "full_name", None) or getattr(examiner, "name", None)
            registration = getattr(examiner, "registration", None) or getattr(examiner, "crp", None)
            if name and registration:
                return f"{name} - {registration}"
            if name:
                return str(name)
        return "Dra. Jacqueline O. Caires - CRP09/6017"

    @classmethod
    def _age_label(cls, patient, raw_payload: dict, applied_on: date | None) -> str:
        raw_age = raw_payload.get("idade") or raw_payload.get("age")
        if raw_age is not None:
            return f"{raw_age} anos" if isinstance(raw_age, int) else str(raw_age)

        explicit_age = getattr(patient, "age", None)
        if explicit_age is not None:
            return f"{explicit_age} anos"

        birth_date = getattr(patient, "birth_date", None)
        if birth_date:
            reference = applied_on or date.today()
            months_total = (reference.year - birth_date.year) * 12 + reference.month - birth_date.month
            if reference.day < birth_date.day:
                months_total -= 1
            years, months = divmod(max(months_total, 0), 12)
            return f"{years} anos" + (f" e {months} meses" if months else "")
        return "Não informado"

    @staticmethod
    def _format_date(value) -> str:
        if not value:
            return "Não informado"
        return value.strftime("%d/%m/%Y") if hasattr(value, "strftime") else str(value)

    @staticmethod
    def _classification_level(classification: str) -> str:
        normalized = classification.lower()
        if "severa" in normalized or "grave" in normalized:
            return "severe"
        if "moderada" in normalized:
            return "moderate"
        if "leve" in normalized:
            return "light"
        if "mínima" in normalized or "minima" in normalized:
            return "minimal"
        return "neutral"

    @staticmethod
    def _clinical_alert(classification: str) -> str:
        normalized = classification.lower()
        if "moderada" not in normalized and "severa" not in normalized:
            return ""
        return (
            "Nessa faixa, recomenda-se investigar em entrevista clínica a presença de humor deprimido, anedonia, "
            "desesperança, ideação suicida e prejuízos funcionais, integrando o resultado aos demais dados da avaliação."
        )

    @staticmethod
    def _critical_items(classified: dict) -> list[dict]:
        return [
            {"item": item.get("item"), "label": ITEM_LABELS.get(item.get("item"), "Item crítico")}
            for item in classified.get("items_criticos") or []
        ]

    @staticmethod
    def _response_rows(classified: dict, raw_payload: dict) -> list[dict]:
        details = {
            int(item.get("item")): item.get("resposta")
            for item in (classified.get("result") or {}).get("detalhe_itens", [])
            if item.get("item") is not None
        }
        if not details:
            details = {
                item: raw_payload.get(f"item_{item:02d}", raw_payload.get(str(item), "—"))
                for item in range(1, 46)
            }

        cells = [
            {
                "item": f"{item:03d}",
                "response": details.get(item, "—"),
                "label": ITEM_LABELS.get(item, ""),
                "is_critical": details.get(item) == 3,
            }
            for item in range(1, 46)
        ]
        rows = []
        for index in range(0, len(cells), 5):
            row_cells = cells[index : index + 5]
            rows.append({"cells": row_cells, "empty_cells": [None] * (5 - len(row_cells))})
        return rows
