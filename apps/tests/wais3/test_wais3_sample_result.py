from apps.tests.wais3.calculators import (
    _build_discrepancy_table,
    _build_strengths_weaknesses_table,
    _resolve_significance_level,
    analyze_supplementary,
    compute_wais3_payload,
)
from apps.tests.wais3.loaders import WAIS3NormLoader


def test_wais3_sample_result_case():
    """Case reproduzindo os dados do WAIS-III 2020 para um adulto de 30 anos.

    Os valores brutos fornecidos correspondem a escores ponderados e QIs
    compatíveis com o perfil cognitivo de um adulto de 30 anos (faixa 30-39).

    A verificação é feita contra os valores extraídos das tabelas normativas
    brasileiras WAIS-III 2020 (Tabelas A.1 a A.9).
    """
    raw_scores = {
        "idade": {"anos": 30, "meses": 0},
        "subtestes": {
            "completar_figuras": {"pontos_brutos": 18},
            "vocabulario": {"pontos_brutos": 36},
            "codigos": {"pontos_brutos": 59},
            "semelhancas": {"pontos_brutos": 22},
            "cubos": {"pontos_brutos": 22},
            "aritmetica": {"pontos_brutos": 8},
            "raciocinio_matricial": {"pontos_brutos": 16},
            "digitos": {"pontos_brutos": 13},
            "informacao": {"pontos_brutos": 13},
            "arranjo_figuras": {"pontos_brutos": 17},
            "compreensao": {"pontos_brutos": 27},
            "procurar_simbolos": {"pontos_brutos": 26},
            "sequencia_numeros_letras": {"pontos_brutos": 10},
            "armar_objetos": {"pontos_brutos": 0},
        },
    }

    payload = compute_wais3_payload(raw_scores)

    # Assertions de estrutura
    assert payload["instrument_code"] == "wais3"
    assert payload["idade_normativa"] == "idade_30-39"

    indices = payload.get("indices") or {}
    subtests = payload.get("subtestes") or {}

    # --- Subtestes: escores ponderados (Tabela A.1, faixa 30-39) ---
    assert subtests["vocabulario"]["escore_ponderado"] == 11
    assert subtests["semelhancas"]["escore_ponderado"] == 10
    assert subtests["aritmetica"]["escore_ponderado"] == 8
    assert subtests["digitos"]["escore_ponderado"] == 9
    assert subtests["informacao"]["escore_ponderado"] == 11
    assert subtests["compreensao"]["escore_ponderado"] == 13
    assert subtests["sequencia_numeros_letras"]["escore_ponderado"] == 12
    assert subtests["completar_figuras"]["escore_ponderado"] == 10
    assert subtests["codigos"]["escore_ponderado"] == 10
    assert subtests["cubos"]["escore_ponderado"] == 8
    assert subtests["raciocinio_matricial"]["escore_ponderado"] == 11
    assert subtests["arranjo_figuras"]["escore_ponderado"] == 13
    assert subtests["procurar_simbolos"]["escore_ponderado"] == 10
    assert subtests["armar_objetos"]["escore_ponderado"] == 1

    # --- Classificações qualitativas (escore ponderado) ---
    assert subtests["vocabulario"]["classificacao"] == "Média"
    assert subtests["compreensao"]["classificacao"] == "Média Superior"
    assert subtests["arranjo_figuras"]["classificacao"] == "Média Superior"
    assert subtests["sequencia_numeros_letras"]["classificacao"] == "Média Superior"
    assert subtests["armar_objetos"]["classificacao"] == "Deficitário"

    # --- QI Total (Tabela A.5, soma=114) ---
    qi_total = indices.get("qi_total") or {}
    assert qi_total["soma_ponderada"] == 114
    assert qi_total["pontuacao_composta"] == 102
    assert qi_total["percentil"] == 55

    # --- QI Verbal (Tabela A.3, soma=62) ---
    qi_verbal = indices.get("qi_verbal") or {}
    assert qi_verbal["soma_ponderada"] == 62
    assert qi_verbal["pontuacao_composta"] == 102
    assert qi_verbal["percentil"] == 55

    # --- QI Execução (Tabela A.4, soma=52) ---
    qi_exec = indices.get("qi_execucao") or {}
    assert qi_exec["soma_ponderada"] == 52
    assert qi_exec["pontuacao_composta"] == 102
    assert qi_exec["percentil"] == 55

    # --- ICV (Tabela A.6, soma=32: Vocab(11)+Semelh(10)+Info(11)) ---
    icv = indices.get("compreensao_verbal") or {}
    assert icv["soma_ponderada"] == 32
    assert icv["pontuacao_composta"] == 104
    assert icv["percentil"] == 61

    # --- IOP (Tabela A.7, soma=29: CF(10)+Cubos(8)+RM(11)) ---
    iop = indices.get("organizacao_perceptual") or {}
    assert iop["soma_ponderada"] == 29
    assert iop["pontuacao_composta"] == 98
    assert iop["percentil"] == 45

    # --- IMO (Tabela A.8, soma=29: Arit(8)+Dig(9)+SeqNL(12)) ---
    imo = indices.get("memoria_operacional") or {}
    assert imo["soma_ponderada"] == 29
    assert imo["pontuacao_composta"] == 98

    # --- IVP (Tabela A.9, soma=20: Cod(10)+PS(10)) ---
    ivp = indices.get("velocidade_processamento") or {}
    assert ivp["soma_ponderada"] == 20
    assert ivp["pontuacao_composta"] == 100
    assert ivp["percentil"] == 50

    # --- Sem warnings, todas as tabelas carregadas ---
    assert not payload.get("warnings"), f"Há warnings: {payload['warnings']}"
    assert payload["has_scaled_score_data"] is True
    assert payload["has_composite_data"] is True
    assert payload["norm_tables_ready"] is True

    assert payload["charts"]["scaled_profile"]
    assert payload["charts"]["composite_profile"]
    assert payload["strengths_weaknesses"]["armar_objetos"]["status"] == "missing_norm"
    assert "Norma B.3 indisponível" in payload["strengths_weaknesses"]["armar_objetos"]["reason"]
    assert payload["discrepancy_analysis"]["verbal_iq_vs_performance_iq"]["difference"] == 0
    assert payload["discrepancy_analysis"]["verbal_iq_vs_performance_iq"]["status"] == "below_threshold"
    assert payload["facilidades_dificuldades_tabela"]["determinacao_facilidades_dificuldades"]["diferenca_media_verbal_execucao"]["checked"] is True
    assert payload["facilidades_dificuldades_tabela"]["headers"][0] == "SUBTESTES"
    assert payload["facilidades_dificuldades_tabela"]["rows"][0]["subteste"] == "Completar Figuras"
    assert "frequencia_da_diferenca_da_amostra_de_padronizacao" in payload["facilidades_dificuldades_tabela"]["rows"][0]
    assert "status" in payload["facilidades_dificuldades_tabela"]["rows"][0]
    assert payload["discrepancias_tabela"]["nivel_composto"][0]["comparacao"] == "QI Verbal - QI de Execução"
    assert payload["discrepancias_tabela"]["headers_nivel_composto"][1] == "Escore 1"
    assert payload["render_ready_tables"]["facilidades_dificuldades"]["linhas"][0]["SUBTESTES"] == "Completar Figuras"
    assert payload["render_ready_tables"]["discrepancias"]["linhas"][0]["Comparações entre as Discrepâncias"] == "QI Verbal - QI de Execução"
    assert payload["render_ready_tables"]["discrepancias"]["linhas"][0]["status"] == "below_threshold"
    assert payload["audit"]["norm_tables_used"]
    assert payload["clinical_aliases"]["indices"]["compreensao_verbal"] == "ICV"
    assert payload["clinical_aliases"]["subtestes"]["digitos"] == "DG"


