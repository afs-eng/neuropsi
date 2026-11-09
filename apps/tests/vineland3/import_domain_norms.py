"""Reproducible extraction of parent/caregiver domain-level norms from supplied PDFs.

Run with PyMuPDF installed: python -m apps.tests.vineland3.import_domain_norms
No PDF text, watermarks or patient information is included in the output.
"""

import hashlib
import json
import re
from pathlib import Path

from .import_norms import age_range, raw_range

ROOT = Path(__file__).resolve().parents[3]
LABELS = ["COM", "AVD", "SOC", "CCA", "HMOT"]


def extract_c3(page):
    words = page.get_text("words")
    headers = sorted([w for w in words if w[4] in {"COM", "AVD", "DLS", "SOC", "ABC", "HMOT", "MOT"}
                      and w[1] < 100], key=lambda w: w[0])[-5:]
    if len(headers) != 5:
        raise ValueError("C.3: cabeçalho incompleto")
    centers = [(w[0] + w[2]) / 2 for w in headers]
    step = centers[1] - centers[0]

    def cell(x, y):
        found = [w[4] for w in words if abs(w[1] - y) < 1.5 and abs((w[0] + w[2]) / 2 - x) < step * .42]
        if len(found) > 1:
            raise ValueError(f"C.3: página {page.number+1}, x={x}, y={y}: célula ambígua: {found}")
        return found[0] if found else ""

    scores = {key: [] for key in LABELS}
    cis = {}
    for word in words:
        if word[4] in {"85%", "90%", "95%"} and word[0] < centers[0] - 5 * step:
            cis[word[4][:2]] = {key: (None if (v := cell(x, word[1])) in {"", "—", "–", "-"} else int(v))
                                for key, x in zip(LABELS, centers)}
        if abs((word[0] + word[2]) / 2 - (centers[0] - 7 * step)) > 3:
            continue
        if 78 < word[1] < 740 and word[4].isdigit() and 20 <= int(word[4]) <= 140:
            score = int(word[4])
            if cell(centers[-1] + 2 * step, word[1]) != str(score):
                raise ValueError("C.3: marcadores laterais divergentes")
            percentile = cell(centers[0] - 6 * step, word[1])
            for key, x in zip(LABELS, centers):
                interval = raw_range(cell(x, word[1]))
                if interval:
                    scores[key].append([*interval, score, percentile])
    return scores, cis


def extract_analysis(document):
    def text_of(page):
        text = page.get_text()
        for source, target in [("Table C.", "Tabela C."), ("Ages ", "Idades "),
                               ("Domain-Level Form Domains", "Domínios do Formulário de Níveis de Domínio"),
                               (" - Mean SS", " - EP Médio"), ("DLS", "AVD")]:
            text = text.replace(source, target)
        return re.sub(r"\bMOT\b", "HMOT", text)

    strengths = []
    for page in document:
        text = text_of(page)
        if "Tabela C.4" not in text or "Conteúdo" in text or "Table of Contents" in text:
            continue
        # Each age group contains extensive, subdomain and domain-level blocks.
        for match in re.finditer(r"Idades (\d+):\d+(?:[–-](\d+):\d+|(\+))", text):
            tail = text[match.end():]
            tail = re.split(r"Idades \d+:", tail)[0]
            block = tail.split("Domínios do Formulário de Níveis de Domínio")[1]
            rows = {}
            for row in re.finditer(r"(COM|AVD|SOC|HMOT) - EP Médio\s*([\d.\s]*?)(?=\n(?:COM|AVD|SOC|HMOT)|\n\d+\nVineland|$)", block):
                numbers = [float(v) for v in row[2].split()]
                if numbers and len(numbers) != 7:
                    raise ValueError(f"C.4: linha inválida {row[1]}: {numbers}")
                rows[row[1]] = numbers
            if len(rows) != 4:
                raise ValueError("C.4: bloco incompleto")
            strengths.append({"min_months": int(match[1]) * 12,
                              "max_months": None if match[3] else int(match[2]) * 12 + 11, "rows": rows})
    page = next(page for page in document if "Tabela C.5" in text_of(page) and "Conteúdo" not in text_of(page) and "Table of Contents" not in text_of(page))
    block = text_of(page).split("Domínios do Formulário de Níveis de Domínio")[1]
    pairs = {}
    for match in re.finditer(r"(COM|AVD|SOC) ([><]) (AVD|SOC|HMOT)\s*([\d.\s]*?)(?=\n(?:COM|AVD|SOC) [><]|\n\d+\nVineland|$)", block):
        values = [float(v) for v in match[4].split()]
        if len(values) != 14:
            raise ValueError(f"C.5: linha incompleta: {match[:3]}")
        pairs[f"{match[1]}{match[2]}{match[3]}"] = values
    if len(strengths) != 4 or len(pairs) != 12:
        raise ValueError("C.4/C.5: tabelas incompletas")
    return strengths, pairs


