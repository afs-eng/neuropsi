"""Extract ALL B–E tables from the supplied PDFs, including rotated tables.

Development only: uv run --no-project --with pymupdf python -m
apps.tests.vineland3.import_csv_tables [--verify-english]
Runtime reads CSVs and does not require PDF libraries or the source PDFs.
"""

import argparse
import csv
import hashlib
import io
import re
from collections import Counter, defaultdict
from pathlib import Path

from .import_norms import age_range, raw_range
from .paths import TABELAS

ROOT = Path(__file__).resolve().parents[3]
FORMS = {"B": "entrevista", "C": "pais_cuidadores", "D": "professores"}
SUBDOMAINS = ["rec", "exp", "esc", "pes", "dom", "com", "rin", "bri", "enf", "cmg", "cmf"]
DOMAINS = ["COM", "AVD", "SOC", "CCA", "HMOT"]
STATS = ["critico_p10", "critico_p05", "base_2", "base_5", "base_10", "base_15", "base_25"]
ALIASES = {"wrn": "esc", "per": "pes", "cmm": "com", "ipr": "rin", "pla": "bri", "cop": "enf",
           "gmo": "cmg", "fmo": "cmf", "scm": "com", "DLS": "AVD", "MOT": "HMOT", "ABC": "CCA"}
AGE = r"\d+(?::\d+){0,2}(?:[–-]\d+(?::\d+){0,2})?\+?"
EXPECTED_PAGES = {**{f"{a}{k}": n for a in "BC" for k, n in [(1, 90), (2, 4), (3, 90), (4, 2), (5, 1), (6, 4)]},
                  **{f"D{k}": n for k, n in [(1, 46), (2, 3), (3, 69), (4, 1), (5, 1), (6, 4)]},
                  "E1": 1, "E2": 1, "E3": 1}
EXPECTED_STATS_ROWS = {"B4": 76, "C4": 76, "D4": 38, "B5": 72, "C5": 48, "D5": 48,
                       "B6": 330, "C6": 220, "D6": 220}


def normalize_text(text):
    for a, b in [("Table ", "Tabela "), ("Ages ", "Idades "), ("Age ", "Idades "),
                 ("Domain-Level Form Domains", "Domínios do Formulário de Níveis de Domínio"),
                 ("Comprehensive Form Domains", "Domínios do Formulário Extensivo"),
                 ("Comprehensive Form Subdomains", "Subdomínios do Formulário Extensivo"),
                 (" - Mean SS", " - EP Médio"), (" - Mean vS", " - Ev Médio")]:
        text = text.replace(a, b)
    return text


def bounds(label):
    label = label.replace("–", "-")
    # E.1/E.2 print 70–90+; preserve the open upper limit rather than guessing.
    if label.endswith("+"):
        lo = label.split("-")[0].rstrip("+")
        return age_range(f"Idades {lo}+")
    if ":" not in label:
        parts = [int(part) for part in label.split("-")]
        return parts[0] * 12, parts[-1] * 12 + 11
    return age_range(f"Idades {label}")


def age_filename(lo, hi):
    return f"idade_{lo:04d}_{hi:04d}.csv" if hi is not None else f"idade_{lo:04d}_mais.csv"


def numeric(value):
    if value in {"", "—", "–", "-"}:
        return ""
    if not re.fullmatch(r"\d+(?:\.\d+)?", value):
        raise ValueError(f"Número inválido: {value!r}")
    return value


