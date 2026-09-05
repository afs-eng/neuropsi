from __future__ import annotations


INDEX_KEYS = [
    "compreensao_verbal",
    "organizacao_perceptual",
    "memoria_operacional",
    "velocidade_processamento",
]

INDEX_DESCRIPTIONS = {
    "compreensao_verbal": "formação de conceitos verbais, raciocínio verbal, vocabulário, abstração e conhecimento cristalizado",
    "organizacao_perceptual": "raciocínio fluido visual, organização visuoespacial, análise perceptiva e síntese de estímulos não verbais",
    "memoria_operacional": "manutenção e manipulação mental de informações, atenção auditiva, sequenciamento e controle mental",
    "velocidade_processamento": "rapidez visuomotora, discriminação visual, atenção sustentada e execução sob limite de tempo",
}

INDEX_SHORT_LABELS = {
    "qi_verbal": "QI Verbal",
    "qi_execucao": "QI de Execução",
    "qi_total": "QI Total",
    "compreensao_verbal": "ICV",
    "organizacao_perceptual": "IOP",
    "memoria_operacional": "IMO",
    "velocidade_processamento": "IVP",
}

DISCREPANCY_PAIRS = [
    ("qi_verbal", "qi_execucao"),
    ("compreensao_verbal", "organizacao_perceptual"),
    ("compreensao_verbal", "memoria_operacional"),
    ("organizacao_perceptual", "velocidade_processamento"),
    ("compreensao_verbal", "velocidade_processamento"),
    ("organizacao_perceptual", "memoria_operacional"),
    ("memoria_operacional", "velocidade_processamento"),
]

SUBTEST_CONSTRUCTS = {
    "completar_figuras": "atenção a detalhes visuais e discriminação perceptiva de informações incompletas",
    "vocabulario": "repertório lexical, conhecimento cristalizado, expressão verbal e formação conceitual",
    "codigos": "velocidade grafomotora, atenção visual sustentada e aprendizagem associativa sob pressão de tempo",
    "semelhancas": "abstração verbal, categorização conceitual e identificação de relações entre conceitos",
    "cubos": "organização visuoespacial, planejamento construtivo e integração visuomotora",
    "aritmetica": "cálculo mental, raciocínio quantitativo, atenção auditiva e memória operacional sob tempo",
    "raciocinio_matricial": "raciocínio fluido não verbal, reconhecimento de padrões visuais e inferência lógica",
    "digitos": "atenção auditiva, memória imediata, sequenciamento e manipulação de informações",
    "informacao": "conhecimento factual, memória semântica e repertório de informações gerais",
    "arranjo_figuras": "sequenciamento lógico, organização temporal e compreensão de relações sociais implícitas",
    "compreensao": "julgamento social, raciocínio prático verbal e compreensão de normas convencionais",
    "procurar_simbolos": "busca visual, discriminação perceptiva, atenção seletiva e velocidade sob limite temporal",
    "sequencia_numeros_letras": "memória operacional, reorganização mental, sequenciamento e controle executivo",
    "armar_objetos": "síntese perceptiva, organização visuoespacial, planejamento construtivo e percepção parte-todo",
}

CLUSTER_DEFINITIONS = [
    ("Gf", "Gf", "Raciocínio Fluido", ["raciocinio_matricial", "arranjo_figuras", "aritmetica"], "raciocínio fluido, solução de problemas novos e análise de relações lógicas"),
    ("Gv", "Gv", "Processamento Visual", ["cubos", "completar_figuras"], "processamento visual, organização visuoespacial e análise perceptiva"),
    ("Gf_nonverbal", "Gf-nv", "Raciocínio Fluido Não Verbal", ["raciocinio_matricial", "arranjo_figuras"], "raciocínio visual não verbal, inferência e organização de padrões perceptivos"),
    ("Gf_verbal", "Gf-v", "Raciocínio Fluido Verbal", ["semelhancas", "compreensao"], "raciocínio verbal aplicado, abstração e julgamento conceitual"),
    ("Gc_LK", "Gc-VL", "Conhecimento Lexical", ["semelhancas", "vocabulario"], "conhecimento lexical, abstração verbal e repertório conceitual"),
    ("Gc_K0", "Gc-K0", "Informações Gerais", ["compreensao", "informacao"], "conhecimento factual, compreensão social e informações culturalmente aprendidas"),
    ("Gc_LTM", "Gc-LTM", "Memória de Longo Prazo", ["vocabulario", "informacao"], "memória semântica, aprendizagem acumulada e recuperação de conhecimento cristalizado"),
    ("Gsm_WM", "Gsm-WM", "Memória de Curto Prazo", ["sequencia_numeros_letras", "digitos"], "memória auditiva imediata, sequenciamento e manipulação mental de informações"),
]

