from __future__ import annotations

from .calculators import CLASSIFICATION_ORDER, classify_bfp_domain
from .config import (
    BFP_CLOSING_TEXT,
    FACTOR_DEFINITIONS,
    FACTOR_INTERPRETIVE_NAMES,
    FACET_DEFINITIONS,
    SAMPLE_LABELS,
)


_CLASSIFICATION_ALIASES = {
    "Médio": "Média",
    "Médio Inferior": "Média Inferior",
    "Médio Superior": "Média Superior",
}

_FACET_BRIEF = {
    "N1": "vulnerabilidade emocional",
    "N2": "instabilidade emocional",
    "N3": "passividade ou energia subjetiva",
    "N4": "desânimo, pessimismo ou vitalidade subjetiva",
    "E1": "comunicação e exposição verbal",
    "E2": "valorização da própria imagem e reconhecimento",
    "E3": "ritmo de atividade e iniciativa",
    "E4": "busca por interação social",
    "S1": "cordialidade e consideração interpessoal",
    "S2": "alinhamento a regras e convenções de convivência",
    "S3": "disposição para confiar nas pessoas",
    "R1": "percepção de competência",
    "R2": "ponderação e prudência",
    "R3": "empenho e comprometimento",
    "A1": "curiosidade intelectual",
    "A2": "flexibilidade frente a valores e perspectivas",
    "A3": "busca por novidades",
}

_FACET_MEANINGS = {
    "N1": {
        "elevado": "maior sensibilidade à aceitação interpessoal, à avaliação dos outros e a situações percebidas como emocionalmente ameaçadoras",
        "reduzido": "menor dependência da aprovação externa e menor vulnerabilidade subjetiva diante de críticas ou desaprovação",
        "medio": "expressão de vulnerabilidade dentro do esperado para a referência normativa",
    },
    "N2": {
        "elevado": "maior oscilação emocional, irritabilidade ou reatividade diante de desconfortos e frustrações",
        "reduzido": "menor tendência a variações emocionais intensas e maior estabilidade autorrelatada em situações de tensão",
        "medio": "nível de instabilidade emocional compatível com a faixa normativa",
    },
    "N3": {
        "elevado": "maior passividade subjetiva, menor energia percebida e possível dificuldade para iniciar ou sustentar ações",
        "reduzido": "menor expressão de passividade, com tendência de iniciativa e prontidão para agir mais preservadas",
        "medio": "energia e iniciativa autorrelatadas dentro do esperado",
    },
    "N4": {
        "elevado": "maior expressão de desânimo, pessimismo ou redução subjetiva de vitalidade, exigindo investigação específica caso haja queixas clínicas compatíveis",
        "reduzido": "menor expressão de pessimismo, desesperança ou desânimo no construto avaliado pela BFP",
        "medio": "expressão de características depressivas dimensionais compatível com a faixa normativa, sem equivaler a diagnóstico clínico",
    },
    "E1": {
        "elevado": "maior facilidade para expressão verbal, exposição e compartilhamento de ideias em contextos interpessoais",
        "reduzido": "menor tendência à exposição verbal ou à comunicação espontânea em situações sociais",
        "medio": "comunicação autorrelatada compatível com a referência normativa",
    },
    "E2": {
        "elevado": "maior percepção do próprio valor, busca de reconhecimento, exposição pessoal ou valorização da própria imagem",
        "reduzido": "menor necessidade de destaque, autopromoção ou reconhecimento externo, sem equivaler diretamente a autoestima baixa",
        "medio": "expressão de altivez dentro da faixa normativa",
    },
    "E3": {
        "elevado": "maior ritmo de atividade, iniciativa e energia para envolver-se em tarefas e situações variadas",
        "reduzido": "menor ritmo de atividade, menor iniciativa espontânea ou preferência por envolvimento mais contido em demandas",
        "medio": "dinamismo compatível com a amostra normativa",
    },
    "E4": {
        "elevado": "maior interesse por contato social, atividades em grupo e busca ativa por interações",
        "reduzido": "menor busca por situações sociais intensas ou preferência por contatos mais seletivos e reservados",
        "medio": "interações sociais dentro do esperado para a referência normativa",
    },
    "S1": {
        "elevado": "maior cordialidade, consideração e disponibilidade afetiva nas relações interpessoais",
        "reduzido": "menor expressão de cordialidade ou disponibilidade interpessoal, descrita de forma dimensional e não moralizante",
        "medio": "amabilidade compatível com a faixa normativa",
    },
    "S2": {
        "elevado": "maior consideração por regras, convenções e padrões de convivência contemplados pelo instrumento",
        "reduzido": "menor alinhamento autorrelatado a regras, convenções ou padrões de convivência, sem concluir comportamento antissocial ou ausência de ética",
        "medio": "pró-sociabilidade compatível com a amostra normativa",
    },
    "S3": {
        "elevado": "maior disposição para confiar nas intenções de outras pessoas",
        "reduzido": "menor disposição para confiar nos outros, sem caracterizar desconfiança patológica ou paranoia",
        "medio": "confiança interpessoal dentro do esperado",
    },
    "R1": {
        "elevado": "maior percepção de eficácia pessoal e de capacidade para lidar com demandas e objetivos",
        "reduzido": "menor percepção de eficácia ou menor segurança subjetiva diante de demandas e objetivos",
        "medio": "competência percebida compatível com a referência normativa",
    },
    "R2": {
        "elevado": "maior tendência a avaliar consequências, refletir e ponderar antes de agir",
        "reduzido": "menor tendência à ponderação prévia, com decisões potencialmente mais rápidas ou menos planejadas",
        "medio": "ponderação e prudência compatíveis com a faixa normativa",
    },
    "R3": {
        "elevado": "maior persistência, dedicação e investimento de esforço em atividades dirigidas a objetivos",
        "reduzido": "menor persistência ou investimento de esforço continuado em tarefas e compromissos",
        "medio": "empenho e comprometimento dentro do esperado",
    },
    "A1": {
        "elevado": "maior curiosidade intelectual, interesse por conceitos e disposição para explorar perspectivas de pensamento",
        "reduzido": "menor inclinação para explorar ideias abstratas ou perspectivas conceituais novas",
        "medio": "abertura a ideias compatível com a amostra normativa",
    },
    "A2": {
        "elevado": "maior flexibilidade frente a valores, costumes, normas ou perspectivas, no sentido psicológico avaliado pela BFP",
        "reduzido": "menor relativização de valores, costumes ou perspectivas, sem inferência política, religiosa ou ideológica",
        "medio": "liberalismo psicológico dentro da faixa normativa",
    },
    "A3": {
        "elevado": "maior interesse por variedade, experiências novas, mudanças e situações pouco rotineiras",
        "reduzido": "menor busca por novidades e maior preferência por previsibilidade ou rotinas conhecidas",
        "medio": "busca por novidades compatível com a referência normativa",
    },
}