class Grid:
    """Words in the table's reading direction, excluding copyright and footers."""

    def __init__(self, page):
        textpage = page.get_textpage()
        lines = {(block.get("number", bi), li): tuple(line["dir"]) for bi, block in enumerate(textpage.extractDICT()["blocks"])
                 for li, line in enumerate(block.get("lines", []))}
        direction = Counter(lines.values()).most_common(1)[0][0]
        rotated = direction == (0.0, -1.0)
        self.height = page.rect.width if rotated else page.rect.height
        self.words = []
        self.page = page.number + 1
        for x0, y0, x1, y1, text, bi, li, _ in textpage.extractWORDS():
            if lines[(bi, li)] != direction:
                continue
            if rotated:
                x0, y0, x1, y1 = page.rect.height - y1, x0, page.rect.height - y0, x1
            if 25 < y0 < self.height - 35:
                self.words.append((x0, y0, x1, y1, text))
        self.rows = []
        for word in sorted(self.words, key=lambda w: (w[1], w[0])):
            if not self.rows or abs(word[1] - self.rows[-1][0][1]) > 1.5:
                self.rows.append([word])
            else:
                self.rows[-1].append(word)
        self.rows = [sorted(row, key=lambda w: w[0]) for row in self.rows]

    @staticmethod
    def x(word):
        return (word[0] + word[2]) / 2

    def cell(self, x, y, tolerance=12):
        found = [w[4] for w in self.words if abs(w[1] - y) < 1.5 and abs(self.x(w) - x) < tolerance]
        if len(found) > 1:
            raise ValueError(f"Página {self.page}: célula ambígua em {x}/{y}: {found}")
        return found[0] if found else ""

    def age_headers(self):
        labels = []
        for row in self.rows:
            text = normalize_text(" ".join(w[4] for w in row))
            if row[0][1] < 100:
                labels.extend(m[1] for m in re.finditer(rf"Idades\s+({AGE})", text))
        return labels


def score_rows(page, kind):
    grid = Grid(page)
    aliases = {**ALIASES}
    if kind == 1:
        labels = SUBDOMAINS.copy()
        if "Tabela D.1" in normalize_text(page.get_text()):
            labels[4:6] = ["num", "cme"]
            aliases.update(scm="cme", cmm="cme")
        headers = sorted([w for w in grid.words if aliases.get(w[4], w[4]) in labels and w[1] < 100], key=grid.x)
        expected = len(labels)
    else:
        labels = DOMAINS * 2
        headers = sorted([w for w in grid.words if aliases.get(w[4], w[4]) in DOMAINS and w[1] < 100], key=grid.x)
        expected = 10
    if len(headers) != expected:
        raise ValueError(f"Página {grid.page}: cabeçalho de escores incompleto ({len(headers)}/{expected})")
    xs = [grid.x(w) for w in headers]
    step = xs[1] - xs[0]
    left = xs[0] - (step if kind == 1 else 2 * step)
    right = xs[-1] + (step if kind == 1 else 2 * step)
    valid_scores = range(1, 25) if kind == 1 else range(20, 141)
    markers = sorted([w for w in grid.words if abs(grid.x(w) - left) < 3 and w[1] > headers[0][1] + 5
                      and w[4].isdigit() and int(w[4]) in valid_scores], key=lambda w: w[1])
    output = []
    for marker in markers:
        score, y = int(marker[4]), marker[1]
        if grid.cell(right, y, step * .42) != str(score):
            raise ValueError(f"Página {grid.page}: marcadores laterais divergentes")
        percentile = grid.cell(left + step, y, step * .42) if kind == 3 else ""
        if kind == 3 and not re.fullmatch(r"[<>]?\d+", percentile):
            raise ValueError("Percentil inválido")
        for index, (label, x) in enumerate(zip(labels, xs)):
            interval = raw_range(grid.cell(x, y, step * .42))
            output.append({"nivel": "niveis_dominio" if kind == 3 and index >= 5 else "extensivo",
                           "escala": label, "entrada_min": interval[0] if interval else "",
                           "entrada_max": interval[1] if interval else "", "escore": score,
                           "percentil": percentile, "pagina": grid.page})
    if kind == 1 and len(markers) != 24 or kind == 3 and len(markers) < 30:
        raise ValueError(f"Página {grid.page}: linhas de escores incompletas")
    ci = []
    if kind == 3:
        for word in grid.words:
            if word[4] not in {"85%", "90%", "95%"} or abs(grid.x(word) - (left + step)) > 5:
                continue
            for index, (label, x) in enumerate(zip(labels, xs)):
                ci.append({"nivel": "niveis_dominio" if index >= 5 else "extensivo", "escala": label,
                           "confianca": word[4][:2], "margem": numeric(grid.cell(x, word[1], step * .42)), "pagina": grid.page})
    return output, ci