CLUSTER_COMPARISONS = [
    ("Gf", "Gv", 21),
    ("Gf_nonverbal", "Gv", 24),
    ("Gf_nonverbal", "Gf_verbal", 24),
    ("Gc_LK", "Gc_K0", 17),
    ("Gc_LTM", "Gsm_WM", 24),
    ("Gc_LTM", "Gf_verbal", 17),
]


def _first_name(patient_name: str | None) -> str:
    if not patient_name:
        return "Paciente"
    return patient_name.strip().split()[0] or "Paciente"


def _score(item: dict, key: str = "pontuacao_composta"):
    return item.get(key)


def _classification(item: dict) -> str:
    return str(item.get("classificacao") or "não classificado")


def _classification_lower(item: dict) -> str:
    return _classification(item).lower()


def _expected_composite_classification(value) -> str | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score <= 69:
        return "extremamente baixo"
    if score <= 79:
        return "limítrofe"
    if score <= 89:
        return "média inferior"
    if score <= 109:
        return "média"
    if score <= 119:
        return "média superior"
    if score <= 129:
        return "superior"
    return "muito superior"


def _parse_interval(interval: str | None) -> tuple[float, float] | None:
    if not interval:
        return None
    parts = str(interval).replace("–", "-").split("-", 1)
    if len(parts) != 2:
        return None
    try:
        return float(parts[0].strip()), float(parts[1].strip())
    except ValueError:
        return None


def _percentile_matches_score(score, percentile) -> bool:
    try:
        score = float(score)
        percentile = float(percentile)
    except (TypeError, ValueError):
        return True
    if score <= 69:
        return percentile <= 3
    if score <= 79:
        return percentile <= 10
    if score <= 89:
        return 5 <= percentile <= 25
    if score <= 109:
        return 20 <= percentile <= 80
    if score <= 119:
        return 70 <= percentile <= 92
    if score <= 129:
        return 88 <= percentile <= 98
    return percentile >= 95


def _cluster_inconsistency_reasons(cluster: dict) -> list[str]:
    score = cluster.get("escore")
    classification = str(cluster.get("classificacao") or "").lower()
    percentile = cluster.get("percentil")
    interval = _parse_interval(cluster.get("ic_95"))
    reasons = []

    expected = _expected_composite_classification(score)
    if expected and classification and expected != classification:
        reasons.append("classificação incompatível com o escore composto")

    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        numeric_score = None
    if interval and numeric_score is not None and not interval[0] <= numeric_score <= interval[1]:
        reasons.append("escore composto fora do intervalo de confiança")

    if not _percentile_matches_score(score, percentile):
        reasons.append("percentil incompatível com o escore composto")

    return reasons


def _metric_text(item: dict) -> str:
    value = item.get("pontuacao_composta")
    percentile = item.get("percentil")
    interval = item.get("ic_95") or item.get("ic_90") or "não informado"
    parts = [f"valor {value}" if value is not None else "valor não informado"]
    parts.append(f"percentil {percentile}" if percentile is not None else "percentil não informado")
    parts.append(f"intervalo de confiança {interval}")
    return ", ".join(parts)


def _metric_short(item: dict) -> str:
    value = item.get("pontuacao_composta")
    percentile = item.get("percentil")
    interval = item.get("ic_95") or item.get("ic_90")
    parts = [f"{value}" if value is not None else "não informado"]
    parts.append(str(_classification_lower(item)))
    if percentile is not None:
        parts.append(f"P{percentile}")
    if interval:
        parts.append(f"IC {interval}")
    return ", ".join(parts)