_FACTOR_DETAILED_INTERPRETATION = {
    "NN": {
        "elevado": (
            "Neuroticismo apresentou classificação elevada, sugerindo maior responsividade emocional, "
            "sensibilidade a estressores e maior expressão de afetividade negativa. "
            "Entre as facetas, destacam-se {facet_highlights}, indicando {facet_meaning}."
            "{intrafactor}"
            " Esse resultado descreve uma dimensão da personalidade e não configura, isoladamente, diagnóstico de transtorno emocional."
        ),
        "medio": (
            "Neuroticismo situou-se na faixa {classification}, indicando funcionamento emocional "
            "compatível com o esperado para a amostra normativa. {facet_observation}"
        ),
        "reduzido": (
            "Neuroticismo apresentou classificação reduzida, sugerindo menor tendência à instabilidade emocional, "
            "menor reatividade a situações de estresse e maior estabilidade afetiva. "
            "Entre as facetas, destacam-se {facet_highlights}, indicando {facet_meaning}."
            "{intrafactor}"
        ),
    },
    "EE": {
        "elevado": (
            "Extroversão apresentou classificação elevada, sugerindo maior tendência à sociabilidade, "
            "iniciativa interpessoal, expressividade comunicativa e busca por interação social. "
            "Entre as facetas, destacam-se {facet_highlights}, indicando {facet_meaning}."
            "{intrafactor}"
        ),
        "medio": (
            "Extroversão situou-se na faixa {classification}, indicando repertório social "
            "compatível com o esperado para a amostra normativa. {facet_observation}"
        ),
        "reduzido": (
            "Extroversão apresentou classificação reduzida, sugerindo tendência a menor busca por interação social, "
            "maior reserva interpessoal e menor expressividade em contextos sociais. "
            "Entre as facetas, destacam-se {facet_highlights}, indicando {facet_meaning}."
            "{intrafactor}"
        ),
    },
    "SS": {
        "elevado": (
            "Socialização apresentou classificação elevada, sugerindo maior tendência a empatia, cooperação, "
            "cordialidade e preocupação com o bem-estar de outras pessoas. "
            "Entre as facetas, destacam-se {facet_highlights}, indicando {facet_meaning}."
            "{intrafactor}"
        ),
        "medio": (
            "Socialização situou-se na faixa {classification}, indicando funcionamento interpessoal "
            "compatível com o esperado para a amostra normativa. {facet_observation}"
        ),
        "reduzido": (
            "Socialização apresentou classificação reduzida, sugerindo menor expressão de disposições cooperativas "
            "ou de abertura interpessoal. "
            "Entre as facetas, destacam-se {facet_highlights}, indicando {facet_meaning}."
            "{intrafactor}"
            " Resultados reduzidos em Pró-Sociabilidade não autorizam afirmar comportamento antissocial, desonestidade ou inadequação moral."
        ),
    },
    "RR": {
        "elevado": (
            "Realização apresentou classificação elevada, sugerindo maior tendência à organização, "
            "persistência, percepção de eficácia e orientação para metas. "
            "Entre as facetas, destacam-se {facet_highlights}, indicando {facet_meaning}."
            "{intrafactor}"
            " Não confundir com inteligência."
        ),
        "medio": (
            "Realização situou-se na faixa {classification}, indicando recursos de organização, "
            "persistência e responsabilidade compatíveis com o esperado para a amostra normativa. {facet_observation}"
        ),
        "reduzido": (
            "Realização apresentou classificação reduzida, sugerindo menor expressão de organização, "
            "persistência, prudência ou percepção de eficácia. "
            "Entre as facetas, destacam-se {facet_highlights}, indicando {facet_meaning}."
            "{intrafactor}"
            " Esse padrão pode impactar demandas que exigem disciplina, constância e gerenciamento de tempo."
        ),
    },
    "AA": {
        "elevado": (
            "Abertura à Experiência apresentou classificação elevada, sugerindo maior curiosidade intelectual, "
            "flexibilidade cognitiva, criatividade e interesse por experiências novas. "
            "Entre as facetas, destacam-se {facet_highlights}, indicando {facet_meaning}."
            "{intrafactor}"
        ),
        "medio": (
            "Abertura à Experiência situou-se na faixa {classification}, indicando equilíbrio entre "
            "interesse por novidades e preferência por situações familiares. {facet_observation}"
        ),
        "reduzido": (
            "Abertura à Experiência apresentou classificação reduzida, sugerindo menor busca por variedade "
            "ou menor flexibilidade diante de ideias, costumes e experiências novas. "
            "Entre as facetas, destacam-se {facet_highlights}, indicando {facet_meaning}."
            "{intrafactor}"
            " Liberalismo não deverá gerar inferências sobre posicionamento político, religioso ou ideológico."
        ),
    },
}