def test_wais3_digit_process_scores_are_computed_when_provided():
    raw_scores = {
        "idade": {"anos": 30, "meses": 0},
        "subtestes": {
            "digitos": {"pontos_brutos": 13},
        },
        "process_scores": {
            "digitos_ordem_direta": 6,
            "digitos_ordem_inversa": 4,
            "maior_sequencia_digitos_direta": 6,
            "maior_sequencia_digitos_inversa": 4,
        },
    }

    payload = compute_wais3_payload(raw_scores)
    digitos = payload["digitos"]

    assert digitos["ordem_direta"]["cumulative_frequency"] == 61.8
    assert digitos["ordem_direta"]["scaled_score"] == 10.0
    assert digitos["ordem_direta"]["classification"] == "Média"

    assert digitos["ordem_inversa"]["cumulative_frequency"] == 70.7
    assert digitos["ordem_inversa"]["classification"] == "Média"

    assert digitos["diferenca_maior_sequencia"]["difference"] == 2
    assert digitos["diferenca_maior_sequencia"]["cumulative_frequency"] == 58.7
    assert digitos["diferenca_maior_sequencia"]["classification"] == "Média"
    assert payload["discrepancias_tabela"]["nivel_subteste_digitos"][2]["diferenca"] == 2
    assert payload["render_ready_tables"]["digitos"]["linhas"][2]["Diferença"] == 2


