"""Build a patient-free layout asset from the professionally approved DOCX."""

from copy import deepcopy
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.oxml.ns import qn
from lxml import etree as ET


def prepare_template(source: Path, destination: Path):
    document = Document(source)
    body = document.element.body
    blocks = [deepcopy(child) for child in body if list(child.iter(qn("c:chart")))]
    if len(blocks) != 10:
        raise ValueError("O modelo aprovado deve conter dez blocos de gráficos nativos.")
    keys = ["wais3", "bpa2", "ravlt", "fdt_auto", "fdt_control", "etdah_ad", "srs2", "srs2_hetero", "srs2_comparison"]
    kept = blocks[:6] + blocks[7:]
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)
    chart_ids = set()
    for key, block in zip(keys, kept):
        for text in block.iter(qn("w:t")):
            text.text = ""
        for properties in block.iter(qn("wp:docPr")):
            properties.set("name", key)
            properties.set("descr", f"neuropsi:test:{key}")
        chart_ids.update(chart.get(qn("r:id")) for chart in block.iter(qn("c:chart")))
        body.insert(len(body) - 1, block)
    for rel_id, rel in list(document.part.rels.items()):
        kind = rel.reltype.rsplit("/", 1)[-1]
        if (kind == "chart" and rel_id not in chart_ids) or kind in {"image", "hyperlink", "comments", "commentsExtended", "people", "customXml", "footnotes", "endnotes"}:
            del document.part.rels[rel_id]
    properties = document.core_properties
    properties.title = "Modelo padrão de laudo WAIS-III"
    for field in ("author", "subject", "keywords", "comments", "last_modified_by", "category", "identifier", "content_status"):
        setattr(properties, field, "")
    for rel_id, rel in list(document.part.package.rels.items()):
        if rel.reltype.endswith("/thumbnail"):
            del document.part.package.rels[rel_id]
    for part in list(document.part.package.parts):
        if "drawingml.chart+xml" not in part.content_type:
            continue
        for rel_id, rel in list(part.rels.items()):
            if rel.is_external or rel.reltype.rsplit("/", 1)[-1] in {"package", "oleObject"}:
                del part.rels[rel_id]
        root = ET.fromstring(part.blob)
        ns = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
        for node in root.findall(".//c:externalData", ns):
            node.getparent().remove(node)
        for series in root.findall(".//c:ser", ns):
            for node in series.findall("c:tx", ns) + series.findall("c:dLbls/c:dLbl", ns):
                node.getparent().remove(node)
            for tag in ("val", "yVal"):
                for point in series.findall(f"c:{tag}//c:v", ns):
                    point.text = "0"
        for node in root.findall(".//c:f", ns):
            node.text = ""
        part._blob = ET.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
    output = BytesIO()
    document.save(output)
    with ZipFile(BytesIO(output.getvalue())) as archive:
        for name in archive.namelist():
            if name.endswith(".xml") and any(value in archive.read(name).lower() for value in (b"eric", b"mascarenhas", b"mariana")):
                raise ValueError(f"Dados de paciente ainda presentes em {name}.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(output.getvalue())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    prepare_template(args.source, args.destination)