_FACET_HIGHLIGHT_TEMPLATES = {
    "N1": {
        "elevado": "Vulnerabilidade em elevação, indicando maior sensibilidade à aceitação interpessoal e à avaliação dos outros",
        "reduzido": "Vulnerabilidade reduzida, sugerindo menor dependência da aprovação externa",
        "medio": None,
    },
    "N2": {
        "elevado": "Instabilidade Emocional em elevação, indicando maior oscilação afetiva e reatividade diante de frustrações",
        "reduzido": "Instabilidade Emocional reduzida, sugerindo maior estabilidade em situações de tensão",
        "medio": None,
    },
    "N3": {
        "elevado": "Passividade em elevação, sugerindo menor iniciativa subjetiva, redução da disposição e possível dificuldade para iniciar atividades",
        "reduzido": "Passividade reduzida, indicando iniciativa e prontidão para agir mais preservadas",
        "medio": None,
    },
    "N4": {
        "elevado": "Depressão em elevação, indicando maior tendência a vivências de desânimo, pessimismo ou redução da vitalidade subjetiva",
        "reduzido": "Depressão reduzida, sugerindo menor expressão de pessimismo ou desesperança",
        "medio": None,
    },
    "E1": {
        "elevado": "Comunicação em elevação, indicando maior facilidade para expressão verbal e compartilhamento de ideias",
        "reduzido": "Comunicação reduzida, sugerindo menor tendência à exposição verbal espontânea",
        "medio": None,
    },
    "E2": {
        "elevado": "Altivez em elevação, indicando maior percepção do próprio valor e busca de reconhecimento",
        "reduzido": "Altivez reduzida, sugerindo menor necessidade de destaque ou reconhecimento externo",
        "medio": None,
    },
    "E3": {
        "elevado": "Dinamismo em elevação, indicando maior ritmo de atividade e iniciativa",
        "reduzido": "Dinamismo reduzido, sugerindo menor ritmo de atividade ou preferência por envolvimento mais contido",
        "medio": None,
    },
    "E4": {
        "elevado": "Interações Sociais em elevação, indicando maior busca por contato social e participação em situações de grupo",
        "reduzido": "Interações Sociais reduzidas, sugerindo preferência por contatos mais seletivos e reservados",
        "medio": None,
    },
    "S1": {
        "elevado": "Amabilidade em elevação, indicando maior cordialidade, acolhimento e disponibilidade nas relações",
        "reduzido": "Amabilidade reduzida, sugerindo menor disponibilidade interpessoal",
        "medio": None,
    },
    "S2": {
        "elevado": "Pró-Sociabilidade em elevação, indicando maior consideração por regras sociais e convenções de convivência",
        "reduzido": "Pró-Sociabilidade reduzida, sugerindo menor alinhamento a regras ou convenções sociais",
        "medio": None,
    },
    "S3": {
        "elevado": "Confiança em elevação, indicando maior disposição para confiar nas intenções de outras pessoas",
        "reduzido": "Confiança reduzida, sugerindo maior cautela ou reserva interpessoal",
        "medio": None,
    },
    "R1": {
        "elevado": "Competência em elevação, indicando maior percepção de eficácia pessoal e capacidade de realização",
        "reduzido": "Competência reduzida, sugerindo menor percepção de eficácia diante de demandas",
        "medio": None,
    },
    "R2": {
        "elevado": "Ponderação em elevação, indicando maior tendência a avaliar consequências antes de agir",
        "reduzido": "Ponderação reduzida, sugerindo decisões potencialmente mais rápidas ou menos planejadas",
        "medio": None,
    },
    "R3": {
        "elevado": "Empenho em elevação, indicando maior persistência e dedicação em atividades dirigidas a objetivos",
        "reduzido": "Empenho reduzido, sugerindo menor investimento de esforço continuado em tarefas",
        "medio": None,
    },
    "A1": {
        "elevado": "Abertura a Ideias em elevação, indicando maior curiosidade intelectual e interesse por conceitos abstratos",
        "reduzido": "Abertura a Ideias reduzida, sugerindo menor inclinação a explorar perspectivas conceituais novas",
        "medio": None,
    },
    "A2": {
        "elevado": "Liberalismo em elevação, indicando maior flexibilidade frente a valores, costumes e perspectivas",
        "reduzido": "Liberalismo reduzido, sugerindo menor relativização de valores ou perspectivas",
        "medio": None,
    },
    "A3": {
        "elevado": "Busca por Novidades em elevação, indicando maior interesse por experiências novas e situações pouco rotineiras",
        "reduzido": "Busca por Novidades reduzida, sugerindo maior preferência por previsibilidade ou rotinas conhecidas",
        "medio": None,
    },
}


