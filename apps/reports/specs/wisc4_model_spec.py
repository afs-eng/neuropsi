WISC4_REPORT_SPEC = {
    "title": "LAUDO DE AVALIAÇÃO NEUROPSICOLÓGICA",
    "subtitle": "De acordo com a Resolução de Elaboração de Documentos-CFP 006/2019",
    "sections": [
        "IDENTIFICAÇÃO",
        "DESCRIÇÃO DA DEMANDA",
        "PROCEDIMENTOS",
        "ANÁLISE",
        "ANÁLISE QUALITATIVA",
        "CONCLUSÃO",
        "CONDUTA E ENCAMINHAMENTOS",
        "CONSIDERAÇÕES FINAIS",
        "REFERÊNCIAS BIBLIOGRÁFICAS",
    ],
}

WISC4_LAYOUT_SPEC = {
    "font_family": "Times New Roman",
    "body_size_pt": 12,
    "table_size_pt": 9,
    "table_header_size_pt": 10,
    "caption_size_pt": 8,
    "body_line_spacing": 1.25,
}

WISC4_CHART_SPEC = {
    "title": "WISC-IV - INDICES DE QIS",
    "caption_template": "Gráfico {index} WISC-IV - INDICES DE QIS",
    "labels": ["QIT", "ICV", "IOP", "IMO", "IVP", "GAI", "CPI"],
    "y_label": "Valores de QI",
    "average_band": (90, 110),
    "average_band_color": "#DDF6FA",
    "background_color": "white",
    "data_label_size_pt": 10,
    "axis_label_size_pt": 10,
    "title_size_pt": 14,
}

WISC4_TABLE_SPECS = {
    "funcao_executiva": {
        "section_title": "Função Executiva",
        "caption": "Resultado da Função executiva",
        "columns": [
            "Testes Utilizados",
            "Escore Máximo",
            "Escore Médio",
            "Escore Mínimo",
            "Escore Obtido",
            "Classificação",
        ],
    },
    "linguagem": {
        "section_title": "Linguagem",
        "caption": "Resultados da Linguagem",
        "columns": [
            "Testes Utilizados",
            "Escore Máximo",
            "Escore Médio",
            "Escore Mínimo",
            "Escore Obtido",
            "Classificação",
        ],
    },
    "gnosias_praxias": {
        "section_title": "Gnosias e Praxias",
        "caption": "Resultados da Gnosias e praxias",
        "columns": [
            "Testes Utilizados",
            "Escore Máximo",
            "Escore Médio",
            "Escore Mínimo",
            "Escore Obtido",
            "Classificação",
        ],
    },
    "memoria_aprendizagem": {
        "section_title": "Memória e Aprendizagem",
        "caption": "Resultados de Memória e Aprendizagem",
        "columns": [
            "Testes Utilizados",
            "Escore Máximo",
            "Escore Médio",
            "Escore Mínimo",
            "Escore Obtido",
            "Classificação",
        ],
    },
    "bpa2": {
        "section_title": "BPA-2",
        "caption": "Atenção BPA-2 Resultados",
        "columns": [
            "ATENÇÃO BPA",
            "Pontos",
            "Percentil",
            "Classificação",
        ],
    },
    "ravlt": {
        "section_title": "RAVLT",
        "caption": "RAVLT Resultados",
        "columns": [
            "Desempenho", "A1", "A2", "A3", "A4", "A5", "B1", "A6", "A7",
            "R", "ALT", "RET", "I.P.", "I.R.",
        ],
    },
    "fdt": {
        "section_title": "FDT – TESTE DOS CINCO DÍGITOS",
        "caption": "FDT - Processos Automáticos e Controlados",
        "columns": [
            "Processo",
            "Tempo Médio",
            "Tempo Obtido",
            "Erros",
            "Desempenho",
            "Classificação",
        ],
    },
    "etdah_pais": {
        "section_title": "E-TDAH-PAIS",
        "caption": "E-TDAH-PAIS Resultados",
        "columns": [
            "Escala",
            "Pontos Brutos",
            "Média",
            "Percentil",
            "Classificação",
        ],
    },
    "etdah_ad": {
        "section_title": "E-TDAH-AD",
        "caption": "E-TDAH-AD Resultado",
        "columns": [
            "Escala",
            "Pontos Brutos",
            "Média",
            "Percentil",
            "Classificação",
        ],
    },
    "scared": {
        "section_title": "SCARED",
        "caption": "SCARED Resultados",
        "columns": [
            "Escala",
            "Pontos Brutos",
            "Média",
            "Percentil",
            "Classificação",
        ],
    },
    "epq_j": {
        "section_title": "EPQ-J",
        "caption": "EPQ-J Resultados da personalidade",
        "columns": [
            "Escala",
            "Escore Bruto",
            "Escore Médio",
            "Percentil",
            "Classificação",
        ],
    },
    "srs2": {
        "section_title": "SRS-2",
        "caption": "SRS-2 Resultados dos fatores",
        "columns": [
            "Escala",
            "Pontos Bruto",
            "T-Score",
            "Percentil",
            "Classificação",
        ],
    },
}

WISC4_QUALITY_RULES = {
    "document_ends_at_references": True,
    "all_tables_have_captions": True,
    "all_charts_have_captions": True,
    "no_patient_mix": True,
    "chart_indices_include_qit_icv_iop_imo_ivp_gai_cpi": True,
    "wisc4_average_band_90_110": True,
    "subscale_label_is_escore_obtido": True,
}
