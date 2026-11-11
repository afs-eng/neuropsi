"""Descriptive, preliminary PDF interpretation of freshly computed extensive scores.

This presentation layer neither scores items nor changes normative results or review.
"""

DOMAIN_DESCRIPTIONS = {
    "COM": "O domínio reúne habilidades de compreensão, expressão e uso da linguagem escrita, conforme os subdomínios aplicáveis à idade.",
    "AVD": "O domínio reúne habilidades práticas do cotidiano nos contextos contemplados pelo formulário do informante.",
    "SOC": "O domínio reúne habilidades de relacionamento, participação em atividades de lazer e manejo de situações sociais.",
    "HMOT": "O domínio reúne habilidades motoras amplas e finas. Seu resultado é analisado separadamente e não compõe o CCA.",
}
SUBDOMAIN_DESCRIPTIONS = {
    "rec": "Compreensão de mensagens e informações recebidas pela linguagem.",
    "exp": "Uso da linguagem para comunicar necessidades, ideias e informações.",
    "esc": "Uso funcional de habilidades de leitura e escrita, quando aplicáveis à idade.",
    "pes": "Habilidades de cuidado pessoal nas atividades habituais.",
    "dom": "Participação nas rotinas e tarefas do ambiente doméstico.",
    "com": "Uso de habilidades práticas em situações da comunidade.",
    "num": "Uso funcional de conceitos numéricos nas atividades escolares e cotidianas.",
    "cme": "Participação nas rotinas e demandas práticas do ambiente escolar.",
    "rin": "Habilidades de interação e manutenção de relacionamentos interpessoais.",
    "bri": "Participação em brincadeiras, lazer e atividades compartilhadas.",
    "enf": "Manejo das demandas sociais e adaptação do comportamento às situações.",
    "cmg": "Uso de movimentos amplos, coordenação corporal e deslocamento.",
    "cmf": "Uso de movimentos finos e manipulação de objetos.",
}


def _number(value):
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _score_text(row):
    score = row["standard_score"]
    if score is None:
        return f"{row['label']}: resultado indisponível ({row.get('unavailable_reason') or 'sem dados normativos'}); não equivale a escore zero."
    ci = row.get("confidence_interval")
    interval = f"IC95% {ci[0]}–{ci[1]}" if ci else "IC95% indisponível"
    percentile = f"percentil {row['percentile']}" if row.get("percentile") is not None else "percentil indisponível"
    classification = (row.get("classification") or "classificação indisponível").lower()
    return f"{row['label']}: escore padrão {score}, {percentile}, {interval}; faixa {classification} na referência normativa americana."


def _relative_text(strength, mean, metric):
    if not strength or strength.get("significant") is None or mean is None:
        return "A análise de força ou fraqueza relativa está indisponível; não é possível concluir ausência de discrepância."
    if strength["significant"]:
        finding = "força relativa" if strength["finding"] == "Força" else "fraqueza relativa"
        return f"É uma {finding} em relação à média pessoal de {metric} {_number(mean)} (p = 0,05)."
    return f"Não apresentou diferença significativa em relação à média pessoal de {metric} {_number(mean)} (p = 0,05)."


def _pair_text(row, metric):
    diff = row["difference"]
    if diff is None or row.get("significant") is None:
        return "Comparação indisponível por ausência de escores ou valor crítico publicado."
    if not row["significant"]:
        return "Diferença não significativa a p = 0,05; isso não demonstra equivalência entre as habilidades."
    higher, lower = (row["first_label"], row["second_label"]) if diff > 0 else (row["second_label"], row["first_label"])
    base = f" Taxa de base da diferença nessa direção: {row['base_rate']}." if row.get("base_rate") else " Taxa de base indisponível."
    return f"{higher} apresenta {abs(diff)} pontos de {metric} a mais que {lower}; diferença significativa (p = 0,05).{base}"