def _performance_descriptor(classification: str) -> str:
    normalized = classification.lower()
    if "muito superior" in normalized:
        return "muito elevado"
    if "superior" in normalized and "média" not in normalized:
        return "elevado"
    if "média superior" in normalized:
        return "acima da média"
    if normalized == "média":
        return "adequado"
    if "inferior" in normalized or "limítrofe" in normalized or "baixo" in normalized:
        return "reduzido"
    return "não classificada"


def _valid_scores(items: dict[str, dict], *, key: str = "pontuacao_composta") -> list[tuple[str, dict, float]]:
    rows = []
    for item_key, item in items.items():
        value = _score(item, key)
        if value is None:
            continue
        try:
            rows.append((item_key, item, float(value)))
        except (TypeError, ValueError):
            continue
    return rows


def _range_span(rows: list[tuple[str, dict, float]]) -> float:
    if not rows:
        return 0
    values = [row[2] for row in rows]
    return max(values) - min(values)


def _is_heterogeneous(indices: dict, discrepancias: list) -> bool:
    index_rows = _valid_scores({key: indices.get(key) or {} for key in ["qi_verbal", "qi_execucao", *INDEX_KEYS]})
    return bool(discrepancias) or _range_span(index_rows) >= 15


def _top_bottom_indices(indices: dict) -> tuple[tuple[str, dict, float] | None, tuple[str, dict, float] | None]:
    rows = _valid_scores({key: indices.get(key) or {} for key in INDEX_KEYS})
    if not rows:
        return None, None
    return max(rows, key=lambda row: row[2]), min(rows, key=lambda row: row[2])


def _relevant_subtests(subtestes: dict) -> tuple[list[tuple[str, dict, float]], list[tuple[str, dict, float]]]:
    rows = _valid_scores(subtestes, key="escore_ponderado")
    if not rows:
        return [], []
    high = [row for row in rows if row[2] >= 13]
    low = [row for row in rows if row[2] <= 7]
    if not high:
        high = sorted(rows, key=lambda row: row[2], reverse=True)[:2]
    if not low:
        low = sorted(rows, key=lambda row: row[2])[:2]
    return high[:4], low[:4]


def _subtest_phrase(rows: list[tuple[str, dict, float]]) -> str:
    parts = []
    for key, item, value in rows[:2]:
        name = item.get("nome") or key.replace("_", " ").title()
        parts.append(f"{name} (PP={int(value)}, {_classification_lower(item)})")
    return "; ".join(parts) if parts else "não foram identificados subtestes com destaque suficiente para análise isolada"


def _index_name(indices: dict, key: str) -> str:
    return str((indices.get(key) or {}).get("nome") or INDEX_SHORT_LABELS.get(key) or key.replace("_", " ").title())


def _index_value(indices: dict, key: str) -> float | None:
    value = (indices.get(key) or {}).get("pontuacao_composta")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _flatten_discrepancies(discrepancias: list) -> list[dict]:
    rows = {}
    for group in discrepancias:
        for pair in group.get("pares") or []:
            label = pair.get("par") or "comparação entre índices"
            current = rows.get(label)
            if current is None or pair.get("nivel") == "0,05":
                rows[label] = pair
    return list(rows.values())


def _match_discrepancy_pair(label: str, indices: dict) -> tuple[str, str] | None:
    normalized = label.lower()
    for left, right in DISCREPANCY_PAIRS:
        left_names = {_index_name(indices, left).lower(), INDEX_SHORT_LABELS.get(left, left).lower()}
        right_names = {_index_name(indices, right).lower(), INDEX_SHORT_LABELS.get(right, right).lower()}
        if any(name in normalized for name in left_names) and any(name in normalized for name in right_names):
            return left, right
    return None


