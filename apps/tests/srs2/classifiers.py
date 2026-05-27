from .norms import classify_tscore, get_age_band, get_norm_data


SCORE_KEYS = [
    "percepção_social",
    "cognição_social",
    "comunicação_social",
    "motivação_social",
    "padrões_restritos",
    "cis",
    "total",
]


def classify_srs2_scores(computed_data: dict, gender: str = "M", age: int = 10) -> dict:
    form = computed_data.get("form", "idade_escolar")
    age_band = get_age_band(age, form)

    results = []
    for key in SCORE_KEYS:
        score_data = computed_data.get(key, {})
        raw = score_data.get("escore", 0)

        tscore, percentil = get_norm_data(raw, form, gender, key)
        classification = classify_tscore(tscore)

        results.append(
            {
                "variável": key,
                "nome": score_data.get("nome", key),
                "bruto": raw,
                "max": score_data.get("max", 0),
                "tscore": tscore,
                "percentil": percentil,
                "classificação": classification,
            }
        )

    return {
        "faixa_etária": age_band,
        "form": form,
        "resultados": results,
    }