def build_extensive_interpretation(analysis):
    """Use existing decisions, not rounded differences, cached prose or new cutoffs."""
    if analysis.get("form_level") != "extensivo" or not analysis.get("normative_scoring"):
        raise ValueError("Interpretação detalhada exclusiva de resultados normativos Extensivos.")
    overview = [_score_text(analysis["cca"])]
    overview.append("O CCA sintetiza Comunicação, Atividades de Vida Diária e Socialização. Habilidades Motoras não entra nesse composto. Escores padrão têm média normativa 100; escala-v dos subdomínios tem média 15 e não deve ser comparada diretamente a essa métrica.")
    domain_strengths = {r["scale"]: r for r in analysis["strengths"]}
    sub_strengths = {r["scale"]: r for r in analysis["subdomain_strengths"]}
    details = []
    for domain in analysis["adaptive"]:
        overview.append(_score_text(domain))
        rows = []
        for subdomain in analysis["subdomains"]:
            if subdomain["domain"] != domain["scale"]:
                continue
            score = subdomain["v_scale"]
            relation = "abaixo da" if score < 15 else "acima da" if score > 15 else "igual à"
            strength = sub_strengths.get(subdomain["scale"])
            text = (f"{SUBDOMAIN_DESCRIPTIONS[subdomain['scale']]} Escala-v {score}, {relation} referência normativa de 15. "
                    f"{_relative_text(strength, analysis['subdomain_mean_v_scale'], 'escala-v')}")
            rows.append({**subdomain, "strength": strength, "interpretation": text})
        if not rows:
            continue
        comparisons = [r for r in analysis["subdomain_pairs"] if r["within_domain"] and r["first"] in {s["scale"] for s in rows}]
        significant = [r for r in comparisons if r["significant"] is True]
        readable = [_pair_text(r, "escala-v") for r in significant]
        if not readable:
            readable = ["Não houve diferença significativa nas comparações disponíveis entre os subdomínios deste domínio." if any(r["significant"] is False for r in comparisons)
                        else "Não há comparações normativas disponíveis entre os subdomínios apresentados."]
        if any(r["significant"] is None for r in comparisons):
            readable.append("Algumas comparações estão indisponíveis e não foram interpretadas como ausência de diferença.")
        details.append({"code": domain["scale"], "label": domain["label"], "description": DOMAIN_DESCRIPTIONS[domain["scale"]],
                        "score_text": _score_text(domain), "relative_text": _relative_text(domain_strengths.get(domain["scale"]), analysis["mean_standard_score"], "escore padrão"),
                        "subdomains": rows, "pairs": comparisons, "pair_interpretations": readable})
    significant_core = [r for r in analysis["pairs"] if r["significant"] is True and r["first"] != "HMOT" and r["second"] != "HMOT"]
    comparable_core = [r for r in analysis["pairs"] if r["significant"] is not None and r["first"] != "HMOT" and r["second"] != "HMOT"]
    if significant_core:
        profile = "Há diferenças significativas entre domínios centrais. O CCA deve ser lido em conjunto com o perfil, sem presumir desempenho uniforme em todas as áreas."
    elif len(comparable_core) == 3:
        profile = "As tabelas não indicaram diferenças significativas entre os domínios centrais. Esse resultado não prova equivalência entre as áreas nem ausência de necessidades no cotidiano."
    else:
        profile = "A análise de discrepâncias entre os domínios centrais está incompleta ou indisponível; não é possível concluir ausência de diferenças significativas."
    strengths = [r["label"] for r in analysis["subdomain_strengths"] if r["significant"] is True and r["finding"] == "Força"]
    weaknesses = [r["label"] for r in analysis["subdomain_strengths"] if r["significant"] is True and r["finding"] == "Fraqueza"]
    synthesis = [profile]
    synthesis.append(f"Forças relativas entre os subdomínios: {', '.join(strengths)}." if strengths else "Não foram identificadas forças relativas estatisticamente significativas nas análises disponíveis dos subdomínios.")
    synthesis.append(f"Fraquezas relativas entre os subdomínios: {', '.join(weaknesses)}." if weaknesses else "Não foram identificadas fraquezas relativas estatisticamente significativas nas análises disponíveis dos subdomínios.")
    if not any(r["significant"] is not None for r in analysis["subdomain_strengths"]):
        synthesis[1:3] = ["A análise de forças e fraquezas relativas dos subdomínios está indisponível; não é possível concluir ausência desses achados."]
    synthesis.append("Força relativa não significa necessariamente desempenho normativo elevado; fraqueza relativa não estabelece, por si só, prejuízo clínico. Valores abaixo de 15 descrevem a posição na escala-v, não um diagnóstico.")
    synthesis.append("A entrevista e a observação devem verificar como esse perfil aparece nas rotinas, considerando oportunidades de aprendizagem, contextos e informações do informante. Os totais não permitem afirmar quais itens específicos são realizados de forma independente ou qual apoio é necessário.")
    return {"preliminary": True, "overview": overview, "domains": details, "synthesis": synthesis,
            "domain_comparisons": [_pair_text(r, "escore padrão") for r in significant_core],
            "limitations": "Interpretação automática descritiva preliminar, sujeita à revisão profissional. Normas americanas; múltiplas comparações exigem cautela. Equivalentes etários não são idade global de desenvolvimento. Não foram inferidos diagnóstico, comportamento mal adaptativo, itens críticos ou mudança longitudinal."}