def _first_name(patient_name: str) -> str:
    return (patient_name or "Paciente").strip().split(" ", 1)[0] or "Paciente"


def _factor_key(factor_code: str) -> str:
    return FACTOR_INTERPRETIVE_NAMES[factor_code]


def _factor_result(factors: dict, code: str) -> dict:
    return factors.get(code) or {}


def _normalize_classification(classification: str | None) -> str:
    value = (classification or "").strip()
    return _CLASSIFICATION_ALIASES.get(value, value)


def _classification_rank(classification: str | None) -> int | None:
    value = _normalize_classification(classification)
    try:
        return CLASSIFICATION_ORDER.index(value)
    except ValueError:
        return None


def _domain_level(result: dict) -> str:
    return result.get("domain_level") or classify_bfp_domain(_normalize_classification(result.get("classification")))


def _interpret_facet(facet_result: dict) -> str:
    code = facet_result.get("code") or ""
    name = facet_result.get("name") or FACET_DEFINITIONS.get(code, {}).get("name") or code
    classification = facet_result.get("classification") or "classificação não informada"
    level = _domain_level(facet_result)
    meaning = (_FACET_MEANINGS.get(code) or {}).get(level) or "resultado a ser integrado aos demais achados"
    return f"{name}: O resultado em faixa {classification} sugere {meaning}."


