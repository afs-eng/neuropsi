from __future__ import annotations

import csv
from pathlib import Path


def classify_wais3_payload(computed_data: dict) -> dict:
    """Return the computed payload augmented with GAI and clusters using WAIS-III tables."""
    if not computed_data:
        return {}

    result = dict(computed_data)
    warnings = list(result.get("warnings") or [])

    indices = result.get("indices", {})
    subtestes = result.get("subtestes", {})

    def get_scaled_score(subtest_key: str) -> int | None:
        subtest = subtestes.get(subtest_key)
        if subtest:
            return subtest.get("escore_ponderado")
        return None

    # Get scaled scores for GAI calculation
    vc = get_scaled_score("vocabulario")
    sm = get_scaled_score("semelhancas")
    info = get_scaled_score("informacao")
    cf = get_scaled_score("completar_figuras")
    cb = get_scaled_score("cubos")
    rm = get_scaled_score("raciocinio_matricial")

    # Get ICV and IOP from indices
    icv = (indices.get("compreensao_verbal") or {}).get("pontuacao_composta")
    iop = (indices.get("organizacao_perceptual") or {}).get("pontuacao_composta")

    # Calculate GAI if all required subtests are available
    gai_data = {
        "calculado": False,
        "interpretavel": False,
        "normativo": False,
        "fonte_normativa": None,
        "soma_ponderados": None,
        "escore_composto": None,
        "percentil": None,
        "intervalo_confianca": None,
        "classificacao": None,
        "diferenca_icv_iop": None,
        "alerta": None,
    }

    if all(s is not None for s in [vc, sm, info, cf, cb, rm]):
        # Calculate difference between ICV and IOP
        if icv is not None and iop is not None:
            diferenca_icv_iop = abs(icv - iop)
            gai_data["diferenca_icv_iop"] = diferenca_icv_iop

            # Check if GAI is interpretable
            gai_data["interpretavel"] = diferenca_icv_iop < 23

            if diferenca_icv_iop >= 23:
                gai_data["alerta"] = f"Diferença entre ICV e IOP ({diferenca_icv_iop} pontos) >= 23. GAI não interpretável."

        # Calculate GAI sum
        soma_gai = vc + sm + info + cf + cb + rm
        gai_data["soma_ponderados"] = soma_gai
        gai_data["calculado"] = True

        # Load GAI table and lookup
        try:
            gai_table = _load_gai_table("tabela_c1_gai.csv")
            row = gai_table.get(soma_gai)
            if row:
                gai_data["escore_composto"] = row.get("gai")
                gai_data["percentil"] = row.get("percentil")
                gai_data["intervalo_confianca"] = [row.get("ic_95_inferior"), row.get("ic_95_superior")]
                gai_data["classificacao"] = _classify_wechsler(row.get("gai"))
                gai_data["normativo"] = True
                gai_data["fonte_normativa"] = "Apêndice C - Norm Tables for Computing Standard Scores on the General Ability Index (GAI) and Clinical Clusters"
            else:
                warnings.append(f"GAI: soma {soma_gai} fora da tabela normativa")
        except Exception as exc:
            warnings.append(f"GAI lookup failed: {exc}")

    # Calculate clusters (C.2 to C.9)
    clusters = _calculate_clusters(subtestes)
    result["clusters"] = clusters

    result["gai_data"] = gai_data
    if warnings:
        result["warnings"] = warnings

    return result


