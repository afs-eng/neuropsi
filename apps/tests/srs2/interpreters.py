from __future__ import annotations


KEY_ALIASES = {
    "percepcao_social": "percepção_social",
    "cognicao_social": "cognição_social",
    "comunicacao_social": "comunicação_social",
    "motivacao_social": "motivação_social",
    "padroes_restritos": "padrões_restritos",
}

PRIMARY_DOMAIN_KEYS = [
    "percepção_social",
    "cognição_social",
    "comunicação_social",
    "motivação_social",
    "padrões_restritos",
]

INTERPRETATION_ORDER = [*PRIMARY_DOMAIN_KEYS, "cis", "total"]

DISPLAY_NAMES = {
    "percepção_social": "Percepção Social",
    "cognição_social": "Cognição Social",
    "comunicação_social": "Comunicação Social",
    "motivação_social": "Motivação Social",
    "padrões_restritos": "Padrões Restritos e Repetitivos",
    "cis": "Comunicação e Interação Social",
    "total": "Pontuação Total do SRS-2",
}

DOMAIN_MODELS = {
    "percepção_social": {
        "normal": "O domínio de Percepção Social situou-se dentro dos limites normativos, indicando ausência de elevação clinicamente significativa, neste instrumento, quanto à percepção de pistas sociais básicas, expressões faciais, gestos, tom de voz e captação de elementos relevantes do contexto interpessoal.",
        "leve": "O domínio de Percepção Social apresentou elevação em nível leve, sugerindo dificuldades discretas na identificação de pistas sociais básicas, como expressões faciais, gestos, tom de voz e sinais contextuais relevantes para a interação interpessoal.",
        "moderado": "O domínio de Percepção Social apresentou elevação em nível moderado, indicando dificuldade clinicamente relevante para perceber pistas sociais básicas e captar elementos importantes do contexto interpessoal, o que pode comprometer a adequação das respostas sociais em situações cotidianas.",
        "severo": "O domínio de Percepção Social apresentou elevação em nível severo, sugerindo prejuízo expressivo na identificação de pistas sociais básicas e na captação de sinais interpessoais relevantes, com potencial impacto importante na adaptação social.",
    },
    "cognição_social": {
        "normal": "O domínio de Cognição Social permaneceu dentro dos limites normativos, sugerindo ausência de elevação clinicamente significativa, neste instrumento, quanto à interpretação de pistas sociais, compreensão de intenções e inferência de estados emocionais ou mentais de outras pessoas.",
        "leve": "O domínio de Cognição Social apresentou elevação em nível leve, sugerindo dificuldades discretas na compreensão de situações sociais, interpretação de intenções e inferência de estados mentais de outras pessoas.",
        "moderado": "O domínio de Cognição Social apresentou elevação em nível moderado, indicando dificuldade clinicamente relevante para interpretar situações sociais, compreender intenções, reconhecer perspectivas e manejar regras sociais implícitas.",
        "severo": "O domínio de Cognição Social apresentou elevação em nível severo, sugerindo prejuízo expressivo na interpretação de informações sociais, na compreensão de intenções e na atribuição de significado às interações interpessoais.",
    },
    "comunicação_social": {
        "normal": "O domínio de Comunicação Social situou-se dentro dos limites normativos, indicando ausência de elevação clinicamente significativa, neste instrumento, quanto à comunicação social expressiva, reciprocidade comunicativa e adequação da comunicação ao contexto.",
        "leve": "O domínio de Comunicação Social apresentou elevação em nível leve, sugerindo dificuldades discretas em sustentar trocas comunicativas recíprocas, ajustar a comunicação ao contexto e integrar recursos verbais e não verbais durante a interação social.",
        "moderado": "O domínio de Comunicação Social apresentou elevação em nível moderado, indicando dificuldades clinicamente relevantes na comunicação social recíproca, incluindo sustentação de trocas comunicativas, adequação da linguagem ao contexto e uso integrado de recursos expressivos verbais e não verbais.",
        "severo": "O domínio de Comunicação Social apresentou elevação em nível severo, sugerindo prejuízo expressivo na comunicação social recíproca, com impacto importante na capacidade de iniciar, manter e adaptar trocas comunicativas em contextos interpessoais.",
    },
    "motivação_social": {
        "normal": "O domínio de Motivação Social permaneceu dentro dos limites normativos, indicando ausência de elevação clinicamente significativa, neste instrumento, quanto ao interesse espontâneo, iniciativa e engajamento em interações sociais.",
        "leve": "O domínio de Motivação Social apresentou elevação em nível leve, sugerindo dificuldades discretas no interesse espontâneo por interações sociais, na iniciativa interpessoal ou no engajamento social.",
        "moderado": "O domínio de Motivação Social apresentou elevação em nível moderado, indicando dificuldades clinicamente relevantes no interesse espontâneo, na iniciativa social e no engajamento interpessoal, podendo refletir menor busca ativa por interação social.",
        "severo": "O domínio de Motivação Social apresentou elevação em nível severo, sugerindo prejuízo expressivo na iniciativa social, no interesse espontâneo por interações e no engajamento interpessoal.",
    },
    "padrões_restritos": {
        "normal": "O domínio de Padrões Restritos e Repetitivos situou-se dentro dos limites normativos, indicando ausência de elevação clinicamente significativa, neste instrumento, quanto à presença de rigidez comportamental, repetitividade, interesses restritos ou resistência a mudanças.",
        "leve": "O domínio de Padrões Restritos e Repetitivos apresentou elevação em nível leve, sugerindo sinais discretos de rigidez comportamental, repetitividade, interesses restritos ou menor flexibilidade diante de mudanças.",
        "moderado": "O domínio de Padrões Restritos e Repetitivos apresentou elevação em nível moderado, indicando dificuldades clinicamente relevantes relacionadas à rigidez comportamental, repetitividade, interesses restritos ou menor flexibilidade diante de mudanças.",
        "severo": "O domínio de Padrões Restritos e Repetitivos apresentou elevação em nível severo, sugerindo prejuízo expressivo associado à rigidez comportamental, comportamentos repetitivos, interesses restritos e resistência significativa a mudanças.",
    },
    "cis": {
        "normal": "A escala de Comunicação e Interação Social situou-se dentro dos limites normativos, sugerindo ausência de elevação clinicamente significativa, neste instrumento, no conjunto de habilidades relacionadas à reciprocidade socioemocional, comunicação social e manutenção de interações interpessoais.",
        "leve": "A escala de Comunicação e Interação Social apresentou elevação em nível leve, sugerindo dificuldades discretas no conjunto de habilidades relacionadas à reciprocidade socioemocional, comunicação social e manutenção de interações interpessoais.",
        "moderado": "A escala de Comunicação e Interação Social apresentou elevação em nível moderado, indicando dificuldades clinicamente relevantes nos componentes centrais de reciprocidade social, comunicação interpessoal e manutenção de relações sociais.",
        "severo": "A escala de Comunicação e Interação Social apresentou elevação em nível severo, sugerindo prejuízo expressivo nas habilidades de reciprocidade socioemocional, comunicação social e interação interpessoal.",
    },
    "total": {
        "normal": "A Pontuação Total do SRS-2 situou-se dentro dos limites normativos, indicando ausência de elevação clinicamente significativa na medida global de responsividade social avaliada pelo instrumento. Esse resultado não exclui a análise clínica quando houver queixas funcionais relevantes, mas não sugere, isoladamente, prejuízo global expressivo no SRS-2.",
        "leve": "A Pontuação Total do SRS-2 situou-se em nível leve, sugerindo dificuldades sutis, porém clinicamente relevantes, na responsividade social global. Esse resultado deve ser integrado à anamnese, observação clínica e demais instrumentos aplicados.",
        "moderado": "A Pontuação Total do SRS-2 situou-se em nível moderado, indicando comprometimento global clinicamente relevante da responsividade social, com impacto potencial na comunicação social recíproca, na interação interpessoal e/ou na flexibilidade comportamental.",
        "severo": "A Pontuação Total do SRS-2 situou-se em nível severo, sugerindo comprometimento global expressivo da responsividade social, com provável impacto funcional importante na comunicação social, interação interpessoal e flexibilidade comportamental.",
    },
}


