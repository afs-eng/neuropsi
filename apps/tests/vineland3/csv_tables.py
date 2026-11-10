"""Indexed local CSV loaders. Never expose the normative corpus through the API."""

import csv
import hashlib
import io
from collections import defaultdict
from functools import lru_cache

from .paths import TABELAS

FORMS = {"B": "entrevista", "C": "pais_cuidadores", "D": "professores"}
DOMAINS = ["COM", "AVD", "SOC", "CCA", "HMOT"]
SUBDOMAINS = ["rec", "exp", "esc", "pes", "dom", "com", "rin", "bri", "enf", "cmg", "cmf"]
STATS = ["critico_p10", "critico_p05", "base_2", "base_5", "base_10", "base_15", "base_25"]


def _read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


@lru_cache(maxsize=1)
def catalog():
    return tuple(_read_csv(TABELAS / "catalogo.csv"))


@lru_cache(maxsize=1)
def sources():
    return {r["apendice"]: {"file": r["arquivo"], "sha256": r["sha256"]}
            for r in _read_csv(TABELAS / "fontes.csv")}


@lru_cache(maxsize=600)
def _rows(relative):
    entry = next((r for r in catalog() if r["arquivo"] == relative), None)
    if entry is None:
        raise ValueError("Arquivo fora do catálogo normativo Vineland-3.")
    path = (TABELAS / relative).resolve()
    if not path.is_relative_to(TABELAS.resolve()):
        raise ValueError("Caminho normativo inválido.")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise ValueError(f"Tabela normativa alterada ou corrompida: {relative}.")
    result = tuple(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))
    if len(result) != int(entry["linhas"]):
        raise ValueError(f"Quantidade de linhas normativa divergente: {relative}.")
    return result


def _contains(row, months):
    return (not row["idade_min_meses"] or int(row["idade_min_meses"]) <= months) and (
        not row["idade_max_meses"] or months <= int(row["idade_max_meses"]))


def load_table(table, *, level=None, months=None, kind=None):
    """Read any B.1–E.3 table as copies of lossless CSV strings + metadata.

    Filter kind='ic' for confidence margins, or kind='dominios' for conversion.
    Empty strings mean no conversion, NEVER zero. This is a backend-only reader.
    """
    selected = [entry for entry in catalog() if entry["tabela"] == table and (kind is None or entry["tipo"] == kind)]
    if not selected:
        raise ValueError(f"Tabela normativa não encontrada: {table}.")
    result = []
    for entry in selected:
        if level is not None and entry["nivel"] not in {level, "misto"}:
            continue
        if months is not None and not _contains(entry, months):
            continue
        for row in _rows(entry["arquivo"]):
            value = {"formulario": entry["formulario"], "nivel": entry["nivel"], "tipo": entry["tipo"],
                     "idade_min_meses": entry["idade_min_meses"], "idade_max_meses": entry["idade_max_meses"], **row}
            if (level is None or value["nivel"] in {level, "misto"}) and (months is None or _contains(value, months)):
                result.append(value)
    return result


def _score_groups(appendix, kind, level):
    code = f"{appendix}.{1 if kind == 'subdomains' else 3}"
    records = [r for r in catalog() if r["tabela"] == code and r["nivel"] == level
               and r["tipo"] == ("subdominios" if kind == "subdomains" else "dominios")]
    labels = SUBDOMAINS.copy() if kind == "subdomains" else DOMAINS
    if appendix == "D" and kind == "subdomains":
        labels[4:6] = ["num", "cme"]
    result = []
    for record in records:
        rows = _rows(record["arquivo"])
        scores = {scale: [] for scale in labels}
        for row in rows:
            if row["entrada_min"] == "":
                continue
            percentile = row["percentil"] if kind == "domains" else None
            scores[row["escala"]].append([int(row["entrada_min"]), int(row["entrada_max"]), int(row["escore"]), percentile])
        for entries in scores.values():
            entries.sort()
        result.append({"min_months": int(record["idade_min_meses"]),
                       "max_months": int(record["idade_max_meses"]) if record["idade_max_meses"] else None,
                       "pages": [int(p) for p in record["paginas"].split(";")], "scores": scores})
    return result


def extensive_norms_from_csv():
    output = {"version": 1, "population": "Normas americanas", "forms": {}}
    for appendix, form in FORMS.items():
        groups = {kind: _score_groups(appendix, kind, "extensivo") for kind in ("subdomains", "domains")}
        for group in groups["domains"]:
            group["scores"] = {"ABC" if key == "CCA" else key: value for key, value in group["scores"].items()}
        output["forms"][form] = {**sources()[appendix], **groups}
    return output


