"""Exporta a aba SRS2-Normas sem executar macros ou fórmulas da planilha."""

import argparse
import csv
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile


NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
TABLES = (
    ("pre_escolar_subescalas_intervencao.csv", "A", 11, 100, 4),
    ("score_total_pre_escolar.csv", "A", 111, 306, 3),
    ("idade_escolar_masculino_subescalas_intervencao.csv", "AA", 11, 100, 4),
    ("idade_escolar_masculino_score_total.csv", "AA", 111, 306, 3),
    ("idade_escolar_feminino_subescalas.csv", "BA", 11, 100, 4),
    ("idade_escolar_feminino_score_total.csv", "BA", 111, 306, 3),
    ("adulto_autorrelato_subescalas.csv", "CA", 11, 100, 4),
    ("adulto_autorrelato_score_total.csv", "CA", 111, 306, 3),
    ("adulto_heterorrelato_subescalas.csv", "DA", 11, 100, 4),
    ("adulto_heterorrelato_score_total.csv", "DA", 111, 306, 3),
)
FACTORS = {
    4: ("percepcao_social", "cognicao_social", "comunicacao_social", "motivacao_social"),
    3: ("padroes_restritos_repetitivos", "comunicacao_interacao_social", "pontuacao_srs2_total"),
}


def column_number(name):
    result = 0
    for char in name:
        result = result * 26 + ord(char) - ord("A") + 1
    return result


def column_name(number):
    result = ""
    while number:
        number, digit = divmod(number - 1, 26)
        result = chr(ord("A") + digit) + result
    return result


def read_norm_cells(workbook):
    with zipfile.ZipFile(workbook) as book:
        strings = [
            "".join(node.text or "" for node in item.findall(".//m:t", NS))
            for item in ET.fromstring(book.read("xl/sharedStrings.xml"))
        ]
        rels = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        }
        sheets = ET.fromstring(book.read("xl/workbook.xml")).find("m:sheets", NS)
        sheet = next(sheet for sheet in sheets if sheet.attrib["name"] == "SRS2-Normas")
        target = rels[sheet.attrib[REL_ID]]
        path = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
        root = ET.fromstring(book.read(path))
        cells = {}
        for cell in root.findall("m:sheetData/m:row/m:c", NS):
            value = cell.find("m:v", NS)
            if value is not None and value.text is not None:
                cells[cell.attrib["r"]] = strings[int(value.text)] if cell.get("t") == "s" else value.text
        return cells


def normalize_value(value, percentile=False):
    value = value.strip()
    if value in ("", "x", "-"):
        return ""
    # A planilha representa os extremos percentílicos por 0,9 e 99,1.
    if percentile and value in ("0.9", "99.1"):
        return "<1" if value == "0.9" else ">99"
    float(value.replace("<", "").replace(">", "").strip())
    return value


def export_norms(workbook, output_dir):
    cells = read_norm_cells(workbook)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for filename, raw_column, start, end, factor_count in TABLES:
        first = column_number(raw_column)
        headers = ["pontuacao_bruta"]
        for factor in FACTORS[factor_count]:
            headers.extend((f"{factor}_percentil", f"{factor}_escore_t"))
        rows = {}
        for row in range(start, end + 1):
            raw = cells.get(f"{raw_column}{row}", "")
            if not raw or raw == "x":
                continue
            values = [str(int(raw))]
            for offset in range(1, factor_count * 2 + 1):
                value = cells.get(f"{column_name(first + offset)}{row}", "")
                values.append(normalize_value(value, percentile=offset % 2 == 1))
            if any(values[1:]):
                if int(raw) in rows:
                    raise ValueError(f"Bruto duplicado em {filename}: {raw}")
                rows[int(raw)] = values
        if not rows:
            raise ValueError(f"Tabela vazia: {filename}")
        with (output_dir / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(headers)
            writer.writerows(rows[raw] for raw in sorted(rows))
        counts[filename] = len(rows)
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "tabelas")
    args = parser.parse_args()
    for filename, count in export_norms(args.workbook, args.output_dir).items():
        print(f"{filename}: {count} linhas")