def _directional_discrepancy_text(pair: dict, indices: dict) -> str:
    label = pair.get("par") or "comparação entre índices"
    difference = pair.get("diferenca")
    base = f"{label}: diferença de {difference} pontos."
    matched = _match_discrepancy_pair(label, indices)
    if not matched:
        return base

    left, right = matched
    left_value = _index_value(indices, left)
    right_value = _index_value(indices, right)
    if left_value is None or right_value is None or left_value == right_value:
        return base

    high, low = (left, right) if left_value > right_value else (right, left)
    high_name = _index_name(indices, high)
    low_name = _index_name(indices, low)
    return (
        f"{base} A direção favorece {high_name} ({int(max(left_value, right_value))}) em relação a {low_name} ({int(min(left_value, right_value))})."
    )


def _discrepancy_text(discrepancias: list, indices: dict, first_name: str) -> str:
    if not discrepancias:
        return (
            "Não foram registradas discrepâncias clinicamente relevantes entre os principais quocientes ou índices."
        )
    pairs = sorted(_flatten_discrepancies(discrepancias), key=lambda pair: pair.get("diferenca") or 0, reverse=True)
    described = _directional_discrepancy_text(pairs[0], indices) if pairs else "diferenças entre índices."
    return (
        f"Discrepâncias relevantes: no perfil de {first_name}, {described} Recomenda-se cautela na leitura isolada do QI Total."
    )


def _facilities_text(facilidades: list, first_name: str) -> str:
    if not facilidades:
        return ""
    parts = []
    for item in facilidades[:2]:
        subtest = item.get("subteste") or "subteste"
        kind = str(item.get("tipo") or "variação").lower()
        difference = item.get("diferenca")
        significance = item.get("significancia") or "significância não informada"
        parts.append(f"{subtest} como {kind} relativa (diferença {difference}, {significance})")
    return (
        f"A análise intraindividual apontou, no perfil de {first_name}, "
        + "; ".join(parts)
        + ". Esses achados são relativos ao próprio padrão de desempenho."
    )


def _score_gap(indices: dict, left: str, right: str) -> float | None:
    left_value = _index_value(indices, left)
    right_value = _index_value(indices, right)
    if left_value is None or right_value is None:
        return None
    return left_value - right_value


def _profile_patterns_text(indices: dict, first_name: str) -> str:
    patterns = []
    icv_ivp = _score_gap(indices, "compreensao_verbal", "velocidade_processamento")
    iop_ivp = _score_gap(indices, "organizacao_perceptual", "velocidade_processamento")
    icv_imo = _score_gap(indices, "compreensao_verbal", "memoria_operacional")
    imo = _index_value(indices, "memoria_operacional")
    ivp = _index_value(indices, "velocidade_processamento")

    if icv_ivp is not None and icv_ivp >= 15:
        patterns.append(
            "O contraste entre ICV e IVP indica melhor rendimento verbal relativo do que eficiência em tarefas rápidas sob pressão temporal."
        )
    if iop_ivp is not None and iop_ivp >= 15:
        patterns.append(
            "O desempenho relativamente superior em organização perceptual, associado a velocidade de processamento inferior, sugere melhor resolução visual quando há tempo suficiente e menor eficiência em tarefas rápidas ou automatizadas."
        )
    if icv_imo is not None and icv_imo >= 15:
        patterns.append(
            "A discrepância entre ICV e IMO sugere recursos verbais mais eficientes do que a manipulação mental de informações em tempo real."
        )
    if imo is not None and ivp is not None and imo < 90 and ivp < 90:
        patterns.append(
            "A associação entre memória operacional e velocidade de processamento reduzidas sugere menor eficiência em tarefas que exigem manter informações ativas e responder rapidamente."
        )

    if not patterns:
        return ""
    return patterns[0]


def _processing_speed_subtest_text(subtestes: dict) -> str:
    codigos = (subtestes.get("codigos") or {}).get("escore_ponderado")
    procurar = (subtestes.get("procurar_simbolos") or {}).get("escore_ponderado")
    try:
        codigos = float(codigos)
        procurar = float(procurar)
    except (TypeError, ValueError):
        return ""

    difference = abs(codigos - procurar)
    if difference < 3:
        return "Em Velocidade de Processamento, Códigos e Procurar Símbolos ficaram relativamente próximos."
    if codigos < procurar:
        return "Códigos ficou abaixo de Procurar Símbolos, sugerindo maior custo grafomotor ou de automatização sob tempo."
    return "Procurar Símbolos ficou abaixo de Códigos, sugerindo maior custo em varredura visual e decisão rápida."