def _relevant_factors(factors: dict) -> list[dict]:
    return [
        result
        for code in FACTOR_DEFINITIONS
        if (result := factors.get(code)) and _domain_level(result) != "medio"
    ]


def _identify_highlights(factors: dict, facets: dict) -> dict:
    """Identifica automaticamente fatores e facetas mais relevantes para o perfil."""
    factor_highlights = []
    for code in FACTOR_DEFINITIONS:
        item = factors.get(code)
        if not item:
            continue
        level = _domain_level(item)
        if level != "medio":
            factor_highlights.append({
                "code": code,
                "name": FACTOR_DEFINITIONS[code]["name"],
                "level": level,
                "classification": item.get("classification"),
                "percentile": item.get("percentile"),
            })

    facet_highlights = []
    for code in FACET_DEFINITIONS:
        item = facets.get(code)
        if not item:
            continue
        level = _domain_level(item)
        if level != "medio":
            facet_highlights.append({
                "code": code,
                "name": item.get("name") or FACET_DEFINITIONS[code]["name"],
                "level": level,
                "classification": item.get("classification"),
                "percentile": item.get("percentile"),
                "factor": FACET_DEFINITIONS[code]["factor"],
            })

    extreme_facets = [
        item for item in facet_highlights
        if _normalize_classification(item.get("classification")) in {"Muito Baixo", "Muito Superior"}
    ]

    return {
        "factors": factor_highlights,
        "facets": facet_highlights,
        "extreme_facets": extreme_facets,
    }


def _build_intrafactor_analysis(factor_code: str, facets: dict) -> str:
    """Detecta discrepâncias clinicamente relevantes entre facetas do mesmo fator."""
    available = [facets[code] for code in FACTOR_DEFINITIONS[factor_code]["facets"] if code in facets]
    ranked = [(facet, _classification_rank(facet.get("classification"))) for facet in available]
    ranked = [(facet, rank) for facet, rank in ranked if rank is not None]
    if len(ranked) < 2:
        return ""

    highest, high_rank = max(ranked, key=lambda item: item[1])
    lowest, low_rank = min(ranked, key=lambda item: item[1])

    if high_rank - low_rank <= 1:
        return ""

    return (
        f" Há contraste relevante entre {highest.get('name')} ({highest.get('classification')}) "
        f"e {lowest.get('name')} ({lowest.get('classification')}), o que pode indicar nuances "
        f"no funcionamento dentro deste fator que merecem atenção integrativa."
    )