def _canonical_key(value: str | None) -> str:
    key = value or ""
    return KEY_ALIASES.get(key, key)


def _tscore(row: dict | None) -> float | None:
    try:
        return float((row or {}).get("tscore"))
    except (TypeError, ValueError):
        return None


def _level_for_tscore(value) -> str:
    try:
        tscore = float(value)
    except (TypeError, ValueError):
        return "normal"
    if tscore <= 59:
        return "normal"
    if tscore <= 65:
        return "leve"
    if tscore <= 75:
        return "moderado"
    return "severo"


def _classification_label(level: str) -> str:
    return {
        "normal": "Dentro dos limites normais",
        "leve": "Nível leve",
        "moderado": "Nível moderado",
        "severo": "Nível severo",
    }.get(level, "Não classificado")


def _normalized_results(rows: list[dict]) -> list[dict]:
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        key = _canonical_key(item.get("variável"))
        item["variável"] = key
        item["nome"] = DISPLAY_NAMES.get(key, item.get("nome") or key)
        item["nível"] = _level_for_tscore(item.get("tscore"))
        item["classificação"] = _classification_label(item["nível"])
        normalized.append(item)
    return normalized


def _join_names(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} e {names[1]}"
    return f"{', '.join(names[:-1])} e {names[-1]}"


