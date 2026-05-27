from __future__ import annotations

from pathlib import Path

from django.template import Context
from django.template import engines

from apps.tests.services.playwright_pdf_service import generate_pdf_from_html


class FDTPdfService:
    TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tests" / "pdf" / "fdt_report.html"
    PROCESS_ORDER = [
        ("leitura", "Leitura", "processos_automaticos", True),
        ("contagem", "Contagem", "processos_automaticos", True),
        ("escolha", "Escolha", "processos_controlados", True),
        ("alternancia", "Alternância", "processos_controlados", True),
        ("inibicao", "Inibição", "indices_executivos", False),
        ("flexibilidade", "Flexibilidade", "indices_executivos", False),
    ]

    PROCESS_CARD_TEXT = [
        {
            "title": "Leitura",
            "text": "Avalia velocidade de nomeação e automatização em tarefa simples de leitura.",
        },
        {
            "title": "Contagem",
            "text": "Investiga processamento visual, rastreio e resposta automática de contagem.",
        },
        {
            "title": "Escolha",
            "text": "Mensura controle inibitório em condição que exige supressão de resposta automática.",
        },
        {
            "title": "Alternância",
            "text": "Avalia alternância atencional e adaptação entre regras de resposta.",
        },
        {
            "title": "Inibição",
            "text": "Indicador derivado associado à eficiência do controle inibitório.",
        },
        {
            "title": "Flexibilidade",
            "text": "Indicador derivado relacionado à flexibilidade cognitiva e mudança de critério.",
        },
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
        patient = application.evaluation.patient
        examiner = application.evaluation.examiner
        classified = application.classified_payload or {}
        stage_totals = classified.get("stage_totals") or {}
        metric_results = {
            item.get("codigo"): item
            for item in classified.get("metric_results") or []
            if item.get("codigo")
        }

        results = {}
        max_time = 1.0
        for code, label, group, show_errors in cls.PROCESS_ORDER:
            result = cls._result_row(code, label, group, show_errors, metric_results, stage_totals)
            results[code] = result
            max_time = max(max_time, result["tempo_medio_num"], result["tempo_obtido_num"])

        for result in results.values():
            result["tempo_medio_width"] = cls._ratio_width(result["tempo_medio_num"], max_time)
            result["tempo_obtido_width"] = cls._ratio_width(result["tempo_obtido_num"], max_time)

        return {
            "codigo_avaliado": cls._application_code(application),
            "codigo_relatorio": cls._report_code(application),
            "data_aplicacao": cls._format_date(application.applied_on),
            "nome": patient.full_name or "Não informado",
            "sexo": cls._sex_label(patient.sex),
            "idade": cls._age_label(classified.get("idade")),
            "escolaridade": cls._schooling_label(patient),
            "profissional": cls._professional_label(examiner),
            "tabela_normativa": classified.get("faixa") or "Não informado",
            "aplicacao": "Válida",
            "process_cards": cls.PROCESS_CARD_TEXT,
            "automatic_rows": [results["leitura"], results["contagem"]],
            "controlled_rows": [results["escolha"], results["alternancia"], results["inibicao"], results["flexibilidade"]],
            "comparison_rows": [results[code] for code, *_ in cls.PROCESS_ORDER],
            "table_groups": [
                {
                    "title": "Processos automáticos",
                    "rows": [results["leitura"], results["contagem"]],
                },
                {
                    "title": "Processos controlados",
                    "rows": [results["escolha"], results["alternancia"]],
                },
                {
                    "title": "Índices executivos derivados",
                    "rows": [results["inibicao"], results["flexibilidade"]],
                },
            ],
            "clinical_note": (
                "A interpretação dos resultados obtidos por meio da aplicação do FDT – Teste dos Cinco Dígitos deve ser realizada por profissional habilitado e integrada à entrevista clínica, observação comportamental e demais instrumentos utilizados. Os dados obtidos não devem ser utilizados de forma isolada para definição diagnóstica."
            ),
            "speed_summary": cls._build_speed_summary(results),
            "inhibition_summary": cls._build_inhibition_summary(results),
            "flexibility_summary": cls._build_flexibility_summary(results),
            "final_summary": cls._build_general_conclusion(results),
        }

    @classmethod
    def _result_row(cls, code: str, label: str, group: str, show_errors: bool, metric_results: dict, stage_totals: dict) -> dict:
        metric = metric_results.get(code, {})
        percentile = cls._metric_percentile(metric)
        errors = 0 if not show_errors else int((stage_totals.get(code) or {}).get("erros", 0))
        weighted_score = cls._number(metric.get("pontos_ponderados"))
        classification = cls._pdf_classification(percentile)
        return {
            "code": code,
            "label": label,
            "group": group,
            "tempo_medio": cls._format_number(metric.get("media")),
            "tempo_medio_num": cls._number(metric.get("media")),
            "tempo_obtido": cls._format_number(metric.get("valor")),
            "tempo_obtido_num": cls._number(metric.get("valor")),
            "percentil": percentile,
            "erros": errors,
            "show_errors": show_errors,
            "error_badge_text": cls._error_badge_text(errors),
            "error_badge_class": "zero" if errors == 0 else "",
            "score": cls._format_score(metric.get("pontos_ponderados")),
            "score_num": weighted_score,
            "bar_width": cls._score_width(weighted_score),
            "fill_class": cls._classification_fill_class(metric.get("classificacao") or classification),
            "classification": classification,
            "classification_class": cls._classification_css_class(classification),
        }

    @classmethod
    def _build_speed_summary(cls, results: dict) -> str:
        leitura = results["leitura"]
        contagem = results["contagem"]
        leitura_class = leitura["classification"]
        contagem_class = contagem["classification"]

        if cls._is_preserved_classification(leitura_class) and cls._is_preserved_classification(contagem_class):
            return (
                "O desempenho nos processos automáticos apresentou-se sem indicativo de déficit, sugerindo preservação da velocidade de processamento, da automatização, do rastreio visual e da resposta rápida em tarefas simples e estruturadas."
            )

        if any(
            [
                cls._is_deficit_classification(leitura_class),
                cls._is_discrete_classification(leitura_class),
                cls._is_deficit_classification(contagem_class),
                cls._is_discrete_classification(contagem_class),
            ]
        ):
            return (
                "O desempenho nos processos automáticos indica fragilidade em tarefas simples e estruturadas que exigem rapidez de resposta, velocidade de processamento e automatização. "
                f"Em Leitura, o resultado foi classificado como {leitura_class.lower()}, enquanto em Contagem observou-se {contagem_class.lower()}. "
                "Esse padrão sugere alteração proporcional ao grau de classificação obtido, devendo ser interpretado em conjunto com a entrevista clínica, observação comportamental e demais instrumentos da avaliação."
            )
        return "O desempenho nos processos automáticos deve ser interpretado em conjunto com os demais indicadores do protocolo."

    @classmethod
    def _build_inhibition_summary(cls, results: dict) -> str:
        escolha = results["escolha"]
        inibicao = results["inibicao"]
        escolha_class = escolha["classification"]
        inibicao_class = inibicao["classification"]

        if cls._is_preserved_classification(escolha_class) and cls._is_preserved_classification(inibicao_class):
            return (
                "Nos processos que demandam controle inibitório, os resultados não indicaram prejuízo clínico significativo. A condição de Escolha e o índice derivado de Inibição situaram-se sem indicativo de déficit, sugerindo preservação da capacidade de suprimir respostas automáticas, selecionar respostas adequadas e manter monitoramento executivo em tarefa estruturada."
            )

        if any(
            [
                cls._is_deficit_classification(escolha_class),
                cls._is_discrete_classification(escolha_class),
                cls._is_deficit_classification(inibicao_class),
                cls._is_discrete_classification(inibicao_class),
            ]
        ):
            return (
                "Nos processos que demandam controle inibitório, observou-se alteração em um ou mais indicadores, "
                f"especialmente com classificação {escolha_class.lower()} em Escolha e {inibicao_class.lower()} em Inibição. "
                "Esse padrão sugere vulnerabilidade proporcional ao grau de classificação obtido, embora deva ser interpretado considerando o desempenho nos demais indicadores executivos e o contexto clínico global."
            )
        return "O controle inibitório deve ser interpretado em conjunto com os demais indicadores do protocolo."

    @classmethod
    def _build_flexibility_summary(cls, results: dict) -> str:
        alternancia = results["alternancia"]
        flexibilidade = results["flexibilidade"]
        alternancia_class = alternancia["classification"]
        flexibilidade_class = flexibilidade["classification"]

        if cls._is_preserved_classification(alternancia_class) and cls._is_preserved_classification(flexibilidade_class):
            return (
                "A condição de Alternância e o índice de Flexibilidade apresentaram desempenho sem indicativo de déficit, sugerindo preservação da alternância atencional, da adaptação a mudanças de regra e da flexibilidade cognitiva no contexto estruturado do instrumento."
            )

        if any(
            [
                cls._is_deficit_classification(alternancia_class),
                cls._is_discrete_classification(alternancia_class),
                cls._is_deficit_classification(flexibilidade_class),
                cls._is_discrete_classification(flexibilidade_class),
            ]
        ):
            return (
                "A condição de Alternância e/ou o índice de Flexibilidade indicaram alteração, "
                f"com classificação {alternancia_class.lower()} em Alternância e {flexibilidade_class.lower()} em Flexibilidade, "
                "sugerindo vulnerabilidade em alternância atencional, mudança de regra e adaptação cognitiva, proporcional ao grau de classificação obtido."
            )
        return "A flexibilidade cognitiva e a alternância atencional devem ser interpretadas em conjunto com os demais indicadores do protocolo."

    @classmethod
    def _build_general_conclusion(cls, results: dict) -> str:
        automaticos = ["leitura", "contagem"]
        controlados = ["escolha", "alternancia", "inibicao", "flexibilidade"]
        automaticos_alterados = [code for code in automaticos if not cls._is_preserved_classification(results[code]["classification"])]
        controlados_alterados = [code for code in controlados if not cls._is_preserved_classification(results[code]["classification"])]

        if automaticos_alterados and not controlados_alterados:
            labels = cls._join_process_labels([results[code]["label"] for code in automaticos_alterados])
            return (
                "Em análise clínica, os resultados obtidos no FDT indicam fragilidade predominante em velocidade de processamento e automatização, "
                f"com maior impacto em {labels}. Em contrapartida, os processos controlados e os índices executivos derivados, incluindo Escolha, Alternância, Inibição e Flexibilidade, não apresentaram indicativo de déficit. Dessa forma, o perfil sugere lentificação em demandas automáticas e de resposta rápida, sem evidência de prejuízo executivo significativo neste instrumento."
            )

        if automaticos_alterados and controlados_alterados:
            return (
                "Em análise clínica, os resultados obtidos no FDT indicam prejuízos tanto em processos automáticos quanto em processos controlados, sugerindo redução da eficiência em velocidade de processamento, automatização, controle inibitório, alternância atencional e/ou flexibilidade cognitiva. Esse padrão pode repercutir funcionalmente em contextos que exigem rapidez de resposta, monitoramento executivo, inibição de respostas automáticas e adaptação a mudanças de regra."
            )

        if not automaticos_alterados and controlados_alterados:
            return (
                "Em análise clínica, os resultados obtidos no FDT indicam preservação dos processos automáticos, com alteração específica em indicadores executivos controlados. Esse padrão sugere vulnerabilidade em controle inibitório, alternância atencional e/ou flexibilidade cognitiva, conforme os processos alterados."
            )

        return (
            "Em análise clínica, os resultados obtidos no FDT não indicam prejuízo clínico significativo nos processos avaliados. Observa-se desempenho preservado em velocidade de processamento, automatização, controle inibitório, alternância atencional e flexibilidade cognitiva no contexto estruturado do instrumento. Esses achados devem ser integrados aos demais dados clínicos e neuropsicológicos, sem serem utilizados isoladamente para definição diagnóstica."
        )

    @classmethod
    def _join_process_labels(cls, labels: list[str]) -> str:
        if not labels:
            return ""
        if len(labels) == 1:
            return labels[0]
        if len(labels) == 2:
            return f"{labels[0]} e {labels[1]}"
        return f"{', '.join(labels[:-1])} e {labels[-1]}"

    @classmethod
    def _is_deficit_classification(cls, classification: str) -> bool:
        return classification == "Indicativo de Déficit"

    @classmethod
    def _is_discrete_classification(cls, classification: str) -> bool:
        return classification == "Indicativo de Dificuldade Discreta"

    @classmethod
    def _is_preserved_classification(cls, classification: str) -> bool:
        return classification == "Sem Indicativo de Déficit"

    @classmethod
    def _pdf_classification(cls, percentile: float | int | None) -> str:
        try:
            percentile_value = float(percentile)
        except (TypeError, ValueError):
            return "Não informado"
        if percentile_value <= 24:
            return "Indicativo de Déficit"
        if percentile_value <= 30:
            return "Indicativo de Dificuldade Discreta"
        return "Sem Indicativo de Déficit"

    @classmethod
    def _pdf_performance(cls, percentile: float | int | None) -> int:
        try:
            percentile_value = float(percentile)
        except (TypeError, ValueError):
            return 0
        if percentile_value <= 24:
            return 5
        if percentile_value <= 30:
            return 25
        if percentile_value >= 95:
            return 95
        if percentile_value > 65:
            return 75
        return 50

    @classmethod
    def _classification_fill_class(cls, classification: str) -> str:
        normalized = cls._normalize(classification)
        if normalized == cls._normalize("Sem Indicativo de Déficit"):
            return ""
        if normalized == cls._normalize("Indicativo de Dificuldade Discreta"):
            return "alert"
        if normalized == cls._normalize("Indicativo de Déficit"):
            return "deficit"
        if "deficit" in normalized or "inferior" in normalized:
            return "deficit"
        if "dificuldade" in normalized or "alerta" in normalized:
            return "alert"
        return ""

    @classmethod
    def _classification_css_class(cls, classification: str) -> str:
        normalized = cls._normalize(classification)
        if normalized == cls._normalize("Sem Indicativo de Déficit"):
            return "normal"
        if normalized == cls._normalize("Indicativo de Dificuldade Discreta"):
            return "alert"
        if normalized == cls._normalize("Indicativo de Déficit"):
            return "deficit"
        if "deficit" in normalized or "inferior" in normalized:
            return "deficit"
        if "dificuldade" in normalized or "alerta" in normalized:
            return "alert"
        return "normal"

    @classmethod
    def _application_code(cls, application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or 0
        return f"AVL-{base_id:03d}"

    @classmethod
    def _report_code(cls, application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or 0
        return f"RPT-FDT-{base_id:03d}"

    @classmethod
    def _format_date(cls, value) -> str:
        return value.strftime("%d/%m/%Y") if hasattr(value, "strftime") else "Não informado"

    @classmethod
    def _format_number(cls, value) -> str:
        if value in (None, ""):
            return "—"
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return str(value)
        return f"{numeric:.2f}".replace(".", ",")

    @classmethod
    def _number(cls, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _metric_percentile(cls, metric: dict | None) -> float:
        if not metric:
            return 0.0
        value = metric.get("percentil_num") or metric.get("percentil_texto") or 0
        try:
            return float(str(value).replace(",", ".").replace("< ", "").replace("<", ""))
        except ValueError:
            return 0.0

    @classmethod
    def _schooling_label(cls, patient) -> str:
        if hasattr(patient, "get_schooling_display") and patient.schooling:
            return patient.get_schooling_display()
        if getattr(patient, "grade_year", None):
            return patient.grade_year
        return patient.schooling or "Não informado"

    @classmethod
    def _professional_label(cls, examiner) -> str:
        return "Jacqueline O. Caires - CRP09/6017"

    @classmethod
    def _sex_label(cls, value: str | None) -> str:
        if value == "M":
            return "Masculino"
        if value == "F":
            return "Feminino"
        return value or "Não informado"

    @classmethod
    def _age_label(cls, age) -> str:
        if age in (None, ""):
            return "Não informado"
        return f"{age} anos"

    @classmethod
    def _ratio_width(cls, value: float, max_value: float) -> float:
        if max_value <= 0:
            return "0"
        return cls._css_percent((value / max_value) * 100)

    @classmethod
    def _score_width(cls, score: float) -> float:
        if score <= 0:
            return "0"
        return cls._css_percent(max(12.0, min((float(score) / 20.0) * 100.0, 100.0)))

    @classmethod
    def _css_percent(cls, value: float) -> str:
        return f"{float(value):.2f}"

    @classmethod
    def _format_score(cls, value) -> str:
        if value in (None, ""):
            return "—"
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return str(value)
        if numeric.is_integer():
            return str(int(numeric))
        return f"{numeric:.1f}".replace(".", ",")

    @classmethod
    def _error_badge_text(cls, errors: int) -> str:
        return f"{errors} erro" if errors == 1 else f"{errors} erros"

    @classmethod
    def _has_deficit_signal(cls, classification: str) -> bool:
        normalized = cls._normalize(classification)
        return "deficit" in normalized or "inferior" in normalized or "rebaixado" in normalized

    @classmethod
    def _normalize(cls, value: str | None) -> str:
        return (
            str(value or "")
            .lower()
            .replace("á", "a")
            .replace("à", "a")
            .replace("ã", "a")
            .replace("â", "a")
            .replace("é", "e")
            .replace("ê", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ô", "o")
            .replace("õ", "o")
            .replace("ú", "u")
            .replace("ç", "c")
            .replace(" ", "")
        )