def _build_factor_paragraph(factor_code: str, factor_result: dict, facets: dict) -> str:
    """Gera parágrafo individualizado de interpretação para cada fator, seguindo a spec."""
    classification = factor_result.get("classification") or "classificação não informada"
    level = _domain_level(factor_result)
    template = _FACTOR_DETAILED_INTERPRETATION.get(factor_code, {}).get(level)
    if not template:
        return f"Classificação {classification} no fator {FACTOR_DEFINITIONS[factor_code]['name']} a ser integrada aos demais achados."

    available_facets = [facets[code] for code in FACTOR_DEFINITIONS[factor_code]["facets"] if code in facets]
    salient_facets = [facet for facet in available_facets if _domain_level(facet) != "medio"]

    facet_highlights_parts = []
    for facet in salient_facets[:3]:
        code = facet.get("code")
        highlight = _FACET_HIGHLIGHT_TEMPLATES.get(code, {}).get(level)
        if not highlight:
            highlight = _FACET_HIGHLIGHT_TEMPLATES.get(code, {}).get(_domain_level(facet))
        if highlight:
            facet_highlights_parts.append(highlight.lower() if facet_highlights_parts else highlight)

    if facet_highlights_parts:
        facet_highlights = "; ".join(facet_highlights_parts)
        if len(salient_facets) > 1:
            facet_highlights = ", ".join(facet_highlights_parts[:-1]) + f" e {facet_highlights_parts[-1]}"
    else:
        facet_highlights = "resultados dentro da faixa esperada nas facetas componentes"

    facet_meaning_parts = []
    for facet in salient_facets[:2]:
        code = facet.get("code")
        meaning = _FACET_MEANINGS.get(code, {}).get(_domain_level(facet))
        if meaning:
            facet_meaning_parts.append(meaning)
    facet_meaning = "; ".join(facet_meaning_parts) if facet_meaning_parts else "padrão geral compatível com o esperado"

    intrafactor = _build_intrafactor_analysis(factor_code, facets)

    if level == "medio":
        facet_observation_parts = []
        for facet in available_facets:
            code = facet.get("code")
            meaning = _FACET_MEANINGS.get(code, {}).get(_domain_level(facet))
            if meaning and _domain_level(facet) != "medio":
                facet_observation_parts.append(
                    f"{facet.get('name')} ({facet.get('classification')}) sugere {meaning}"
                )
        if facet_observation_parts:
            facet_observation = "Destaca-se " + "; ".join(facet_observation_parts[:2]) + "."
        else:
            facet_observation = "As facetas componentes apresentaram resultados coerentes com a classificação global."
        return template.format(classification=classification, facet_observation=facet_observation)

    return template.format(
        classification=classification,
        facet_highlights=facet_highlights,
        facet_meaning=facet_meaning,
        intrafactor=intrafactor,
    )


