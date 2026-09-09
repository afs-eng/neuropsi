import re
from typing import Any, Dict


CLINICAL_DIFFICULTY = {"Média Superior", "Superior"}

FACTOR_ORDER = ["fator_1", "fator_2", "fator_3", "fator_4", "escore_geral"]

FACTOR_LABELS = {
    "fator_1": "Fator 1 — Regulação Emocional",
    "fator_2": "Fator 2 — Hiperatividade/Impulsividade",
    "fator_3": "Fator 3 — Comportamento Adaptativo",
    "fator_4": "Fator 4 — Atenção",
    "escore_geral": "Escore Geral",
}

DOMAIN_NAMES = {
    "fator_1": "regulação emocional",
    "fator_2": "hiperatividade/impulsividade",
    "fator_3": "comportamento adaptativo",
    "fator_4": "atenção",
}


def get_faixa_etaria(idade: int) -> str:
    if 2 <= idade <= 5:
        return "2_5"
    if 6 <= idade <= 9:
        return "6_9"
    if 10 <= idade <= 13:
        return "10_13"
    if 14 <= idade <= 17:
        return "14_17"
    raise ValueError("Idade fora da faixa normativa do E-TDAH-PAIS (2 a 17 anos).")


def interpret_results(raw_scores: Dict[str, int], age: int, sex: str) -> Dict[str, Any]:
    from .config import FACTOR_NAMES, NORMS
    from .calculators import (
        classificar_percentil,
        classify_guilmette,
        manual_percentile_from_raw,
        percentile_guilmette,
        points_scaled,
    )

    faixa = get_faixa_etaria(age)
    sex_key = "feminino" if sex.upper() == "F" else "masculino"
    norms = NORMS[sex_key][faixa]

    results = {}
    metric_keys = ["fator_1", "fator_2", "fator_3", "fator_4", "escore_geral"]

    for metric_key in metric_keys:
        raw_score = raw_scores.get(metric_key, 0)

        pct_manual_num, pct_manual_text = manual_percentile_from_raw(
            raw_score, norms["scores"][metric_key]
        )
        class_manual = classificar_percentil(pct_manual_num)

        mean = norms["stats"][metric_key]["media"]
        std = norms["stats"][metric_key]["dp"]
        z = 0.0 if std == 0 else (raw_score - mean) / std
        pp = points_scaled(z)
        pct_g = percentile_guilmette(z)
        class_g = classify_guilmette(pct_g)

        results[metric_key] = {
            "name": FACTOR_NAMES.get(metric_key, metric_key),
            "raw_score": raw_score,
            "mean": mean,
            "std": std,
            "z_score": z,
            "points_scaled": pp,
            "percentile_text": pct_manual_text,
            "percentile_guilmette": pct_g,
            "classification": class_manual,
            "classification_guilmette": class_g,
        }

    return results


def _first_name(patient_name: str | None) -> str:
    if not patient_name:
        return "a criança"
    return patient_name.strip().split()[0] or "a criança"


def _is_clinical(classification: str) -> bool:
    return classification in CLINICAL_DIFFICULTY


def _classification_text(result: dict) -> str:
    return str(result.get("classification") or "Média")


def _percentile_text(result: dict) -> str:
    text = str(result.get("percentile_text") or "")
    return _single_percentile(text)


def _single_percentile(value) -> str:
    text = str(value or "-").replace("Percentil ", "").replace("percentil ", "").strip()
    numbers = [float(match.replace(",", ".")) for match in re.findall(r"\d+(?:[\.,]\d+)?", text)]
    if not numbers:
        return text or "-"
    if len(numbers) >= 2:
        number = sum(numbers[:2]) / 2
    else:
        number = numbers[0]
    return str(int(number)) if number.is_integer() else f"{number:.1f}".replace(".", ",")


