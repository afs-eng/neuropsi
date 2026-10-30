from .config import DOMAINS, FORMS, SUBDOMAINS, TECHNICAL_NOTES
from .norms import age_months, age_table, domain_members, load_norms, lookup
from .validators import validate_input


def compute_scores(raw):
    errors = validate_input(raw)
    if errors:
        raise ValueError("; ".join(errors))
    form = raw["form"]
    months = age_months(raw)
    subtable = age_table(form, "subdomains", months)
    domtable = age_table(form, "domains", months)
    subdomains = []
    for key, value in raw["raw_scores"].items():
        score, _ = lookup(subtable["scores"][key], value)
        subdomains.append({"scale": key, "label": SUBDOMAINS[key], "raw_score": value, "v_scale": score})
    values = {row["scale"]: row["v_scale"] for row in subdomains}
    domains = []
    for key, members in domain_members(form).items():
        applicable = [member for member in members if subtable["scores"][member]]
        if not applicable or not all(member in values for member in applicable):
            continue
        total = sum(values[member] for member in applicable)
        score, percentile = lookup(domtable["scores"][key], total)
        domains.append({"scale": key, "label": DOMAINS[key], "sum_v_scale": total,
                        "standard_score": score, "percentile": percentile})
    total = sum(row["standard_score"] for row in domains if row["scale"] != "HMOT")
    score, percentile = lookup(domtable["scores"]["ABC"], total)
    domains.append({"scale": "ABC", "label": DOMAINS["ABC"], "sum_standard_scores": total,
                    "standard_score": score, "percentile": percentile})
    source = load_norms()["forms"][form]
    return {
        "form": form, "form_label": FORMS[form], "respondent": raw["respondent"].strip(),
        "age_months": months, "entry_mode": "totals", "subdomains": subdomains,
        "domains": domains, "results": subdomains + domains,
        "norm_source": {"population": "Normas americanas", "file": source["file"], "sha256": source["sha256"],
                        "subdomain_pages": subtable["pages"], "domain_pages": domtable["pages"]},
        "technical_notes": list(TECHNICAL_NOTES), "requires_clinical_review": True,
    }
