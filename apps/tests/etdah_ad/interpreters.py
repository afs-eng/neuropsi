import re
from typing import Any, Dict, Union

from .calculators import formatar_percentil_e_classificacao
from .config import FACTOR_NAMES, FACTOR_ORDER, MEANS, NORMS


CLINICAL_DIFFICULTY = {"Média Superior", "Superior"}

FACTOR_LABELS = {
    "D": "Fator 1 — Desatenção",
    "I": "Fator 2 — Impulsividade",
    "AE": "Fator 3 — Aspectos Emocionais",
    "AAMA": "Fator 4 — Autorregulação da Atenção, Motivação e Ação",
    "H": "Fator 5 — Hiperatividade",
}

DOMAIN_NAMES = {
    "D": "desatenção",
    "I": "impulsividade",
    "AE": "aspectos emocionais",
    "AAMA": "autorregulação da atenção, motivação e ação",
    "H": "hiperatividade",
}


def get_schooling_level(schooling: Union[int, str]) -> str:
    if isinstance(schooling, str):
        if schooling in ("preschool", "elementary"):
            return "fundamental"
        if schooling in ("middle",):
            return "medio"
        if schooling in ("higher", "higher_incomplete"):
            return "superior"
    if isinstance(schooling, (int, float)):
        if schooling <= 9:
            return "fundamental"
        if schooling <= 12:
            return "medio"
        return "superior"
    return "fundamental"


def interpret_results(raw_scores: Dict[str, int], schooling: Union[int, str]) -> Dict[str, Any]:
    schooling_level = get_schooling_level(schooling)

    results = {}
    for factor in FACTOR_ORDER:
        score = raw_scores.get(factor, 0)
        mean = MEANS[schooling_level][factor]
        percentil_txt, classificacao = formatar_percentil_e_classificacao(
            score, NORMS[schooling_level][factor]
        )

        results[factor] = {
            "name": FACTOR_NAMES[factor],
            "raw_score": score,
            "mean": mean,
            "percentile_text": percentil_txt,
            "classification": classificacao,
        }

    return results


def _first_name(patient_name: str | None) -> str:
    if not patient_name:
        return "o avaliado"
    return patient_name.strip().split()[0] or "o avaliado"


def _is_clinical(classification: str) -> bool:
    return classification in CLINICAL_DIFFICULTY


def _classification_text(result: dict) -> str:
    return str(result.get("classification") or "Média")


def _percentile_text(result: dict) -> str:
    return _single_percentile(result.get("percentile_text") or "-")


def _single_percentile(value) -> str:
    text = str(value or "-").replace("Percentil ", "").replace("percentil ", "").strip()
    numbers = [float(match.replace(",", ".")) for match in re.findall(r"\d+(?:[\.,]\d+)?", text)]
    if not numbers:
        return text or "-"
    number = sum(numbers[:2]) / 2 if len(numbers) >= 2 else numbers[0]
    return str(int(number)) if number.is_integer() else f"{number:.1f}".replace(".", ",")