def _subtest_span(subtestes: dict, keys: list[str]) -> float | None:
    scores = []
    for key in keys:
        score = (subtestes.get(key) or {}).get("escore_ponderado")
        try:
            scores.append(float(score))
        except (TypeError, ValueError):
            return None
    return max(scores) - min(scores) if scores else None


def _cluster_rows(clusters: dict, subtestes: dict) -> list[dict]:
    rows = []
    for key, code, label, subtest_keys, construct in CLUSTER_DEFINITIONS:
        cluster = clusters.get(key) or {}
        score = cluster.get("escore")
        span = _subtest_span(subtestes, subtest_keys)
        inconsistency_reasons = _cluster_inconsistency_reasons(cluster) if cluster else []
        interpretable = bool(cluster) and score is not None and span is not None and span < 5 and not inconsistency_reasons
        rows.append(
            {
                "key": key,
                "code": code,
                "label": label,
                "construct": construct,
                "score": score,
                "classification": cluster.get("classificacao"),
                "percentile": cluster.get("percentil"),
                "ic_95": cluster.get("ic_95"),
                "span": span,
                "interpretable": interpretable,
                "has_score": bool(cluster) and score is not None,
                "inconsistency_reasons": inconsistency_reasons,
            }
        )
    return rows


def _cluster_metric_text(row: dict) -> str:
    percentile = row.get("percentile")
    interval = row.get("ic_95") or "não informado"
    parts = [f"escore composto {row.get('score')}"]
    parts.append(f"percentil {percentile}" if percentile is not None else "percentil não informado")
    parts.append(f"IC 95% {interval}")
    return ", ".join(parts)


def _cluster_comparison_text(rows: list[dict]) -> str:
    by_key = {row["key"]: row for row in rows if row.get("interpretable")}
    rare = []
    for left_key, right_key, critical in CLUSTER_COMPARISONS:
        left = by_key.get(left_key)
        right = by_key.get(right_key)
        if not left or not right:
            continue
        difference = (left.get("score") or 0) - (right.get("score") or 0)
        if abs(difference) >= critical:
            direction = ">" if difference > 0 else "<"
            high, low = (left, right) if difference > 0 else (right, left)
            rare.append(
                f"{left['code']} {direction} {right['code']} (diferença {abs(int(difference))}, valor crítico {critical}), favorecendo {high['label']} em relação a {low['label']}"
            )
    if not rare:
        return "As comparações clínicas entre clusters interpretáveis não acrescentaram contrastes raros a partir dos valores críticos disponíveis."
    return "Nas comparações clínicas entre clusters, observou-se padrão raro em " + "; ".join(rare[:3]) + "."