def domain_norms_from_csv():
    domains = _score_groups("C", "domains", "niveis_dominio")
    cis = load_table("C.3", kind="ic", level="niveis_dominio")
    for group in domains:
        group["ci"] = {str(level): {} for level in (85, 90, 95)}
        for row in cis:
            if int(row["idade_min_meses"]) == group["min_months"]:
                group["ci"][row["confianca"]][row["escala"]] = int(row["margem"]) if row["margem"] else None
    strengths = {}
    for row in load_table("C.4", level="niveis_dominio"):
        lo = int(row["idade_min_meses"])
        group = strengths.setdefault(lo, {"min_months": lo, "max_months": int(row["idade_max_meses"]) if row["idade_max_meses"] else None, "rows": {}})
        group["rows"][row["escala"]] = [float(row[k]) for k in STATS] if row["critico_p05"] else []
    pairs = defaultdict(list)
    for row in load_table("C.5", level="niveis_dominio"):
        pairs[f"{row['escala']}{row['direcao']}{row['outra_escala']}"].extend(float(row[k]) for k in STATS)
    behavior = {}
    for row in load_table("E.2"):
        lo = int(row["idade_min_meses"])
        group = behavior.setdefault(lo, {"min_months": lo,
                                        # The domain-level form's C.3 ends at 90:11.
                                        "max_months": int(row["idade_max_meses"]) if row["idade_max_meses"] else 1091,
                                        "scores": {"internalizante": [], "externalizante": []}})
        if row["bruto_min"]:
            group["scores"][row["escala"]].append([int(row["bruto_min"]), int(row["bruto_max"]), int(row["escala_v"])])
    return {"version": 1, "population": "Normas americanas", "form": "pais_cuidadores_niveis_dominio",
            "sources": [sources()[letter] for letter in "CE"], "domains": domains,
            "strengths": list(strengths.values()), "pairs": dict(pairs), "behavior": list(behavior.values())}


@lru_cache(maxsize=3)
def domain_form_norms(form):
    """Domain-level norms for each informant, never extensive conversion columns."""
    appendix = next((key for key, value in FORMS.items() if value == form), None)
    if appendix is None:
        raise ValueError("Formulário Vineland-3 inválido.")
    domains = _score_groups(appendix, "domains", "niveis_dominio")
    cis = load_table(f"{appendix}.3", kind="ic", level="niveis_dominio")
    for group in domains:
        group["ci"] = {str(level): {} for level in (85, 90, 95)}
        for row in cis:
            if int(row["idade_min_meses"]) == group["min_months"]:
                group["ci"][row["confianca"]][row["escala"]] = int(row["margem"]) if row["margem"] else None

    def statistical_groups(number):
        groups = {}
        for row in load_table(f"{appendix}.{number}", level="niveis_dominio"):
            lo = int(row["idade_min_meses"])
            group = groups.setdefault(lo, {"min_months": lo,
                                          "max_months": int(row["idade_max_meses"]) if row["idade_max_meses"] else None, "rows": {}})
            key = row["escala"] if number == 4 else f"{row['escala']}{row['direcao']}{row['outra_escala']}"
            group["rows"][key] = [float(row[k]) if row[k] else None for k in STATS]
        return list(groups.values())

    behavior = {}
    enumber = {"B": 1, "C": 2, "D": 3}[appendix]
    for row in load_table(f"E.{enumber}"):
        lo = int(row["idade_min_meses"])
        group = behavior.setdefault(lo, {"min_months": lo,
                                        "max_months": int(row["idade_max_meses"]) if row["idade_max_meses"] else None,
                                        "scores": {"internalizante": [], "externalizante": []}})
        if row["bruto_min"]:
            group["scores"][row["escala"]].append([int(row["bruto_min"]), int(row["bruto_max"]), int(row["escala_v"])])
    return {"version": 1, "population": "Normas americanas", "form": form,
            "sources": [sources()[key] for key in (appendix, "E")], "domains": domains,
            "strengths": statistical_groups(4), "pairs_by_age": statistical_groups(5), "behavior": list(behavior.values()),
            "table_codes": f"{appendix}.3, {appendix}.4, {appendix}.5 e E.{enumber}"}
