from apps.tests.bfp.interpreters import build_bfp_interpretation, build_bfp_interpretation_payload, build_bfp_report_highlights


def _scale(code, name, classification, percentile, raw_score=3.5):
    return {
        "code": code,
        "name": name,
        "raw_score": raw_score,
        "percentile": percentile,
        "classification": classification,
    }


def _complete_payload():
    factor_names = {
        "NN": "Neuroticismo",
        "EE": "Extroversão",
        "SS": "Socialização",
        "RR": "Realização",
        "AA": "Abertura",
    }
    facet_names = {
        "N1": "Vulnerabilidade",
        "N2": "Instabilidade Emocional",
        "N3": "Passividade/Falta de Energia",
        "N4": "Depressão",
        "E1": "Comunicação",
        "E2": "Altivez",
        "E3": "Dinamismo",
        "E4": "Interações Sociais",
        "S1": "Amabilidade",
        "S2": "Pró-Sociabilidade",
        "S3": "Confiança nas Pessoas",
        "R1": "Competência",
        "R2": "Ponderação/Prudência",
        "R3": "Empenho/Comprometimento",
        "A1": "Abertura a Ideias",
        "A2": "Liberalismo",
        "A3": "Busca por Novidades",
    }
    return {
        "sample": "geral",
        "factors": {code: _scale(code, name, "Média", 50) for code, name in factor_names.items()},
        "facets": {code: _scale(code, name, "Média", 50) for code, name in facet_names.items()},
    }


def test_build_bfp_report_highlights_empty():
    payload = {}
    out = build_bfp_report_highlights(payload)
    assert isinstance(out, dict)
    assert out.get("summary") == "Perfil sem alterações clinicamente salientes nos fatores principais."
    assert out.get("relevant") == []


def test_build_bfp_report_highlights_elevation_and_reduction():
    payload = {
        "factors": {
            "NN": {"percentile": 90, "classification": "Muito elevado"},
            "RR": {"percentile": 10, "classification": "Reduzido"},
            "EE": {"percentile": 50, "classification": "Média"},
            "SS": {"percentile": 40, "classification": "Média"},
            "AA": {"percentile": 55, "classification": "Média"},
        }
    }
    out = build_bfp_report_highlights(payload)
    assert "elevação" in out.get("summary") or "redução" in out.get("summary")
    assert any(item["code"] == "NN" for item in out.get("relevant"))
    assert any(item["code"] == "RR" for item in out.get("relevant"))


def test_build_bfp_interpretation_includes_all_available_facets_and_cautions():
    payload = _complete_payload()
    payload["factors"]["NN"] = _scale("NN", "Neuroticismo", "Superior", 90)
    payload["facets"]["N4"] = _scale("N4", "Depressão", "Muito Superior", 99)
    payload["facets"]["S2"] = _scale("S2", "Pró-Sociabilidade", "Baixo", 10)
    payload["facets"]["A2"] = _scale("A2", "Liberalismo", "Média Inferior", 20)

    text = build_bfp_interpretation(payload, patient_name="Leticia Bolonha Lucati")

    assert text.startswith("INTERPRETAÇÃO DOS RESULTADOS")
    assert "\n\nNeuroticismo\n\n" in text
    assert "O resultado em Neuroticismo situa-se em faixa Superior" in text
    assert "Depressão em faixa Muito Superior" in text
    assert "exigindo investigação específica" in text
    assert "sem concluir comportamento antissocial ou ausência de ética" in text
    assert "sem inferência política, religiosa ou ideológica" in text
    assert "SÍNTESE INTEGRATIVA" in text
    assert "Síntese dos resultados" not in text
    assert "INTERPRETAÇÃO CLÍNICA" not in text
    assert "diagnóstico" in text
    assert "escore" not in text.lower()
    assert "percentil" not in text.lower()
    assert "Análise intrafator" not in text
    assert "Análise interfatores" not in text
    assert "A faceta apresentou" not in text
    assert "Depressão:" not in text
    assert "a maior" not in text
    assert "a menor" not in text


def test_build_bfp_interpretation_payload_compares_facets_within_factor():
    payload = _complete_payload()
    payload["factors"]["EE"] = _scale("EE", "Extroversão", "Média", 50)
    payload["facets"]["E1"] = _scale("E1", "Comunicação", "Muito Superior", 99)
    payload["facets"]["E4"] = _scale("E4", "Interações Sociais", "Baixo", 10)

    out = build_bfp_interpretation_payload(payload, patient_name="Paciente")

    assert "não se expressa de modo uniforme" in out["factors"]["EE"]
    assert "Comunicação aparece em faixa Muito Superior" in out["factors"]["EE"]
    assert "Interações Sociais se situa em Baixo" in out["factors"]["EE"]
    assert 2 <= len(out["synthesis"]) <= 4