def test_wais3_discrepancy_analysis_includes_base_rate_and_interpretation():
    loader = WAIS3NormLoader()
    result = analyze_supplementary(
        loader,
        "idade_30-39",
        computed_subtests={},
        indices={
            "compreensao_verbal": {"nome": "Índice de Compreensão Verbal", "pontuacao_composta": 120},
            "organizacao_perceptual": {"nome": "Índice de Organização Perceptual", "pontuacao_composta": 90},
        },
    )

    discrepancy = result["discrepancy_analysis"]["comprehension_vs_perceptual"]
    assert discrepancy["difference"] == 30
    assert discrepancy["is_significant"] is True
    assert discrepancy["base_rate"] == 0.3
    assert discrepancy["status"] == "significant"
    assert discrepancy["direction"] == "Índice de Compreensão Verbal maior que Índice de Organização Perceptual"
    assert "superior" in discrepancy["interpretation"].lower()


def test_wais3_significance_level_prefers_005_then_015():
    assert _resolve_significance_level(6, critical_005=7, critical_015=5) == "0,15"
    assert _resolve_significance_level(8, critical_005=7, critical_015=5) == "0,05"
    assert _resolve_significance_level(4, critical_005=7, critical_015=5) is None


def test_wais3_render_tables_keep_015_significance_level():
    discrepancy_table = _build_discrepancy_table(
        discrepancy_analysis={
            "comprehension_vs_perceptual": {
                "score_1": 104,
                "score_2": 96,
                "difference": 8,
                "significance_level": "0,15",
                "is_significant": True,
                "base_rate": 25,
                "status": "significant",
                "reason": "Teste",
                "interpretation": "Teste",
            }
        },
        digitos={},
    )

    assert discrepancy_table["nivel_composto"][1]["significancia_estatistica_nivel"] == "0,15"
    assert discrepancy_table["nivel_composto"][1]["status"] == "significant"

    strengths_table = _build_strengths_weaknesses_table(
        computed_subtests={
            "vocabulario": {"nome": "Vocabulário", "escore_ponderado": 12},
        },
        strengths_weaknesses={
            "vocabulario": {
                "reference_mean": 10.0,
                "difference": 2.0,
                "significance_level": "0,15",
                "is_significant": True,
                "type": "facilidade",
                "base_rate": 25,
                "status": "significant",
                "reason": "Teste",
                "interpretation": "Teste",
            }
        },
        verbal_scores=[12],
        exec_scores=[],
    )

    assert strengths_table["rows"][0]["significancia_estatistica_nivel"] == "0,15"
    assert strengths_table["rows"][0]["significancia_estatistica_nivel_formulario"] == "0,15"