def _build_synthesis_paragraphs(factors: dict, facets: dict, patient_name: str | None = None) -> list[str]:
    """Gera síntese integrativa individualizada seguindo a spec: configuração global,
    fatores principais, facetas relevantes, contrastes, recursos, vulnerabilidades e ressalva."""
    name = _first_name(patient_name or "Paciente")
    highlights = _identify_highlights(factors, facets)

    elev_factors = [f for f in highlights["factors"] if f["level"] == "elevado"]
    reduz_factors = [f for f in highlights["factors"] if f["level"] == "reduzido"]

    config_parts = []
    if elev_factors:
        elev_names = [f["name"] for f in elev_factors]
        if len(elev_names) == 1:
            config_parts.append(f"elevação em {elev_names[0]}")
        else:
            config_parts.append("elevação em " + ", ".join(elev_names[:-1]) + f" e {elev_names[-1]}")
    if reduz_factors:
        reduz_names = [f["name"] for f in reduz_factors]
        if len(reduz_names) == 1:
            config_parts.append(f"redução em {reduz_names[0]}")
        else:
            config_parts.append("redução em " + ", ".join(reduz_names[:-1]) + f" e {reduz_names[-1]}")

    if not config_parts:
        config_description = (
            f"Os resultados indicam um perfil globalmente situado em faixas médias, "
            f"compatível com a amostra normativa nos cinco fatores avaliados."
        )
    else:
        config_description = f"Os resultados indicam um perfil caracterizado por {', '.join(config_parts)} entre os fatores principais."

    resources = []
    vulnerabilities = []
    for f in highlights["factors"]:
        if f["level"] == "elevado":
            if f["code"] in ("EE", "SS", "RR", "AA"):
                resources.append(f"maior expressão de {f['name'].lower()}")
        elif f["level"] == "reduzido":
            if f["code"] in ("NN",):
                resources.append("menor reatividade emocional")
            elif f["code"] in ("RR",):
                vulnerabilities.append("menor orientação para metas e organização")
            elif f["code"] in ("NN",):
                vulnerabilities.append("maior vulnerabilidade emocional")

    for f in highlights["factors"]:
        if f["level"] == "elevado" and f["code"] == "NN":
            vulnerabilities.append("maior vulnerabilidade emocional e reatividade a estressores")
        elif f["level"] == "reduzido" and f["code"] == "RR":
            vulnerabilities.append("menor orientação para metas e organização")

    salient_facets = [f for f in highlights["facets"] if _normalize_classification(f.get("classification")) in {"Muito Baixo", "Muito Superior"}]

    contrasts = []
    nn_level = _domain_level(_factor_result(factors, "NN"))
    ee_level = _domain_level(_factor_result(factors, "EE"))
    ss_level = _domain_level(_factor_result(factors, "SS"))
    rr_level = _domain_level(_factor_result(factors, "RR"))
    aa_level = _domain_level(_factor_result(factors, "AA"))

    if nn_level == "elevado" and rr_level == "reduzido":
        contrasts.append("a elevação em Neuroticismo combinada à redução em Realização pode impactar a organização e manutenção de metas")
    if nn_level == "elevado" and ee_level == "reduzido":
        contrasts.append("o Neuroticismo elevado com Extroversão reduzida pode sugerir vivência interna de sofrimento com menor busca de apoio social")
    if ss_level == "reduzido" and nn_level == "elevado":
        contrasts.append("a Socialização reduzida combinada ao Neuroticismo elevado pode aumentar a vulnerabilidade a conflitos interpessoais")

    parts = [config_description]

    if resources:
        unique_resources = list(dict.fromkeys(resources))[:3]
        parts.append("Como recursos, destacam-se " + ", ".join(unique_resources) + ".")

    if contrasts:
        parts.append("Em termos de contrastes, " + "; ".join(contrasts[:2]) + ".")

    if salient_facets:
        extreme_names = [f["name"] for f in salient_facets[:3]]
        parts.append(
            "Resultados extremos foram observados em " + ", ".join(extreme_names) + ", "
            "devendo receber atenção especial na integração clínica."
        )

    if vulnerabilities:
        unique_vuln = list(dict.fromkeys(vulnerabilities))[:2]
        parts.append("Como vulnerabilidades, destacam-se " + ", ".join(unique_vuln) + ".")

    parts.append(
        "Os achados devem ser compreendidos de maneira integrada às informações clínicas e aos demais "
        "procedimentos de avaliação, não constituindo, isoladamente, indicadores diagnósticos."
    )

    return [" ".join(parts)]


def build_bfp_interpretation_payload(merged_data: dict, patient_name: str | None = None) -> dict:
    name = _first_name(patient_name or "Paciente")
    sample = merged_data.get("sample", "geral")
    factors = merged_data.get("factors", {})
    facets = merged_data.get("facets", {})

    if not factors or not facets:
        return {
            "summary": "Sem resultados suficientes para interpretação do BFP.",
            "factors": {},
            "facets": {},
            "clinical_integration": BFP_CLOSING_TEXT,
            "synthesis": [],
            "closing": "",
        }

    relevant_factors = _relevant_factors(factors)

    factor_texts = {}
    for code in FACTOR_DEFINITIONS:
        if code not in factors:
            continue
        factor_texts[code] = _build_factor_paragraph(code, factors[code], facets)

    facet_texts = {
        code: _interpret_facet(facets[code])
        for code in FACET_DEFINITIONS
        if code in facets and _interpret_facet(facets[code])
    }

    synthesis = _build_synthesis_paragraphs(factors, facets, patient_name=patient_name)

    return {
        "summary": _build_summary(name, relevant_factors),
        "sample_label": SAMPLE_LABELS.get(sample, sample.title()),
        "factors": factor_texts,
        "facets": facet_texts,
        "clinical_integration": "\n\n".join(synthesis),
        "synthesis": synthesis,
        "closing": (
            "Os resultados descrevem características dimensionais de personalidade, "
            "não estabelecem diagnóstico isoladamente e devem ser interpretados em conjunto "
            "com entrevista clínica, observação comportamental, história de vida e demais "
            "instrumentos utilizados no processo avaliativo."
        ),
    }


