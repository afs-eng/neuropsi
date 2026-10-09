"""Present saved scale results without calculating scores or normative cutoffs."""

import math


def saved_scale_rows(test: dict) -> list[dict]:
    results = test.get("report_results") or (test.get("report_payload") or {}).get("results")
    if not results:
        for payload in (test.get("structured_results"), test.get("classified_payload"), test.get("computed_payload")):
            if not isinstance(payload, dict):
                continue
            results = payload.get("results") or payload.get("resultados") or payload.get("dimensions") or payload.get("factors")
            if results:
                break
    if isinstance(results, dict):
        results = [{"scale": key, **value} for key, value in results.items() if isinstance(value, dict)]
    rows = []
    for result in results or []:
        if not isinstance(result, dict):
            continue
        def first_value(*keys):
            return next((result[key] for key in keys if result.get(key) is not None), None)

        label = first_value("scale", "name", "nome", "label")
        if not label:
            continue
        rows.append({
            "label": str(label),
            "score": first_value("raw_score", "escore_bruto", "score", "valor", "bruto"),
            "percentile": first_value("percentil", "percentile"),
            "classification": first_value("classificacao", "classification", "classificação"),
        })
    return rows


def numeric_profile(rows: list[dict], field: str):
    labels, values = [], []
    for row in rows:
        try:
            score = float(row.get(field))
        except (TypeError, ValueError):
            continue
        if math.isfinite(score):
            labels.append(row["label"])
            values.append(score)
    return labels, values