def _load_gai_table(filename: str) -> dict:
    """Load GAI table from CSV."""
    base_path = Path(__file__).parent / "tabelas" / "gai"
    table_path = base_path / filename

    if not table_path.exists():
        raise FileNotFoundError(f"GAI table not found: {table_path}")

    result = {}
    with open(table_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("soma_ponderados") or not row["soma_ponderados"].strip():
                continue
            try:
                soma = int(float(row["soma_ponderados"]))
            except (ValueError, TypeError):
                continue
            result[soma] = {
                "gai": int(float(row["gai"])),
                "percentil": float(row["percentil"]),
                "ic_95_inferior": int(float(row["ic_95_inferior"])),
                "ic_95_superior": int(float(row["ic_95_superior"])),
            }
    return result


def _load_cluster_table(filename: str) -> dict:
    """Load cluster table from CSV."""
    base_path = Path(__file__).parent / "tabelas" / "gai"
    table_path = base_path / filename

    if not table_path.exists():
        raise FileNotFoundError(f"Cluster table not found: {table_path}")

    result = {}
    with open(table_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("soma_ponderados") or not row["soma_ponderados"].strip():
                continue
            try:
                soma = int(float(row["soma_ponderados"]))
            except (ValueError, TypeError):
                continue
            result[soma] = {
                "cluster": int(float(row["cluster"])),
                "percentil": float(row["percentil"]),
                "ic_95": row.get("ic_95", ""),
            }
    return result


def _calculate_clusters(subtestes: dict) -> dict:
    """Calculate clinical clusters C.2 to C.9."""
    def get_scaled(key: str) -> int | None:
        subtest = subtestes.get(key)
        return subtest.get("escore_ponderado") if subtest else None

    clusters = {}

    # C.2 - Fluid Reasoning (Gf): RM + AF + AR
    rm = get_scaled("raciocinio_matricial")
    af = get_scaled("arranjo_figuras")
    ar = get_scaled("aritmetica")

    if all(s is not None for s in [rm, af, ar]):
        try:
            table = _load_cluster_table("tabela_c2_gf.csv")
            soma = rm + af + ar
            row = table.get(soma)
            if row:
                clusters["Gf"] = {
                    "nome": "Raciocínio Fluido (Gf)",
                    "soma": soma,
                    "escore": row["cluster"],
                    "percentil": row["percentil"],
                    "ic_95": row["ic_95"],
                    "classificacao": _classify_wechsler(row["cluster"]),
                }
        except Exception:
            pass

    # C.3 - Visual Processing (Gv): CB + CF
    cb = get_scaled("cubos")
    cf = get_scaled("completar_figuras")

    if all(s is not None for s in [cb, cf]):
        try:
            table = _load_cluster_table("tabela_c3_gv.csv")
            soma = cb + cf
            row = table.get(soma)
            if row:
                clusters["Gv"] = {
                    "nome": "Processamento Visual (Gv)",
                    "soma": soma,
                    "escore": row["cluster"],
                    "percentil": row["percentil"],
                    "ic_95": row["ic_95"],
                    "classificacao": _classify_wechsler(row["cluster"]),
                }
        except Exception:
            pass

    # C.4 - Nonverbal Fluid Reasoning: RM + AF
    if all(s is not None for s in [rm, af]):
        try:
            table = _load_cluster_table("tabela_c4_gf_nonverbal.csv")
            soma = rm + af
            row = table.get(soma)
            if row:
                clusters["Gf_nonverbal"] = {
                    "nome": "Raciocínio Fluido Não Verbal",
                    "soma": soma,
                    "escore": row["cluster"],
                    "percentil": row["percentil"],
                    "ic_95": row["ic_95"],
                    "classificacao": _classify_wechsler(row["cluster"]),
                }
        except Exception:
            pass

    # C.5 - Verbal Fluid Reasoning: SM + CO
    sm = get_scaled("semelhancas")
    co = get_scaled("compreensao")

    if all(s is not None for s in [sm, co]):
        try:
            table = _load_cluster_table("tabela_c5_gf_verbal.csv")
            soma = sm + co
            row = table.get(soma)
            if row:
                clusters["Gf_verbal"] = {
                    "nome": "Raciocínio Fluido Verbal",
                    "soma": soma,
                    "escore": row["cluster"],
                    "percentil": row["percentil"],
                    "ic_95": row["ic_95"],
                    "classificacao": _classify_wechsler(row["cluster"]),
                }
        except Exception:
            pass

    # C.6 - Lexical Knowledge: VC + SM
    vc = get_scaled("vocabulario")

    if all(s is not None for s in [vc, sm]):
        try:
            table = _load_cluster_table("tabela_c6_gc_lk.csv")
            soma = vc + sm
            row = table.get(soma)
            if row:
                clusters["Gc_LK"] = {
                    "nome": "Conhecimento Lexical (Gc-LK)",
                    "soma": soma,
                    "escore": row["cluster"],
                    "percentil": row["percentil"],
                    "ic_95": row["ic_95"],
                    "classificacao": _classify_wechsler(row["cluster"]),
                }
        except Exception:
            pass

    # C.7 - General Information: IN + CO
    info = get_scaled("informacao")

    if all(s is not None for s in [info, co]):
        try:
            table = _load_cluster_table("tabela_c7_gc_k0.csv")
            soma = info + co
            row = table.get(soma)
            if row:
                clusters["Gc_K0"] = {
                    "nome": "Informação Geral (Gc-K0)",
                    "soma": soma,
                    "escore": row["cluster"],
                    "percentil": row["percentil"],
                    "ic_95": row["ic_95"],
                    "classificacao": _classify_wechsler(row["cluster"]),
                }
        except Exception:
            pass

    # C.8 - Long-Term Memory: VC + IN
    if all(s is not None for s in [vc, info]):
        try:
            table = _load_cluster_table("tabela_c8_gc_ltm.csv")
            soma = vc + info
            row = table.get(soma)
            if row:
                clusters["Gc_LTM"] = {
                    "nome": "Memória de Longo Prazo (Gc-LTM)",
                    "soma": soma,
                    "escore": row["cluster"],
                    "percentil": row["percentil"],
                    "ic_95": row["ic_95"],
                    "classificacao": _classify_wechsler(row["cluster"]),
                }
        except Exception:
            pass

    # C.9 - Short-Term Memory: DG + SNL
    dg = get_scaled("digitos")
    snl = get_scaled("sequencia_numeros_letras")

    if all(s is not None for s in [dg, snl]):
        try:
            table = _load_cluster_table("tabela_c9_gsm_wm.csv")
            soma = dg + snl
            row = table.get(soma)
            if row:
                clusters["Gsm_WM"] = {
                    "nome": "Memória de Curto Prazo (Gsm-WM)",
                    "soma": soma,
                    "escore": row["cluster"],
                    "percentil": row["percentil"],
                    "ic_95": row["ic_95"],
                    "classificacao": _classify_wechsler(row["cluster"]),
                }
        except Exception:
            pass

    return clusters


def _classify_wechsler(valor: int | float) -> str:
    """Classify Wechsler scale score."""
    if valor <= 69:
        return "Extremamente Baixo"
    elif valor <= 79:
        return "Limítrofe"
    elif valor <= 89:
        return "Média Inferior"
    elif valor <= 109:
        return "Média"
    elif valor <= 119:
        return "Média Superior"
    elif valor <= 129:
        return "Superior"
    else:
        return "Muito Superior"
