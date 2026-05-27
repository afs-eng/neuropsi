TITLE = "Interpretação e Observações Clínicas"

INDEX_LABELS = {
    "qit": "Quociente de Inteligência Total",
    "icv": "Índice de Compreensão Verbal",
    "iop": "Índice de Organização Perceptual",
    "imt": "Índice de Memória Operacional",
    "ivp": "Índice de Velocidade de Processamento",
}

INDEX_ABBREVIATIONS = {
    "qit": "QIT",
    "icv": "ICV",
    "iop": "IOP",
    "imt": "IMO",
    "ivp": "IVP",
}

INDEX_TEXT_LABELS = {
    "icv": "compreensão verbal",
    "iop": "organização perceptual",
    "imt": "memória operacional",
    "ivp": "velocidade de processamento",
}

QIT_SUMMARIES = {
    "Muito Superior": "substancialmente acima do esperado para a faixa etária",
    "Superior": "acima do esperado para a faixa etária",
    "Média Superior": "discretamente acima do esperado para a faixa etária",
    "Média": "dentro do esperado para a faixa etária",
    "Média Inferior": "abaixo do esperado para a faixa etária",
    "Limítrofe": "com fragilidade importante em comparação ao esperado para a faixa etária",
    "Inferior": "com importante redução do funcionamento intelectual global",
    "Extremamente Baixo": "com comprometimento expressivo do funcionamento intelectual global",
}

INDEX_SUMMARIES = {
    "icv": {
        "high": "repertório verbal desenvolvido, boa formação de conceitos e raciocínio mediado pela linguagem",
        "average": "repertório verbal preservado, boa formação de conceitos e raciocínio mediado pela linguagem",
        "low": "maior esforço em tarefas de compreensão verbal, formação de conceitos e raciocínio mediado pela linguagem",
    },
    "iop": {
        "high": "bons recursos em raciocínio não verbal, análise visuoespacial, organização perceptual e resolução de problemas visuais",
        "average": "funcionamento adequado em raciocínio não verbal, análise visuoespacial, organização perceptual e resolução de problemas visuais",
        "low": "maior vulnerabilidade em raciocínio não verbal, análise visuoespacial, organização perceptual e resolução de problemas visuais",
    },
    "imt": {
        "high": "bons recursos para retenção, manipulação mental de informações e controle atencional",
        "average": "funcionamento preservado em retenção, manipulação mental de informações e controle atencional",
        "low": "maior esforço em tarefas de retenção, manipulação mental de informações e controle atencional",
    },
    "ivp": {
        "high": "boa eficiência em rapidez, precisão visual, atenção sustentada e eficiência grafomotora",
        "average": "desempenho preservado em rapidez, precisão visual, atenção sustentada e eficiência grafomotora",
        "low": "menor eficiência em rapidez, precisão visual, atenção sustentada e eficiência grafomotora",
    },
}

GAI_SUMMARIES = {
    "high": "potencial global de raciocínio relativamente mais eficiente",
    "average": "potencial global de raciocínio dentro do esperado",
    "low": "potencial global de raciocínio mais vulnerável",
}

CPI_SUMMARIES = {
    "high": "eficiência cognitiva operacional relativamente mais preservada",
    "average": "eficiência cognitiva operacional dentro do esperado",
    "low": "eficiência cognitiva operacional relativamente mais vulnerável",
}


def _first_name(name: str) -> str:
    return (name or "Paciente").split(" ", 1)[0]


def _classification_bucket(classificacao: str | None) -> str:
    if classificacao in {"Muito Superior", "Superior", "Média Superior"}:
        return "high"
    if classificacao == "Média":
        return "average"
    return "low"


def _index_map(merged_data: dict) -> dict:
    return {item.get("indice"): item for item in merged_data.get("indices", [])}


def _available_core_indices(indices: dict) -> dict:
    return {
        key: item
        for key, item in indices.items()
        if key in {"icv", "iop", "imt", "ivp"} and item.get("escore_composto") is not None
    }


def _profile_spread(indices: dict) -> float:
    scores = [item.get("escore_composto") for item in _available_core_indices(indices).values()]
    if len(scores) < 2:
        return 0
    return max(scores) - min(scores)


def _relative_profile(indices: dict) -> tuple[list[str], str | None, float]:
    available = _available_core_indices(indices)
    if not available:
        return [], None, 0
    ordered = sorted(available.items(), key=lambda entry: entry[1].get("escore_composto", 0), reverse=True)
    spread = ordered[0][1].get("escore_composto", 0) - ordered[-1][1].get("escore_composto", 0)
    if spread < 15:
        return [], None, spread
    top_codes = [code for code, _ in ordered[:2]]
    low_code = ordered[-1][0]
    return top_codes, low_code, spread


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


