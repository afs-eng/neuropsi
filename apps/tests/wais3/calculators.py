from __future__ import annotations

import csv
from datetime import datetime, timezone
import math
from pathlib import Path
from typing import Any

from .constants import (
    WAIS3_ALL_SUBTESTS,
    WAIS3_EXECUTION_SUBTESTS,
    WAIS3_INDEXES,
    WAIS3_INDEX_CODES,
    WAIS3_NAME,
    WAIS3_SUBTEST_CODES,
    WAIS3_SUBTEST_ORDER,
    WAIS3_VERBAL_SUBTESTS,
    classify_composite_score,
    classify_scaled_score,
)
from .loaders import WAIS3NormLoader
from .norm_utils import resolve_age_range


# ------------------------------------------------------------------
# Análise complementar (Tabelas B.1 a B.7)
# ------------------------------------------------------------------

B1_PAIR_SPECS = [
    ("qi_verbal", "qi_execucao", "qiv_qie", "verbal_iq_vs_performance_iq"),
    ("compreensao_verbal", "organizacao_perceptual", "icv_iop", "comprehension_vs_perceptual"),
    ("compreensao_verbal", "memoria_operacional", "icv_imo", "comprehension_vs_working_memory"),
    ("organizacao_perceptual", "velocidade_processamento", "iop_ivp", "perceptual_vs_processing_speed"),
    ("compreensao_verbal", "velocidade_processamento", "icv_ivp", "comprehension_vs_processing_speed"),
    ("organizacao_perceptual", "memoria_operacional", "iop_imo", "perceptual_vs_working_memory"),
    ("memoria_operacional", "velocidade_processamento", "imo_ivp", "working_memory_vs_processing_speed"),
]

B3_ROW_LABELS = {
    "vocabulario": "Vocabulário",
    "semelhancas": "Semelhanças",
    "aritmetica": "Aritmética",
    "digitos": "Dígitos",
    "informacao": "Informação",
    "compreensao": "Compreensão",
    "sequencia_numeros_letras": "Seq. N. e Letras",
    "completar_figuras": "Comp. Figuras",
    "codigos": "Códigos",
    "cubos": "Cubos",
    "raciocinio_matricial": "Rac. Matricial",
    "arranjo_figuras": "Ar. de Figuras",
    "procurar_simbolos": "Proc. Símbolos",
    "armar_objetos": "Armar Objetos",
}

def _load_b1(loader: WAIS3NormLoader) -> dict[str, Any]:
    """Carrega Tabela B.1: valores críticos para discrepâncias entre índices."""
    rows = loader.get_supplementary_tables().get("b1") or []
    if not rows:
        return {}
    result = {}
    for row in rows:
        age = str(row.get("col_0") or "").strip()
        if not age or not age[0].isdigit():
            continue
        nivel = str(row.get("col_1") or "").strip()
        result[f"{age}_{nivel}"] = {
            "age": age,
            "nivel": nivel,
            "qiv_qie": _norm_float(row.get("col_2")),
            "icv_iop": _norm_float(row.get("col_3")),
            "icv_imo": _norm_float(row.get("col_4")),
            "iop_ivp": _norm_float(row.get("col_5")),
            "icv_ivp": _norm_float(row.get("col_6")),
            "iop_imo": _norm_float(row.get("col_7")),
            "imo_ivp": _norm_float(row.get("col_8")),
        }
    return result


def _load_b3(loader: WAIS3NormLoader) -> dict[str, Any]:
    """Carrega Tabela B.3: diferenças entre subteste e média."""
    rows = loader.get_supplementary_tables().get("b3") or []
    if not rows:
        return {}
    result: dict[str, dict[str, Any]] = {}
    section = None
    for row in rows:
        first_col = str(row.get("col_0") or "").strip()
        if first_col.startswith("Subtestes") and "Média dos" in str(row.get("col_1") or ""):
            header = str(row.get("col_1") or "")
            if "Média dos 6 Subtestes Verbais" in header:
                section = "verbal_6"
            elif "Média dos 5 Subtestes de Execução" in header:
                section = "exec_5"
            elif "Média dos 7 Subtestes Verbais" in header:
                section = "verbal_7"
            elif "Média dos 7 Subtestes de Execução" in header:
                section = "exec_7"
            continue
        if first_col in {"", "Subtestes"} or first_col.startswith("Tabela B.3") or section is None:
            continue
        entry = {
            "critical_015": _norm_float(row.get("col_1")),
            "critical_005": _norm_float(row.get("col_2")),
            "base_rates": {
                1: _norm_float(row.get("col_3")),
                2: _norm_float(row.get("col_4")),
                5: _norm_float(row.get("col_5")),
                10: _norm_float(row.get("col_6")),
                25: _norm_float(row.get("col_7")),
            },
        }
        result.setdefault(first_col.lower(), {})[section] = entry
    return result


def _load_b2(loader: WAIS3NormLoader) -> dict[int, dict[str, float | None]]:
    rows = loader.get_supplementary_tables().get("b2") or []
    if not rows:
        return {}
    result = {}
    for row in rows:
        size = str(row.get("col_0") or "").strip().replace("≥", "")
        if not size.isdigit():
            continue
        result[int(size)] = {
            "qiv_qie": _norm_float(row.get("col_1")),
            "icv_iop": _norm_float(row.get("col_2")),
            "icv_imo": _norm_float(row.get("col_3")),
            "iop_ivp": _norm_float(row.get("col_4")),
            "icv_ivp": _norm_float(row.get("col_5")),
            "iop_imo": _norm_float(row.get("col_6")),
            "imo_ivp": _norm_float(row.get("col_7")),
        }
    return result


