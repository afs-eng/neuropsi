from __future__ import annotations

from datetime import date
from pathlib import Path

from django.template import Context
from django.template import engines

from apps.tests.bpa2.interpreters import build_gold_standard_interpretation
from apps.tests.services.playwright_pdf_service import generate_pdf_from_html


class BPA2PdfService:
    TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tests" / "pdf" / "bpa2_report.html"
    ROW_ORDER = ["ac", "ad", "aa", "ag"]
    ROW_LABELS = {
        "ac": "Atenção Concentrada - AC",
        "ad": "Atenção Dividida - AD",
        "aa": "Atenção Alternada - AA",
        "ag": "Atenção Geral - AG",
    }
    SHORT_LABELS = {"ac": "AC", "ad": "AD", "aa": "AA", "ag": "AG"}

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
        subtests = classified.get("subtestes") or []
        rows = cls._result_rows(subtests)
        row_by_code = {row["code"]: row for row in rows}
        ag_row = row_by_code.get("ag", {})
        ac_row = row_by_code.get("ac", {})
        ad_row = row_by_code.get("ad", {})
        aa_row = row_by_code.get("aa", {})
        total_errors = sum(cls._int(row.get("errors_raw")) for row in rows if row.get("code") != "ag")
        short_name = cls._short_name(patient.full_name)

        interpretation = build_gold_standard_interpretation(subtests, short_name)

        return {
            "codigo_avaliado": cls._application_code(application),
            "codigo_relatorio": cls._report_code(application),
            "data_aplicacao": cls._format_date(application.applied_on),
            "nome": patient.full_name or "Não informado",
            "sexo": cls._sex_label(getattr(patient, "sex", None)),
            "idade": cls._age_label(patient, application.applied_on),
            "escolaridade": cls._schooling_label(patient),
            "profissional": cls._professional_label(getattr(evaluation, "examiner", None)),
            "tabela_normativa": cls._normative_label(classified, patient, application.applied_on),
            "referencia_normativa": cls._reference_label(classified),
            "aplicacao": "Válida",
            "rows": rows,
            "chart_bars": cls._chart_bars(row_by_code, total_errors),
            "clinical_paragraphs": interpretation["clinical_paragraphs"],
            "clinical_paragraphs_html": [cls._emphasize_terms(paragraph) for paragraph in interpretation["clinical_paragraphs"]],
            "clinical_box_text": interpretation["clinical_box_text"],
            "clinical_box_text_html": cls._emphasize_terms(interpretation["clinical_box_text"]),
            "synthesis_text": interpretation["synthesis_text"],
            "synthesis_text_html": cls._emphasize_terms(interpretation["synthesis_text"]),
        }

    @classmethod
    def _result_rows(cls, subtests: list[dict]) -> list[dict]:
        by_code = {item.get("codigo"): item for item in subtests}
        rows = []
        for code in cls.ROW_ORDER:
            item = by_code.get(code) or {}
            classification = item.get("classificacao") or "Não classificado"
            percentile = cls._int(item.get("percentil"))
            rows.append(
                {
                    "code": code,
                    "label": cls.ROW_LABELS[code],
                    "short_label": cls.SHORT_LABELS[code],
                    "points": cls._format_number(item.get("total")),
                    "errors": cls._format_number(item.get("erros")),
                    "errors_raw": cls._int(item.get("erros")),
                    "percentile": cls._format_number(percentile),
                    "percentile_raw": percentile,
                    "classification": classification,
                    "badge_class": cls._badge_class(classification),
                }
            )
        return rows

    @classmethod
    def _chart_bars(cls, row_by_code: dict, total_errors: int) -> list[dict]:
        bars = []
        for code in ["ac", "ad", "aa"]:
            row = row_by_code.get(code, {})
            percentile = cls._int(row.get("percentile_raw"))
            bars.append(
                {
                    "label": cls.SHORT_LABELS[code],
                    "value": cls._format_number(percentile),
                    "height": cls._chart_height(percentile),
                    "is_error": False,
                }
            )
        bars.append(
            {
                "label": "Erros",
                "value": cls._format_number(total_errors),
                "height": cls._chart_height(total_errors),
                "is_error": True,
            }
        )
        ag = row_by_code.get("ag", {})
        ag_percentile = cls._int(ag.get("percentile_raw"))
        bars.append(
            {
                "label": "AG",
                "value": cls._format_number(ag_percentile),
                "height": cls._chart_height(ag_percentile),
                "is_error": False,
            }
        )
        return bars

    @classmethod
    def _clinical_paragraphs(cls, short_name: str, ac: dict, ad: dict, aa: dict, ag: dict, total_errors: int) -> list[str]:
        ag_class = ag.get("classification") or "Não classificado"
        ac_class = ac.get("classification") or "Não classificado"
        ad_class = ad.get("classification") or "Não classificado"
        aa_class = aa.get("classification") or "Não classificado"

        return [
            (
                f"A BPA-2 indicou desempenho atencional geral situado na faixa {ag_class}, {cls._global_meaning(ag_class)}. "
                "Esse resultado deve ser compreendido como indicativo do funcionamento atencional no contexto estruturado de aplicação, especialmente quando analisado em conjunto com os domínios específicos avaliados."
            ),
            (
                f"Na Atenção Concentrada, o desempenho foi classificado como {ac_class}, {cls._ac_meaning(ac_class)} "
                f"Os erros observados nesse domínio devem ser considerados qualitativamente, pois podem refletir oscilações pontuais de monitoramento, velocidade de execução ou controle da resposta durante a tarefa."
            ),
            (
                f"Na Atenção Dividida, o resultado foi classificado como {ad_class}, {cls._ad_meaning(ad_class)} "
                "Esse achado informa a capacidade de distribuir recursos atencionais e responder diante de demandas concorrentes."
            ),
            (
                f"Na Atenção Alternada, o desempenho situou-se na faixa {aa_class}, {cls._aa_meaning(aa_class)} "
                "Esse resultado deve ser integrado à análise da flexibilidade atencional, mudança de estratégia e adaptação às regras da tarefa."
            ),
            (
                f"A Atenção Geral apresentou classificação {ag_class}, refletindo {cls._ag_meaning(ag_class)} "
                f"O total de erros observado foi {cls._format_number(total_errors)}, indicador complementar de precisão, autocorreção, monitoramento e controle da resposta."
            ),
        ]

    @classmethod
    def _synthesis_text(cls, short_name: str, ac: dict, ad: dict, aa: dict, ag: dict, total_errors: int) -> str:
        ag_class = ag.get("classification") or "Não classificado"
        ac_class = ac.get("classification") or "Não classificado"
        ad_class = ad.get("classification") or "Não classificado"
        aa_class = aa.get("classification") or "Não classificado"
        strengths = [label for label, classification in [("atenção concentrada", ac_class), ("atenção dividida", ad_class), ("atenção alternada", aa_class)] if cls._is_high(classification)]
        lowered = [label for label, classification in [("atenção concentrada", ac_class), ("atenção dividida", ad_class), ("atenção alternada", aa_class)] if cls._is_low(classification)]

        if lowered:
            profile = f"com pontos de atenção em {cls._join(lowered)}"
        elif strengths:
            profile = f"com melhor desempenho em {cls._join(strengths)}"
        else:
            profile = "sem discrepâncias expressivas entre os domínios específicos"

        return (
            f"A BPA-2 indicou desempenho atencional geral na faixa {ag_class}, com atenção concentrada {ac_class}, atenção dividida {ad_class} e atenção alternada {aa_class}. "
            f"Em análise clínica, o perfil de {short_name} sugere funcionamento atencional {cls._profile_status(ag_class)}, {profile}. "
            f"Os erros observados ({cls._format_number(total_errors)}) devem ser compreendidos como indicadores qualitativos de precisão e monitoramento da resposta, não devendo ser interpretados de forma isolada."
        )

    @staticmethod
    def _global_meaning(classification: str) -> str:
        if classification in {"Média Superior", "Superior", "Muito Superior"}:
            return "sugerindo funcionamento global acima da média normativa para a faixa etária e grupo de referência utilizado"
        if classification == "Média":
            return "sugerindo funcionamento global compatível com a média normativa para a faixa etária e grupo de referência utilizado"
        if classification in {"Média Inferior", "Inferior", "Muito Inferior"}:
            return "sugerindo menor eficiência global em comparação aos parâmetros normativos utilizados"
        return "demandando interpretação cautelosa em relação aos parâmetros normativos utilizados"

    @staticmethod
    def _ac_meaning(classification: str) -> str:
        if classification in {"Média Superior", "Superior", "Muito Superior"}:
            return "indicando boa capacidade para selecionar uma fonte principal de informação e manter o foco diante de estímulos distratores."
        if classification == "Média":
            return "indicando capacidade adequada para selecionar uma fonte principal de informação e manter o foco diante de estímulos distratores."
        return "sugerindo menor eficiência na seleção e sustentação do foco atencional diante de estímulos distratores."

    @staticmethod
    def _ad_meaning(classification: str) -> str:
        if classification in {"Média Superior", "Superior", "Muito Superior"}:
            return "evidenciando desempenho acima da média em tarefa que exige monitoramento simultâneo de mais de um estímulo."
        if classification == "Média":
            return "indicando desempenho compatível com o esperado em tarefa que exige monitoramento simultâneo de mais de um estímulo."
        return "sugerindo menor eficiência para monitorar simultaneamente mais de um estímulo ou demanda."

    @staticmethod
    def _aa_meaning(classification: str) -> str:
        if classification in {"Média Superior", "Superior", "Muito Superior"}:
            return "indicando boa flexibilidade atencional e capacidade preservada para alternar o foco entre estímulos ou critérios distintos."
        if classification == "Média":
            return "indicando flexibilidade atencional compatível com o esperado para alternar o foco entre estímulos ou critérios distintos."
        return "sugerindo menor eficiência para alternar o foco entre estímulos, regras ou critérios distintos."

    @staticmethod
    def _ag_meaning(classification: str) -> str:
        if classification in {"Média Superior", "Superior", "Muito Superior"}:
            return "desempenho global favorável na bateria."
        if classification == "Média":
            return "desempenho global preservado e compatível com o esperado."
        return "fragilidade global relativa nos processos atencionais avaliados."

    @classmethod
    def _profile_status(cls, classification: str) -> str:
        if cls._is_high(classification):
            return "global preservado e acima da média normativa"
        if classification == "Média":
            return "global preservado"
        if cls._is_low(classification):
            return "global com sinais de menor eficiência"
        return "a ser integrado aos demais dados clínicos"

    @staticmethod
    def _is_high(classification: str) -> bool:
        return classification in {"Média Superior", "Superior", "Muito Superior"}

    @staticmethod
    def _is_low(classification: str) -> bool:
        return classification in {"Média Inferior", "Inferior", "Muito Inferior"}

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
        terms = [
            "BPA-2",
            "Atenção Concentrada",
            "Atenção Dividida",
            "Atenção Alternada",
            "Atenção Geral",
            "Em análise clínica",
        ]
        html = str(text or "")
        for term in terms:
            html = html.replace(term, f"<strong>{term}</strong>")
        return html

    @staticmethod
    def _join(items: list[str]) -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
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
        return f"RPT-BPA2-{int(base_id):03d}" if str(base_id).isdigit() else f"RPT-BPA2-{base_id}"

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

    @classmethod
    def _normative_label(cls, classified: dict, patient, applied_on) -> str:
        faixa = classified.get("faixa") or "Não informado"
        norm_type = classified.get("norm_type") or "idade"
        if norm_type == "escolaridade":
            return f"Escolaridade / {faixa}"
        age_text = cls._age_label(patient, applied_on)
        try:
            age = int(str(age_text).split(" ", 1)[0])
        except (TypeError, ValueError):
            age = 18
        stage = "Infantil" if age < 18 else "Adulto"
        return f"{stage} / {faixa}"

    @staticmethod
    def _reference_label(classified: dict) -> str:
        faixa = classified.get("faixa") or "Não informado"
        norm_type = classified.get("norm_type") or "idade"
        suffix = " de escolaridade" if norm_type == "escolaridade" else ""
        return f"Percentis - 2022 - {faixa}{suffix} - Brasil"

    @staticmethod
    def _short_name(full_name: str | None) -> str:
        token = (full_name or "Paciente").strip().split(" ", 1)[0]
        return token[:1].upper() + token[1:] if token else "Paciente"