def _format_interval(value) -> str:
    if not value:
        return "—"
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return f"{value[0]}-{value[1]}"
    return str(value)


def _composite_line(label: str, sigla: str, score, percentile, interval, classificacao: str, summary: str) -> str:
    return (
        f"O {label} ({sigla} = {_format_number(score)}; percentil {_format_number(percentile, decimals=1)}; "
        f"IC 95% = {_format_interval(interval)}) situou-se na faixa {classificacao}, indicando {summary}."
    )


def _qit_paragraph(qit_data: dict, spread: float) -> str:
    classificacao = qit_data.get("classificacao") or "não classificado"
    summary = QIT_SUMMARIES.get(classificacao, "em faixa não classificada")
    paragraph = _composite_line(
        INDEX_LABELS["qit"],
        INDEX_ABBREVIATIONS["qit"],
        qit_data.get("escore_composto"),
        qit_data.get("percentil"),
        qit_data.get("intervalo_confianca"),
        classificacao,
        f"funcionamento intelectual global {summary}",
    )
    if spread >= 15:
        paragraph += " A interpretação do QIT deve considerar a heterogeneidade entre os índices, especialmente diante de discrepâncias clinicamente relevantes entre os domínios avaliados."
    else:
        paragraph += " A interpretação do QIT deve ser integrada à configuração dos índices fatoriais e aos demais dados clínicos disponíveis."
    return paragraph


def _index_summary(index_code: str, classificacao: str, is_relative_strength: bool) -> str:
    bucket = _classification_bucket(classificacao)
    summary = INDEX_SUMMARIES[index_code][bucket]
    if not is_relative_strength:
        return summary
    relative = {
        "icv": "melhor desempenho relativo em repertório verbal, formação de conceitos e raciocínio mediado pela linguagem",
        "iop": "melhor desempenho relativo em raciocínio não verbal, análise visuoespacial e organização perceptual",
        "imt": "melhor desempenho relativo em retenção, manipulação mental de informações e controle atencional",
        "ivp": "melhor desempenho relativo em rapidez, precisão visual, atenção sustentada e eficiência grafomotora",
    }
    return relative[index_code]


def _index_paragraph(index_code: str, index_data: dict, top_codes: list[str], low_code: str | None) -> str:
    if index_data.get("escore_composto") is None or not index_data.get("classificacao"):
        return ""
    classificacao = index_data.get("classificacao")
    paragraph = _composite_line(
        INDEX_LABELS[index_code],
        INDEX_ABBREVIATIONS[index_code],
        index_data.get("escore_composto"),
        index_data.get("percentil"),
        index_data.get("intervalo_confianca"),
        classificacao,
        _index_summary(index_code, classificacao, index_code in top_codes),
    )
    if index_code == "ivp" and low_code == "ivp" and _classification_bucket(classificacao) != "low":
        paragraph += " Apesar de preservado normativamente, constitui fragilidade relativa quando comparado aos demais índices."
    return paragraph


def _gai_cpi_paragraph(merged_data: dict) -> str:
    gai_data = merged_data.get("gai_data") or {}
    cpi_data = merged_data.get("cpi_data") or {}
    if gai_data.get("escore_composto") is None or cpi_data.get("escore_composto") is None:
        return ""

    gai_class = gai_data.get("classificacao") or "não classificado"
    cpi_class = cpi_data.get("classificacao") or "não classificado"
    difference = (gai_data.get("escore_composto") or 0) - (cpi_data.get("escore_composto") or 0)
    if difference >= 8:
        relation = "raciocínio global relativamente mais eficiente do que os processos operacionais de rapidez, atenção e manipulação mental"
    elif difference <= -8:
        relation = "eficiência cognitiva operacional relativamente mais preservada do que o potencial global de raciocínio"
    else:
        relation = "equilíbrio relativo entre raciocínio global e eficiência cognitiva operacional"

    return (
        f"O Índice de Habilidade Geral (GAI = {_format_number(gai_data.get('escore_composto'))}; percentil {_format_number(gai_data.get('percentil'), decimals=1)}; IC 95% = {_format_interval(gai_data.get('intervalo_confianca'))}) situou-se na faixa {gai_class}, "
        f"enquanto o Índice de Proficiência Cognitiva (CPI = {_format_number(cpi_data.get('escore_composto'))}; percentil {_format_number(cpi_data.get('percentil'), decimals=1)}; IC 95% = {_format_interval(cpi_data.get('intervalo_confianca'))}) situou-se na faixa {cpi_class}. "
        f"Essa diferença sugere {relation}."
    )


def _strengths_text(top_codes: list[str]) -> str:
    if not top_codes:
        return "recursos cognitivos globalmente preservados"
    labels = [INDEX_TEXT_LABELS[code] for code in top_codes]
    if len(labels) == 1:
        return f"melhor desempenho relativo em {labels[0]}"
    return f"melhores desempenhos relativos em {labels[0]} e {labels[1]}"