def _factor_paragraph(factor_key: str, result: dict, name: str) -> str:
    classification = _classification_text(result)
    percentile = _percentile_text(result)
    elevated = _is_clinical(classification)

    if factor_key == "D":
        body = "O achado descreve a frequência relativa de manifestações autorreferidas relacionadas à manutenção da atenção, organização atencional e manejo de demandas que exigem continuidade do foco."
        if elevated:
            body += " O resultado indica elevação dessas manifestações em comparação ao grupo normativo."
    elif factor_key == "I":
        body = "O achado descreve manifestações relacionadas ao controle de respostas imediatas, tomada de decisão e manejo comportamental diante de situações que exigem inibição."
        if elevated:
            body += " Observa-se elevação de indicadores relacionados à impulsividade, sugerindo maior frequência de respostas precipitadas ou dificuldade de inibição comportamental segundo o autorrelato."
    elif factor_key == "AE":
        body = "O fator contempla manifestações emocionais autorreferidas que podem se associar à autorregulação, reatividade afetiva e manejo de demandas cotidianas."
        if elevated:
            body += " O resultado aponta elevação de indicadores emocionais em relação ao grupo normativo, sem que isso estabeleça, isoladamente, condição clínica específica."
    elif factor_key == "AAMA":
        body = "O fator contempla manifestações relacionadas à organização e autorregulação do comportamento dirigido a objetivos, incluindo início, manutenção e conclusão de atividades."
        if elevated:
            body += " O resultado aponta elevação de manifestações autorreferidas relacionadas à autorregulação da atenção, motivação e ação, podendo estar associado a dificuldades para iniciar atividades, manter constância, organizar etapas ou sustentar esforço diante de tarefas prolongadas ou pouco estimulantes."
    elif factor_key == "H":
        body = "O achado reflete a posição do avaliado em relação às manifestações autorreferidas relacionadas à inquietação, atividade motora e necessidade aumentada de movimento."
        if elevated:
            body += " Observa-se elevação normativa nesse domínio, que deve ser analisada separadamente dos indicadores de impulsividade."
    else:
        body = "O resultado global deve ser interpretado a partir da distribuição dos fatores, sem conversão automática para diagnóstico ou apresentação clínica do TDAH."

    if factor_key == "escore_geral":
        return f"Escore Geral: o resultado situou-se no percentil {percentile}, classificado como {classification}. {body}"
    return f"No {FACTOR_LABELS[factor_key]}, o resultado situou-se no percentil {percentile}, classificado como {classification}. {body} O resultado deve ser integrado aos demais dados clínicos e medidas objetivas disponíveis."


def _joined(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " e " + items[-1]


def _elevated_domains(results: Dict[str, Any]) -> list[str]:
    return [
        DOMAIN_NAMES[key]
        for key in FACTOR_ORDER
        if key != "escore_geral" and _is_clinical(results[key].get("classification", ""))
    ]


def _preserved_domains(results: Dict[str, Any]) -> list[str]:
    return [
        DOMAIN_NAMES[key]
        for key in FACTOR_ORDER
        if key != "escore_geral" and not _is_clinical(results[key].get("classification", ""))
    ]


def _integrated_analysis(results: Dict[str, Any]) -> str:
    elevated = _elevated_domains(results)
    preserved = _preserved_domains(results)

    if not elevated:
        return (
            "Em análise integrada, o perfil obtido na E-TDAH-AD não apresentou elevações normativas nos fatores investigados. Esse achado descreve apenas os indicadores autorreferidos captados pelo instrumento e deve ser compreendido à luz dos dados clínicos, observacionais e demais resultados do processo avaliativo."
        )

    synthesis = _joined(elevated)
    preserved_text = _joined(preserved) if preserved else "os demais fatores"

    return (
        f"Em análise integrada, o perfil obtido caracteriza-se principalmente por elevação nos fatores {synthesis}, enquanto {preserved_text} não apresentaram elevação equivalente. Esse padrão sugere concentração das manifestações autorreferidas em determinados domínios, não devendo ser interpretado isoladamente como definição de apresentação clínica do TDAH."
    )


def _hypothesis_text(results: Dict[str, Any]) -> str:
    return (
        "Os resultados constituem indicadores comportamentais derivados do instrumento e devem ser integrados aos demais dados do processo avaliativo. Isoladamente, a E-TDAH-AD não estabelece diagnóstico nem determina a apresentação clínica do TDAH."
    )


def generate_report(raw_scores: Dict[str, int], schooling: Union[int, str], patient_name: str | None = None) -> str:
    results = interpret_results(raw_scores, schooling)
    first_name = _first_name(patient_name)

    paragraphs = [
        "Interpretação e Observações Clínicas: A Escala E-TDAH-AD tem como finalidade identificar manifestações comportamentais e emocionais autorreferidas relacionadas à atenção, impulsividade, regulação emocional, motivação e hiperatividade, fornecendo indicadores quantitativos do funcionamento autorregulatório e atencional no contexto deste instrumento (Benczik, 2005).",
    ]

    for factor in FACTOR_ORDER:
        paragraphs.append(_factor_paragraph(factor, results[factor], first_name))

    paragraphs.append(_integrated_analysis(results))
    paragraphs.append(_hypothesis_text(results))

    return "\n\n".join(paragraphs)