def _load_b6(loader: WAIS3NormLoader) -> dict[str, Any]:
    """Carrega Tabela B.6: Dígitos Ordem Direta e Inversa."""
    rows = loader.get_supplementary_tables().get("b6") or []
    if not rows:
        return {}
    result = {}
    for row in rows:
        maximo = str(row.get("col_0") or "").strip()
        if not maximo or not maximo.isdigit():
            continue
        result[int(maximo)] = {
            "direta": {age: _norm_float(row.get(f"col_{i}")) for i, age in enumerate([16, 18, 20, 30, 40, 50, 60, 65, "todas"], start=1)},
            "inversa": {age: _norm_float(row.get(f"col_{i}")) for i, age in enumerate([16, 18, 20, 30, 40, 50, 60, 65, "todas"], start=2)},
        }
    return result


def _norm_float(val: Any) -> float | None:
    """Converte string '2,4' → 2.4 ou None."""
    if val is None:
        return None
    s = str(val).strip().replace(",", ".")
    if s in ("", "–", "-", "nan", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _map_faixa_b(faixa: str) -> str:
    """Mapeia 'idade_30-39' → chave B.1 '30-39'."""
    return faixa.replace("idade_", "")


def _map_faixa_b6(faixa: str) -> int:
    """Mapeia faixa etaria para coluna B.6: retorna índice da coluna."""
    mapping = {
        "idade_16-17": 1,
        "idade_18-19": 3,
        "idade_20-29": 5,
        "idade_30-39": 7,
        "idade_40-49": 9,
        "idade_50-59": 11,
        "idade_60-64": 13,
        "idade_65-89": 15,
    }
    return mapping.get(faixa, 7)  # default 30-39


def _b6_columns_for_age(age_range_key: str) -> tuple[str, str]:
    mapping = {
        "idade_16-17": ("col_1", "col_2"),
        "idade_18-19": ("col_3", "col_4"),
        "idade_20-29": ("col_5", "col_6"),
        "idade_30-39": ("col_7", "col_8"),
        "idade_40-49": ("col_9", "col_10"),
        "idade_50-59": ("col_11", "col_12"),
        "idade_60-64": ("col_13", "col_14"),
        "idade_65-89": ("col_15", "col_16"),
    }
    return mapping.get(age_range_key, ("col_7", "col_8"))


def _b7_column_for_age(age_range_key: str) -> str:
    mapping = {
        "idade_16-17": "col_1",
        "idade_18-19": "col_2",
        "idade_20-29": "col_3",
        "idade_30-39": "col_4",
        "idade_40-49": "col_5",
        "idade_50-59": "col_6",
        "idade_60-64": "col_7",
        "idade_65-89": "col_8",
    }
    return mapping.get(age_range_key, "col_4")


def _lookup_percentile_from_csv_rows(rows: list[dict[str, str]], raw_value: int, value_column: str) -> float | None:
    for row in rows:
        key = str(row.get("col_0") or "").strip()
        if not key or key in {"Média", "DP", "Mediana"}:
            continue
        try:
            row_value = int(float(key))
        except ValueError:
            continue
        if row_value == raw_value:
            return _norm_float(row.get(value_column))
    return None


def _row_value(rows: list[dict[str, str]], row_key: str, value_column: str) -> float | None:
    for row in rows:
        key = str(row.get("col_0") or "").strip()
        if key == row_key:
            return _norm_float(row.get(value_column))
    return None


def _build_process_result(raw_value: int, mean: float | None, sd: float | None, percentile: float | None, *, reverse_z: bool = False) -> dict:
    z_score = None
    if mean is not None and sd not in (None, 0):
        z_score = ((mean - raw_value) / sd) if reverse_z else ((raw_value - mean) / sd)

    return {
        "raw_score": raw_value,
        "cumulative_frequency": percentile,
        "mean": mean,
        "sd": sd,
        "z_score": round(z_score, 3) if z_score is not None else None,
        "scaled_score": round((z_score * 3) + 10, 1) if z_score is not None else None,
        "percentile": round(_xlfn_norm_s_dist(z_score) * 100, 1) if z_score is not None else None,
        "classification": _classify_z_score(z_score),
    }


def _resolve_b3_section(domain: str, applied_count: int) -> str:
    if domain == "verbal":
        return "verbal_7" if applied_count > 6 else "verbal_6"
    return "exec_7" if applied_count > 5 else "exec_5"


def _lookup_b3_base_rate(base_rates: dict[int, float | None], difference: float) -> float | None:
    absolute_difference = abs(difference)
    for percentage in (1, 2, 5, 10, 25):
        critical_value = base_rates.get(percentage)
        if critical_value is not None and absolute_difference >= critical_value:
            return float(percentage)
    return None


def _lookup_b2_base_rate(b2_data: dict[int, dict[str, float | None]], column: str, difference: float) -> float | None:
    if not b2_data:
        return None
    absolute_difference = int(abs(difference))
    for threshold in sorted(b2_data.keys(), reverse=True):
        if absolute_difference >= threshold:
            return b2_data[threshold].get(column)
    return b2_data.get(0, {}).get(column)


def _resolve_significance_level(difference: float, critical_005: float | None, critical_015: float | None) -> str | None:
    absolute_difference = abs(difference)
    if critical_005 is not None and absolute_difference >= critical_005:
        return "0,05"
    if critical_015 is not None and absolute_difference >= critical_015:
        return "0,15"
    return None


def _format_norm_value(value: float | None) -> str:
    if value is None:
        return "N/D"
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _build_below_threshold_reason(difference: float, critical_005: float | None, critical_015: float | None) -> str:
    threshold_parts = []
    if critical_015 is not None:
        threshold_parts.append(f"0,15 >= {_format_norm_value(critical_015)}")
    if critical_005 is not None:
        threshold_parts.append(f"0,05 >= {_format_norm_value(critical_005)}")
    thresholds = "; ".join(threshold_parts) if threshold_parts else "sem cortes normativos carregados"
    return f"Diferença de {_format_norm_value(abs(difference))} abaixo dos cortes normativos ({thresholds})."


def _describe_discrepancy_direction(label_1: str, score_1: float, label_2: str, score_2: float) -> str:
    if score_1 > score_2:
        return f"{label_1} maior que {label_2}"
    if score_2 > score_1:
        return f"{label_2} maior que {label_1}"
    return "Sem diferença entre os escores"


def _lookup_strength_weakness_norm(*, label: str, section: str, section_data: dict[str, Any], difference: float) -> dict[str, Any]:
    critical_005 = section_data.get("critical_005")
    critical_015 = section_data.get("critical_015")
    significance_level = _resolve_significance_level(difference, critical_005, critical_015)
    is_significant = significance_level is not None

    if critical_005 is None and critical_015 is None:
        return {
            "critical_value": critical_005,
            "critical_value_015": critical_015,
            "is_significant": False,
            "significance_level": None,
            "type": None,
            "base_rate": None,
            "status": "missing_norm",
            "reason": f"Norma B.3 indisponível para {label} na seção {section}.",
            "norm_source": "B.3",
        }

    if not is_significant:
        return {
            "critical_value": critical_005,
            "critical_value_015": critical_015,
            "is_significant": False,
            "significance_level": None,
            "type": None,
            "base_rate": None,
            "status": "below_threshold",
            "reason": _build_below_threshold_reason(difference, critical_005, critical_015),
            "norm_source": "B.3",
        }

    return {
        "critical_value": critical_005,
        "critical_value_015": critical_015,
        "is_significant": True,
        "significance_level": significance_level,
        "type": "facilidade" if difference > 0 else "dificuldade" if difference < 0 else None,
        "base_rate": _lookup_b3_base_rate(section_data.get("base_rates", {}), difference),
        "status": "significant",
        "reason": f"Diferença atingiu o corte normativo de {significance_level}.",
        "norm_source": "B.3",
    }


def _lookup_composite_discrepancy_norm(*, column: str, difference: float, row_005: dict[str, Any], row_015: dict[str, Any], b2_data: dict[int, dict[str, float | None]]) -> dict[str, Any]:
    critical_005 = row_005.get(column)
    critical_015 = row_015.get(column)
    significance_level = _resolve_significance_level(difference, critical_005, critical_015)
    is_significant = significance_level is not None

    if critical_005 is None and critical_015 is None:
        return {
            "critical_value": critical_005,
            "critical_value_015": critical_015,
            "is_significant": False,
            "significance_level": None,
            "base_rate": None,
            "status": "missing_norm",
            "reason": f"Norma B.1 indisponível para o par {column} na faixa etária solicitada.",
            "norm_source": "B.1/B.2",
        }

    if not is_significant:
        return {
            "critical_value": critical_005,
            "critical_value_015": critical_015,
            "is_significant": False,
            "significance_level": None,
            "base_rate": None,
            "status": "below_threshold",
            "reason": _build_below_threshold_reason(difference, critical_005, critical_015),
            "norm_source": "B.1/B.2",
        }

    return {
        "critical_value": critical_005,
        "critical_value_015": critical_015,
        "is_significant": True,
        "significance_level": significance_level,
        "base_rate": _lookup_b2_base_rate(b2_data, column, difference),
        "status": "significant",
        "reason": f"Diferença atingiu o corte normativo de {significance_level}.",
        "norm_source": "B.1/B.2",
    }


def _build_discrepancy_interpretation(label_1: str, label_2: str, difference: float, is_significant: bool, base_rate: float | None) -> str:
    if not is_significant:
        return f"A diferença entre {label_1} e {label_2} não atingiu significância estatística."
    higher_label = label_1 if difference > 0 else label_2
    lower_label = label_2 if difference > 0 else label_1
    rarity = "comum"
    if base_rate is not None:
        if base_rate <= 5:
            rarity = "raro"
        elif base_rate <= 15:
            rarity = "pouco frequente"
        elif base_rate <= 25:
            rarity = "moderadamente frequente"
    frequency_text = f" A frequência acumulada estimada dessa discrepância é de {base_rate}% na amostra normativa, sugerindo padrão {rarity}." if base_rate is not None else ""
    return f"{higher_label} ficou superior a {lower_label} em {abs(difference)} pontos, configurando discrepância estatisticamente significativa.{frequency_text}"


def _build_strengths_weaknesses_table(
    computed_subtests: dict,
    strengths_weaknesses: dict,
    verbal_scores: list[int],
    exec_scores: list[int],
) -> dict:
    total_scores = [
        subtest["escore_ponderado"]
        for subtest in computed_subtests.values()
        if subtest.get("escore_ponderado") is not None
    ]
    mean_total = round(sum(total_scores) / len(total_scores), 2) if total_scores else None
    mean_verbal = round(sum(verbal_scores) / len(verbal_scores), 2) if verbal_scores else None
    mean_exec = round(sum(exec_scores) / len(exec_scores), 2) if exec_scores else None

    rows = []
    for key in WAIS3_SUBTEST_ORDER:
        subtest = computed_subtests.get(key)
        if not subtest:
            continue
        analysis = strengths_weaknesses.get(key, {})
        scaled_score = subtest.get("escore_ponderado")
        scale_mean = analysis.get("reference_mean")
        total_difference = round(scaled_score - mean_total, 2) if scaled_score is not None and mean_total is not None else None
        significance_level = analysis.get("significance_level")
        rows.append({
            "subteste": subtest.get("nome"),
            "escore_ponderado": scaled_score,
            "escore_medio": scale_mean,
            "escore_medio_total": mean_total,
            "escore_medio_verbal": mean_verbal if key in WAIS3_VERBAL_SUBTESTS else None,
            "escore_medio_execucao": mean_exec if key in WAIS3_EXECUTION_SUBTESTS else None,
            "diferenca_da_media": analysis.get("difference"),
            "diferenca_da_media_total": total_difference,
            "significancia_estatistica_nivel": significance_level,
            "facilidade_positivo": analysis.get("difference") if analysis.get("type") == "facilidade" else None,
            "dificuldade_negativo": analysis.get("difference") if analysis.get("type") == "dificuldade" else None,
            "frequencia_amostra_padronizacao": analysis.get("base_rate"),
            "determinacao": analysis.get("type"),
            "status": analysis.get("status"),
            "reason": analysis.get("reason"),
            "norm_source": analysis.get("norm_source"),
            "interpretation": analysis.get("interpretation"),
            "escores_ponderados": scaled_score,
            "escore_medio_formulario": scale_mean,
            "diferenca_da_media_formulario": analysis.get("difference"),
            "significancia_estatistica_nivel_formulario": significance_level,
            "facilidade_mais": analysis.get("difference") if analysis.get("type") == "facilidade" else None,
            "dificuldade_menos": analysis.get("difference") if analysis.get("type") == "dificuldade" else None,
            "frequencia_da_diferenca_da_amostra_de_padronizacao": analysis.get("base_rate"),
            "status_formulario": analysis.get("status"),
            "reason_formulario": analysis.get("reason"),
        })

    return {
        "headers": [
            "SUBTESTES",
            "Escores Ponderados",
            "Escore Médio",
            "Diferença da Média",
            "Significância Estatística - Nível",
            "Facilidade (+)",
            "Dificuldade (-)",
            "Frequência da Diferença da Amostra de Padronização",
        ],
        "determinacao_facilidades_dificuldades": {
            "diferenca_media_total": {
                "checked": False,
                "mean_total": mean_total,
                "label": "Diferença da Média Total",
            },
            "diferenca_media_verbal_execucao": {
                "checked": True,
                "mean_verbal": mean_verbal,
                "mean_execucao": mean_exec,
                "label": "Diferença da Média Verbal e da Média de Execução",
            },
        },
        "rows": rows,
    }


def _build_discrepancy_table(discrepancy_analysis: dict, digitos: dict) -> dict:
    comparison_rows = []
    labels = {
        "verbal_iq_vs_performance_iq": ("QI Verbal - QI de Execução", "QIV", "QIE"),
        "comprehension_vs_perceptual": ("Compreensão Verbal - Organização Perceptual", "ICV", "IOP"),
        "comprehension_vs_working_memory": ("Compreensão Verbal - Memória Operacional", "ICV", "IMO"),
        "perceptual_vs_processing_speed": ("Organização Perceptual - Velocidade de Processamento", "IOP", "IVP"),
        "comprehension_vs_processing_speed": ("Compreensão Verbal - Velocidade de Processamento", "ICV", "IVP"),
        "perceptual_vs_working_memory": ("Organização Perceptual - Memória Operacional", "IOP", "IMO"),
        "working_memory_vs_processing_speed": ("Memória Operacional - Velocidade de Processamento", "IMO", "IVP"),
    }
    for key, (comparison_label, score_1_label, score_2_label) in labels.items():
        entry = discrepancy_analysis.get(key)
        if not entry:
            comparison_rows.append({
                "comparacao": comparison_label,
                "escore_1_label": score_1_label,
                "escore_2_label": score_2_label,
                "escore_1": None,
                "escore_2": None,
                "diferenca": None,
                "significancia_estatistica_nivel": None,
                "frequencia_amostra_padronizacao": None,
                "status": "missing_score",
                "reason": "Escore composto ausente para esta comparação.",
                "interpretation": None,
            })
            continue
        comparison_rows.append({
            "comparacao": comparison_label,
            "escore_1_label": score_1_label,
            "escore_2_label": score_2_label,
            "escore_1": entry.get("score_1"),
            "escore_2": entry.get("score_2"),
            "diferenca": entry.get("difference"),
            "significancia_estatistica_nivel": entry.get("significance_level"),
            "frequencia_amostra_padronizacao": entry.get("base_rate"),
            "status": entry.get("status"),
            "reason": entry.get("reason"),
            "interpretation": entry.get("interpretation"),
            "frequencia_da_diferenca_na_amostra_de_padronizacao": entry.get("base_rate"),
        })

    digits_rows = [
        {
            "comparacao": "Maior Sequência Dígitos Ordem Direta",
            "escore_1_label": "Direta",
            "escore_2_label": None,
            "escore_1": ((digitos.get("maior_sequencia_direta") or {}).get("raw_score")),
            "escore_2": None,
            "diferenca": None,
            "significancia_estatistica_nivel": None,
            "frequencia_amostra_padronizacao": ((digitos.get("maior_sequencia_direta") or {}).get("cumulative_frequency")),
        },
        {
            "comparacao": "Maior Sequência Dígitos Ordem Inversa",
            "escore_1_label": "Inversa",
            "escore_2_label": None,
            "escore_1": ((digitos.get("maior_sequencia_inversa") or {}).get("raw_score")),
            "escore_2": None,
            "diferenca": None,
            "significancia_estatistica_nivel": None,
            "frequencia_amostra_padronizacao": ((digitos.get("maior_sequencia_inversa") or {}).get("cumulative_frequency")),
        },
        {
            "comparacao": "Dígitos Ordem Direta - Ordem Inversa",
            "escore_1_label": "Direta",
            "escore_2_label": "Inversa",
            "escore_1": ((digitos.get("maior_sequencia_direta") or {}).get("raw_score")),
            "escore_2": ((digitos.get("maior_sequencia_inversa") or {}).get("raw_score")),
            "diferenca": ((digitos.get("diferenca_maior_sequencia") or {}).get("difference")),
            "significancia_estatistica_nivel": None,
            "frequencia_amostra_padronizacao": ((digitos.get("diferenca_maior_sequencia") or {}).get("cumulative_frequency")),
        },
    ]

    return {
        "headers_nivel_composto": [
            "Comparações entre as Discrepâncias",
            "Escore 1",
            "Escore 2",
            "Diferença",
            "Significância Estatística - nível",
            "Frequência da Diferença na Amostra de Padronização",
        ],
        "headers_nivel_subteste": [
            "Nível Subteste",
            "Escore 1",
            "Escore 2",
            "Diferença",
            "Frequência da Diferença na Amostra de Padronização",
        ],
        "nivel_composto": comparison_rows,
        "nivel_subteste_digitos": digits_rows,
    }


def _build_render_ready_tables(
    facilidades_dificuldades_tabela: dict,
    discrepancias_tabela: dict,
) -> dict:
    strengths_rows = []
    for row in facilidades_dificuldades_tabela.get("rows", []):
        strengths_rows.append({
            "SUBTESTES": row.get("subteste"),
            "Escores Ponderados": row.get("escores_ponderados"),
            "Escore Médio": row.get("escore_medio_formulario"),
            "Diferença da Média": row.get("diferenca_da_media_formulario"),
            "Significância Estatística - Nível": row.get("significancia_estatistica_nivel_formulario"),
            "Facilidade (+)": row.get("facilidade_mais"),
            "Dificuldade (-)": row.get("dificuldade_menos"),
            "Frequência da Diferença da Amostra de Padronização": row.get("frequencia_da_diferenca_da_amostra_de_padronizacao"),
            "status": row.get("status_formulario"),
            "reason": row.get("reason_formulario"),
        })

    composite_rows = []
    for row in discrepancias_tabela.get("nivel_composto", []):
        composite_rows.append({
            "Comparações entre as Discrepâncias": row.get("comparacao"),
            "Escore 1": row.get("escore_1"),
            "Escore 2": row.get("escore_2"),
            "Diferença": row.get("diferenca"),
            "Significância Estatística - nível": row.get("significancia_estatistica_nivel"),
            "Frequência da Diferença na Amostra de Padronização": row.get("frequencia_da_diferenca_na_amostra_de_padronizacao"),
            "sigla_escore_1": row.get("escore_1_label"),
            "sigla_escore_2": row.get("escore_2_label"),
            "status": row.get("status"),
            "reason": row.get("reason"),
        })

    digits_rows = []
    for row in discrepancias_tabela.get("nivel_subteste_digitos", []):
        digits_rows.append({
            "Nível Subteste": row.get("comparacao"),
            "Escore 1": row.get("escore_1"),
            "Escore 2": row.get("escore_2"),
            "Diferença": row.get("diferenca"),
            "Frequência da Diferença na Amostra de Padronização": row.get("frequencia_amostra_padronizacao"),
            "sigla_escore_1": row.get("escore_1_label"),
            "sigla_escore_2": row.get("escore_2_label"),
        })

    return {
        "facilidades_dificuldades": {
            "titulo": "Determinação das Facilidades e Dificuldades",
            "colunas": facilidades_dificuldades_tabela.get("headers", []),
            "determinacao": facilidades_dificuldades_tabela.get("determinacao_facilidades_dificuldades", {}),
            "linhas": strengths_rows,
        },
        "discrepancias": {
            "titulo": "Comparações entre as Discrepâncias",
            "colunas": discrepancias_tabela.get("headers_nivel_composto", []),
            "linhas": composite_rows,
        },
        "digitos": {
            "titulo": "Nível Subteste",
            "colunas": discrepancias_tabela.get("headers_nivel_subteste", []),
            "linhas": digits_rows,
        },
    }


def _xlfn_norm_s_dist(z_score: float | None) -> float:
    if z_score is None:
        return float("nan")
    return 0.5 * (1 + math.erf(z_score / math.sqrt(2)))


def _classify_z_score(z_score: float | None) -> str | None:
    if z_score is None:
        return None
    if z_score >= 2:
        return "Muito Superior"
    if z_score >= 1.333:
        return "Superior"
    if z_score >= 0.666:
        return "Média Superior"
    if z_score >= -0.667:
        return "Média"
    if z_score >= -1.333:
        return "Média Inferior"
    if z_score >= -2:
        return "Limítrofe"
    return "Deficitário"


def analyze_supplementary(loader: WAIS3NormLoader, age_range_key: str, computed_subtests: dict, indices: dict, raw_scores: dict | None = None) -> dict:
    """Executa análises complementares B.1, B.3, B.6, B.7."""
    result = {
        "facilidades_dificuldades": [],
        "discrepancias": [],
        "strengths_weaknesses": {},
        "discrepancy_analysis": {},
        "digitos": {},
    }

    b1_data = _load_b1(loader)
    b2_data = _load_b2(loader)
    b3_data = _load_b3(loader)

    # ----- B.3: facilidades e dificuldades -----
    verbal_subtests = list(WAIS3_VERBAL_SUBTESTS.keys())
    exec_subtests = list(WAIS3_EXECUTION_SUBTESTS.keys())

    verbal_scores = [computed_subtests[k]["escore_ponderado"] for k in verbal_subtests if computed_subtests.get(k) and computed_subtests[k]["escore_ponderado"] is not None]
    exec_scores = [computed_subtests[k]["escore_ponderado"] for k in exec_subtests if computed_subtests.get(k) and computed_subtests[k]["escore_ponderado"] is not None]
    media_verbal = sum(verbal_scores) / len(verbal_scores) if verbal_scores else 0
    media_exec = sum(exec_scores) / len(exec_scores) if exec_scores else 0

    for key in list(verbal_subtests) + list(exec_subtests):
        data = computed_subtests.get(key)
        if not data or data["escore_ponderado"] is None:
            continue
        score = data["escore_ponderado"]
        is_verbal = key in verbal_subtests
        media = media_verbal if is_verbal else media_exec
        diff = score - media
        section = _resolve_b3_section("verbal" if is_verbal else "execucao", len(verbal_scores) if is_verbal else len(exec_scores))
        b3_key = B3_ROW_LABELS[key].lower()
        section_data = b3_data.get(b3_key, {}).get(section, {})
        norm_result = _lookup_strength_weakness_norm(
            label=WAIS3_ALL_SUBTESTS[key],
            section=section,
            section_data=section_data,
            difference=diff,
        )
        strength_entry = {
            "label": WAIS3_ALL_SUBTESTS[key],
            "scaled": score,
            "reference_mean": round(media, 2),
            "difference": round(diff, 2),
            "section": section,
            "interpretation": None,
            **norm_result,
        }
        if strength_entry["type"] == "facilidade":
            strength_entry["interpretation"] = f"Foi observada facilidade relativa em {WAIS3_ALL_SUBTESTS[key]}, com desempenho acima da média pessoal nesse conjunto de habilidades."
        elif strength_entry["type"] == "dificuldade":
            strength_entry["interpretation"] = f"Foi observada dificuldade relativa em {WAIS3_ALL_SUBTESTS[key]}, com desempenho abaixo da média pessoal nesse conjunto de habilidades."
        result["strengths_weaknesses"][key] = strength_entry

        if strength_entry["is_significant"]:
            tipo = strength_entry["type"]
            result["facilidades_dificuldades"].append({
                "subteste": WAIS3_ALL_SUBTESTS[key],
                "escore": score,
                "media": round(media, 2),
                "diferenca": round(diff, 2),
                "tipo": tipo,
                "significancia": f"α={strength_entry['significance_level']}",
                "critical_value": strength_entry["critical_value"],
                "base_rate": strength_entry["base_rate"],
                "interpretation": strength_entry["interpretation"],
            })

    # ----- B.1: discrepâncias entre índices -----
    age_key_b1 = _map_faixa_b(age_range_key)
    row_005 = b1_data.get(f"{age_key_b1}_0,05") or {}
    row_015 = b1_data.get(f"{age_key_b1}_0,15") or {}

    for index_1, index_2, column, output_key in B1_PAIR_SPECS:
        score_1 = (indices.get(index_1) or {}).get("pontuacao_composta")
        score_2 = (indices.get(index_2) or {}).get("pontuacao_composta")
        if score_1 is None or score_2 is None:
            continue
        difference = score_1 - score_2
        norm_result = _lookup_composite_discrepancy_norm(
            column=column,
            difference=difference,
            row_005=row_005,
            row_015=row_015,
            b2_data=b2_data,
        )
        label_1 = (indices.get(index_1) or {}).get("nome") or index_1
        label_2 = (indices.get(index_2) or {}).get("nome") or index_2
        entry = {
            "score_1": score_1,
            "score_2": score_2,
            "difference": difference,
            "label_1": label_1,
            "label_2": label_2,
            "direction": _describe_discrepancy_direction(label_1, score_1, label_2, score_2),
            **norm_result,
        }
        entry["interpretation"] = _build_discrepancy_interpretation(
            label_1,
            label_2,
            difference,
            entry["is_significant"],
            entry["base_rate"],
        )
        result["discrepancy_analysis"][output_key] = entry
        if entry["is_significant"]:
            result["discrepancias"].append({
                "par": f"{label_1} × {label_2}",
                "diferenca": difference,
                "critico": entry["critical_value"],
                "nivel": entry["significance_level"],
                "base_rate": entry["base_rate"],
                "interpretation": entry["interpretation"],
            })

    # ----- B.6 e B.7: análise de Dígitos -----
    digitos_data = computed_subtests.get("digitos")
    if digitos_data and digitos_data.get("escore_ponderado") is not None:
        raw_digitos = digitos_data.get("pontos_brutos", 0) or 0
        col_direta = _map_faixa_b6(age_range_key)
        col_inversa = col_direta + 1

        # Tentar ler B.6 do CSV raw para frequência cumulativa
        b6_path = Path(loader.base_path) / "supplementary" / "b6_digitos_ordem_direta_inversa.csv"
        freq_direta = None
        freq_inversa = None
        if b6_path.exists():
            try:
                with b6_path.open(encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        if r.get("col_0") and str(r.get("col_0")).strip().isdigit():
                            maximo = int(str(r.get("col_0")).strip())
                            if maximo == raw_digitos:
                                freq_direta = _norm_float(r.get(f"col_{col_direta}"))
                                freq_inversa = _norm_float(r.get(f"col_{col_inversa}"))
                                break
            except Exception:
                pass

        result["digitos"] = {
            "maximo_ordem_direta": raw_digitos,
            "maximo_ordem_inversa": None,  # raw não distingue; calculado via B.7 se necessário
            "diferenca_direta_inversa": None,
            "frequencia_b6_direta": freq_direta,
            "frequencia_b6_inversa": freq_inversa,
        }

    process_scores = (raw_scores or {}).get("process_scores") or {}
    b6_rows = loader.get_supplementary_tables().get("b6") or []
    b7_rows = loader.get_supplementary_tables().get("b7") or []
    direct_col, inverse_col = _b6_columns_for_age(age_range_key)
    b7_col = _b7_column_for_age(age_range_key)

    digits_forward = process_scores.get("digitos_ordem_direta")
    digits_backward = process_scores.get("digitos_ordem_inversa")
    forward_span = process_scores.get("maior_sequencia_digitos_direta")
    backward_span = process_scores.get("maior_sequencia_digitos_inversa")

    if digits_forward is not None:
        result["digitos"]["ordem_direta"] = _build_process_result(
            raw_value=int(digits_forward),
            mean=_row_value(b6_rows, "Média", direct_col),
            sd=_row_value(b6_rows, "DP", direct_col),
            percentile=_lookup_percentile_from_csv_rows(b6_rows, int(digits_forward), direct_col),
        )

    if digits_backward is not None:
        result["digitos"]["ordem_inversa"] = _build_process_result(
            raw_value=int(digits_backward),
            mean=_row_value(b6_rows, "Média", inverse_col),
            sd=_row_value(b6_rows, "DP", inverse_col),
            percentile=_lookup_percentile_from_csv_rows(b6_rows, int(digits_backward), inverse_col),
        )

    if forward_span is not None:
        result["digitos"]["maior_sequencia_direta"] = _build_process_result(
            raw_value=int(forward_span),
            mean=_row_value(b6_rows, "Média", direct_col),
            sd=_row_value(b6_rows, "DP", direct_col),
            percentile=_lookup_percentile_from_csv_rows(b6_rows, int(forward_span), direct_col),
        )

    if backward_span is not None:
        result["digitos"]["maior_sequencia_inversa"] = _build_process_result(
            raw_value=int(backward_span),
            mean=_row_value(b6_rows, "Média", inverse_col),
            sd=_row_value(b6_rows, "DP", inverse_col),
            percentile=_lookup_percentile_from_csv_rows(b6_rows, int(backward_span), inverse_col),
        )

    if forward_span is not None and backward_span is not None:
        difference = int(forward_span) - int(backward_span)
        result["digitos"]["diferenca_maior_sequencia"] = _build_process_result(
            raw_value=difference,
            mean=_row_value(b7_rows, "Média", b7_col),
            sd=_row_value(b7_rows, "DP", b7_col),
            percentile=_lookup_percentile_from_csv_rows(b7_rows, difference, b7_col),
            reverse_z=True,
        )
        result["digitos"]["diferenca_maior_sequencia"]["difference"] = difference

    result["facilidades_dificuldades_tabela"] = _build_strengths_weaknesses_table(
        computed_subtests=computed_subtests,
        strengths_weaknesses=result["strengths_weaknesses"],
        verbal_scores=verbal_scores,
        exec_scores=exec_scores,
    )
    result["discrepancias_tabela"] = _build_discrepancy_table(
        discrepancy_analysis=result["discrepancy_analysis"],
        digitos=result["digitos"],
    )

    return result


# ------------------------------------------------------------------
# Cálculo principal
# ------------------------------------------------------------------

def compute_wais3_payload(raw_scores: dict, loader: WAIS3NormLoader | None = None) -> dict:
    loader = loader or WAIS3NormLoader()
    idade = raw_scores.get("idade") or {}
    anos = int(idade.get("anos", 0) or 0)
    meses = int(idade.get("meses", 0) or 0)
    age_range_key = resolve_age_range(anos, meses)

    computed_subtests: dict[str, dict] = {}
    warnings: list[str] = []
    supplementary_tables = loader.get_supplementary_tables()
    psychometrics_tables = loader.get_psychometrics_tables()

    for key, label in WAIS3_ALL_SUBTESTS.items():
        payload = (raw_scores.get("subtestes") or {}).get(key)
        if not payload:
            continue
        raw_value = int(payload.get("pontos_brutos", 0) or 0)
        scaled_score = None
        warning = None
        try:
            scaled_score = loader.get_scaled_score(key, raw_value, age_range_key)
        except Exception as exc:
            try:
                scaled_score = loader.get_scaled_score(key, raw_value, "grupo_referencia_20-34")
                warning = f"fallback: used grupo_referencia_20-34 for {age_range_key}"
            except Exception as exc2:
                warning = str(exc2)
                warnings.append(f"{label}: {warning}")
        computed_subtests[key] = {
            "nome": label,
            "pontos_brutos": raw_value,
            "escore_ponderado": scaled_score,
            "classificacao": classify_scaled_score(scaled_score),
            "dominio": "verbal" if key in {"vocabulario", "semelhancas", "aritmetica", "digitos", "informacao", "compreensao", "sequencia_numeros_letras"} else "execucao",
            "warning": warning,
        }

    # Subtestes ordenados
    subtestes_ordenados = [
        computed_subtests[key]
        for key in WAIS3_SUBTEST_ORDER
        if key in computed_subtests
    ]

    computed_indexes: dict[str, dict] = {}
    for index_key, index_cfg in WAIS3_INDEXES.items():
        present_subtests = [
            code
            for code in index_cfg["subtests"]
            if computed_subtests.get(code) and computed_subtests[code].get("escore_ponderado") is not None
        ]
        missing_subtests = [code for code in index_cfg["subtests"] if code not in present_subtests]
        scaled_sum = sum(computed_subtests[code]["escore_ponderado"] for code in present_subtests) if present_subtests else None
        composite_data = None
        warning = None
        if scaled_sum is not None:
            try:
                composite_data = loader.get_composite_score(index_key, scaled_sum)
            except Exception as exc:
                warning = str(exc)
                warnings.append(f"{index_cfg['label']}: {warning}")
        composite_score = composite_data.get("pontuacao_composta") if composite_data else None
        computed_indexes[index_key] = {
            "nome": index_cfg["label"],
            "subtestes": index_cfg["subtests"],
            "subtestes_utilizados": present_subtests,
            "soma_ponderada": scaled_sum,
            "pontuacao_composta": composite_score,
            "percentil": composite_data.get("percentil") if composite_data else None,
            "ic_90": composite_data.get("ic_90") if composite_data else None,
            "ic_95": composite_data.get("ic_95") if composite_data else None,
            "classificacao": composite_data.get("classificacao") if composite_data and composite_data.get("classificacao") else classify_composite_score(composite_score),
            "fonte_tabela": composite_data.get("source") if composite_data else None,
            "subtestes_ausentes": missing_subtests,
            "warning": warning,
        }

    # Análises complementares
    supplementary = analyze_supplementary(loader, age_range_key, computed_subtests, computed_indexes, raw_scores=raw_scores)
    render_ready_tables = _build_render_ready_tables(
        facilidades_dificuldades_tabela=supplementary["facilidades_dificuldades_tabela"],
        discrepancias_tabela=supplementary["discrepancias_tabela"],
    )
    charts = {
        "scaled_profile": [
            {
                "key": key,
                "label": computed_subtests[key]["nome"],
                "scaled": computed_subtests[key]["escore_ponderado"],
                "classification": computed_subtests[key]["classificacao"],
            }
            for key in WAIS3_SUBTEST_ORDER
            if key in computed_subtests and computed_subtests[key].get("escore_ponderado") is not None
        ],
        "composite_profile": [
            {
                "key": key,
                "label": value["nome"],
                "score": value["pontuacao_composta"],
                "percentile": value["percentil"],
                "classification": value["classificacao"],
            }
            for key, value in computed_indexes.items()
            if value.get("pontuacao_composta") is not None
        ],
    }
    audit_tables = sorted({
        *(data.get("fonte_tabela") for data in computed_indexes.values() if data.get("fonte_tabela")),
        *(f"raw_to_scaled/{data['dominio']}/{age_range_key}.csv" for data in computed_subtests.values() if data.get("escore_ponderado") is not None),
        *(f"supplementary/{name}" for name in ("b1", "b2", "b3", "b6", "b7") if name in supplementary_tables),
    })

    return {
        "instrument_code": "wais3",
        "instrument_name": WAIS3_NAME,
        "idade": {"anos": anos, "meses": meses},
        "idade_normativa": age_range_key,
        "subtestes": computed_subtests,
        "subtestes_ordenados": subtestes_ordenados,
        "indices": computed_indexes,
        "sums": {key: value.get("soma_ponderada") for key, value in computed_indexes.items()},
        "composites": computed_indexes,
        "clinical_aliases": {
            "subtestes": WAIS3_SUBTEST_CODES,
            "indices": WAIS3_INDEX_CODES,
        },
        "supplementary_tables": supplementary_tables,
        "psychometrics_tables": psychometrics_tables,
        "supplementary_tables_available": sorted(supplementary_tables.keys()),
        "psychometrics_available": sorted(psychometrics_tables.keys()),
        "has_scaled_score_data": loader.has_scaled_score_data(),
        "has_composite_data": loader.has_composite_data(),
        "norm_tables_ready": loader.has_normative_data(),
        "warnings": warnings,
        "manifest": loader.load_manifest(),
        # Análises complementares
        "facilidades_dificuldades": supplementary["facilidades_dificuldades"],
        "discrepancias": supplementary["discrepancias"],
        "strengths_weaknesses": supplementary["strengths_weaknesses"],
        "discrepancy_analysis": supplementary["discrepancy_analysis"],
        "facilidades_dificuldades_tabela": supplementary["facilidades_dificuldades_tabela"],
        "discrepancias_tabela": supplementary["discrepancias_tabela"],
        "render_ready_tables": render_ready_tables,
        "digitos": supplementary["digitos"],
        "charts": charts,
        "audit": {
            "norm_tables_used": audit_tables,
            "substitutions_used": list((raw_scores.get("substitutions") or {}).keys()),
            "proration_used": False,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
