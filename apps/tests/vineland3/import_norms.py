"""Extract only extensive-form score tables, without copying PDF watermarks.

Run with: uv run --no-project --with pymupdf python apps/tests/vineland3/import_norms.py
"""

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FORMS = {"entrevista": "B", "pais_cuidadores": "C", "professores": "D"}
SUBDOMAINS = ["rec", "exp", "esc", "pes", "dom", "com", "rin", "bri", "enf", "cmg", "cmf"]
DOMAINS = ["COM", "AVD", "SOC", "ABC", "HMOT"]


def age_range(text):
    # D.3 repeats "Idades" in its heading; the final occurrence is authoritative.
    age = text.rsplit("Idades", 1)[1]
    match = re.match(r"\s*(\d+(?::\d+){0,2})(\+)?(?:\s*[–-]\s*(\d+(?::\d+){0,2}))?", age)
    if not match:
        raise ValueError(f"Faixa etária não reconhecida: {age[:100]}")

    def months(value):
        parts = [int(part) for part in value.split(":")]
        return parts[0] * 12 + (parts[1] if len(parts) > 1 else 0)

    low = months(match[1])
    return low, None if match[2] else months(match[3] or match[1])


def raw_range(value):
    if value in ("", "—", "–", "-"):
        return None
    match = re.fullmatch(r"(\d+)(?:[–-](\d+))?", value)
    if not match:
        raise ValueError(f"Escore não reconhecido: {value!r}")
    return int(match[1]), int(match[2] or match[1])


def extract_page(page, kind):
    words = page.get_text("words")
    labels = DOMAINS if kind == "domains" else SUBDOMAINS
    aliases = {"num": "dom", "cme": "com"}
    headers = sorted(
        [word for word in words if aliases.get(word[4], word[4]) in labels and word[1] < 100],
        key=lambda word: word[0],
    )[:len(labels)]
    if len(headers) != len(labels):
        raise ValueError("Cabeçalho incompleto")
    centers = [(word[0] + word[2]) / 2 for word in headers]
    step = centers[1] - centers[0]
    score_x = centers[0] - step * (2 if kind == "domains" else 1)
    right_x = centers[-1] + step * (7 if kind == "domains" else 1)
    rows = [word for word in words if abs((word[0] + word[2]) / 2 - score_x) < 3
            and word[1] > headers[0][1] + 5 and word[4].isdigit() and word[1] < 740]
    result = {label: [] for label in labels}
    row_scores = []
    for word in rows:
        score = int(word[4])
        if not (1 <= score <= 24 if kind == "subdomains" else 20 <= score <= 140):
            continue

        def cell(x):
            found = [w[4] for w in words if abs(w[1] - word[1]) < 1.5
                     and abs((w[0] + w[2]) / 2 - x) < step * 0.42]
            if len(found) > 1:
                raise ValueError(f"Célula ambígua: {found}")
            return found[0] if found else ""

        if cell(right_x) != str(score):
            raise ValueError(f"Marcadores laterais divergentes: {score}")
        row_scores.append(score)
        percentile = cell(centers[0] - step) if kind == "domains" else None
        if kind == "domains" and not re.fullmatch(r"[<>]?\d+", percentile):
            raise ValueError(f"Percentil inválido: {percentile}")
        for label, x in zip(labels, centers):
            interval = raw_range(cell(x))
            if interval:
                result[label].append([*interval, score, percentile])
    if kind == "subdomains" and row_scores != list(range(1, 25)):
        raise ValueError("Tabela de subdomínios deve conter 24 linhas")
    if kind == "domains" and len(row_scores) < 30:
        raise ValueError("Tabela de domínios incompleta")
    return result


def extract_norms(directory):
    import pymupdf

    output = {"version": 1, "population": "Normas americanas", "forms": {}}
    for form, appendix in FORMS.items():
        path = directory / f"Vineland3_AppMan_APX_{appendix}.pdf"
        tables = {"subdomains": [], "domains": []}
        with pymupdf.open(path) as document:
            for number, page in enumerate(document, 1):
                text = page.get_text()
                if "Conteúdo" in text:
                    continue
                for kind, table in [("subdomains", 1), ("domains", 3)]:
                    if not re.search(rf"Tabela {appendix}\.{table}\b", text):
                        continue
                    low, high = age_range(text)
                    scores = extract_page(page, kind)
                    if form == "professores" and kind == "subdomains":
                        scores = {{"dom": "num", "com": "cme"}.get(key, key): value for key, value in scores.items()}
                    target = next((t for t in tables[kind] if t["min_months"] == low), None)
                    if target is None:
                        target = {"min_months": low, "max_months": high, "pages": [], "scores": {k: [] for k in scores}}
                        tables[kind].append(target)
                    target["pages"].append(number)
                    for scale, entries in scores.items():
                        target["scores"][scale].extend(entries)
        for kind, groups in tables.items():
            groups.sort(key=lambda group: group["min_months"])
            for group in groups:
                for scale, entries in group["scores"].items():
                    entries.sort()
                    for previous, current in zip(entries, entries[1:]):
                        if previous[1] + 1 != current[0]:
                            raise ValueError(f"Lacuna/sobreposição: {form}/{kind}/{scale}/{group['min_months']}")
                if kind == "domains" and len(group["pages"]) != 3:
                    raise ValueError("Tabela de domínios deve ocupar três páginas")
        output["forms"][form] = {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), **tables}
    return output


if __name__ == "__main__":
    data = extract_norms(ROOT / "aux" / "vineland")
    destination = Path(__file__).with_name("norms.json")
    destination.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    print({form: {kind: len(value[kind]) for kind in ("subdomains", "domains")}
           for form, value in data["forms"].items()})