def _factor_paragraph(factor_key: str, result: dict) -> str:
    classification = _classification_text(result)
    percentile = _percentile_text(result)
    elevated = _is_clinical(classification)

    if factor_key == "fator_1":
        body = "O achado descreve manifestações observadas pelos responsáveis relacionadas à modulação emocional, reatividade afetiva e manejo de frustrações no cotidiano."
        if elevated:
            body += " Observa-se elevação de indicadores relacionados à regulação emocional em comparação ao grupo normativo."
    elif factor_key == "fator_2":
        body = "O fator reúne manifestações percebidas pelos responsáveis relativas à inquietação, atividade motora, respostas imediatas e manejo comportamental diante de situações que exigem inibição."
        if elevated:
            body += " O resultado aponta elevação de indicadores relacionados à hiperatividade/impulsividade segundo a percepção dos responsáveis."
    elif factor_key == "fator_3":
        body = "O fator contempla indicadores de comportamento adaptativo observados no contexto familiar e cotidiano, conforme a direção normativa da escala."
        if elevated:
            body += " O resultado indica elevação de manifestações nesse domínio em relação ao grupo normativo, devendo ser interpretado com atenção à direção dos itens e ao contexto informante."
    elif factor_key == "fator_4":
        body = "O achado descreve manifestações relacionadas à manutenção do foco, organização atencional, persistência em tarefas e resistência à distração segundo a percepção dos responsáveis."
        if elevated:
            body += " O resultado indica elevação de indicadores relacionados à atenção em comparação ao grupo normativo."
    else:
        body = "O escore geral sintetiza os indicadores comportamentais informados pelos responsáveis, mas não deve ser convertido automaticamente em diagnóstico, prejuízo funcional ou apresentação clínica do TDAH."

    prefix = FACTOR_LABELS[factor_key]
    if factor_key == "escore_geral":
        return f"{prefix}: o resultado situou-se no percentil {percentile}, classificado como {classification}. {body}"
    return f"No {prefix}, o resultado situou-se no percentil {percentile}, classificado como {classification}. {body} O resultado deve ser integrado à anamnese, observação clínica, funcionamento em diferentes contextos e demais instrumentos utilizados."


def _elevated_domains(results: Dict[str, Any]) -> list[str]:
    return [
        DOMAIN_NAMES[key]
        for key in ["fator_1", "fator_2", "fator_3", "fator_4"]
        if _is_clinical(results[key].get("classification", ""))
    ]


def _joined(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " e " + items[-1]


def _analysis_text(name: str, results: Dict[str, Any]) -> str:
    elevated = _elevated_domains(results)

    if not elevated:
        return (
            "Em análise clínica, o perfil obtido no E-TDAH-PAIS não apresentou elevações normativas nos fatores investigados. Esse achado descreve indicadores comportamentais informados pelos responsáveis e deve ser compreendido de forma integrada aos dados cognitivos, atencionais, executivos, emocionais, comportamentais e contextuais obtidos ao longo da avaliação."
        )

    joined = _joined(elevated)
    remaining = [DOMAIN_NAMES[key] for key in ["fator_1", "fator_2", "fator_3", "fator_4"] if DOMAIN_NAMES[key] not in elevated]
    remaining_text = _joined(remaining) if remaining else "os demais domínios"

    return (
        f"Em análise clínica, o perfil obtido caracteriza-se principalmente por elevação nos fatores {joined}, enquanto {remaining_text} não apresentaram elevação equivalente. Esse padrão sugere concentração dos indicadores comportamentais em determinados domínios, não devendo ser interpretado isoladamente como definição diagnóstica ou apresentação clínica do TDAH."
    )


def _hypothesis_text(results: Dict[str, Any]) -> str:
    return "Os resultados constituem indicadores comportamentais derivados do instrumento e devem ser integrados aos demais dados do processo avaliativo. Isoladamente, a E-TDAH-PAIS não estabelece diagnóstico nem determina a apresentação clínica do TDAH."


def generate_report(raw_scores: Dict[str, int], age: int, sex: str, patient_name: str | None = None) -> str:
    results = interpret_results(raw_scores, age, sex)
    first_name = _first_name(patient_name)

    paragraphs = [
        f"Interpretação e Observações Clínicas: A avaliação comportamental de {first_name} por meio da Escala E-TDAH-PAIS permitiu investigar indicadores relacionados à regulação emocional, hiperatividade/impulsividade, comportamento adaptativo e atenção a partir da percepção dos responsáveis. Os resultados descrevem manifestações observadas no contexto deste instrumento e devem ser integrados às demais fontes do processo avaliativo.",
    ]

    for key in FACTOR_ORDER:
        paragraphs.append(_factor_paragraph(key, results[key]))

    paragraphs.append(_analysis_text(first_name, results))
    hypothesis = _hypothesis_text(results)
    if hypothesis:
        paragraphs.append(hypothesis)

    return "\n\n".join(paragraphs)
