from __future__ import annotations

from .constants import WAIS3_ALL_SUBTESTS, WAIS3_INDEXES, WAIS3_MAX_AGE, WAIS3_MIN_AGE
from .schemas import WAIS3RawInput


_WAIS3_OPTIONAL_MISSING_BY_INDEX = {
    "qi_execucao": {"arranjo_figuras"},
    "qi_total": {"arranjo_figuras"},
}


def validate_wais3_input(data: WAIS3RawInput) -> list[str]:
    errors: list[str] = []

    if data.idade.anos < WAIS3_MIN_AGE or data.idade.anos > WAIS3_MAX_AGE:
        errors.append("WAIS-III é indicado para a faixa etária de 16 a 89 anos.")

    invalid_keys = [key for key in data.subtestes if key not in WAIS3_ALL_SUBTESTS]
    if invalid_keys:
        errors.append("Subtestes inválidos no payload do WAIS-III: " + ", ".join(sorted(invalid_keys)))

    for key, item in data.subtestes.items():
        if item.pontos_brutos < 0:
            errors.append(f"{WAIS3_ALL_SUBTESTS.get(key, key)}: pontos brutos não podem ser negativos.")

    for index_key, index_cfg in WAIS3_INDEXES.items():
        optional_missing = _WAIS3_OPTIONAL_MISSING_BY_INDEX.get(index_key, set())
        missing = [code for code in index_cfg["subtests"] if code not in data.subtestes and code not in optional_missing]
        if index_key in {"qi_verbal", "qi_execucao", "qi_total"} and missing:
            errors.append(
                f"Subtestes obrigatórios ausentes para {index_cfg['label']}: {', '.join(missing)}"
            )

    return errors