def _cluster_analysis_text(clusters: dict, subtestes: dict, first_name: str) -> str:
    rows = _cluster_rows(clusters, subtestes)
    interpretable = [row for row in rows if row["interpretable"]]
    inconsistent = [row for row in rows if row.get("inconsistency_reasons")]
    not_interpretable = [row for row in rows if row.get("span") is not None and not row["interpretable"] and not row.get("inconsistency_reasons")]

    if not interpretable and not not_interpretable and not inconsistent:
        return (
            "A análise de clusters clínicos ficou limitada pela ausência de dados suficientes para conversão ou verificação de interpretabilidade. "
            "Quando disponíveis, esses clusters devem ser tratados como indicadores complementares aos índices fatoriais e aos subtestes, não como medidas diagnósticas isoladas."
        )

    parts = ["Análise dos Clusters e Comparações Complementares: recurso complementar à interpretação principal do WAIS-III."]
    if interpretable:
        highest = max(interpretable, key=lambda row: row.get("score") or 0)
        lowest = min(interpretable, key=lambda row: row.get("score") or 0)
        parts.append(
            f"No perfil de {first_name}, maior cluster interpretável: {highest['label']} ({highest['code']}, escore {highest.get('score')}, {str(highest.get('classification') or 'não classificado').lower()}); menor: {lowest['label']} ({lowest['code']}, escore {lowest.get('score')}, {str(lowest.get('classification') or 'não classificado').lower()})."
        )
        parts.append(_cluster_comparison_text(rows))
    if inconsistent:
        blocked = "; ".join(
            f"{row['label']} ({row['code']}), por {', '.join(row['inconsistency_reasons'])}"
            for row in inconsistent[:4]
        )
        parts.append(
            f"Clusters bloqueados por inconsistência psicométrica: {blocked}."
        )
    if not_interpretable:
        limited = "; ".join(
            f"{row['label']} ({row['code']}), com diferença interna de {int(row['span'])} pontos ponderados"
            for row in not_interpretable[:4]
        )
        parts.append(
            f"Clusters não interpretáveis por heterogeneidade interna: {limited}; nesses casos, a leitura deve retornar aos subtestes."
        )
    return " ".join(parts)