def _explicit_sentence_anchor(row: dict) -> str:
    key = row.get("variável")
    name = (row.get("nome") or DISPLAY_NAMES.get(key, "")).lower()
    if key == "cis":
        return f"a escala de {name}"
    if key in PRIMARY_DOMAIN_KEYS:
        return f"o domínio de {name}"
    return name


def _ordered_rows(by_key: dict[str, dict]) -> list[dict]:
    return [by_key[key] for key in INTERPRETATION_ORDER if key in by_key]


def _elevated_domains(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("variável") != "total" and _is_elevated(row)]


def _normal_domains(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("variável") != "total" and not _is_elevated(row)]


def _is_elevated(row: dict | None) -> bool:
    value = _tscore(row)
    return value is not None and value >= 60


def _is_moderate_or_severe(row: dict | None) -> bool:
    value = _tscore(row)
    return value is not None and value >= 66


def _highest_domain(rows: list[dict]) -> dict | None:
    domains = [row for row in rows if row.get("variável") != "total"]
    return max(domains, key=lambda row: _tscore(row) or 0, default=None)


def _domain_text(row: dict) -> str:
    key = row.get("variável")
    level = row.get("nível", "normal")
    return DOMAIN_MODELS.get(key, {}).get(level, "")


def _global_profile_text(total: dict | None, elevated: list[dict], highest: dict | None) -> str:
    total_level = (total or {}).get("nível", "normal")
    total_t = (total or {}).get("tscore", "-")
    highest_name = (highest or {}).get("nome", "domínio de maior escore")
    highest_t = (highest or {}).get("tscore", "-")
    highest_level = (highest or {}).get("nível", "normal")

    if total_level == "normal" and not elevated:
        return (
            "Em análise clínica, o perfil obtido no SRS-2 situou-se dentro dos limites normativos, "
            "com Pontuação Total sem elevação clinicamente significativa. Os domínios avaliados não "
            "indicam, neste instrumento, prejuízo global expressivo na responsividade social. Quando "
            "houver queixas clínicas, os achados devem ser compreendidos de forma integrada à anamnese, "
            "observação comportamental e demais instrumentos, pois resultado normativo no SRS-2 não "
            "exclui, por si só, a necessidade de investigação clínica. "
            f"O maior escore entre os domínios foi observado em {highest_name}, com T={highest_t}."
        )

    if total_level == "normal":
        elevated_names = _join_names([row.get("nome", "domínio") for row in elevated])
        return (
            "Em análise clínica, embora o Escore Total esteja dentro dos limites normativos, observa-se elevação "
            f"pontual em {elevated_names}. Esse padrão sugere perfil heterogêneo, no qual uma "
            "ou mais áreas específicas apresentam maior vulnerabilidade, sem configurar elevação "
            "global no instrumento. A interpretação deve ser cautelosa e integrada aos dados clínicos. "
            f"A maior elevação ocorreu em {highest_name}, com Escore T={highest_t}, classificada como {_classification_label(highest_level).lower()}."
        )

    if total_level == "leve" and highest_level in {"moderado", "severo"}:
        return (
            "Em análise clínica, o perfil obtido no SRS-2 evidenciou elevação global em nível "
            f"leve na responsividade social, com destaque para {highest_name}, que apresentou "
            f"elevação em nível {highest_level}. O Escore Total foi T={total_t}. A interpretação "
            "deve considerar se as elevações se distribuem de forma ampla ou se permanecem "
            "concentradas em domínios específicos."
        )

    if total_level == "leve":
        return (
            "Em análise clínica, o perfil obtido no SRS-2 evidenciou elevação global em nível leve "
            "da responsividade social. Esse resultado sugere dificuldades sutis, porém clinicamente "
            "relevantes, na qualidade das interações interpessoais, na comunicação social recíproca "
            "e/ou na flexibilidade comportamental. A interpretação deve considerar se as elevações "
            "se distribuem de forma ampla ou se permanecem concentradas em domínios específicos. "
            f"A maior elevação ocorreu em {highest_name}, com Escore T={highest_t}, classificada como {_classification_label(highest_level).lower()}."
        )

    if total_level == "moderado":
        return (
            "Em análise clínica, o perfil obtido no SRS-2 evidenciou elevação global em nível "
            "moderado da responsividade social. Esse resultado indica comprometimento clinicamente "
            "relevante no funcionamento sociointeracional, podendo envolver prejuízos na comunicação "
            "social recíproca, na interpretação de situações interpessoais, no engajamento social "
            "e/ou na flexibilidade comportamental. "
            f"A maior elevação ocorreu em {highest_name}, com Escore T={highest_t}, classificada como {_classification_label(highest_level).lower()}."
        )

    return (
        "Em análise clínica, o perfil obtido no SRS-2 evidenciou elevação global em nível severo "
        "da responsividade social. Esse resultado sugere comprometimento expressivo no funcionamento "
        "sociointeracional, com impacto funcional importante na comunicação social, na reciprocidade "
        "interpessoal e/ou na presença de padrões restritos e repetitivos. A interpretação deve ser "
        "realizada com cautela e sempre integrada ao histórico do desenvolvimento, observação clínica, "
        "funcionamento adaptativo e demais instrumentos. "
        f"A maior elevação ocorreu em {highest_name}, com Escore T={highest_t}, classificada como {_classification_label(highest_level).lower()}."
    )