def equivalent_rows(page):
    grid = Grid(page)
    headers = sorted([w for w in grid.words if w[4] in {"IE", "EI", "AE", "VEC", "GSV"} and w[1] < 105], key=grid.x)
    if len(headers) != 22:
        raise ValueError(f"Página {grid.page}: EI/VEC incompleto")
    xs = [grid.x(w) for w in headers]
    labels = SUBDOMAINS.copy()
    if "Tabela D.2" in normalize_text(page.get_text()):
        labels[4:6] = ["num", "cme"]
    left = xs[0] - (xs[1] - xs[0])
    right = xs[-1] + (xs[1] - xs[0])
    markers = sorted([w for w in grid.words if abs(grid.x(w) - left) < 3 and w[1] > headers[0][1] + 5 and w[4].isdigit()], key=lambda w: w[1])
    result = []
    for marker in markers:
        if grid.cell(right, marker[1]) != marker[4]:
            raise ValueError(f"Página {grid.page}: marcador EI/VEC divergente")
        for index, label in enumerate(labels):
            age = grid.cell(xs[index * 2], marker[1])
            if age in {"—", "–", "-"}:
                age = ""
            if age and not re.fullmatch(r"[<>]?\d+:\d+\+?", age):
                raise ValueError(f"Equivalente etário inválido: {age}")
            result.append({"escala": label, "bruto": marker[4], "equivalente_idade": age,
                           "vec": numeric(grid.cell(xs[index * 2 + 1], marker[1])), "pagina": grid.page})
    if not markers:
        raise ValueError("EI/VEC sem linhas")
    return result


