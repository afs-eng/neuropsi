from .config import FORMS, SUBDOMAINS
from .norms import age_months, age_table, lookup


def validate_input(raw):
    if not isinstance(raw, dict):
        return ["Dados Vineland-3 inválidos."]
    if raw.get("form") not in FORMS:
        return ["Selecione Entrevista, Pais/Cuidadores ou Professores."]
    if not isinstance(raw.get("respondent"), str) or not raw["respondent"].strip():
        return ["Identifique o respondente."]
    if raw.get("entry_mode", "totals") != "totals" or raw.get("item_responses") is not None:
        return ["Correção item a item ainda bloqueada: faltam protocolos e regras de aplicação verificados."]
    try:
        table = age_table(raw["form"], "subdomains", age_months(raw))
    except ValueError as error:
        return [str(error)]
    scores = raw.get("raw_scores")
    if not isinstance(scores, dict):
        return ["Informe as pontuações brutas por subdomínio."]
    active = {key: entries for key, entries in table["scores"].items() if entries}
    errors = []
    for key in scores.keys() - active.keys():
        errors.append(f"Subdomínio {key} não aplicável a este formulário/idade.")
    motors = {"cmg", "cmf"}
    required = active.keys() - motors
    if motors & scores.keys():
        required |= motors
    for key in sorted(required):
        if key not in scores:
            errors.append(f"Informe a pontuação de {SUBDOMAINS[key]}.")
    for key in scores.keys() & active.keys():
        try:
            lookup(active[key], scores[key])
        except ValueError as error:
            errors.append(f"{SUBDOMAINS[key]}: {error}")
    return errors
