from __future__ import annotations

from datetime import date
from pathlib import Path

from django.template import Context
from django.template import engines

from apps.tests.epq_j.interpreters import get_report_interpretation, get_synthesis
from apps.tests.services.playwright_pdf_service import generate_pdf_from_html


class EPQJPdfService:
    TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tests" / "pdf" / "epq_j_report.html"
    FACTOR_ORDER = ["P", "E", "N", "S"]
    FACTOR_LABELS = {
        "P": "Psicoticismo - P",
        "E": "Extroversão - E",
        "N": "Neuroticismo - N",
        "S": "Sinceridade - S",
    }
    FACTOR_DEFINITIONS = {
        "P": "Psicoticismo descreve tendência à rigidez, impulsividade, baixa modulação interpessoal e oposição diante de frustrações, quando elevado.",
        "E": "Extroversão indica sociabilidade, atividade, espontaneidade e busca por contato interpessoal, ou reserva e introspecção em níveis baixos.",
        "N": "Neuroticismo refere-se à instabilidade emocional, sensibilidade ao estresse, ansiedade e oscilação afetiva.",
        "S": "Sinceridade avalia desejabilidade social e estilo de autoapresentação, funcionando como indicador de cautela interpretativa.",
    }

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
        computed = application.computed_payload or {}
        classified = application.classified_payload or {}
        fatores = classified.get("fatores") or computed.get("resultados") or {}
        sexo = classified.get("sexo") or computed.get("sexo") or (application.raw_payload or {}).get("sexo") or getattr(patient, "sex", None)
        rows = cls._result_rows(fatores)
        short_name = cls._short_name(patient.full_name)
        interpretation = application.interpretation_text or get_report_interpretation(fatores, patient.full_name)
        clinical_paragraphs = cls._paragraphs(interpretation)
        synthesis = classified.get("sintese") or get_synthesis(fatores)

        return {
            "codigo_avaliado": cls._application_code(application),
            "codigo_relatorio": cls._report_code(application),
            "data_aplicacao": cls._format_date(application.applied_on),
            "nome": patient.full_name or "Não informado",
            "sexo": cls._sex_label(getattr(patient, "sex", None) or sexo),
            "idade": cls._age_label(patient, application.applied_on),
            "escolaridade": cls._schooling_label(patient),
            "profissional": cls._professional_label(getattr(evaluation, "examiner", None)),
            "tabela_normativa": cls._normative_label(sexo),
            "referencia_normativa": f"Percentis EPQ-J - tabela normativa {cls._normative_label(sexo)} - Brasil",
            "aplicacao": "Válida",
            "rows": rows,
            "chart_bars": cls._chart_bars(rows),
            "factor_definitions": [
                {"label": cls.FACTOR_LABELS[code], "text": cls.FACTOR_DEFINITIONS[code]}
                for code in cls.FACTOR_ORDER
            ],
            "clinical_paragraphs_html": [cls._emphasize_terms(paragraph) for paragraph in clinical_paragraphs],
            "clinical_box_text_html": cls._emphasize_terms(cls._clinical_box_text(short_name, rows)),
            "synthesis_text_html": cls._emphasize_terms(cls._synthesis_text(short_name, synthesis, rows)),
        }

    @classmethod
    def _result_rows(cls, fatores: dict) -> list[dict]:
        rows = []
        for code in cls.FACTOR_ORDER:
            item = fatores.get(code) or {}
            classification = item.get("classificacao") or "Não classificado"
            percentile = cls._int(item.get("percentil"))
            rows.append(
                {
                    "code": code,
                    "label": cls.FACTOR_LABELS[code],
                    "short_label": code,
                    "score": cls._format_number(item.get("escore")),
                    "percentile": cls._format_number(percentile),
                    "percentile_raw": percentile,
                    "classification": cls._classification_label(classification),
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
                "is_validity": row["code"] == "S",
            }
            for row in rows
        ]

    @classmethod
    def _clinical_box_text(cls, short_name: str, rows: list[dict]) -> str:
        high = [row["label"].split(" - ", 1)[0].lower() for row in rows if row["badge_class"] in {"alto", "muito-alto"} and row["code"] != "S"]
        if high:
            return f"Em análise clínica, o perfil de {short_name} sugere pontos de atenção em {cls._join(high)}, devendo ser integrado à anamnese, observação clínica e demais instrumentos aplicados."
        return f"Em análise clínica, o perfil de {short_name} deve ser interpretado como descrição dimensional dos traços de personalidade, sem valor diagnóstico isolado."

    @classmethod
    def _synthesis_text(cls, short_name: str, synthesis: str, rows: list[dict]) -> str:
        if synthesis:
            return f"O EPQ-J apresentou o seguinte perfil sintético: {synthesis}. Os resultados contribuem para compreender o estilo emocional e comportamental de {short_name}, sem constituírem diagnóstico isolado."
        summary = ", ".join(f"{row['short_label']}: {row['classification']}" for row in rows)
        return f"O EPQ-J apresentou perfil {summary}. Os achados devem ser integrados ao conjunto da avaliação psicológica."

    @staticmethod
    def _paragraphs(text: str) -> list[str]:
        return [paragraph.strip() for paragraph in str(text or "").split("\n\n") if paragraph.strip()]

    @staticmethod
    def _classification_label(value: str) -> str:
        return str(value or "Não classificado").replace("MEDIO", "Médio").replace("NAO", "Não").title()

    @staticmethod
    def _badge_class(classification: str) -> str:
        normalized = str(classification or "").strip().upper()
        if normalized == "MUITO ALTO":
            return "muito-alto"
        if normalized == "ALTO":
            return "alto"
        if normalized == "MEDIO":
            return "medio"
        if normalized == "BAIXO":
            return "baixo"
        if normalized == "MUITO BAIXO":
            return "muito-baixo"
        return "nao-classificado"

    @staticmethod
    def _chart_height(value: int | float) -> str:
        return str(max(0, min(100, int(value or 0))))

    @staticmethod
    def _int(value) -> int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0

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
    def _emphasize_terms(text: str) -> str:
        html = str(text or "")
        for term in ["EPQ-J", "Psicoticismo", "Extroversão", "Neuroticismo", "Sinceridade", "Em análise clínica", "Análise Clínica"]:
            html = html.replace(term, f"<strong>{term}</strong>")
        return html

    @staticmethod
    def _join(items: list[str]) -> str:
        if len(items) <= 1:
            return items[0] if items else ""
        if len(items) == 2:
            return f"{items[0]} e {items[1]}"
        return f"{', '.join(items[:-1])} e {items[-1]}"

    @staticmethod
    def _application_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"AVL-{int(base_id):03d}" if str(base_id).isdigit() else f"AVL-{base_id}"

    @staticmethod
    def _report_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"RPT-EPQJ-{int(base_id):03d}" if str(base_id).isdigit() else f"RPT-EPQJ-{base_id}"

    @staticmethod
    def _format_date(value) -> str:
        if not value:
            return "-"
        return value.strftime("%d/%m/%Y") if hasattr(value, "strftime") else str(value)

    @staticmethod
    def _sex_label(value: str | None) -> str:
        normalized = str(value or "").strip().upper()
        if normalized == "M":
            return "Masculino"
        if normalized == "F":
            return "Feminino"
        return str(value or "Não informado")

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

    @classmethod
    def _normative_label(cls, sexo: str | None) -> str:
        return f"{cls._sex_label(sexo)} / 10 a 16 anos"

    @staticmethod
    def _short_name(full_name: str | None) -> str:
        token = (full_name or "Paciente").strip().split(" ", 1)[0]
        return token[:1].upper() + token[1:] if token else "Paciente"
