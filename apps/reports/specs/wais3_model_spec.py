WAIS3_REPORT_SPEC = {
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

WAIS3_LAYOUT_SPEC = {
    "font_family": "Times New Roman",
    "body_size_pt": 12,
    "table_size_pt": 9,
    "table_header_size_pt": 10,
    "caption_size_pt": 8,
    "body_line_spacing": 1.25,
}

WAIS3_CHART_SPEC = {
    "title": "WAIS III - ÍNDICES DE QIS",
    "caption_template": "Gráfico {index} WAIS III - ÍNDICES DE QIS",
    "labels": ["ICV", "IOP", "IMO", "IVP", "QI Verbal", "QI Execução", "GAI", "QI Total"],
    "y_label": "Valores de QI",
    "average_band": (90, 110),
    "average_band_color": "#DDF6FA",
    "background_color": "white",
    "data_label_size_pt": 10,
    "axis_label_size_pt": 10,
    "title_size_pt": 14,
}

WAIS3_TABLE_SPECS = {
    "linguagem": {
        "section_title": "Linguagem",
        "caption": "Resultado da escala Linguagem",
        "columns": [
            "Testes Utilizados",
            "Escore Máximo",
            "Escore Médio",
            "Escore Mínimo",
            "Escore Bruto",
            "Classificação",
        ],
    },
    "gnosias_praxias": {
        "section_title": "Gnosias e Praxias",
        "caption": "Resultados da escala Gnosias e praxias",
        "columns": [
            "Testes Utilizados",
            "Escore Máximo",
            "Escore Médio",
            "Escore Mínimo",
            "Escore Bruto",
            "Classificação",
        ],
    },
    "funcao_executiva": {
        "section_title": "Função Executiva",
        "caption": "Resultados da escala Função Executiva",
        "columns": [
            "Testes Utilizados",
            "Escore Máximo",
            "Escore Médio",
            "Escore Mínimo",
            "Escore Bruto",
            "Classificação",
        ],
    },
    "memoria_aprendizagem": {
        "section_title": "Memória e Aprendizagem",
        "caption": "Resultados da escala Memória e Aprendizagem",
        "columns": [
            "Testes Utilizados",
            "Escore Máximo",
            "Escore Médio",
            "Escore Mínimo",
            "Escore Bruto",
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
    "ebadep_a": {
        "section_title": "EBADEP-A",
        "caption": "EBADEP-A - Resultado da sintomatologia",
        "columns": [
            "Indicador",
            "Valor",
        ],
    },
    "srs2_adulto": {
        "section_title": "SRS-2",
        "caption": "SRS-2 Adulto Autorrelato - Resultados dos fatores",
        "columns": [
            "Fator",
            "Pontos Brutos",
            "T-Score",
            "Percentil",
            "Classificação",
        ],
    },
}

WAIS3_QUALITY_RULES = {
    "document_ends_at_references": True,
    "all_tables_have_captions": True,
    "all_charts_have_captions": True,
    "no_patient_mix": True,
    "chart_indices_include_all_eight": True,
    "wais3_average_band_90_110": True,
    "subscale_label_is_escore_bruto": True,
}
