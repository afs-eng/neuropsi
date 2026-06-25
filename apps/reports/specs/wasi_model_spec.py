from __future__ import annotations

WASI_REPORT_SPEC = {
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

WASI_LAYOUT_SPEC = {
    "font_family": "Times New Roman",
    "body_size_pt": 12,
    "table_size_pt": 10,
    "table_header_size_pt": 10,
    "caption_size_pt": 8,
    "body_line_spacing": 1.15,
}

WASI_CHART_SPEC = {
    "title": "WASI - INDICES DE QIS",
    "caption_template": "Gráfico {index} WASI - INDICES DE QIS",
    "labels": ["QIV", "QIE", "QIT"],
    "y_label": "Valores de QI",
    "average_band": (90, 110),
    "average_band_color": "#F4C2F4",
    "background_color": "white",
    "data_label_size_pt": 10,
    "axis_label_size_pt": 10,
    "title_size_pt": 14,
}

WASI_TABLE_SPECS = {
    "verbal": {
        "section_title": "5.2.1. Escala Verbal",
        "caption": "Resultado da escala verbal",
        "columns": [
            "Testes Utilizados",
            "Escore Máximo",
            "Escore Médio",
            "Escore Mínimo",
            "Escore Obtido",
            "Classificação",
        ],
    },
    "execucao": {
        "section_title": "5.2.2. Escala de Execução",
        "caption": "Resultados da escala de execução",
        "columns": [
            "Testes Utilizados",
            "Escore Máximo",
            "Escore Médio",
            "Escore Mínimo",
            "Escore Obtido",
            "Classificação",
        ],
    },
}

WASI_QUALITY_RULES = {
    "document_ends_at_references": True,
    "all_tables_have_captions": True,
    "all_charts_have_captions": True,
    "no_patient_mix": True,
    "wasi_average_band_90_110": True,
}