def build_wais3_interpretation(merged_data: dict, patient_name: str) -> str:
    first_name = _first_name(patient_name)
    indices = merged_data.get("indices") or {}
    gai = merged_data.get("gai_data") or {}
    discrepancias = merged_data.get("discrepancias") or []
    facilidades = merged_data.get("facilidades_dificuldades") or []
    subtestes = merged_data.get("subtestes") or {}
    clusters = merged_data.get("clusters") or {}
    qit = indices.get("qi_total") or {}
    qiv = indices.get("qi_verbal") or {}
    qie = indices.get("qi_execucao") or {}

    if qit.get("pontuacao_composta") is None:
        return (
            "WAIS-III – Escala de Inteligência Wechsler para Adultos\n\n"
            f"A avaliação da eficiência intelectual de {first_name} por meio da Escala de Inteligência Wechsler para Adultos – Terceira Edição (WAIS-III) foi registrada no sistema, porém não há dados normativos suficientes para interpretação quantitativa completa do QI Total, dos quocientes, dos índices fatoriais, percentis e intervalos de confiança. A conversão de pontos brutos em pontos ponderados e a conversão das somas ponderadas em pontos compostos devem ser realizadas exclusivamente por tabelas normativas oficiais correspondentes à idade cronológica do avaliado.\n\n"
            "Em análise clínica, os dados disponíveis devem ser tratados como incompletos. Não é adequado estimar ou interpolar escores ausentes, nem formular conclusões diagnósticas a partir de pontuações parciais. Recomenda-se revisar o protocolo, a faixa etária normativa, as substituições de subtestes e a disponibilidade das tabelas antes da redação interpretativa final."
        )

    heterogeneous = _is_heterogeneous(indices, discrepancias)
    qiv_score = _score(qiv)
    qie_score = _score(qie)
    qiv_qie_difference = abs(qiv_score - qie_score) if qiv_score is not None and qie_score is not None else None
    highest_index, lowest_index = _top_bottom_indices(indices)
    high_subtests, low_subtests = _relevant_subtests(subtestes)

    profile_note = (
        "perfil heterogêneo, exigindo maior peso interpretativo aos índices fatoriais e subtestes"
        if heterogeneous
        else f"perfil relativamente homogêneo, compatível com funcionamento intelectual {_performance_descriptor(_classification(qit))}"
    )
    global_text = (
        f"No WAIS-III, {first_name} apresentou QI Total de {qit.get('pontuacao_composta')}, classificado como {_classification_lower(qit)} ({_metric_short(qit)}), com {profile_note}."
    )

    if qiv_qie_difference is None:
        qiv_qie_text = "A comparação entre QI Verbal e QI de Execução não pôde ser detalhada por ausência de um dos valores compostos necessários."
    elif qiv_qie_difference == 0:
        qiv_qie_text = "A comparação entre QI Verbal e QI de Execução sugere equilíbrio entre habilidades verbais e não verbais, sem diferença observada entre os pontos compostos registrados."
    elif qiv_score > qie_score:
        qiv_qie_text = (
            f"QIV={_metric_short(qiv)} e QIE={_metric_short(qie)}; diferença de {qiv_qie_difference} pontos favorece o desempenho verbal."
        )
    else:
        qiv_qie_text = (
            f"QIV={_metric_short(qiv)} e QIE={_metric_short(qie)}; diferença de {qiv_qie_difference} pontos favorece o desempenho não verbal."
        )

    index_texts = []
    for key in INDEX_KEYS:
        item = indices.get(key) or {}
        if item.get("pontuacao_composta") is None:
            continue
        index_texts.append(
            f"{INDEX_SHORT_LABELS.get(key)}={_metric_short(item)}"
        )
    index_analysis = "Índices fatoriais: " + "; ".join(index_texts) + "." if index_texts else "A análise dos índices fatoriais ficou limitada pela ausência de pontos compostos suficientes."

    if highest_index and lowest_index and highest_index[0] != lowest_index[0] and highest_index[2] != lowest_index[2]:
        contrast = (
            f"No contraste intraindividual, o maior índice foi {highest_index[1].get('nome')} ({int(highest_index[2])}, {_classification_lower(highest_index[1])}) e o menor foi {lowest_index[1].get('nome')} ({int(lowest_index[2])}, {_classification_lower(lowest_index[1])})."
        )
    else:
        contrast = "Não foi observado contraste relevante entre índices fatoriais a partir dos dados disponíveis."

    subtest_analysis = (
        f"Subtestes com maior rendimento relativo: {_subtest_phrase(high_subtests)}. "
        f"Menor rendimento relativo: {_subtest_phrase(low_subtests)}. "
        f"{_processing_speed_subtest_text(subtestes)}"
    )

    discrepancy_analysis = _discrepancy_text(discrepancias, indices, first_name)
    facilities_analysis = _facilities_text(facilidades, first_name)
    cluster_analysis = _cluster_analysis_text(clusters, subtestes, first_name)
    profile_patterns = _profile_patterns_text(indices, first_name)

    optional_indexes = []
    if gai.get("calculado") and gai.get("escore_composto") is not None:
        gai_source = " por tabela normativa do Apêndice C" if gai.get("fonte_normativa") else ""
        optional_indexes.append(
            f"GAI obtido{gai_source}: escore composto {gai.get('escore_composto')} ({str(gai.get('classificacao') or '').lower()}), percentil {gai.get('percentil')}, IC {gai.get('intervalo_confianca')}."
            + (" Embora tenha sido calculado, sua interpretação clínica não é recomendada neste caso; deve ser mantido apenas como dado técnico complementar." if gai.get("alerta") else "")
        )
    optional_text = " ".join(optional_indexes)

    synthesis_parts = [f"Em síntese, {first_name} apresentou funcionamento intelectual global na faixa {_classification_lower(qit)}."]
    if highest_index and lowest_index and highest_index[0] != lowest_index[0] and highest_index[2] != lowest_index[2]:
        synthesis_parts.append(
            f"Os resultados sugerem maior eficiência relativa em {highest_index[1].get('nome')} e menor rendimento relativo em {lowest_index[1].get('nome')}."
        )
    synthesis_parts.append(
        "Os achados devem ser integrados à anamnese, observação clínica, funcionamento adaptativo e demais instrumentos, sem uso isolado para fechamento diagnóstico."
    )
    synthesis = " ".join(synthesis_parts)

    sections = [
        "WAIS-III – Escala de Inteligência Wechsler para Adultos",
        "Análise dos Resultados Psicométricos",
        f"{global_text} {qiv_qie_text} {index_analysis} {contrast}",
        f"{subtest_analysis} {discrepancy_analysis} {facilities_analysis} {profile_patterns}".strip(),
    ]
    if optional_text:
        sections.append(optional_text)
    sections.append(cluster_analysis)
    sections.append(synthesis)
    return "\n\n".join(section for section in sections if section.strip())
