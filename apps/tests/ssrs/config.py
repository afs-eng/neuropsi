SSRS_CODE = "ssrs"
SSRS_NAME = "SSRS - Inventario de Habilidades Sociais, Problemas de Comportamento e Competencia Academica"

SSRS_INFORMANTS = {
    "crianca": "Crianca",
    "pais": "Pais",
    "professores": "Professores",
}

SSRS_GENDERS = {
    "F": "Feminino",
    "M": "Masculino",
}

SSRS_DOMAINS = {
    "social_skills": "Habilidades Sociais",
    "behavior_problems": "Problemas de Comportamento",
    "academic_competence": "Competencia Academica",
}

SSRS_ITEMS = {
    "crianca": {
        "social_skills": {
            "f1": {"name": "Empatia/Afetividade", "items": [9, 10, 12, 16, 18]},
            "f2": {"name": "Responsabilidade", "items": [5, 6, 13, 14, 15]},
            "f3": {"name": "Autocontrole/Civilidade", "items": [1, 2, 4, 8, 11, 19]},
            "f4": {"name": "Assertividade", "items": [3, 7, 17, 20]},
        }
    },
    "pais": {
        "social_skills": {
            "f1": {"name": "Responsabilidade", "items": [8, 11, 12, 18]},
            "f2": {"name": "Autocontrole", "items": [7, 9, 13, 15, 16]},
            "f3": {"name": "Afetividade/Cooperacao", "items": [1, 6, 17, 21, 22, 23]},
            "f4": {"name": "Desenvoltura Social", "items": [3, 4, 5, 14]},
            "f5": {"name": "Civilidade", "items": [2, 10, 19, 20]},
        },
        "behavior_problems": {
            "f1": {"name": "Problemas externalizantes", "items": [24, 28, 29, 31, 32, 33, 34, 35, 36, 38]},
            "f2": {"name": "Problemas internalizantes", "items": [25, 26, 27, 30, 37]},
        },
    },
    "professores": {
        "social_skills": {
            "f1": {"name": "Responsabilidade", "items": [6, 10, 13, 14, 20, 21]},
            "f2": {"name": "Autocontrole", "items": [1, 4, 8, 9, 12, 18, 22]},
            "f3": {"name": "Assertividade/Desenvoltura Social", "items": [2, 3, 5, 7, 11]},
            "f4": {"name": "Cooperacao/Afetividade", "items": [15, 16, 17]},
        },
        "behavior_problems": {
            "f1": {"name": "Problemas externalizantes", "items": [23, 25, 31, 32, 33, 34]},
            "f2": {"name": "Hiperatividade", "items": [27, 28, 30, 36]},
            "f3": {"name": "Problemas internalizantes", "items": [24, 26, 29, 35]},
        },
        "academic_competence": {
            "eg": {"name": "Competencia academica geral", "items": [39, 40, 41, 42, 43, 44, 45, 46, 47]},
        },
    },
}

SSRS_EXPECTED_ITEMS = {
    "crianca": 20,
    "pais": 38,
    "professores": 47,
}