def test_wais3_strength_status_distinguishes_missing_norm_and_below_threshold():
    payload = compute_wais3_payload(
        {
            "idade": {"anos": 30, "meses": 0},
            "subtestes": {
                "armar_objetos": {"pontos_brutos": 0},
                "vocabulario": {"pontos_brutos": 36},
                "semelhancas": {"pontos_brutos": 22},
                "aritmetica": {"pontos_brutos": 8},
                "digitos": {"pontos_brutos": 13},
                "informacao": {"pontos_brutos": 13},
                "compreensao": {"pontos_brutos": 27},
                "sequencia_numeros_letras": {"pontos_brutos": 10},
            },
        }
    )

    assert payload["strengths_weaknesses"]["armar_objetos"]["status"] == "missing_norm"
    assert payload["strengths_weaknesses"]["vocabulario"]["status"] == "below_threshold"


def test_wais3_age_16_17_marks_icv_iop_as_significant_at_015():
    payload = compute_wais3_payload(
        {
            "idade": {"anos": 17, "meses": 0},
            "subtestes": {
                "cubos": {"pontos_brutos": 22},
                "codigos": {"pontos_brutos": 59},
                "digitos": {"pontos_brutos": 13},
                "aritmetica": {"pontos_brutos": 8},
                "informacao": {"pontos_brutos": 13},
                "compreensao": {"pontos_brutos": 27},
                "semelhancas": {"pontos_brutos": 22},
                "vocabulario": {"pontos_brutos": 36},
                "arranjo_figuras": {"pontos_brutos": 17},
                "completar_figuras": {"pontos_brutos": 18},
                "procurar_simbolos": {"pontos_brutos": 26},
                "raciocinio_matricial": {"pontos_brutos": 16},
                "sequencia_numeros_letras": {"pontos_brutos": 10},
            },
        }
    )

    discrepancy = payload["discrepancy_analysis"]["comprehension_vs_perceptual"]
    assert discrepancy["significance_level"] == "0,15"
    assert discrepancy["status"] == "significant"
    assert discrepancy["base_rate"] == 41.1


def test_wais3_keeps_partial_sums_when_arranjo_figuras_is_missing():
    raw_scores = {
        "idade": {"anos": 19, "meses": 0},
        "subtestes": {
            "cubos": {"pontos_brutos": 56},
            "codigos": {"pontos_brutos": 69},
            "digitos": {"pontos_brutos": 18},
            "aritmetica": {"pontos_brutos": 17},
            "informacao": {"pontos_brutos": 23},
            "compreensao": {"pontos_brutos": 30},
            "semelhancas": {"pontos_brutos": 31},
            "vocabulario": {"pontos_brutos": 50},
            "completar_figuras": {"pontos_brutos": 22},
            "procurar_simbolos": {"pontos_brutos": 40},
            "raciocinio_matricial": {"pontos_brutos": 22},
            "sequencia_numeros_letras": {"pontos_brutos": 12},
        },
    }

    payload = compute_wais3_payload(raw_scores)
    indices = payload.get("indices") or {}

    qi_exec = indices.get("qi_execucao") or {}
    qi_total = indices.get("qi_total") or {}

    assert qi_exec["subtestes_ausentes"] == ["arranjo_figuras"]
    assert qi_exec["subtestes_utilizados"] == [
        "completar_figuras",
        "codigos",
        "cubos",
        "raciocinio_matricial",
    ]
    assert qi_exec["soma_ponderada"] == 53
    assert qi_exec["pontuacao_composta"] == 103
    assert qi_exec["percentil"] == 58

    assert qi_total["subtestes_ausentes"] == ["arranjo_figuras"]
    assert qi_total["subtestes_utilizados"] == [
        "vocabulario",
        "semelhancas",
        "aritmetica",
        "digitos",
        "informacao",
        "compreensao",
        "completar_figuras",
        "codigos",
        "cubos",
        "raciocinio_matricial",
    ]
    assert qi_total["soma_ponderada"] == 141
    assert qi_total["pontuacao_composta"] == 117
    assert qi_total["percentil"] == 87