def _build_summary(name: str, relevant_factors: list[dict]) -> str:
    if not relevant_factors:
        return (
            f"{name} apresentou resultados globalmente situados em faixas médias nos fatores principais do BFP, "
            "com perfil geral compatível com a amostra normativa nos domínios avaliados."
        )

    parts = []
    for factor in relevant_factors:
        level = _domain_level(factor)
        direction = "elevação" if level == "elevado" else "redução"
        parts.append(f"{direction} em {factor['name']}")

    if len(parts) == 1:
        joined = parts[0]
    else:
        joined = ", ".join(parts[:-1]) + f" e {parts[-1]}"

    return f"{name} apresentou {joined} entre os fatores principais do BFP. Esses achados descrevem tendências dimensionais de personalidade e devem ser compreendidos em conjunto com as facetas de cada domínio."


def build_bfp_interpretation(merged_data: dict, patient_name: str | None = None) -> str:
    payload = build_bfp_interpretation_payload(merged_data, patient_name=patient_name)
    paragraphs = ["INTERPRETAÇÃO DOS RESULTADOS"]

    factor_texts = payload.get("factors", {})
    for code in FACTOR_DEFINITIONS:
        if code not in factor_texts:
            continue
        paragraphs.append(FACTOR_DEFINITIONS[code]["name"])
        paragraphs.append(factor_texts[code])

    paragraphs.append("SÍNTESE INTEGRATIVA")
    paragraphs.extend(payload.get("synthesis") or [payload["clinical_integration"]])
    paragraphs.append(payload["closing"])
    return "\n\n".join(paragraphs)


def get_report_interpretation(merged_data: dict, patient_name: str | None = None) -> str:
    return build_bfp_interpretation(merged_data, patient_name=patient_name)


def build_bfp_report_highlights(merged_data: dict) -> dict:
    """Gera um resumo compacto (highlights) para uso em laudos e legendas de gráficos."""
    factors = merged_data.get("factors") or {}
    facets = merged_data.get("facets") or {}
    mapping = {code: _factor_key(code) for code in FACTOR_DEFINITIONS}

    relevant = []
    for code in FACTOR_DEFINITIONS:
        item = factors.get(code)
        if not item:
            continue
        pct = float(item.get("percentile") or 0)
        classification = item.get("classification") or "-"
        flag = None
        if pct >= 97.5 or pct < 2.5:
            flag = "extremo"
        elif pct >= 85 or pct < 15:
            flag = "relevante"
        if flag:
            relevant.append({
                "code": code,
                "name": mapping.get(code, code),
                "percentile": pct,
                "classification": classification,
                "flag": flag,
            })

    elev = [r for r in relevant if r["percentile"] >= 85]
    reduz = [r for r in relevant if r["percentile"] < 15]

    parts = []
    if elev:
        parts.append("elevação em " + ", ".join([f"{r['name']} ({r['classification']})" for r in elev]))
    if reduz:
        parts.append("redução em " + ", ".join([f"{r['name']} ({r['classification']})" for r in reduz]))

    summary = "Perfil sem alterações clinicamente salientes nos fatores principais." if not parts else ("; ".join(parts) + ".")

    combinations = []
    nn = factors.get("NN") or {}
    ee = factors.get("EE") or {}
    rr = factors.get("RR") or {}
    ss = factors.get("SS") or {}

    try:
        if float(nn.get("percentile") or 0) >= 85 and float(rr.get("percentile") or 100) < 30:
            combinations.append(
                "Neuroticismo elevado associado a Realização reduzida pode indicar impacto emocional sobre organização e manutenção de metas."
            )
        if float(nn.get("percentile") or 0) >= 85 and float(ee.get("percentile") or 100) < 30:
            combinations.append(
                "Neuroticismo elevado com Extroversão reduzida pode sugerir vivência interna de sofrimento com menor procura de apoio social."
            )
        if float(ss.get("percentile") or 100) < 30 and float(nn.get("percentile") or 0) >= 85:
            combinations.append(
                "Socialização reduzida combinada à elevação em Neuroticismo pode aumentar a vulnerabilidade a conflitos interpessoais."
            )
    except Exception:
        pass

    recommendations = [
        "Integrar estes achados à anamnese e à observação clínica.",
        "Confrontar com instrumentos de humor/ansiedade quando aplicável.",
    ]

    return {
        "summary": summary,
        "relevant": relevant,
        "combinations": combinations,
        "recommendations": recommendations,
    }
