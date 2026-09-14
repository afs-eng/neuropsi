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

_FACTOR_MEANINGS = {
    "NN": {
        "elevado": "maior responsividade emocional, sensibilidade a estressores e maior expressão de afetividade negativa, conforme os componentes específicos observados nas facetas",
        "reduzido": "menor expressão de responsividade emocional e de características associadas à afetividade negativa, sem que isso represente ausência de dificuldades emocionais",
        "medio": "funcionamento emocional compatível com a faixa esperada para a amostra normativa",
    },
    "EE": {
        "elevado": "maior tendência à expressão interpessoal, exposição social, iniciativa e busca por interações, dependendo da configuração das facetas",
        "reduzido": "menor tendência à exposição interpessoal, ao contato social espontâneo ou ao ritmo expansivo de interação, conforme indicado pelas facetas",
        "medio": "padrão de expressão interpessoal compatível com a referência normativa",
    },
    "SS": {
        "elevado": "maior expressão de cordialidade, cooperação e disposição para confiar ou considerar o outro nas relações interpessoais",
        "reduzido": "menor expressão de disposições cooperativas ou de abertura interpessoal, sem inferir inadequação social, desonestidade ou comportamento antissocial",
        "medio": "funcionamento interpessoal dentro do esperado para a referência normativa",
    },
    "RR": {
        "elevado": "maior orientação para metas, percepção de eficácia, planejamento ou persistência, conforme a combinação das facetas",
        "reduzido": "menor expressão de organização, persistência, prudência ou percepção de eficácia, a depender das facetas disponíveis",
        "medio": "padrão de realização e investimento em objetivos compatível com a faixa normativa",
    },
    "AA": {
        "elevado": "maior abertura intelectual e comportamental para ideias, mudanças, variedade e perspectivas diferentes",
        "reduzido": "menor busca por variedade ou menor flexibilidade diante de ideias, costumes e experiências novas, conforme as facetas avaliadas",
        "medio": "abertura intelectual e comportamental compatível com a amostra normativa",
    },
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
        "reduzido": "menor expressão de passividade, com tendência a maior iniciativa e prontidão para agir",
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


def _interpret_result(result: dict, meanings: dict[str, str]) -> str:
    classification = result.get("classification") or "classificação não informada"
    level = _domain_level(result)
    meaning = meanings.get(level) or meanings.get("medio") or "resultado a ser integrado aos demais achados"
    return f"a classificação {classification} sugere {meaning}."


def _interpret_factor(factor_result: dict) -> str:
    code = factor_result.get("code")
    name = factor_result.get("name") or FACTOR_DEFINITIONS.get(code, {}).get("name") or code
    return f"{name}: No fator {name}, {_interpret_result(factor_result, _FACTOR_MEANINGS.get(code, {}))}"


def _interpret_facet(facet_result: dict) -> str:
    code = facet_result.get("code")
    name = facet_result.get("name") or FACET_DEFINITIONS.get(code, {}).get("name") or code
    classification = facet_result.get("classification") or "classificação não informada"
    level = _domain_level(facet_result)
    meaning = _FACET_MEANINGS.get(code, {}).get(level) or "resultado a ser integrado aos demais achados"
    return f"{name}: O resultado em faixa {classification} sugere {meaning}."


def _relevant_factors(factors: dict) -> list[dict]:
    return [
        result
        for code in FACTOR_DEFINITIONS
        if (result := factors.get(code)) and _domain_level(result) != "medio"
    ]


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


def _build_intrafactor_analysis(factor_code: str, factor_result: dict, facets: dict) -> str:
    available = [facets[code] for code in FACTOR_DEFINITIONS[factor_code]["facets"] if code in facets]
    ranked = [(facet, _classification_rank(facet.get("classification"))) for facet in available]
    ranked = [(facet, rank) for facet, rank in ranked if rank is not None]
    if len(ranked) < 2:
        return ""

    highest, high_rank = max(ranked, key=lambda item: item[1])
    lowest, low_rank = min(ranked, key=lambda item: item[1])
    factor_classification = factor_result.get("classification") or "classificação não informada"

    if high_rank - low_rank <= 1:
        labels = ", ".join(facet.get("name") or facet.get("code") for facet, _ in ranked)
        return (
            f"As facetas desse domínio mostraram padrão relativamente convergente ({labels}), o que torna a leitura global em {factor_classification} mais homogênea."
        )

    return (
        f"Apesar da classificação global em {factor_classification}, o domínio não se expressa de modo uniforme: "
        f"{highest.get('name')} aparece em faixa {highest.get('classification')}, enquanto {lowest.get('name')} se situa em {lowest.get('classification')}. "
        "Esse contraste sugere que componentes distintos do mesmo fator podem se manifestar de maneira diferente no cotidiano."
    )


def _build_synthesis_paragraphs(factors: dict, facets: dict) -> list[str]:
    notes: list[str] = []
    nn = _factor_result(factors, "NN")
    ee = _factor_result(factors, "EE")
    ss = _factor_result(factors, "SS")
    rr = _factor_result(factors, "RR")
    aa = _factor_result(factors, "AA")

    if _domain_level(nn) == "elevado" and _domain_level(rr) == "reduzido":
        notes.append(
            "maior responsividade emocional associada a menor orientação para organização, persistência ou autorregulação de metas"
        )
    if _domain_level(nn) == "elevado" and _domain_level(ee) == "reduzido":
        notes.append(
            "maior sensibilidade emocional combinada a menor exposição interpessoal ou menor busca espontânea por contato social"
        )
    if _domain_level(ss) == "reduzido" and _domain_level(nn) == "elevado":
        notes.append(
            "menor abertura cooperativa ou interpessoal combinada a maior reatividade emocional em contextos relacionais"
        )
    if _domain_level(rr) == "reduzido":
        notes.append(
            "menor expressão de recursos ligados a planejamento, persistência e manutenção de esforço em objetivos"
        )
    if _domain_level(aa) == "reduzido":
        notes.append(
            "maior preferência por previsibilidade e menor busca por variedade intelectual ou comportamental"
        )

    extreme_facets = [
        item.get("name") or code
        for code, item in facets.items()
        if _normalize_classification(item.get("classification")) in {"Muito Baixo", "Muito Superior"}
    ]
    if extreme_facets:
        notes.append(
            "resultados extremos em " + ", ".join(extreme_facets[:4]) + ", que merecem integração clínica proporcional, sem interpretação diagnóstica isolada"
        )

    if not notes:
        return [
            "O conjunto dos resultados sugere funcionamento emocional, interpessoal, motivacional e de abertura à experiência globalmente compatível com a amostra normativa. Nesse contexto, não se observam contrastes fatoriais amplos que modifiquem de modo expressivo a leitura clínica geral do perfil.",
            "A comunicação, a interação social, a orientação para metas e a tomada de decisão devem ser compreendidas a partir da relação entre fatores e facetas, pois a BFP descreve tendências dimensionais e não sintomas. A interpretação ganha maior precisão quando articulada à entrevista clínica, à observação comportamental e aos demais instrumentos utilizados.",
        ]

    if len(notes) == 1:
        joined = notes[0]
    else:
        joined = "; ".join(notes[:-1]) + f"; e {notes[-1]}"
    resources = []
    if _domain_level(ee) in {"medio", "elevado"}:
        resources.append("recursos de comunicação ou envolvimento interpessoal")
    if _domain_level(rr) in {"medio", "elevado"}:
        resources.append("capacidade de organização e investimento em objetivos")
    if _domain_level(ss) in {"medio", "elevado"}:
        resources.append("disposição para convivência cooperativa")
    resources_text = ", ".join(resources) if resources else "recursos que devem ser examinados em conjunto com a história clínica e observacional"

    return [
        f"A integração dos cinco fatores sugere {joined}. Essa combinação ajuda a compreender como aspectos emocionais, interpessoais, motivacionais e de abertura à experiência podem se articular no funcionamento cotidiano.",
        f"Entre os recursos do perfil, destacam-se {resources_text}. Quando há contrastes entre fator global e facetas específicas, a leitura clínica deve privilegiar essa heterogeneidade em vez de reduzir o resultado a uma única característica geral.",
        "As possíveis vulnerabilidades indicadas pela BFP devem ser entendidas como tendências dimensionais de personalidade, sem valor diagnóstico isolado. A interpretação final depende da convergência com entrevista clínica, observação comportamental, história de vida e demais instrumentos utilizados no processo avaliativo.",
    ]


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
        parts = [_interpret_factor(factors[code])]
        intrafactor = _build_intrafactor_analysis(code, factors[code], facets)
        if intrafactor:
            parts.append(intrafactor)
        factor_texts[code] = "\n\n".join(parts)

    facet_texts = {
        code: _interpret_facet(facets[code])
        for code in FACET_DEFINITIONS
        if code in facets and _interpret_facet(facets[code])
    }

    synthesis = _build_synthesis_paragraphs(factors, facets)

    return {
        "summary": _build_summary(name, relevant_factors),
        "sample_label": SAMPLE_LABELS.get(sample, sample.title()),
        "factors": factor_texts,
        "facets": facet_texts,
        "clinical_integration": "\n\n".join(synthesis),
        "synthesis": synthesis,
        "closing": "Os resultados descrevem características dimensionais de personalidade, não estabelecem diagnóstico isoladamente e devem ser interpretados em conjunto com entrevista clínica, observação comportamental, história de vida e demais instrumentos utilizados no processo avaliativo.",
    }


def build_bfp_interpretation(merged_data: dict, patient_name: str | None = None) -> str:
    payload = build_bfp_interpretation_payload(merged_data, patient_name=patient_name)
    sample_label = payload.get("sample_label", "Geral")
    paragraphs = [
        f"A Bateria Fatorial de Personalidade (BFP) foi utilizada para investigar traços dimensionais de personalidade com base no modelo dos Cinco Grandes Fatores. A correção foi realizada com base na amostra {sample_label.lower()}, e a leitura clínica abaixo considera as classificações normativas apresentadas na tabela de resultados.",
        payload["summary"],
    ]

    factor_texts = payload.get("factors", {})
    facet_texts = payload.get("facets", {})
    for code in FACTOR_DEFINITIONS:
        if code not in factor_texts:
            continue
        paragraphs.append(factor_texts[code])
        paragraphs.extend(
            facet_texts[facet_code]
            for facet_code in FACTOR_DEFINITIONS[code]["facets"]
            if facet_code in facet_texts
        )

    paragraphs.append("SÍNTESE INTEGRATIVA")
    paragraphs.extend(payload.get("synthesis") or [payload["clinical_integration"]])
    paragraphs.append(payload["closing"])
    return "\n\n".join(paragraphs)


def get_report_interpretation(merged_data: dict, patient_name: str | None = None) -> str:
    return build_bfp_interpretation(merged_data, patient_name=patient_name)


def build_bfp_report_highlights(merged_data: dict) -> dict:
    """Gera um resumo compacto (highlights) para uso em laudos e legendas de gráficos.

    Usa o payload já normalizado (merged_data) produzido pela pipeline do teste.
    Retorna:
      {
        'summary': <curto parágrafo>,
        'relevant': [ {'code','name','percentile','classification','flag'} ],
        'combinations': [str,...],
        'recommendations': [str,...]
      }
    """
    factors = merged_data.get("factors") or {}
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
            relevant.append(
                {
                    "code": code,
                    "name": mapping.get(code, code),
                    "percentile": pct,
                    "classification": classification,
                    "flag": flag,
                }
            )

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
        # proteção simples; não falhar em caso de dados inesperados
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