def _weakness_text(indices: dict, low_code: str | None) -> str:
    if not low_code:
        return "sem fragilidades relativas clinicamente relevantes entre os índices disponíveis"
    low_data = indices.get(low_code) or {}
    classificacao = low_data.get("classificacao") or "não classificado"
    label = INDEX_TEXT_LABELS.get(low_code, low_code)
    if low_code == "ivp" and _classification_bucket(classificacao) != "low":
        return "fragilidade relativa em velocidade de processamento, embora preservada normativamente"
    if _classification_bucket(classificacao) == "low":
        return f"maior vulnerabilidade em {label}"
    return f"menor eficiência relativa em {label}"


def _global_resources_text(qit_classificacao: str | None) -> str:
    if qit_classificacao in {"Muito Superior", "Superior", "Média Superior"}:
        return "preservados e acima da média"
    if qit_classificacao == "Média":
        return "preservados"
    return "com maior vulnerabilidade"


def _profile_label(spread: float) -> str:
    return "globalmente preservado, porém heterogêneo" if spread >= 15 else "globalmente preservado e relativamente homogêneo"


def _integrated_closing(merged_data: dict, patient_name: str) -> str:
    indices = _index_map(merged_data)
    qit_class = (merged_data.get("qit_data") or {}).get("classificacao") or "não classificado"
    top_codes, low_code, _spread = _relative_profile(indices)
    strength_text = _strengths_text(top_codes)
    weakness_text = _weakness_text(indices, low_code)
    first_name = _first_name(patient_name)
    return (
        f"Em análise clínica, o WISC-IV indicou QI Total na faixa {qit_class}, com {strength_text}. "
        f"{first_name} apresentou funcionamento cognitivo global {_global_resources_text(qit_class)}, com {weakness_text}. "
        "Os achados devem ser interpretados de forma integrada às observações clínicas, dados escolares, comportamentais e demais instrumentos, sem inferências diagnósticas isoladas."
    )


def _summary_closing(merged_data: dict, patient_name: str) -> str:
    indices = _index_map(merged_data)
    qit_class = (merged_data.get("qit_data") or {}).get("classificacao") or "não classificado"
    top_codes, low_code, spread = _relative_profile(indices)
    strength_text = _strengths_text(top_codes)
    weakness_text = _weakness_text(indices, low_code)
    return (
        f"Em análise clínica, {_first_name(patient_name)} apresentou funcionamento cognitivo global na faixa {qit_class}, com recursos {_global_resources_text(qit_class)} nos principais domínios avaliados. "
        f"Observou-se {strength_text}, em contraste com {weakness_text}. "
        f"O perfil deve ser compreendido como {_profile_label(spread)}, exigindo integração com dados clínicos, escolares, comportamentais e demais instrumentos da avaliação."
    )


def interpret_index(indice: str, classificacao: str) -> str:
    if indice not in INDEX_LABELS or indice == "qit":
        return "Interpretação não disponível."
    return _composite_line(
        INDEX_LABELS[indice],
        INDEX_ABBREVIATIONS[indice],
        0,
        None,
        None,
        classificacao,
        _index_summary(indice, classificacao, False),
    )


def interpret_qi(classificacao: str) -> str:
    summary = QIT_SUMMARIES.get(classificacao)
    if not summary:
        return "Interpretação não disponível."
    return _composite_line(
        INDEX_LABELS["qit"],
        INDEX_ABBREVIATIONS["qit"],
        0,
        None,
        None,
        classificacao,
        f"funcionamento intelectual global {summary}",
    )


def interpret_wisc4_profile(merged_data: dict, patient_name: str) -> str:
    indices = _index_map(merged_data)
    qit_data = merged_data.get("qit_data") or {}
    qit_classificacao = qit_data.get("classificacao")
    qit_score = qit_data.get("escore_composto", merged_data.get("qi_total"))
    top_codes, low_code, spread = _relative_profile(indices)

    parts = [TITLE]
    if qit_classificacao and qit_score is not None:
        parts.append(_qit_paragraph(qit_data, spread))
    else:
        parts.append(
            f"{_first_name(patient_name)} apresentou protocolo parcial no WISC-IV. Como há subtestes sem pontuação informada, o QI Total e parte das composições derivadas não puderam ser estimados com segurança."
        )

    for index_code in ("icv", "iop", "imt", "ivp"):
        paragraph = _index_paragraph(index_code, indices.get(index_code) or {}, top_codes, low_code)
        if paragraph:
            parts.append(paragraph)

    gai_cpi = _gai_cpi_paragraph(merged_data)
    if gai_cpi:
        parts.append(gai_cpi)

    return "\n\n".join(parts)
