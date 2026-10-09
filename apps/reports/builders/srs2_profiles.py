import math

from apps.tests.srs2.interpreters import DISPLAY_NAMES, INTERPRETATION_ORDER, KEY_ALIASES


def profile_label(test: dict, index: int) -> str:
    raw = test.get("raw_payload") or {}
    form = (test.get("classified_payload") or {}).get("form") or raw.get("form") or ""
    if form == "adulto_autorrelato":
        label = "Autorrelato"
    elif form == "adulto_heterorrelato":
        label = "Heterorrelato"
    else:
        label = f"Aplicação {index + 1}"
    respondent = raw.get("respondent_name") or test.get("respondent_name")
    return f"{label} — {respondent}" if respondent else label


def profile_chart(test: dict):
    fallback = ["Perc.S", "Cog.S", "Com.S", "Mot.S", "PRR", "CIS", "TOTAL"]
    categories, values = [], []
    for index, row in enumerate((test.get("classified_payload") or {}).get("resultados") or []):
        key = row.get("variável") or row.get("variavel")
        key = KEY_ALIASES.get(key, key)
        categories.append(row.get("nome") or DISPLAY_NAMES.get(key) or (fallback[index] if index < len(fallback) else str(index + 1)))
        try:
            values.append(float(row.get("tscore")))
        except (TypeError, ValueError) as exc:
            raise ValueError("Escore T ausente no gráfico SRS-2.") from exc
    return categories, values


def comparable_profiles(tests: list[dict]):
    if len(tests) < 2:
        return [], [], []
    profiles = []
    families = set()
    for test in tests:
        form = (test.get("classified_payload") or {}).get("form") or (test.get("raw_payload") or {}).get("form")
        if not form:
            return [], [], []
        families.add("adulto" if form in {"adulto_autorrelato", "adulto_heterorrelato"} else form)
        rows = {}
        for row in (test.get("classified_payload") or {}).get("resultados") or []:
            key = row.get("variável") or row.get("variavel")
            key = KEY_ALIASES.get(key, key)
            try:
                score = float(row.get("tscore"))
            except (TypeError, ValueError):
                continue
            if key in INTERPRETATION_ORDER and math.isfinite(score):
                rows[key] = score
        profiles.append(rows)
    if len(families) != 1:
        return [], [], []
    keys = [key for key in INTERPRETATION_ORDER if all(key in profile for profile in profiles)]
    if not keys:
        return [], [], []
    return (
        [DISPLAY_NAMES[key] for key in keys],
        [[profile[key] for key in keys] for profile in profiles],
        [profile_label(test, index) for index, test in enumerate(tests)],
    )
