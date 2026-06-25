from __future__ import annotations

from datetime import date
from pathlib import Path

from django.template import Context
from django.template import engines

from apps.tests.services.playwright_pdf_service import generate_pdf_from_html

from .config import SCARED_FORMS
from .norms import PAIS_CORTES


class SCAREDPdfService:
    TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tests" / "pdf" / "scared_report.html"
    DOMAIN_ORDER = [
        ("panico_sintomas_somaticos", "Pânico/Sintomas somáticos", "Pânico/somático"),
        ("ansiedade_generalizada", "Ansiedade generalizada", "Ans. generalizada"),
        ("ansiedade_separacao", "Ansiedade de separação", "Separação"),
        ("fobia_social", "Ansiedade social", "Social"),
        ("evitacao_escolar", "Evitação escolar", "Escola"),
    ]
    DOMAIN_CONTEXTS = {
        "panico_sintomas_somaticos": "manifestações físicas de ansiedade, desconfortos somáticos e episódios de medo intenso",
        "ansiedade_generalizada": "preocupação excessiva, antecipação negativa e tensão diante de demandas cotidianas",
        "ansiedade_separacao": "insegurança diante de separações, necessidade de reasseguramento e maior dependência de figuras de referência",
        "fobia_social": "situações de exposição, avaliação social e desconforto em interações interpessoais",
        "evitacao_escolar": "frequência e permanência em contexto escolar, com possível recusa ou sofrimento associado à escola",
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
        evaluation = getattr(application, "evaluation", None)
        patient = getattr(evaluation, "patient", None)
        raw_payload = getattr(application, "raw_payload", None) or {}
        computed = getattr(application, "computed_payload", None) or {}
        classified = getattr(application, "classified_payload", None) or {}
        rows = {
            row.get("fator"): row
            for row in classified.get("analise_geral") or []
            if isinstance(row, dict) and row.get("fator")
        }
        form_type = classified.get("form_type") or raw_payload.get("form") or computed.get("form") or "child"
        total_score = cls._score_value(rows.get("total"), computed.get("brutos"), "total")
        total_cutoff = PAIS_CORTES["total"]
        domain_rows = []
        elevated_labels = []

        for factor, label, short_label in cls.DOMAIN_ORDER:
            row = rows.get(factor) or {}
            score = cls._score_value(row, computed.get("brutos"), factor)
            cutoff = PAIS_CORTES[factor]
            classification = cls._classification_label(form_type, row, score, cutoff)
            is_elevated = score >= cutoff
            if is_elevated:
                elevated_labels.append(label)
            ratio = cls._ratio(score, cutoff)
            domain_rows.append(
                {
                    "factor": factor,
                    "label": label,
                    "short_label": short_label,
                    "score": score,
                    "cutoff": str(cutoff),
                    "relative_index": int(round(ratio)),
                    "relative_index_label": f"{int(round(ratio))}%",
                    "classification": classification,
                    "status_class": "status-alert" if is_elevated else "status-ok",
                    "bar_width": cls._bar_width(ratio),
                    "bar_fill_class": "alert" if is_elevated else "",
                    "ratio_label": f"{int(round(ratio))}%",
                    "at_cutoff": score == cutoff,
                }
            )

        total_clinical = total_score >= total_cutoff
        interpretation_paragraphs = cls._interpretation_paragraphs(
            patient_name=getattr(patient, "full_name", None) or "Paciente",
            form_type=form_type,
            total_score=total_score,
            total_cutoff=total_cutoff,
            total_clinical=total_clinical,
            domain_rows=domain_rows,
        )

        return {
            "nome_paciente": getattr(patient, "full_name", None) or "Não informado",
            "idade": cls._age_label(application),
            "data_aplicacao": cls._format_date(getattr(application, "applied_on", None)),
            "respondente": cls._respondent_label(form_type, raw_payload),
            "versao_label": cls._version_label(form_type),
            "escore_total": total_score,
            "corte_total": total_cutoff,
            "indicador_badge_class": "alert" if total_clinical else "ok",
            "indicador_badge_text": "Rastreio positivo" if total_clinical else "Abaixo do corte",
            "dominios_elevados": f"{len(elevated_labels)}/5",
            "dominios_elevados_descricao": cls._elevated_description(elevated_labels),
            "leitura_clinica": cls._clinical_reading(total_score, total_clinical, len(elevated_labels)),
            "leitura_clinica_caption": cls._clinical_caption(total_score, total_clinical, len(elevated_labels)),
            "result_rows": domain_rows,
            "interpretation_paragraphs": interpretation_paragraphs,
            "response_rows": cls._response_rows(raw_payload),
            "technical_note": cls._technical_note(form_type),
        }

    @staticmethod
    def _score_value(row: dict | None, gross_scores: dict | None, factor: str) -> int:
        value = (row or {}).get("escore_bruto")
        if value in (None, ""):
            value = (gross_scores or {}).get(factor)
        try:
            return int(round(float(value or 0)))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _ratio(score: int, cutoff: int) -> float:
        if cutoff <= 0:
            return 0.0
        return max(0.0, (float(score) / float(cutoff)) * 100.0)

    @staticmethod
    def _bar_width(ratio: float) -> float:
        return min(100.0, round(ratio / 1.5, 1))

    @staticmethod
    def _classification_label(form_type: str, row: dict, score: int, cutoff: int) -> str:
        if form_type == "parent":
            return "Clínico" if score >= cutoff else "Não Clínico"

        percentile = row.get("percentil")
        try:
            percentile_value = float(percentile)
        except (TypeError, ValueError):
            percentile_value = None

        if percentile_value is None:
            if score >= cutoff:
                return "Média Superior"
            return "Média"
        if percentile_value >= 95:
            return "Superior"
        if percentile_value >= 75:
            return "Média Superior"
        if percentile_value >= 25:
            return "Média"
        if percentile_value >= 10:
            return "Média Inferior"
        return "Inferior"

    @staticmethod
    def _respondent_label(form_type: str, raw_payload: dict) -> str:
        respondent_name = str(raw_payload.get("respondent_name") or "").strip()
        if respondent_name:
            return respondent_name
        return SCARED_FORMS.get(form_type, "Autorrelato")

    @staticmethod
    def _version_label(form_type: str) -> str:
        if form_type == "parent":
            return "pais/responsáveis"
        return "autorrelato"

    @staticmethod
    def _elevated_description(labels: list[str]) -> str:
        if not labels:
            return "Nenhum domínio acima do critério clínico"
        if len(labels) == 1:
            return labels[0]
        if len(labels) == 2:
            return f"{labels[0]} e {labels[1]}"
        return ", ".join(labels[:-1]) + f" e {labels[-1]}"

    @staticmethod
    def _clinical_reading(total_score: int, total_clinical: bool, elevated_count: int) -> str:
        if total_clinical:
            return "Rastreio positivo para sintomas ansiosos"
        if elevated_count:
            return "Elevação específica em domínio ansioso"
        return "Sem elevação global no SCARED"

    @staticmethod
    def _clinical_caption(total_score: int, total_clinical: bool, elevated_count: int) -> str:
        if total_score >= 31:
            return "Rastreio positivo com maior especificidade clínica"
        if total_clinical:
            return "Rastreio positivo a integrar com entrevista e impacto funcional"
        if elevated_count:
            return "Resultado global abaixo do corte, com domínio no limiar ou elevado"
        return "Resultado global abaixo do ponto de corte clínico"

    @classmethod
    def _interpretation_paragraphs(
        cls,
        patient_name: str,
        form_type: str,
        total_score: int,
        total_cutoff: int,
        total_clinical: bool,
        domain_rows: list[dict],
    ) -> list[str]:
        respondent_label = "pais/cuidadores" if form_type == "parent" else "autorrelato"
        status_total = "acima" if total_clinical else "abaixo"
        if total_clinical:
            first = (
                f"{patient_name} apresentou escore total de {total_score} no SCARED, resultado {status_total} do ponto de corte clínico usual de {total_cutoff}. "
                f"Esse achado sugere rastreio positivo para sintomas ansiosos segundo o relato de {respondent_label}, devendo ser interpretado como indicador de rastreamento e não como diagnóstico isolado."
            )
        else:
            first = (
                f"{patient_name} apresentou escore total de {total_score} no SCARED, resultado {status_total} do ponto de corte clínico usual de {total_cutoff}. "
                f"Esse achado não sugere, neste instrumento, rastreio positivo global para sintomas ansiosos clinicamente relevantes segundo o relato de {respondent_label}."
            )

        elevated_domains = [row for row in domain_rows if row["status_class"] == "status-alert"]
        non_elevated_domains = [row for row in domain_rows if row["status_class"] != "status-alert"]
        if elevated_domains:
            ordered = sorted(
                elevated_domains,
                key=lambda row: float(str(row["ratio_label"]).rstrip("%") or 0),
                reverse=True,
            )
            elevated_labels = [row["label"] for row in ordered]
            predominant = ordered[0]
            threshold_labels = [row["label"] for row in ordered if row["at_cutoff"]]
            second = [
                f"Na análise por domínios, observaram-se elevações em {cls._elevated_description(elevated_labels)}.",
                f"O perfil sugere predomínio de {predominant['label']}, com repercussões possíveis em {cls.DOMAIN_CONTEXTS.get(predominant['factor'], 'contextos funcionais relacionados à ansiedade')}."
            ]
            if threshold_labels:
                second.append(
                    f"{cls._elevated_description(threshold_labels)} encontra-se no limiar clínico, devendo ser descrito como indicador limítrofe e interpretado com cautela técnica."
                )
            if not total_clinical:
                second.append(
                    "A ausência de elevação global no SCARED não exclui a possibilidade de manifestações ansiosas situacionais ou específicas, especialmente quando houver queixas funcionais ou observação clínica compatível."
                )
            second_paragraph = " ".join(second)
        else:
            second_paragraph = (
                "Na análise por domínios, não se observaram elevações acima dos pontos de corte em pânico/sintomas somáticos, ansiedade generalizada, "
                "ansiedade de separação, ansiedade social ou evitação escolar."
            )
            if not total_clinical:
                second_paragraph += " A ausência de elevação global no SCARED não exclui a possibilidade de manifestações ansiosas situacionais ou específicas observadas por outros meios clínicos."

        if non_elevated_domains:
            third = (
                f"Os domínios {cls._elevated_description([row['label'] for row in non_elevated_domains])} permaneceram abaixo dos pontos de corte, "
                "não indicando, neste instrumento, elevação clinicamente relevante nesses agrupamentos sintomáticos específicos."
            )
        else:
            third = "Todos os domínios avaliados atingiram o limiar clínico ou situaram-se acima dos respectivos pontos de corte, exigindo análise integrada do impacto funcional."

        fourth = (
            "Os resultados do SCARED devem ser integrados à entrevista clínica, à observação comportamental, às informações familiares e escolares e aos demais instrumentos do protocolo, "
            "especialmente quando houver impacto funcional em contexto social, acadêmico ou emocional."
        )
        return [first, second_paragraph, third, fourth]

    @staticmethod
    def _technical_note(form_type: str) -> str:
        if form_type == "parent":
            return (
                "O SCARED é um instrumento de rastreamento de sintomas ansiosos. Nesta versão, a leitura clínica utiliza os pontos de corte do formulário de pais/cuidadores."
            )
        return (
            "O SCARED é um instrumento de rastreamento de sintomas ansiosos. Nesta versão, a classificação integra percentis normativos do autorrelato e a leitura clínica dos pontos de corte usuais do instrumento."
        )

    @staticmethod
    def _response_rows(raw_payload: dict) -> list[list[dict]]:
        responses = raw_payload.get("responses") or {}
        rows: list[list[dict]] = []
        for row_index in range(9):
            row: list[dict] = []
            for offset in [1, 10, 19, 28, 37]:
                item_number = row_index + offset
                if item_number > 41:
                    row.append({"item": "", "value": "", "badge_class": "empty"})
                    continue
                value = responses.get(str(item_number), "")
                row.append(
                    {
                        "item": f"{item_number:02d}",
                        "value": value,
                        "badge_class": SCAREDPdfService._response_badge_class(value),
                    }
                )
            rows.append(row)
        return rows

    @staticmethod
    def _response_badge_class(value) -> str:
        if value == 2:
            return "is-two"
        if value == 1:
            return "is-one"
        if value == 0:
            return "is-zero"
        return "empty"

    @staticmethod
    def _age_label(application) -> str:
        patient = getattr(getattr(application, "evaluation", None), "patient", None)
        patient_age = getattr(patient, "age", None)
        if patient_age is not None:
            return f"{int(patient_age)} anos"

        raw_age = (getattr(application, "raw_payload", None) or {}).get("age")
        if raw_age is not None:
            try:
                return f"{int(raw_age)} anos"
            except (TypeError, ValueError):
                pass

        birth_date = getattr(patient, "birth_date", None)
        applied_on = getattr(application, "applied_on", None)
        if isinstance(birth_date, date) and isinstance(applied_on, date):
            years = applied_on.year - birth_date.year
            months = applied_on.month - birth_date.month
            if applied_on.day < birth_date.day:
                months -= 1
            if months < 0:
                years -= 1
                months += 12
            return f"{max(years, 0)} anos" + (f" e {months} meses" if months else "")

        return "Não informado"

    @staticmethod
    def _format_date(value) -> str:
        if isinstance(value, date):
            return value.strftime("%d/%m/%Y")
        return str(value or "Não informado")