def _combination_text(cis: dict | None, repetitive: dict | None) -> str:
    cis_elevated = _is_elevated(cis)
    repetitive_elevated = _is_elevated(repetitive)

    if cis_elevated and repetitive_elevated:
        return (
            "A elevação conjunta em Comunicação e Interação Social e Padrões Restritos e Repetitivos "
            "indica comprometimento nos dois grandes eixos sintomatológicos relacionados ao Transtorno "
            "do Espectro Autista, conforme descritos no DSM-5-TR. Esse achado não estabelece diagnóstico "
            "isoladamente, mas fortalece a necessidade de investigação clínica de características associadas "
            "ao TEA, especialmente quando houver convergência com anamnese, observação clínica, histórico do "
            "desenvolvimento e prejuízos funcionais."
        )
    if cis_elevated and not repetitive_elevated:
        return (
            "A elevação em Comunicação e Interação Social, na ausência de elevação em Padrões Restritos "
            "e Repetitivos, sugere dificuldades predominantemente relacionadas à reciprocidade social, "
            "comunicação interpessoal e manutenção de relações sociais. Esse perfil deve ser diferenciado "
            "de quadros em que há presença consistente de rigidez, repetitividade e interesses restritos, "
            "sendo necessária análise clínica integrada."
        )
    if repetitive_elevated and not cis_elevated:
        return (
            "A elevação em Padrões Restritos e Repetitivos, com Comunicação e Interação Social dentro "
            "dos limites normativos, sugere presença de rigidez comportamental, repetitividade ou interesses "
            "restritos sem indicação, neste instrumento, de prejuízo global nas habilidades de comunicação e "
            "interação social. Esse padrão deve ser analisado qualitativamente e correlacionado ao funcionamento cotidiano."
        )
    return ""


def _diagnostic_caution(total: dict | None, rows: list[dict], cis: dict | None, repetitive: dict | None) -> str:
    total_moderate = _is_moderate_or_severe(total)
    cis_moderate = _is_moderate_or_severe(cis)
    repetitive_moderate = _is_moderate_or_severe(repetitive)
    any_moderate_domain = any(_is_moderate_or_severe(row) for row in rows if row.get("variável") != "total")

    if cis_moderate and repetitive_moderate:
        return (
            "Considerando exclusivamente os resultados do SRS-2, observa-se elevação clinicamente "
            "relevante nos dois eixos centrais associados ao Transtorno do Espectro Autista: "
            "comunicação/interação social e padrões restritos e repetitivos. Esse achado não confirma "
            "diagnóstico isoladamente, mas fortalece a necessidade de investigar hipótese diagnóstica de "
            "Transtorno do Espectro Autista quando houver convergência com anamnese, observação clínica, "
            "histórico do desenvolvimento, funcionamento adaptativo e prejuízos funcionais."
        )
    if total_moderate or cis_moderate or repetitive_moderate:
        return (
            "Considerando exclusivamente os resultados do SRS-2, observa-se elevação clinicamente "
            "relevante na responsividade social. Esse achado não confirma diagnóstico isoladamente, mas "
            "sustenta a necessidade de investigar hipótese diagnóstica de Transtorno do Espectro Autista "
            "quando houver convergência com anamnese, observação clínica, histórico do desenvolvimento, "
            "funcionamento adaptativo e prejuízos funcionais."
        )
    if _is_elevated(total) or any_moderate_domain:
        return (
            "Os resultados indicam elevações que justificam investigação clínica complementar, sem "
            "sustentar diagnóstico isoladamente. Recomenda-se integrar os achados à anamnese, observação "
            "clínica, histórico do desenvolvimento e funcionamento adaptativo."
        )
    return (
        "Os resultados do SRS-2 não sustentam, isoladamente, hipótese diagnóstica de Transtorno do "
        "Espectro Autista. Caso existam queixas clínicas relevantes, recomenda-se integração com "
        "anamnese, observação clínica, funcionamento adaptativo e demais instrumentos."
    )