def extract_e2(document):
    page = next(page for page in document if any(t in page.get_text() for t in ("Tabela E.2", "Table E.2"))
                and "Conteúdo" not in page.get_text() and "Table of Contents" not in page.get_text())
    words = page.get_text("words")
    headers = sorted([w for w in words if w[4] in {"int", "ext"} and w[1] < 150], key=lambda w: w[0])
    if len(headers) != 10:
        raise ValueError("E.2: cabeçalho incompleto")
    centers = [(w[0] + w[2]) / 2 for w in headers]
    rows = [w for w in words if w[0] < headers[0][0] - 10 and w[4].isdigit()
            and 1 <= int(w[4]) <= 24 and headers[0][1] < w[1] < 700]
    result = [{"min_months": lo, "max_months": hi, "scores": {"internalizante": [], "externalizante": []}}
              for lo, hi in [(36, 83), (84, 143), (144, 251), (252, 839), (840, 1091)]]
    for row in rows:
        for index, x in enumerate(centers):
            found = [w[4] for w in words if abs(w[1] - row[1]) < 1.5 and abs((w[0] + w[2]) / 2 - x) < 12]
            if len(found) != 1:
                raise ValueError(f"E.2: célula ambígua: {found}")
            interval = raw_range(found[0])
            if interval:
                result[index // 2]["scores"]["internalizante" if index % 2 == 0 else "externalizante"].append([*interval, int(row[4])])
    return result


def extract(directory):
    import pymupdf

    paths = [directory / f"Vineland3_AppMan_APX_{letter}.pdf" for letter in ("C", "E")]
    with pymupdf.open(paths[0]) as document:
        tables = []
        for number, page in enumerate(document, 1):
            text = page.get_text()
            if "Tabela C.3" not in text or "Conteúdo" in text:
                continue
            lo, hi = age_range(text)
            scores, cis = extract_c3(page)
            if not tables or tables[-1]["min_months"] != lo:
                tables.append({"min_months": lo, "max_months": hi, "pages": [], "scores": {key: [] for key in LABELS}, "ci": {}})
            group = tables[-1]
            group["pages"].append(number)
            group["ci"].update(cis)
            for key in LABELS:
                group["scores"][key].extend(scores[key])
        strengths, pairs = extract_analysis(document)
    with pymupdf.open(paths[1]) as document:
        behavior = extract_e2(document)
    if len(tables) != 30:
        raise ValueError("C.3: esperadas 30 faixas etárias")
    for group in tables:
        if len(group["pages"]) != 3 or set(group["ci"]) != {"85", "90", "95"}:
            raise ValueError("C.3: páginas/IC incompletos")
    for group in [*tables, *behavior]:
        for key, entries in group["scores"].items():
            entries.sort()
            for previous, current in zip(entries, entries[1:]):
                if previous[1] + 1 != current[0]:
                    raise ValueError(f"Lacuna/sobreposição: {key}/{group['min_months']}")
    return {"version": 1, "population": "Normas americanas", "form": "pais_cuidadores_niveis_dominio",
            "sources": [{"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
            "domains": tables, "strengths": strengths, "pairs": pairs, "behavior": behavior}


if __name__ == "__main__":
    import sys

    if "--verify-english" in sys.argv:
        import pymupdf

        saved = json.loads(Path(__file__).with_name("domain_norms.json").read_text())
        checked = 0
        pages = 0
        intervals = 0
        with pymupdf.open(ROOT / "aux" / "vineland" / "vineland-3-manual-appendices.pdf") as document:
            for page in document:
                text = page.get_text()
                if "Table C.3" not in text or "Table of Contents" in text:
                    continue
                lo, _ = age_range(text)
                pages += 1
                group = next(g for g in saved["domains"] if g["min_months"] == lo)
                scores, cis = extract_c3(page)
                for key, entries in scores.items():
                    for entry in entries:
                        if entry not in group["scores"][key]:
                            raise ValueError(f"Divergência inglês: {lo}/{key}/{entry}")
                        checked += 1
                if cis and cis != group["ci"]:
                    raise ValueError(f"Divergência IC inglês: {lo}")
                if cis:
                    intervals += 1
            strengths, pairs = extract_analysis(document)
            if strengths != saved["strengths"] or pairs != saved["pairs"]:
                raise ValueError("Divergência inglês C.4/C.5")
            if extract_e2(document) != saved["behavior"]:
                raise ValueError("Divergência inglês E.2")
        if checked != sum(len(entries) for g in saved["domains"] for entries in g["scores"].values()) or pages != 90 or intervals != 30:
            raise ValueError("Conferência inglês incompleta")
        print({"english_c3_cells_verified": checked, "c3_pages": pages, "ci_age_groups": intervals,
               "c4_c5_e2_verified": True})
        sys.exit(0)
    output = extract(ROOT / "aux" / "vineland")
    Path(__file__).with_name("domain_norms.json").write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n")
    print({"age_groups": len(output["domains"]), "strengths": len(output["strengths"]), "pairs": len(output["pairs"]), "behavior": len(output["behavior"])})
