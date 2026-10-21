"""Resultados individuais do WAIS-III, sem tabelas normativas ou cópias de renderização."""

from copy import deepcopy


WAIS3_INPUT_VERSION = "1-wais3-2"
RESULT_KEYS = (
    "instrument_code", "instrument_name", "idade", "idade_normativa",
    "subtestes", "indices", "strengths_weaknesses", "discrepancy_analysis",
    "digitos", "gai_data", "clusters", "warnings", "has_scaled_score_data",
    "has_composite_data", "norm_tables_ready",
)


def _additional_results(original, additional) -> dict:
    """Conserva somente campos novos; divergências nunca elegem uma fonte."""
    if isinstance(original, dict) and isinstance(additional, dict):
        result = {}
        for key, value in additional.items():
            if key not in original:
                result[key] = deepcopy(value)
            else:
                delta = _additional_results(original[key], value)
                if delta:
                    result[key] = delta
        return result
    if original != additional or type(original) is not type(additional):
        raise ValueError("Resultados WAIS-III divergentes entre fontes calculadas/classificadas ou aliases.")
    return {}


def _selected_results(source: dict) -> dict:
    if not isinstance(source, dict):
        raise ValueError("Formato dos resultados WAIS-III inválido.")
    result = {key: deepcopy(source[key]) for key in RESULT_KEYS if key in source}
    if "composites" in source:
        composites = source["composites"]
        if "indices" in result:
            if (_additional_results(result["indices"], composites)
                    or _additional_results(composites, result["indices"])):
                raise ValueError("Aliases de índices WAIS-III divergentes.")
        else:
            result["indices"] = deepcopy(composites)
    return result


def wais3_specialist_sources(computed: dict, classified: dict) -> tuple[dict, dict]:
    computed = _selected_results(computed)
    classified = _selected_results(classified)
    warnings = classified.pop("warnings", [])
    if not isinstance(warnings, list) or not isinstance(computed.get("warnings", []), list):
        raise ValueError("Formato dos alertas WAIS-III inválido.")
    additional = _additional_results(computed, classified)
    new_warnings = [warning for warning in warnings if warning not in computed.get("warnings", [])]
    if new_warnings:
        additional["warnings"] = new_warnings
    return computed, additional
