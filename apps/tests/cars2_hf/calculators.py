from __future__ import annotations

from .constants import ITEMS
from .loaders import load_cars2_hf_norms


def calculate_raw_total(items: dict) -> float:
    total = sum(float(items[key]["score"]) for key, _ in ITEMS)
    return float(int(total))


def convert_raw_to_norms(raw_total: float) -> dict:
    for row in load_cars2_hf_norms():
        if row["raw_min"] <= raw_total <= row["raw_max"]:
            return {"t_score": row["t_score"], "percentile": row["percentile"]}

    return {"t_score": None, "percentile": None}


def get_highest_domains(items: dict, top_n: int = 3) -> list[str]:
    sorted_items = sorted(
        items.items(), key=lambda pair: pair[1]["score"], reverse=True
    )
    return [name for name, _ in sorted_items[:top_n]]


def build_computed_payload(payload: dict) -> dict:
    items = payload["items"]
    raw_total = calculate_raw_total(items)
    norms = convert_raw_to_norms(raw_total)

    return {
        "raw_total": raw_total,
        "t_score": norms["t_score"],
        "percentile": norms["percentile"],
        "highest_domains": get_highest_domains(items),
        "domain_scores": {key: items[key]["score"] for key, _ in ITEMS},
    }
