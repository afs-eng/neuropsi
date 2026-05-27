from __future__ import annotations

from pathlib import Path

from django.template import Context
from django.template import engines

from apps.tests.services.playwright_pdf_service import generate_pdf_from_html
from apps.tests.services.ai_interpretation_orchestrator import TestAIInterpretationOrchestrator
from apps.tests.services.ai_interpretation_types import TestAIInterpretationDraft


class RAVLTPdfService:
    TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tests" / "pdf" / "ravlt_report.html"

    RESULT_DESCRIPTIONS = {
        "A1": "Evocação imediata inicial",
        "A2": "Segunda tentativa de aprendizagem",
        "A3": "Terceira tentativa de aprendizagem",
        "A4": "Quarta tentativa de aprendizagem",
        "A5": "Quinta tentativa de aprendizagem",
        "B1": "Lista interferente",
        "A6": "Evocação pós-interferência",
        "A7": "Evocação tardia",
        "Reconhecimento Lista A": "Reconhecimento verbal",
        "Escore Total": "Soma das tentativas A1 a A5",
        "Aprend. longo das Tentativas": "Aprendizagem ao longo das tentativas",
        "Velocidade de Esquecimento": "Retenção após interferência",
        "Interferência Proativa": "Interferência proativa",
        "Interferência Retroativa": "Interferência retroativa",
    }

    RESULT_SHORT_LABELS = {
        "A1": "A1",
        "A2": "A2",
        "A3": "A3",
        "A4": "A4",
        "A5": "A5",
        "B1": "B1",
        "A6": "A6",
        "A7": "A7",
        "Reconhecimento Lista A": "R",
        "Escore Total": "Escore Total",
        "Aprend. longo das Tentativas": "Aprend. longo das tentativas",
        "Velocidade de Esquecimento": "Velocidade de esquecimento",
        "Interferência Proativa": "I.P.",
        "Interferência Retroativa": "I.R.",
    }

    CHART_RESULT_KEYS = ["A1", "A2", "A3", "A4", "A5", "B1", "A6", "A7", "Reconhecimento Lista A"]

    INDICATOR_FORMULAS = {
        "Escore Total": "A1 + A2 + A3 + A4 + A5",
        "ALT": "Escore Total - (5 × A1)",
        "RET": "A7 / A6",
        "IP": "B1 / A1",
        "IR": "A6 / A5",
        "Ganho de aprendizagem": "A5 - A1",
        "Perda tardia": "A6 - A7",
    }

    PRESERVED_CLASSES = {"Média", "Média Superior", "Superior", "Muito Superior"}
    LOW_CLASSES = {"Média Inferior", "Inferior", "Muito Inferior"}

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
        classified = application.classified_payload or {}
        resultados = classified.get("resultados") or []
        result_map = {item.get("variavel"): item for item in resultados}
        raw_payload = application.raw_payload or {}
        report_payload = getattr(application, "report_payload", None) or {}
        interpretation = application.interpretation_text or report_payload.get("interpretation") or ""
        paragraphs = [paragraph.strip() for paragraph in interpretation.split("\n\n") if paragraph.strip()]
        summary_for_report = report_payload.get("summary_for_report") or (paragraphs[-1] if paragraphs else "")
        clinical_paragraphs = cls._clinical_paragraphs(patient.full_name or "Paciente", raw_payload, result_map)
        summary_for_report = cls._summary_for_report(patient.full_name or "Paciente", raw_payload, result_map)

        if "Escore Total" not in result_map:
            total = (
                cls._num(raw_payload.get("a1"))
                + cls._num(raw_payload.get("a2"))
                + cls._num(raw_payload.get("a3"))
                + cls._num(raw_payload.get("a4"))
                + cls._num(raw_payload.get("a5"))
            )
            alt_class = result_map.get("Aprend. longo das Tentativas", {}).get("classificacao")
            result_map["Escore Total"] = {"bruto": total, "classificacao": alt_class}

        quantitative_rows = [
            cls._result_row(result_map, key)
            for key in [
                "A1", "A2", "A3", "A4", "A5",
                "B1", "A6", "A7",
                "Reconhecimento Lista A",
                "Escore Total",
                "Aprend. longo das Tentativas",
                "Velocidade de Esquecimento",
                "Interferência Proativa",
                "Interferência Retroativa",
            ]
            if key in result_map
        ]

        chart = classified.get("chart") or {}
        indicator_rows = cls._indicator_rows(raw_payload, result_map)
        clinical_box_text = cls._clinical_box_text(patient.full_name or "Paciente", raw_payload, result_map)
        fallback_draft = TestAIInterpretationDraft(
            clinical_paragraphs=clinical_paragraphs,
            clinical_box_text=clinical_box_text,
            summary_for_report=summary_for_report,
        )
        interpretation_draft = TestAIInterpretationOrchestrator.generate_for_application(application, fallback_draft)

        return {
            "codigo_avaliado": cls._application_code(application),
            "codigo_relatorio": cls._report_code(application),
            "data_aplicacao": cls._format_date(application.applied_on),
            "nome": patient.full_name or "Não informado",
            "sexo": cls._sex_label(patient.sex),
            "idade": cls._age_label(classified.get("idade")),
            "escolaridade": cls._schooling_label(patient),
            "profissional": "Jacqueline O. Caires - CRP09/6017",
            "tabela_normativa": cls._normative_label(classified.get("faixa_etaria"), classified.get("idade")),
            "status_aplicacao": "Válida",
            "quantitative_rows": quantitative_rows,
            "indicator_rows": indicator_rows,
            "clinical_paragraphs": interpretation_draft.clinical_paragraphs,
            "clinical_box_text": interpretation_draft.clinical_box_text,
            "summary_for_report": interpretation_draft.summary_for_report,
            "interpretation_metadata": interpretation_draft.metadata,
            "interpretation_warnings": interpretation_draft.warnings,
            "interpretation_source_label": cls._interpretation_source_label(interpretation_draft.metadata),
            "chart_svg": cls._chart_svg(chart),
        }

    @classmethod
    def _interpretation_source_label(cls, metadata: dict | None) -> str:
        generation_path = str((metadata or {}).get("generation_path") or "fallback").lower()
        if generation_path == "ai":
            model = str((metadata or {}).get("model") or "").strip()
            return f"Interpretação: IA assistida{f' ({model})' if model else ''}"
        return "Interpretação: Determinística"

    @classmethod
    def _result_row(cls, result_map: dict, key: str) -> dict:
        item = result_map.get(key, {})
        return {
            "label": cls.RESULT_SHORT_LABELS.get(key, key),
            "description": cls.RESULT_DESCRIPTIONS.get(key, key),
            "result": cls._format_score(item.get("bruto")),
            "classification": cls._table_classification(item.get("classificacao")),
        }

    @classmethod
    def _indicator_rows(cls, raw_payload: dict, result_map: dict) -> list[dict]:
        a1 = cls._num(raw_payload.get("a1"))
        a2 = cls._num(raw_payload.get("a2"))
        a3 = cls._num(raw_payload.get("a3"))
        a4 = cls._num(raw_payload.get("a4"))
        a5 = cls._num(raw_payload.get("a5"))
        a6 = cls._num(raw_payload.get("a6"))
        a7 = cls._num(raw_payload.get("a7"))
        total = a1 + a2 + a3 + a4 + a5
        rows = [
            {
                "label": "Escore Total",
                "formula": cls.INDICATOR_FORMULAS["Escore Total"],
                "result": cls._format_score(result_map.get("Escore Total", {}).get("bruto") or total),
                "interpretation": cls._indicator_interpretation(result_map.get("Escore Total", {}).get("classificacao"), "Aprendizagem verbal total"),
            },
            {
                "label": "Aprend. longo das tentativas",
                "formula": cls.INDICATOR_FORMULAS["ALT"],
                "result": cls._format_score(result_map.get("Aprend. longo das Tentativas", {}).get("bruto")),
                "interpretation": cls._indicator_interpretation(result_map.get("Aprend. longo das Tentativas", {}).get("classificacao"), "Aprendizagem ao longo das tentativas"),
            },
            {
                "label": "Velocidade de esquecimento",
                "formula": cls.INDICATOR_FORMULAS["RET"],
                "result": cls._format_score(result_map.get("Velocidade de Esquecimento", {}).get("bruto")),
                "interpretation": cls._indicator_interpretation(result_map.get("Velocidade de Esquecimento", {}).get("classificacao"), "Retenção tardia"),
            },
            {
                "label": "I.P.",
                "formula": cls.INDICATOR_FORMULAS["IP"],
                "result": cls._format_score(result_map.get("Interferência Proativa", {}).get("bruto")),
                "interpretation": cls._indicator_interpretation(result_map.get("Interferência Proativa", {}).get("classificacao"), "Sensibilidade à interferência proativa"),
            },
            {
                "label": "I.R.",
                "formula": cls.INDICATOR_FORMULAS["IR"],
                "result": cls._format_score(result_map.get("Interferência Retroativa", {}).get("bruto")),
                "interpretation": cls._indicator_interpretation(result_map.get("Interferência Retroativa", {}).get("classificacao"), "Resistência à interferência retroativa"),
            },
            {
                "label": "Ganho de aprendizagem",
                "formula": cls.INDICATOR_FORMULAS["Ganho de aprendizagem"],
                "result": cls._format_score(a5 - a1),
                "interpretation": "Boa resposta à repetição" if (a5 - a1) >= 4 else "Ganho discreto ao longo das repetições",
            },
            {
                "label": "Perda tardia",
                "formula": cls.INDICATOR_FORMULAS["Perda tardia"],
                "result": cls._format_score(a6 - a7),
                "interpretation": "Ausência de perda relevante após intervalo" if (a6 - a7) <= 1 else "Perda tardia acima do ideal",
            },
        ]
        return rows

    @classmethod
    def _indicator_interpretation(cls, classification: str | None, prefix: str) -> str:
        if cls._display_classification(classification) == "Acima do esperado":
            return f"{prefix} acima do esperado"
        if cls._display_classification(classification) == "Dentro do esperado":
            return f"{prefix} preservada"
        if cls._display_classification(classification) == "Abaixo do esperado":
            return f"{prefix} abaixo do esperado"
        return f"{prefix} abaixo do mínimo esperado"

    @classmethod
    def _raw_class(cls, result_map: dict, key: str) -> str:
        return result_map.get(key, {}).get("classificacao") or "Média"

    @classmethod
    def _text_classification(cls, classification: str | None) -> str:
        mapping = {
            "Muito Superior": "Superior",
            "Superior": "Superior",
            "Média Superior": "Média Superior",
            "Média": "Média",
            "Média Inferior": "Média Inferior",
            "Inferior": "Inferior",
            "Muito Inferior": "Deficitário",
        }
        if not classification:
            return "Média"
        return mapping.get(classification, classification)

    @classmethod
    def _faixa_text(cls, classificacao: str | None, nivel: bool = False) -> str:
        normalized = cls._text_classification(classificacao)
        if not normalized:
            return "na faixa média"
        map_nivel = {"Superior": "Superior", "Média Superior": "Média Superior", "Média": "média", "Média Inferior": "Média Inferior", "Inferior": "Inferior", "Deficitário": "Deficitário"}
        map_faixa = {"Superior": "na faixa Superior", "Média Superior": "na faixa Média Superior", "Média": "dentro da média", "Média Inferior": "na faixa Média Inferior", "Inferior": "em nível Inferior", "Deficitário": "em nível Deficitário"}
        return map_nivel.get(normalized, normalized) if nivel else map_faixa.get(normalized, normalized)

    @classmethod
    def _format_text_number(cls, value) -> str:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return str(value)
        if numeric.is_integer():
            return str(int(numeric))
        return f"{numeric:.2f}".replace(".", ",")

    @classmethod
    def _metric_status_text(cls, classification: str | None) -> str:
        normalized = cls._text_classification(classification)
        mapping = {
            "Superior": "na faixa Superior",
            "Média Superior": "na faixa Média Superior",
            "Média": "dentro da média",
            "Média Inferior": "na faixa Média Inferior",
            "Inferior": "em nível Inferior",
            "Deficitário": "em nível Deficitário",
        }
        return mapping.get(normalized, normalized)

    @classmethod
    def _curve_pattern_text(cls, a1: float, a2: float, a3: float, a4: float, a5: float, alt_class: str | None) -> str:
        gain = a5 - a1
        if a1 < a2 <= a3 <= a4 <= a5:
            return "ascendente e consistente"
        if a5 > a1:
            return "com tendência ascendente, embora com oscilações"
        if gain < 0:
            return "pouco consistente, com ganho negativo entre A1 e A5"
        if gain == 0:
            return "pouco consistente, com ganho nulo entre A1 e A5"
        if gain in {1, 2} or cls._text_classification(alt_class) in {"Média Inferior", "Inferior", "Deficitário"}:
            return "pouco consistente, com benefício limitado da repetição sucessiva"
        return "pouco consistente"

    @classmethod
    def _gain_text(cls, gain: float) -> str:
        formatted = cls._format_text_number(gain)
        if gain < 0:
            return f"O ganho entre A1 e A5 foi negativo ({formatted} palavras), sugerindo baixa consistência da curva de aprendizagem."
        if gain == 0:
            return "O ganho líquido entre A1 e A5 foi nulo, indicando ausência de incremento na evocação ao longo das repetições."
        if gain in {1, 2}:
            return f"O ganho entre A1 e A5 foi discreto ({formatted} palavras), sugerindo benefício limitado da repetição sucessiva."
        return f"Observou-se ganho de {formatted} palavras entre A1 e A5, compatível com benefício da repetição sucessiva."

    @classmethod
    def _process_profile_text(cls, result_map: dict) -> str:
        def rc(key): return cls._raw_class(result_map, key)

        a1_ok = rc("A1") in cls.PRESERVED_CLASSES
        total_ok = rc("Escore Total") in cls.PRESERVED_CLASSES
        alt_ok = rc("Aprend. longo das Tentativas") in cls.PRESERVED_CLASSES
        b1_low = rc("B1") in cls.LOW_CLASSES
        a6_low = rc("A6") in cls.LOW_CLASSES
        a7_ok = rc("A7") in cls.PRESERVED_CLASSES
        a7_low = rc("A7") in cls.LOW_CLASSES
        r_ok = rc("Reconhecimento Lista A") in cls.PRESERVED_CLASSES
        r_low = rc("Reconhecimento Lista A") in cls.LOW_CLASSES
        ip_low = rc("Interferência Proativa") in cls.LOW_CLASSES
        ir_low = rc("Interferência Retroativa") in cls.LOW_CLASSES
        forgetting_ok = rc("Velocidade de Esquecimento") in cls.PRESERVED_CLASSES

        if total_ok and alt_ok and not b1_low and not a6_low and a7_ok and r_ok and not ip_low and not ir_low:
            return "funcionamento mnésico verbal globalmente preservado, com desempenho compatível com os parâmetros normativos nos processos de aprendizagem, retenção, reconhecimento verbal e resistência à interferência"
        if a1_ok and not alt_ok:
            return "aquisição inicial preservada, porém com menor eficiência na aquisição progressiva e no benefício da repetição sucessiva"
        if total_ok and not alt_ok:
            return "volume global de evocação verbal preservado, mas aprendizagem ao longo das tentativas rebaixada, sugerindo baixa consistência da curva e menor aproveitamento da repetição sucessiva"
        if not total_ok and not alt_ok and a7_ok and forgetting_ok:
            return "menor eficiência na aprendizagem verbal global e na aquisição progressiva, com retenção tardia preservada"
        if b1_low or ip_low:
            return "vulnerabilidade à interferência proativa, sugerindo dificuldade em registrar novo material verbal após aprendizagem prévia"
        if a6_low or ir_low:
            return "sensibilidade à interferência retroativa, com redução na recuperação da lista original após apresentação de material concorrente"
        if a7_ok and r_low:
            return "retenção tardia preservada, porém reconhecimento verbal rebaixado, sugerindo fragilidade no acesso ao material com apoio de pistas ou inconsistência no monitoramento de resposta"
        if a7_low and r_low:
            return "vulnerabilidade nos processos de retenção tardia e reconhecimento verbal, sugerindo fragilidade mais ampla na manutenção e recuperação do material verbal"
        return "funcionamento mnésico verbal heterogêneo, com necessidade de leitura integrada entre aquisição, retenção, reconhecimento e interferência"

    @classmethod
    def _closing_integrated_text(cls, result_map: dict) -> str:
        def rc(key): return cls._raw_class(result_map, key)

        preserved: list[str] = []
        vulnerabilities: list[str] = []

        if rc("A1") in cls.PRESERVED_CLASSES:
            preserved.append("aquisição inicial")
        if rc("Escore Total") in cls.PRESERVED_CLASSES:
            preserved.append("volume global de evocação verbal")
        if rc("A7") in cls.PRESERVED_CLASSES:
            preserved.append("retenção tardia")
        if rc("Reconhecimento Lista A") in cls.PRESERVED_CLASSES:
            preserved.append("reconhecimento verbal")

        if rc("Aprend. longo das Tentativas") in cls.LOW_CLASSES:
            vulnerabilities.extend(["aquisição progressiva", "benefício da repetição sucessiva"])
        if rc("B1") in cls.LOW_CLASSES or rc("Interferência Proativa") in cls.LOW_CLASSES:
            vulnerabilities.append("interferência proativa")
        if rc("A6") in cls.LOW_CLASSES or rc("Interferência Retroativa") in cls.LOW_CLASSES:
            vulnerabilities.append("interferência retroativa")
        if rc("A7") in cls.LOW_CLASSES:
            vulnerabilities.append("retenção tardia")
        if rc("Reconhecimento Lista A") in cls.LOW_CLASSES:
            vulnerabilities.append("reconhecimento verbal")

        preserved_text = cls._join_labels(preserved)
        vulnerabilities_text = cls._join_labels(vulnerabilities)
        if preserved and vulnerabilities:
            return f"Em análise clínica, o perfil sugere preservação relativa de {preserved_text}, com vulnerabilidades em {vulnerabilities_text}."
        if vulnerabilities:
            return f"Em análise clínica, o perfil sugere vulnerabilidades em {vulnerabilities_text}."
        return "Em análise clínica, o perfil sugere preservação dos processos de aprendizagem, retenção, reconhecimento verbal e resistência à interferência."

    @classmethod
    def _clinical_paragraphs(cls, full_name: str, raw_payload: dict, result_map: dict) -> list[str]:
        short_name = cls._short_name(full_name)
        a1 = cls._num(raw_payload.get("a1"))
        a2 = cls._num(raw_payload.get("a2"))
        a3 = cls._num(raw_payload.get("a3"))
        a4 = cls._num(raw_payload.get("a4"))
        a5 = cls._num(raw_payload.get("a5"))
        b1 = cls._num(raw_payload.get("b"))
        a6 = cls._num(raw_payload.get("a6"))
        a7 = cls._num(raw_payload.get("a7"))

        def rc(key): return cls._raw_class(result_map, key)
        def ft(c): return cls._faixa_text(c)

        total = a1 + a2 + a3 + a4 + a5
        alt_val = result_map.get("Aprend. longo das Tentativas", {}).get("bruto") or (total - 5 * a1 if a1 else 0)
        gain = a5 - a1
        a1_class = rc("A1")
        total_class = rc("Escore Total")
        alt_class = rc("Aprend. longo das Tentativas")
        b1_class = rc("B1")
        a6_class = rc("A6")
        a7_class = rc("A7")
        r_class = rc("Reconhecimento Lista A")
        ip_class = rc("Interferência Proativa")
        ir_class = rc("Interferência Retroativa")
        forgetting_class = rc("Velocidade de Esquecimento")

        if a1_class in cls.PRESERVED_CLASSES:
            p1_end = (
                f"A aquisição inicial situou-se {ft(a1_class)}, indicando registro imediato funcional e desempenho preservado na memória verbal de curto prazo."
            )
        else:
            p1_end = (
                "A aquisição inicial situou-se abaixo do esperado, sugerindo fragilidade no registro imediato do material verbal, "
                "podendo refletir dificuldade de atenção inicial, codificação verbal ou memória verbal de curto prazo."
            )
        p1 = f"O desempenho de {short_name} no RAVLT revelou {cls._process_profile_text(result_map)}. {p1_end}"

        total_sentence = (
            f"O Escore Total situou-se {ft(total_class)}, indicando volume global de evocação verbal preservado ao longo das cinco tentativas."
            if total_class in cls.PRESERVED_CLASSES else
            f"O Escore Total situou-se {ft(total_class)}, indicando menor eficiência na aprendizagem verbal episódica global."
        )
        alt_sentence = (
            f"A aprendizagem ao longo das tentativas situou-se {ft(alt_class)}, sugerindo benefício funcional da repetição sucessiva."
            if alt_class in cls.PRESERVED_CLASSES else
            f"A aprendizagem ao longo das tentativas situou-se {ft(alt_class)}, indicando baixo benefício da repetição sucessiva e menor eficiência na aquisição progressiva do material verbal."
        )
        discrepancy_sentence = ""
        if total_class in cls.PRESERVED_CLASSES and alt_class in cls.LOW_CLASSES:
            discrepancy_sentence = (
                " Apesar do Escore Total preservado, a aprendizagem ao longo das tentativas esteve rebaixada, sugerindo que o volume global de evocação pode refletir desempenho inicial elevado ou oscilações da curva, e não necessariamente benefício consistente da repetição."
            )
        p2 = (
            f"A curva de aprendizagem apresentou padrão {cls._curve_pattern_text(a1, a2, a3, a4, a5, alt_class)}. "
            f"{cls._gain_text(gain)} {total_sentence} {alt_sentence}{discrepancy_sentence}"
        )

        b1_sentence = (
            f"O desempenho em B1 situou-se {ft(b1_class)}, sugerindo registro funcional de novo material verbal e resistência preservada à interferência proativa."
            if b1_class in cls.PRESERVED_CLASSES else
            f"O desempenho em B1 situou-se {ft(b1_class)}, sugerindo vulnerabilidade à interferência proativa, com possível dificuldade em inibir a influência do material previamente aprendido para assimilar novo conteúdo verbal."
        )
        ip_sentence = (
            f"O índice de interferência proativa situou-se {ft(ip_class)}, indicando resistência funcional à competição proativa."
            if ip_class in cls.PRESERVED_CLASSES else
            f"O índice de interferência proativa situou-se {ft(ip_class)}, sugerindo maior susceptibilidade à interferência proativa."
        )
        if b1_class in cls.LOW_CLASSES or ip_class in cls.LOW_CLASSES:
            ip_sentence += " Esse padrão pode estar associado a dificuldades de controle inibitório, atualização da memória operacional ou flexibilidade cognitiva, devendo ser integrado a outros instrumentos executivos."
        p3 = f"{b1_sentence} {ip_sentence}"

        a6_sentence = (
            f"Após a interferência, A6 situou-se {ft(a6_class)}, indicando recuperação funcional da lista original após apresentação de material concorrente."
            if a6_class in cls.PRESERVED_CLASSES else
            f"Após a interferência, A6 situou-se {ft(a6_class)}, indicando redução na recuperação imediata da lista original após apresentação de material concorrente."
        )
        ir_sentence = (
            f"O índice de interferência retroativa situou-se {ft(ir_class)}, sugerindo resistência funcional aos efeitos da interferência retroativa."
            if ir_class in cls.PRESERVED_CLASSES else
            f"O índice de interferência retroativa situou-se {ft(ir_class)}, indicando maior impacto do material interferente sobre a recuperação do conteúdo previamente aprendido."
        )
        if a6_class in cls.LOW_CLASSES and ir_class in cls.PRESERVED_CLASSES:
            ir_sentence += " Embora o índice I.R. esteja preservado, o desempenho absoluto em A6 situou-se abaixo do esperado, sugerindo redução pontual na recuperação imediata da lista original após interferência."
        a7_sentence = (
            f"Na evocação tardia, A7 situou-se {ft(a7_class)}, sugerindo retenção tardia preservada."
            if a7_class in cls.PRESERVED_CLASSES else
            f"Na evocação tardia, A7 situou-se {ft(a7_class)}, sugerindo fragilidade na recuperação tardia do conteúdo verbal."
        )
        forgetting_sentence = (
            f"A velocidade de esquecimento situou-se {ft(forgetting_class)}, sugerindo retenção funcional do conteúdo verbal após intervalo."
            if forgetting_class in cls.PRESERVED_CLASSES else
            f"A velocidade de esquecimento situou-se {ft(forgetting_class)}, sugerindo maior perda ou menor recuperação do conteúdo verbal após intervalo."
        )
        p4 = f"{a6_sentence} {ir_sentence} {a7_sentence} {forgetting_sentence}"

        recognition_sentence = (
            f"O reconhecimento verbal situou-se {ft(r_class)}, sugerindo acesso funcional ao material verbal com apoio de pistas externas."
            if r_class in cls.PRESERVED_CLASSES else
            f"O reconhecimento verbal situou-se {ft(r_class)}, indicando fragilidade no acesso ao material verbal com apoio de pistas de reconhecimento."
        )
        discrepancy = ""
        if a7_class in cls.PRESERVED_CLASSES and r_class in cls.LOW_CLASSES:
            discrepancy = (
                " Observa-se discrepância entre evocação tardia preservada e reconhecimento verbal rebaixado. Esse padrão deve ser interpretado com cautela, podendo refletir oscilações atencionais, falhas de monitoramento, inconsistência na estratégia de resposta ou dificuldade específica no reconhecimento."
            )
        elif a7_class in cls.LOW_CLASSES and r_class in cls.PRESERVED_CLASSES:
            discrepancy = (
                " A preservação do reconhecimento diante de evocação tardia rebaixada sugere benefício com pistas externas, indicando que parte do material pode ter sido armazenada, embora a recuperação espontânea esteja menos eficiente."
            )
        elif a7_class in cls.LOW_CLASSES and r_class in cls.LOW_CLASSES:
            discrepancy = (
                " A associação entre evocação tardia e reconhecimento rebaixados sugere maior fragilidade nos processos de retenção e reconhecimento verbal."
            )
        p5 = (
            f"{recognition_sentence}{discrepancy} {cls._closing_integrated_text(result_map)} "
            "Os achados devem ser integrados à anamnese, observação clínica, histórico escolar/profissional e demais instrumentos utilizados na avaliação."
        )

        return [p1, p2, p3, p4, p5]

    @classmethod
    def _perfil_global(cls, alt_class: str, a7_class: str, rec_class: str, ip_class: str, ir_class: str) -> str:
        preserved = cls.PRESERVED_CLASSES
        alt_ok = alt_class in preserved
        a7_ok = a7_class in preserved
        rec_ok = rec_class in preserved
        ok_count = sum([alt_ok, a7_ok, rec_ok])
        has_weakness = ip_class in cls.LOW_CLASSES or ir_class in cls.LOW_CLASSES
        if ok_count >= 2 and not has_weakness:
            return "globalmente preservado"
        if ok_count >= 2:
            return "predominantemente preservado, com pontos específicos de atenção"
        return "com oscilações, demandando leitura clínica integrada"

    @classmethod
    def _clinical_box_text(cls, full_name: str, raw_payload: dict, result_map: dict) -> str:
        short_name = cls._short_name(full_name)
        def rc(key): return cls._raw_class(result_map, key)

        preserved_points: list[str] = []
        vulnerable_points: list[str] = []

        if rc("A1") in cls.PRESERVED_CLASSES:
            preserved_points.append(f"aquisição inicial {cls._metric_status_text(rc('A1'))}")
        if rc("Escore Total") in cls.PRESERVED_CLASSES:
            preserved_points.append(f"Escore Total {cls._metric_status_text(rc('Escore Total'))}")
        if rc("A7") in cls.PRESERVED_CLASSES:
            preserved_points.append(f"retenção tardia {cls._metric_status_text(rc('A7'))}")
        if rc("Reconhecimento Lista A") in cls.PRESERVED_CLASSES:
            preserved_points.append(f"reconhecimento verbal {cls._metric_status_text(rc('Reconhecimento Lista A'))}")

        if rc("Aprend. longo das Tentativas") in cls.LOW_CLASSES:
            vulnerable_points.append(f"aprendizagem ao longo das tentativas {cls._metric_status_text(rc('Aprend. longo das Tentativas'))}")
        if rc("B1") in cls.LOW_CLASSES:
            vulnerable_points.append(f"B1 {cls._metric_status_text(rc('B1'))}")
        if rc("Interferência Proativa") in cls.LOW_CLASSES:
            vulnerable_points.append(f"I.P. {cls._metric_status_text(rc('Interferência Proativa'))}")
        if rc("A6") in cls.LOW_CLASSES:
            vulnerable_points.append(f"A6 {cls._metric_status_text(rc('A6'))}")
        if rc("Interferência Retroativa") in cls.LOW_CLASSES:
            vulnerable_points.append(f"I.R. {cls._metric_status_text(rc('Interferência Retroativa'))}")
        if rc("Reconhecimento Lista A") in cls.LOW_CLASSES:
            vulnerable_points.append(f"reconhecimento verbal {cls._metric_status_text(rc('Reconhecimento Lista A'))}")

        return (
            f"o RAVLT indicou {cls._process_profile_text(result_map)}. "
            f"{short_name} apresentou {cls._join_labels(preserved_points) if preserved_points else 'perfil sem pontos preservados destacados'}. "
            f"Os principais pontos de atenção envolveram {cls._join_labels(vulnerable_points) if vulnerable_points else 'ausência de vulnerabilidades significativas neste instrumento'}."
        )

    @classmethod
    def _summary_for_report(cls, full_name: str, raw_payload: dict, result_map: dict) -> str:
        short_name = cls._short_name(full_name)
        def rc(key): return cls._raw_class(result_map, key)

        preserved_points: list[str] = []
        if rc("A1") in cls.PRESERVED_CLASSES:
            preserved_points.append(f"aquisição inicial {cls._metric_status_text(rc('A1'))}")
        if rc("Escore Total") in cls.PRESERVED_CLASSES:
            preserved_points.append(f"Escore Total {cls._metric_status_text(rc('Escore Total'))}")
        if rc("A7") in cls.PRESERVED_CLASSES:
            preserved_points.append(f"evocação tardia {cls._metric_status_text(rc('A7'))}")
        if rc("Reconhecimento Lista A") in cls.PRESERVED_CLASSES:
            preserved_points.append(f"reconhecimento verbal {cls._metric_status_text(rc('Reconhecimento Lista A'))}")

        vulnerable_points: list[str] = []
        if rc("Aprend. longo das Tentativas") in cls.LOW_CLASSES:
            vulnerable_points.append(f"aprendizagem ao longo das tentativas {cls._metric_status_text(rc('Aprend. longo das Tentativas'))}")
        if rc("B1") in cls.LOW_CLASSES or rc("Interferência Proativa") in cls.LOW_CLASSES:
            vulnerable_points.append("interferência proativa")
        if rc("A6") in cls.LOW_CLASSES or rc("Interferência Retroativa") in cls.LOW_CLASSES:
            vulnerable_points.append("interferência retroativa")
        if rc("Reconhecimento Lista A") in cls.LOW_CLASSES:
            vulnerable_points.append(f"reconhecimento verbal {cls._metric_status_text(rc('Reconhecimento Lista A'))}")

        return (
            f"O RAVLT indicou {cls._process_profile_text(result_map)}. "
            f"{short_name} apresentou {cls._join_labels(preserved_points) if preserved_points else 'desempenho sem pontos preservados destacados'}. "
            f"Os principais pontos de atenção envolveram {cls._join_labels(vulnerable_points) if vulnerable_points else 'ausência de vulnerabilidades significativas neste instrumento'}. "
            f"{cls._closing_integrated_text(result_map)}"
        )

    @classmethod
    def _join_labels(cls, labels: list[str]) -> str:
        items = [item for item in labels if item]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} e {items[1]}"
        return f"{', '.join(items[:-1])} e {items[-1]}"

    @classmethod
    def _interference_evidence_text(cls, rc, ip_baixo: bool, ir_baixo: bool, b1_baixo: bool, a6_baixo: bool) -> str:
        if ip_baixo and b1_baixo and ir_baixo and a6_baixo:
            return f"desempenho em B1 {cls._metric_status_text(rc('B1'))} e A6 {cls._metric_status_text(rc('A6'))}"
        if ip_baixo and b1_baixo:
            return f"desempenho em B1 {cls._metric_status_text(rc('B1'))}"
        if ir_baixo and a6_baixo:
            return f"desempenho em A6 {cls._metric_status_text(rc('A6'))}"
        return ""

    @classmethod
    def _short_name(cls, full_name: str | None) -> str:
        token = (full_name or "Paciente").strip().split(" ", 1)[0]
        if not token:
            return "Paciente"
        return token[:1].upper() + token[1:]

    @classmethod
    def _chart_svg(cls, chart: dict) -> str:
        labels = chart.get("labels") or []
        series = chart.get("series") or []
        if not labels or not series:
            return ""

        title = chart.get("title") or "RAVLT – Quantidade de palavras evocadas"
        n = len(labels)

        width = 1200
        height = 420
        ml = 70
        mr = 40
        mt = 56
        mb = 92
        pw = width - ml - mr
        ph = height - mt - mb
        sx = pw / max(n - 1, 1)

        all_values = []
        for item in series:
            for v in (item.get("values") or []):
                if v is not None:
                    all_values.append(float(v))
        data_max = max(all_values) if all_values else 15
        if data_max <= 15:
            y_max = 15
        elif data_max <= 20:
            y_max = 20
        elif data_max <= 30:
            y_max = 30
        elif data_max <= 40:
            y_max = 40
        elif data_max <= 50:
            y_max = 50
        else:
            y_max = (int(data_max / 10) + 1) * 10

        tick_step = 5 if y_max <= 20 else 10
        ticks = list(range(0, y_max + 1, tick_step))
        if ticks[-1] < y_max:
            ticks.append(y_max)
        y_min = 0

        def xs(i): return ml + i * sx
        def ys(v): return mt + ((y_max - v) / max(y_max - y_min, 1)) * ph

        lines = []
        for t in ticks:
            y = ys(float(t))
            lines.append(f'<line x1="{ml}" y1="{y:.2f}" x2="{width - mr}" y2="{y:.2f}" stroke="#d1d5db" stroke-width="1" />')
            lines.append(f'<text x="{ml - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Times New Roman" font-size="11" fill="#6b7280">{t}</text>')

        x_labels = []
        font_sizes = {"R": 11, "ALT": 11, "RET": 11, "I.P.": 10, "I.R.": 10}
        for i, lb in enumerate(labels):
            fs = font_sizes.get(lb, 12)
            x_labels.append(f'<text x="{xs(i):.2f}" y="{height - mb + 22}" text-anchor="middle" font-family="Times New Roman" font-size="{fs}" fill="#4b5563">{lb}</text>')

        color_map = {"esperado": "#1d4ed8", "minimo": "#60a5fa", "obtido": "#0f172a"}
        plotted = []
        legend_items = []
        for item in series:
            key = item.get("key", "")
            label = item.get("label", key)
            values = item.get("values") or []
            color = color_map.get(key, "#1d4ed8")
            pts = []
            for i in range(min(n, len(values))):
                v = float(values[i] or 0)
                pts.append((xs(i), ys(v)))
            if not pts:
                continue
            d = " ".join(f'{"M" if i == 0 else "L"} {x:.2f} {y:.2f}' for i, (x, y) in enumerate(pts))
            plotted.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />')
            for x, y in pts:
                plotted.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="{color}" />')
            legend_items.append((color, label))

        lx_start = (width - len(legend_items) * 150) / 2
        for i, (c, lb) in enumerate(legend_items):
            lx = lx_start + i * 150
            ly = height - 26
            plotted.append(f'<line x1="{lx}" y1="{ly}" x2="{lx + 28}" y2="{ly}" stroke="{c}" stroke-width="2.5" />')
            plotted.append(f'<circle cx="{lx + 14}" cy="{ly}" r="3" fill="{c}" />')
            plotted.append(f'<text x="{lx + 36}" y="{ly + 4}" font-family="Times New Roman" font-size="11" fill="#374151">{lb}</text>')

        return (
            f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
            f'<text x="{width / 2}" y="28" text-anchor="middle" font-family="Times New Roman" font-size="16" font-weight="bold" fill="#1e3a8a">{title}</text>'
            + "".join(lines)
            + "".join(x_labels)
            + "".join(plotted)
            + '</svg>'
        )

    @classmethod
    def _display_classification(cls, classification: str | None) -> str:
        mapping = {
            "Muito Superior": "Acima do esperado",
            "Superior": "Acima do esperado",
            "Média Superior": "Acima do esperado",
            "Média": "Dentro do esperado",
            "Limítrofe": "Abaixo do esperado",
            "Média Inferior": "Abaixo do esperado",
            "Inferior": "Abaixo do mínimo esperado",
            "Muito Inferior": "Abaixo do mínimo esperado",
        }
        if not classification:
            return "Classificação normativa indisponível"
        return mapping.get(classification, classification)

    @classmethod
    def _table_classification(cls, classification: str | None) -> str:
        mapping = {
            "Muito Inferior": "Deficitário",
            "Inferior": "Inferior",
            "Média Inferior": "Média Inferior",
            "Média": "Média",
            "Média Superior": "Média Superior",
            "Superior": "Superior",
            "Muito Superior": "Superior",
        }
        if not classification:
            return "Classificação normativa indisponível"
        return mapping.get(classification, classification)

    @classmethod
    def _application_code(cls, application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or 0
        return f"AVL-{base_id:03d}"

    @classmethod
    def _report_code(cls, application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or 0
        return f"RPT-RAVLT-{base_id:03d}"

    @classmethod
    def _format_date(cls, value) -> str:
        return value.strftime("%d/%m/%Y") if hasattr(value, "strftime") else "Não informado"

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
    def _schooling_label(cls, patient) -> str:
        labels = {
            "fundamental_incompleto": "Ensino fundamental incompleto",
            "fundamental_completo": "Ensino fundamental completo",
            "ensino_medio_incompleto": "Ensino médio incompleto",
            "ensino_medio_completo": "Ensino médio completo",
            "superior_incompleto": "Ensino superior incompleto",
            "superior_completo": "Ensino superior completo",
            "middle_complete": "Ensino médio completo",
            "higher_complete": "Ensino superior completo",
        }
        if hasattr(patient, "get_schooling_display") and patient.schooling:
            return cls._normalize_schooling_text(patient.get_schooling_display())
        if getattr(patient, "grade_year", None):
            return cls._normalize_schooling_text(patient.grade_year)
        value = patient.schooling or ""
        normalized = str(value).strip().lower()
        if normalized:
            return cls._normalize_schooling_text(labels.get(normalized, str(value)))
        return "Não informado"

    @classmethod
    def _normalize_schooling_text(cls, value: str | None) -> str:
        text = str(value or "").replace("_", " ").strip()
        if not text:
            return "Não informado"
        return text[:1].upper() + text[1:]

    @classmethod
    def _normative_label(cls, faixa: str | None, age=None) -> str:
        faixa_text = str(faixa or "").strip()
        age_value = None
        try:
            age_value = int(age) if age not in (None, "") else None
        except (TypeError, ValueError):
            age_value = None

        stage = "Infantil" if age_value is not None and age_value < 18 else "Adulto"
        if not faixa_text:
            return f"{stage} / idade e escolaridade"
        if any(char.isdigit() for char in faixa_text) and "ano" not in faixa_text.lower():
            faixa_text = f"{faixa_text} anos"
        return f"{stage} / {faixa_text}"

    @classmethod
    def _format_score(cls, value) -> str:
        if value is None:
            return "-"
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return str(value)
        if numeric.is_integer():
            return str(int(numeric))
        return f"{numeric:.2f}".replace(".", ",")

    @classmethod
    def _num(cls, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
