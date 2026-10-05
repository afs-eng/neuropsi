def classify_z_score(z_score: float | None) -> str | None:
    if z_score is None:
        return None
    for cutoff, label in [
        (2, "Muito Superior"), (1.333, "Superior"), (0.666, "Média Superior"),
        (-0.666, "Média"), (-1.333, "Média Inferior"), (-2, "Limítrofe"),
    ]:
        if z_score >= cutoff:
            return label
    return "Deficitário"


def classify_thcp_scores(computed: dict) -> dict:
    results = []
    for row in computed["results"]:
        # Classify before display rounding: a rounded Z must not change a boundary.
        if row.get("mean") is not None:
            z = (row["raw_score"] - row["mean"]) / row["sd"]
        elif isinstance(row["t_score"], (int, float)):
            z = (row["t_score"] - 50) / 10
        else:
            z = None
        results.append({**row, "classification": classify_z_score(z)})
    return {"results": results, "summary": results[-1], "warnings": computed["warnings"]}
