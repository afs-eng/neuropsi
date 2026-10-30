import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from dateutil.relativedelta import relativedelta


@lru_cache(maxsize=1)
def load_norms():
    return json.loads(Path(__file__).with_name("norms.json").read_text())


def age_months(raw):
    try:
        birth = date.fromisoformat(raw["birth_date"])
        applied = date.fromisoformat(raw["reference_date"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Informe datas válidas de nascimento e aplicação.") from error
    if applied < birth:
        raise ValueError("A aplicação não pode anteceder o nascimento.")
    delta = relativedelta(applied, birth)
    return delta.years * 12 + delta.months


def age_table(form, kind, months):
    try:
        tables = load_norms()["forms"][form][kind]
    except KeyError as error:
        raise ValueError("Formulário Vineland-3 inválido.") from error
    for table in tables:
        if table["min_months"] <= months and (table["max_months"] is None or months <= table["max_months"]):
            return table
    raise ValueError("Não há normas para este formulário e idade (Professores: 3 anos a 18 anos e 11 meses).")


def lookup(entries, raw):
    if type(raw) is not int:
        raise ValueError("A pontuação deve ser um número inteiro.")
    for low, high, score, percentile in entries:
        if low <= raw <= high:
            return score, percentile
    raise ValueError(f"Pontuação {raw} fora da tabela normativa; não será extrapolada.")


def domain_members(form):
    return {
        "COM": ["rec", "exp", "esc"],
        "AVD": ["pes", "num", "cme"] if form == "professores" else ["pes", "dom", "com"],
        "SOC": ["rin", "bri", "enf"], "HMOT": ["cmg", "cmf"],
    }