def statistics_rows(page, kind):
    grid = Grid(page)
    aliases = {**ALIASES}
    if re.search(r"Tabela D\.", normalize_text(page.get_text())):
        aliases.update(scm="cme", cmm="cme")
    headers = sorted([w for w in grid.words if w[4] in {".10", ".05", "≤2%", "≤5%", "≤10%", "≤15%", "≤25%"}
                      and w[1] < 100], key=grid.x)
    if not headers or len(headers) % 7:
        raise ValueError(f"Página {grid.page}: cabeçalho estatístico incompleto")
    xs = [grid.x(w) for w in headers]
    age_labels = grid.age_headers() if kind != 4 else []
    if kind != 4 and len(age_labels) != len(headers) // 7:
        raise ValueError(f"Página {grid.page}: faixas estatísticas incompletas: {age_labels}")
    level, category, age = "extensivo", "subdominio" if kind == 6 else "dominio", None
    result = []
    for row in grid.rows:
        text = normalize_text(" ".join(w[4] for w in row))
        if "Formulário de Níveis de Domínio" in text:
            level, category = "niveis_dominio", "dominio"
        elif "Subdomínios do Formulário" in text:
            level, category = "extensivo", "subdominio"
        elif "Domínios do Formulário" in text:
            level = "niveis_dominio" if "Níveis de Domínio" in text else "extensivo"
            category = "dominio"
        if kind == 4:
            if match := re.search(rf"Idades\s+({AGE})", text):
                age = match[1]
            match = re.match(r"([A-Za-z]+)\s*-\s*(?:EP|[Ee][Vv]|vS)\s+Médio", text)
        else:
            match = re.match(r"([A-Za-z]+)\s*([><])\s*([A-Za-z]+)", text)
        if not match:
            continue
        values = [numeric(grid.cell(x, row[0][1], 10)) for x in xs]
        for index in range(len(xs) // 7):
            label = age if kind == 4 else age_labels[index]
            if label is None:
                raise ValueError("Faixa etária ausente")
            low, high = bounds(label)
            entry = {"nivel": level, "categoria": category, "idade_min_meses": low, "idade_max_meses": high,
                     "idade_texto": label, "escala": aliases.get(match[1], match[1]),
                     **dict(zip(STATS, values[index * 7:index * 7 + 7])), "pagina": grid.page}
            if kind != 4:
                entry.update(direcao=match[2], outra_escala=aliases.get(match[3], match[3]))
            result.append(entry)
    if not result:
        raise ValueError(f"Página {grid.page}: tabela estatística vazia")
    return result


def behavior_rows(page):
    grid = Grid(page)
    headers = sorted([w for w in grid.words if w[4] in {"int", "ext"} and w[1] < 130], key=grid.x)
    age_labels = grid.age_headers()
    if not headers or len(age_labels) * 2 != len(headers):
        raise ValueError(f"Página {grid.page}: E cabeçalho incompleto: {age_labels}")
    xs = [grid.x(w) for w in headers]
    markers = sorted([w for w in grid.words if grid.x(w) < xs[0] - 15 and w[4].isdigit()
                      and 1 <= int(w[4]) <= 24 and w[1] > headers[0][1] + 5], key=lambda w: w[1])
    if len(markers) != 24:
        raise ValueError(f"Página {grid.page}: esperadas 24 linhas escala-v; encontradas {len(markers)}")
    result = []
    for marker in markers:
        right = [w[4] for w in grid.words if grid.x(w) > xs[-1] + 15 and abs(w[1] - marker[1]) < 1.5]
        if right != [marker[4]]:
            raise ValueError("E: marcadores laterais divergentes")
        for index, x in enumerate(xs):
            interval = raw_range(grid.cell(x, marker[1]))
            label = age_labels[index // 2]
            lo, hi = bounds(label)
            result.append({"idade_min_meses": lo, "idade_max_meses": hi, "idade_texto": label,
                           "escala": "internalizante" if index % 2 == 0 else "externalizante",
                           "bruto_min": interval[0] if interval else "", "bruto_max": interval[1] if interval else "",
                           "escala_v": marker[4], "pagina": grid.page})
    return result


def extract(directory, english=False):
    import pymupdf

    groups = defaultdict(list)
    coverage = defaultdict(set)
    sources = []
    for appendix in "BCDE":
        path = directory / ("vineland-3-manual-appendices.pdf" if english else f"Vineland3_AppMan_APX_{appendix}.pdf")
        sources.append({"apendice": appendix, "arquivo": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        with pymupdf.open(path) as document:
            for page in document:
                text = normalize_text(page.get_text())
                if "Conteúdo" in text or "of Contents" in text:
                    continue
                match = re.search(rf"Tabela ({appendix})\.(\d+)\b", text)
                if not match:
                    continue
                kind, table = int(match[2]), f"{appendix}{match[2]}"
                coverage[table].add(page.number + 1)
                prefix = f"tabelas-{appendix.lower()}/{table.lower()}"
                if appendix == "E":
                    groups[f"{prefix}/comportamento.csv"].extend(behavior_rows(page))
                elif kind in (1, 3):
                    lo, hi = age_range(text)
                    rows, cis = score_rows(page, kind)
                    for row in rows:
                        level = row.pop("nivel")
                        groups[f"{prefix}/{level}/{age_filename(lo, hi)}"].append(row)
                    for row in cis:
                        level = row.pop("nivel")
                        groups[f"{prefix}/ic/{level}/{age_filename(lo, hi)}"].append(row)
                elif kind == 2:
                    groups[f"{prefix}/equivalentes.csv"].extend(equivalent_rows(page))
                elif kind in (4, 5, 6):
                    groups[f"{prefix}/estatisticas.csv"].extend(statistics_rows(page, kind))
                else:
                    raise ValueError(f"Tabela não suportada: {table}")
    if {k: len(v) for k, v in coverage.items()} != EXPECTED_PAGES:
        raise ValueError("Cobertura incompleta de tabelas/páginas dos apêndices B–E")
    for relative, rows in groups.items():
        table = relative.split("/")[1].upper()
        if table in EXPECTED_STATS_ROWS and len(rows) != EXPECTED_STATS_ROWS[table]:
            raise ValueError(f"Tabela estatística incompleta: {table}")
        if "/ic/" in relative and len(rows) != 15:
            raise ValueError(f"IC incompleto: {relative}")
        if "/b3/" in relative or "/c3/" in relative or "/d3/" in relative:
            if "/ic/" not in relative and len(rows) != 605:
                raise ValueError(f"Tabela de domínio incompleta: {relative}")
    return dict(groups), dict(coverage), sources


def csv_text(rows):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def catalog_rows(groups):
    catalog = []
    for relative, rows in sorted(groups.items()):
        table = relative.split("/")[1].upper()
        text = csv_text(rows)
        match = re.search(r"idade_(\d+)_(\d+|mais)", relative)
        kind = "comportamento" if table[0] == "E" else "ic" if "/ic/" in relative else {
            "1": "subdominios", "2": "equivalentes", "3": "dominios", "4": "forcas_fraquezas",
            "5": "pares_dominios", "6": "pares_subdominios"}[table[1]]
        level = "niveis_dominio" if "/niveis_dominio/" in relative else (
            "extensivo" if "/extensivo/" in relative or kind in {"equivalentes", "pares_subdominios"} else "misto")
        catalog.append({"arquivo": relative, "tabela": f"{table[0]}.{table[1]}",
                        "formulario": FORMS.get(table[0], {"E1": "entrevista", "E2": "pais_cuidadores", "E3": "professores"}.get(table)),
                        "tipo": kind,
                        "nivel": level,
                        "idade_min_meses": int(match[1]) if match else "",
                        "idade_max_meses": int(match[2]) if match and match[2] != "mais" else "",
                        "paginas": ";".join(map(str, sorted({int(row['pagina']) for row in rows}))),
                        "linhas": len(rows), "sha256": hashlib.sha256(text.encode()).hexdigest()})
    return catalog


def verify_written(groups, sources, destination=TABELAS):
    for relative, rows in groups.items():
        if (destination / relative).read_bytes() != csv_text(rows).encode("utf-8"):
            raise ValueError(f"CSV divergente do PDF de origem: {relative}")
    if (destination / "catalogo.csv").read_bytes() != csv_text(catalog_rows(groups)).encode("utf-8"):
        raise ValueError("Catálogo CSV divergente das fontes")
    if (destination / "fontes.csv").read_bytes() != csv_text(sources).encode("utf-8"):
        raise ValueError("Índice de fontes divergente dos PDFs")


def write_tables(groups, coverage, sources, destination=TABELAS):
    for relative, rows in sorted(groups.items()):
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(csv_text(rows), encoding="utf-8", newline="")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "catalogo.csv").write_text(csv_text(catalog_rows(groups)), encoding="utf-8", newline="")
    (destination / "fontes.csv").write_text(csv_text(sources), encoding="utf-8", newline="")
    print({"tables": len(coverage), "source_pages": sum(map(len, coverage.values())),
           "csv_files": len(groups), "data_rows": sum(map(len, groups.values()))})


def verify_english(directory):
    portuguese, coverage, source_files = extract(directory)
    verify_written(portuguese, source_files)
    english, english_coverage, _ = extract(directory, english=True)
    if set(portuguese) != set(english):
        raise ValueError(f"Arquivos divergentes: {set(portuguese) ^ set(english)}")
    checked = 0
    for path, rows in portuguese.items():
        def normalized(entries):
            result = []
            for row in entries:
                row = {k: str(v).replace("–", "-") if v is not None else "" for k, v in row.items() if k not in {"pagina", "idade_texto"}}
                result.append(row)
            return result
        if normalized(rows) != normalized(english[path]):
            for i, (a, b) in enumerate(zip(normalized(rows), normalized(english[path]))):
                if a != b:
                    raise ValueError(f"Divergência inglês {path}, linha {i}: {a} != {b}")
            raise ValueError(f"Contagem divergente: {path}: {len(rows)} != {len(english[path])}")
        checked += len(rows)
    if {k: len(v) for k, v in coverage.items()} != {k: len(v) for k, v in english_coverage.items()}:
        raise ValueError("Quantidade de páginas divergente")
    print({"tables_verified": len(coverage), "files_verified": len(portuguese), "rows_verified": checked})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-english", action="store_true")
    args = parser.parse_args()
    if args.verify_english:
        verify_english(ROOT / "aux" / "vineland")
    else:
        write_tables(*extract(ROOT / "aux" / "vineland"))
