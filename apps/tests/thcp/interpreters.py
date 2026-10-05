from .config import TECHNICAL_NOTES
from .presentation import format_score


def interpret_thcp_results(data: dict, patient_name: str) -> str:
    total = data.get("summary") or next((r for r in data.get("results", []) if r["code"] == "total"), {})
    if not total:
        return ""
    intro = (
        f"No THCP, {patient_name or 'o paciente'} obteve escore bruto total de {total['raw_score']} de 91 pontos, "
        f"com referência normativa {data.get('norm_label', 'não informada')} e T-score {format_score(total['t_score'])}."
    )
    if total.get("manual_classification"):
        intro += f" A classificação do manual é {total['manual_classification']}."
    if total.get("classification"):
        intro += f" A classificação por Z-score é {total['classification']}, com percentil estimado {format_score(total['percentile'])}."
    else:
        intro += " O intervalo de T-score não permite determinar percentil ou classificação por Z-score pontuais."
    details = []
    for row in data.get("results", []):
        if row["code"] == "total":
            continue
        details.append(
            f"{row['label']}: {row['raw_score']}/{row['max_score']} pontos; "
            f"faixa de percentil do manual {row['manual_percentile_band']} ({row['manual_classification']}); "
            f"percentil estimado {format_score(row['percentile'])} e classificação por Z-score {row.get('classification') or 'indisponível'}."
        )
    return "\n\n".join([intro, *details, *data.get("warnings", []), TECHNICAL_NOTES[-1]])
