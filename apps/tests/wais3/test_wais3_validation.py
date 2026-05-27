from apps.tests.wais3.schemas import WAIS3RawInput
from apps.tests.wais3.validators import validate_wais3_input


def test_validate_wais3_allows_missing_arranjo_figuras():
    data = WAIS3RawInput(
        idade={"anos": 30, "meses": 0},
        subtestes={
            "vocabulario": {"pontos_brutos": 36},
            "semelhancas": {"pontos_brutos": 22},
            "aritmetica": {"pontos_brutos": 8},
            "digitos": {"pontos_brutos": 13},
            "informacao": {"pontos_brutos": 13},
            "compreensao": {"pontos_brutos": 27},
            "completar_figuras": {"pontos_brutos": 18},
            "codigos": {"pontos_brutos": 59},
            "cubos": {"pontos_brutos": 22},
            "raciocinio_matricial": {"pontos_brutos": 16},
        },
    )

    errors = validate_wais3_input(data)

    assert "Subtestes obrigatórios ausentes para QI de Execução: arranjo_figuras" not in errors
    assert "Subtestes obrigatórios ausentes para QI Total: arranjo_figuras" not in errors


def test_validate_wais3_still_requires_other_execucao_subtests():
    data = WAIS3RawInput(
        idade={"anos": 30, "meses": 0},
        subtestes={
            "vocabulario": {"pontos_brutos": 36},
            "semelhancas": {"pontos_brutos": 22},
            "aritmetica": {"pontos_brutos": 8},
            "digitos": {"pontos_brutos": 13},
            "informacao": {"pontos_brutos": 13},
            "compreensao": {"pontos_brutos": 27},
            "codigos": {"pontos_brutos": 59},
            "cubos": {"pontos_brutos": 22},
            "raciocinio_matricial": {"pontos_brutos": 16},
        },
    )

    errors = validate_wais3_input(data)

    assert "Subtestes obrigatórios ausentes para QI de Execução: completar_figuras" in errors
