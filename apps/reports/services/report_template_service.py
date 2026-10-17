from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from lxml import etree
from django.db import transaction

from apps.reports.models import ReportTemplate, ReportTemplateVersion


class ReportTemplateService:
    MAX_UPLOAD_BYTES = 10 * 1024 * 1024
    MAX_EXPANDED_BYTES = 50 * 1024 * 1024
    MAX_ENTRIES = 2000

    @staticmethod
    def _xml(content):
        root = etree.fromstring(
            content, parser=etree.XMLParser(resolve_entities=False, no_network=True)
        )
        if root.getroottree().docinfo.doctype:
            raise ValueError("Declarações DTD não são permitidas no DOCX.")
        return root

    @classmethod
    def inspect_docx(cls, data: bytes) -> dict:
        if not data or len(data) > cls.MAX_UPLOAD_BYTES:
            raise ValueError("Envie um DOCX de até 10 MB.")
        try:
            with ZipFile(BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > cls.MAX_ENTRIES or sum(e.file_size for e in entries) > cls.MAX_EXPANDED_BYTES:
                    raise ValueError("DOCX excede o limite de conteúdo descompactado.")
                names = [e.filename for e in entries]
                if len(names) != len(set(names)):
                    raise ValueError("DOCX contém entradas duplicadas.")
                if not {"[Content_Types].xml", "word/document.xml"}.issubset(names):
                    raise ValueError("Arquivo não é um documento DOCX.")
                for entry in entries:
                    path = PurePosixPath(entry.filename)
                    if path.is_absolute() or ".." in path.parts or "\\" in entry.filename or entry.flag_bits & 1:
                        raise ValueError("DOCX contém entradas não permitidas.")
                    lowered = entry.filename.lower()
                    if lowered.endswith("vbaproject.bin") or lowered.startswith("word/activex/"):
                        raise ValueError("Macros e controles ativos não são permitidos.")
                    content = archive.read(entry)
                    if lowered.endswith((".xml", ".rels")):
                        root = cls._xml(content)
                        if lowered.endswith(".rels") and any(
                            rel.attrib.get("TargetMode", "").lower() == "external"
                            for rel in root
                        ):
                            raise ValueError("Remova os vínculos externos do modelo antes de enviá-lo.")
                document = cls._xml(archive.read("word/document.xml"))
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                if document.find("w:body", ns) is None:
                    raise ValueError("DOCX sem corpo de documento válido.")
                return {
                    "status": "draft",
                    "export_enabled": False,
                    "tables": len(document.findall(".//w:tbl", ns)),
                    "charts": sum(n.startswith("word/charts/chart") and n.endswith(".xml") for n in names),
                    "message": "Arquivo recebido; campos, tabelas e gráficos ainda precisam de homologação.",
                }
        except (BadZipFile, RuntimeError, KeyError, etree.XMLSyntaxError, NotImplementedError) as exc:
            raise ValueError("DOCX inválido ou corrompido.") from exc

    @classmethod
    def add_version(cls, *, owner, template_id: int, filename: str, data: bytes):
        # Verifica propriedade antes de analisar qualquer conteúdo enviado.
        with transaction.atomic():
            template = ReportTemplate.objects.select_for_update().get(pk=template_id, owner=owner)
            validation = cls.inspect_docx(data)
            latest = template.versions.first()
            return ReportTemplateVersion.objects.create(
                template=template,
                version_number=latest.version_number + 1 if latest else 1,
                document=data,
                sha256=sha256(data).hexdigest(),
                original_filename=PurePosixPath(filename.replace("\\", "/")).name[:255],
                validation_payload=validation,
            )