def validate_srs2_interpretation(rows: list[dict], text: str) -> list[str]:
    errors = []
    lowered = text.lower()
    forbidden_global = [
        "confirmou diagnóstico",
        "confirma diagnóstico pelo srs-2",
        "diagnóstico de tea pelo srs-2",
        "srs-2 confirmou",
        "autismo leve",
        "autismo moderado",
        "autismo severo",
        "elevação em nível dentro dos limites normais",
        "em contraste",
        "informante",
    ]
    for phrase in forbidden_global:
        if phrase in lowered:
            errors.append(f"Texto proibido encontrado: {phrase}")

    if "em análise clínica" not in lowered:
        errors.append("A síntese deve conter 'Em análise clínica'.")
    if "rastreio" not in lowered:
        errors.append("O SRS-2 deve ser descrito como instrumento de rastreio.")

    sentences = [sentence.strip() for sentence in text.replace("\n", " ").split(".") if sentence.strip()]
    normal_forbidden = [
        "apresentou elevação",
        "apresentou déficit",
        "indicando dificuldades",
        "indicou dificuldade",
        "evidenciou prejuízo",
        "sugerindo dificuldades",
        "comprometimento clinicamente relevante",
        "prejuízo expressivo",
    ]
    for row in rows:
        if row.get("variável") == "total" or _is_elevated(row):
            continue
        name = row.get("nome") or DISPLAY_NAMES.get(row.get("variável"), "")
        anchor = _explicit_sentence_anchor(row)
        related_sentences = [sentence.lower() for sentence in sentences if anchor in sentence.lower()]
        for sentence in related_sentences:
            for phrase in normal_forbidden:
                if phrase in sentence:
                    errors.append(f"Domínio normal interpretado como alterado: {name}")
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if "domínios elevados" in sentence_lower and name.lower() in sentence_lower:
                errors.append(f"Domínio normal listado como elevado: {name}")
    return errors


def interpret_srs2_results(merged_data: dict) -> str:
    results = _normalized_results(merged_data.get("resultados", []))
    if not results:
        return "Sem resultados para interpretação."

    by_key = {row.get("variável"): row for row in results}
    rows = _ordered_rows(by_key)
    total = by_key.get("total")
    cis = by_key.get("cis")
    repetitive = by_key.get("padrões_restritos")
    elevated = _elevated_domains(rows)
    highest = _highest_domain(rows)

    domain_texts = [_domain_text(row) for row in rows if row.get("variável") in PRIMARY_DOMAIN_KEYS]
    cis_text = _domain_text(cis) if cis else ""
    total_text = _domain_text(total) if total else ""
    combination = _combination_text(cis, repetitive)

    normal_names = _join_names([row.get("nome", "") for row in _normal_domains(rows) if row.get("variável") in PRIMARY_DOMAIN_KEYS])
    elevated_names = _join_names([row.get("nome", "") for row in elevated if row.get("variável") in PRIMARY_DOMAIN_KEYS])
    distribution = []
    if normal_names:
        distribution.append(f"Domínios dentro dos limites normativos: {normal_names}.")
    if elevated_names:
        distribution.append(f"Domínios elevados: {elevated_names}.")

    paragraphs = [
        "A Escala de Responsividade Social - Segunda Edição (SRS-2) foi aplicada com o objetivo de investigar possíveis dificuldades na comunicação social, cognição social, motivação social, percepção social e presença de padrões restritos e repetitivos, auxiliando no rastreio de indicadores associados ao Transtorno do Espectro Autista (TEA).",
        _global_profile_text(total, elevated, highest),
        " ".join([*domain_texts[:3], *distribution]).strip(),
        " ".join([*domain_texts[3:], cis_text, total_text, combination]).strip(),
        _diagnostic_caution(total, rows, cis, repetitive),
    ]
    interpretation = "\n\n".join(paragraph for paragraph in paragraphs if paragraph)
    errors = validate_srs2_interpretation(rows, interpretation)
    if errors:
        raise ValueError("Interpretação SRS-2 inválida: " + "; ".join(errors))
    return interpretation
