INTERPRETATIONS = {
    "Sintomatologia Depressiva Mínima (sem sintomatologia)": {
        "geral": "O resultado situa-se na classificação normativa de sintomatologia depressiva mínima, sem indicação de elevação no escore total da escala. A interpretação deve ser integrada aos demais dados clínicos e contextuais do processo avaliativo.",
        "nivel": "mínimo",
        "descricao": "ausência de sintomatologia depressiva clinicamente relevante",
        "cor": "positivo",
    },
    "Sintomatologia Depressiva Leve": {
        "geral": "O resultado situa-se na classificação normativa de sintomatologia depressiva leve. Esse achado indica presença de indicadores leves no escore total da escala, devendo ser interpretado como dado de rastreio e integrado à entrevista clínica e às demais informações disponíveis.",
        "nivel": "leve",
        "descricao": "sintomatologia depressiva leve",
        "cor": "leve",
    },
    "Sintomatologia Depressiva Moderada": {
        "geral": "O resultado situa-se na classificação normativa de sintomatologia depressiva moderada. Esse achado indica presença aumentada de indicadores depressivos no escore total da escala, recomendando investigação clínica cuidadosa dos sintomas referidos, de sua duração, intensidade e repercussão contextual.",
        "nivel": "moderado",
        "descricao": "sintomatologia depressiva moderada",
        "cor": "moderado",
    },
    "Sintomatologia Depressiva Severa": {
        "geral": "O resultado situa-se na classificação normativa de sintomatologia depressiva severa. Esse achado indica presença elevada de indicadores depressivos no escore total da escala e demanda avaliação clínica criteriosa, especialmente quanto a humor deprimido, anedonia, desesperança e itens de risco quando presentes.",
        "nivel": "severo",
        "descricao": "sintomatologia depressiva severa",
        "cor": "grave",
    },
}

SYNTHESIS_LEVELS = {
    "Sintomatologia Depressiva Mínima (sem sintomatologia)": "sem indicadores significativos de depressão",
    "Sintomatologia Depressiva Leve": "com indicadores leves de sintomatologia depressiva",
    "Sintomatologia Depressiva Moderada": "com indicadores moderados de sintomatologia depressiva",
    "Sintomatologia Depressiva Severa": "com indicadores severos de sintomatologia depressiva",
}


def interpret_result(classificacao: str) -> dict:
    return INTERPRETATIONS.get(
        classificacao,
        {
            "geral": "Classificação não disponível.",
            "nivel": "indefinido",
            "descricao": "não classificado",
            "cor": "neutro",
        },
    )


def get_synthesis(classificacao: str) -> str:
    return SYNTHESIS_LEVELS.get(classificacao, "não classificado")


def get_report_interpretation(classificacao: str, nome: str) -> str:
    interp = INTERPRETATIONS.get(classificacao, {})
    return interp.get("geral", "Interpretação não disponível.")


def build_pdf_interpretation(score, percentile, classification: str, patient_name: str) -> dict:
    interpretation = get_report_interpretation(classification, patient_name)
    integrated = (
        f"Na análise integrada do EBADEP-A, o escore total de {patient_name} foi {score}, correspondente ao percentil {percentile}, "
        f"com classificação normativa {classification}. Por se tratar de uma medida de rastreio unifatorial, a leitura deve se concentrar no escore total e nos itens assinalados, sem criar comparação entre domínios que não fazem parte da estrutura desta impressão."
    )
    synthesis = (
        f"A EBADEP-A apresentou escore total {score}, percentil {percentile}, classificado como {classification}. "
        "O resultado deve ser compreendido como indicador psicométrico de sintomatologia depressiva e integrado à anamnese, entrevista clínica, observação e demais dados do processo avaliativo."
    )
    return {
        "factor_interpretation": interpretation,
        "integrated_analysis": integrated,
        "synthesis": synthesis,
    }
