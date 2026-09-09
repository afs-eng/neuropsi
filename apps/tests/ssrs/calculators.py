from .config import SSRS_ITEMS


def _normalize_response(value) -> int:
    if value is None or value == "":
        return 0
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(numeric, 5))


def _item_score(responses: dict, item: int) -> int:
    return _normalize_response(responses.get(str(item), responses.get(item, 0)))


def compute_ssrs_scores(responses: dict, informant: str) -> dict:
    config = SSRS_ITEMS[informant]
    domains = {}
    for domain, factors in config.items():
        factor_results = {}
        for code, factor in factors.items():
            score = sum(_item_score(responses, item) for item in factor["items"])
            factor_results[code] = {
                "name": factor["name"],
                "raw_score": score,
                "items": factor["items"],
            }
        domains[domain] = {
            "eg": sum(item["raw_score"] for item in factor_results.values()),
            "factors": factor_results,
        }
    return {"informant": informant, "domains": domains}


def compute_ssrs_importance(importance: dict, informant: str) -> dict:
    factors = SSRS_ITEMS.get(informant, {}).get("social_skills", {})
    factor_results = {}
    for code, factor in factors.items():
        factor_results[code] = {
            "name": factor["name"],
            "raw_score": sum(_item_score(importance, item) for item in factor["items"]),
            "items": factor["items"],
        }
    return {
        "eg": sum(item["raw_score"] for item in factor_results.values()),
        "factors": factor_results,
    }
