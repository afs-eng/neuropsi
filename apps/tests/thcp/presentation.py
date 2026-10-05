from .config import TECHNICAL_NOTES


def format_score(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return str(value)


def result_rows(data: dict) -> list[dict]:
    return [{
        **row,
        "raw_label": f"{row['raw_score']}/{row['max_score']}",
        "t_label": format_score(row.get("t_score")),
        "z_label": format_score(row.get("z_score")),
        "weighted_label": format_score(row.get("weighted_score")),
        "percentile_label": format_score(row.get("percentile")),
        "manual_label": row.get("manual_classification") or "—",
        "band_label": row.get("manual_percentile_band") or "—",
        "classification_label": row.get("classification") or "Indisponível",
    } for row in data.get("results", [])]


def docx_rows(data: dict) -> list[list[str]]:
    return [["Escala", "Bruto", "T-score", "Manual / faixa de percentil", "Percentil estimado", "Classificação Z"], *[
        [row["label"], row["raw_label"], row["t_label"],
         f"{row['manual_label']} / {row['band_label']}", row["percentile_label"], row["classification_label"]]
        for row in result_rows(data)
    ]]


def technical_notes(data: dict) -> list[str]:
    return [*TECHNICAL_NOTES, *data.get("warnings", [])]
