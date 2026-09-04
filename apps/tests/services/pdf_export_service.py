from __future__ import annotations

import math
import re
from pathlib import Path

from django.template import Context
from django.template import engines

from apps.tests.bpa2.pdf_service import BPA2PdfService
from apps.tests.bfp.config import FACTOR_DEFINITIONS, FACET_DEFINITIONS, SAMPLE_LABELS
from apps.tests.bfp.interpreters import build_bfp_interpretation_payload
from apps.tests.ebadep_a.pdf_service import EBADEPAPdfService
from apps.tests.fdt.pdf_service import FDTPdfService
from apps.tests.ravlt.pdf_service import RAVLTPdfService
from apps.tests.scared.pdf_service import SCAREDPdfService
from apps.tests.srs2.pdf_service import SRS2PdfService
from apps.tests.wais3.pdf_service import WAIS3PdfService
from apps.tests.wisc4.pdf_service import WISC4PdfService


def _polar_point(cx: float, cy: float, radius: float, angle: float) -> tuple[float, float]:
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def _polygon_points(values: list[float], cx: float, cy: float, radius: float) -> str:
    points: list[str] = []
    for index, value in enumerate(values):
        angle = (-math.pi / 2) + (index / len(values)) * math.pi * 2
        px, py = _polar_point(cx, cy, (max(0.0, min(100.0, value)) / 100.0) * radius, angle)
        points.append(f"{px:.2f},{py:.2f}")
    return " ".join(points)


class BaseTestPdfExporter:
    instrument_code: str = ""

    @classmethod
    def build_pdf_bytes(cls, application) -> bytes:
        raise NotImplementedError


class FDTPdfExporter(BaseTestPdfExporter):
    instrument_code = "fdt"

    @classmethod
    def build_pdf_bytes(cls, application) -> bytes:
        return FDTPdfService.generate_pdf_bytes(application)


class EBADEPAPdfExporter(BaseTestPdfExporter):
    instrument_code = "ebadep_a"

    @classmethod
    def build_pdf_bytes(cls, application) -> bytes:
        return EBADEPAPdfService.generate_pdf_bytes(application)


class BPA2PdfExporter(BaseTestPdfExporter):
    instrument_code = "bpa2"

    @classmethod
    def build_pdf_bytes(cls, application) -> bytes:
        return BPA2PdfService.generate_pdf_bytes(application)


class BFPPdfExporter(BaseTestPdfExporter):
    instrument_code = "bfp"
    FACTOR_ORDER = ["NN", "EE", "SS", "RR", "AA"]
    FACET_ORDER = [
        "N1",
        "N2",
        "N3",
        "N4",
        "E1",
        "E2",
        "E3",
        "E4",
        "S1",
        "S2",
        "S3",
        "R1",
        "R2",
        "R3",
        "A1",
        "A2",
        "A3",
    ]
    FACET_LABEL_POSITIONS = [
        (260, 44, "middle", "Vulnerabilidade"),
        (346, 63, "middle", "Instabilidade emocional"),
        (427, 104, "middle", "Passividade"),
        (480, 168, "middle", "Depressão"),
        (492, 247, "middle", "Comunicação"),
        (470, 328, "middle", "Altivez"),
        (424, 389, "middle", "Dinamismo"),
        (360, 438, "middle", "Interações sociais"),
        (301, 489, "middle", "Amabilidade"),
        (219, 489, "middle", "Pró-sociabilidade"),
        (150, 438, "middle", "Confiança"),
        (84, 392, "middle", "Competência"),
        (45, 325, "middle", "Ponderação"),
        (33, 247, "middle", "Empenho"),
        (60, 168, "middle", "Abertura a ideias"),
        (96, 104, "middle", "Liberalismo"),
        (174, 63, "middle", "Busca por novidades"),
    ]
    FACTOR_COLORS = {
        "NN": "#c2410c",
        "EE": "#2563eb",
        "SS": "#0f766e",
        "RR": "#d97706",
        "AA": "#6366f1",
    }
    TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "bfp" / "templates" / "tests" / "pdf" / "bfp_report.html"

    @staticmethod
    def _format_schooling(value: str | None) -> str:
        labels = {
            "preschool": "Ensino pré-escolar",
            "elementary": "Ensino fundamental",
            "elementary_incomplete": "Ensino fundamental incompleto",
            "elementary_complete": "Ensino fundamental completo",
            "middle": "Ensino médio",
            "middle_incomplete": "Ensino médio incompleto",
            "middle_complete": "Ensino médio completo",
            "higher_incomplete": "Ensino superior incompleto",
            "higher": "Ensino superior",
            "higher_complete": "Ensino superior completo",
            "postgraduate": "Pós-graduação",
        }
        if not value:
            return "—"
        normalized = str(value).strip().lower()
        return labels.get(normalized, str(value).replace("_", " ").strip().title())

    @staticmethod
    def _format_sex(value: str | None) -> str:
        if value == "M":
            return "Masculino"
        if value == "F":
            return "Feminino"
        return value or "—"

    @staticmethod
    def _factor_summary(factor_name: str) -> str:
        summaries = {
            "Neuroticismo": "Relaciona-se à vulnerabilidade emocional, oscilação afetiva, passividade e tendência a interpretações negativas do cotidiano.",
            "Extroversão": "Descreve comunicação, senso de valor pessoal, dinamismo e busca por interação social.",
            "Socialização": "Refere-se à amabilidade, postura pró-social e confiança nas outras pessoas.",
            "Realização": "Avalia busca de objetivos, prudência para agir e nível de comprometimento com tarefas.",
            "Abertura": "Descreve abertura a ideias, flexibilização de valores e busca por novidades.",
        }
        return summaries.get(factor_name, "")

    @staticmethod
    def _application_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"AVL-{base_id}"

    @staticmethod
    def _report_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"RPT-BFP-{base_id}"

    @staticmethod
    def _format_value(value, decimals: int = 1) -> str:
        if value is None or value == "":
            return "—"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        text = f"{number:.{decimals}f}".replace(".", ",")
        if decimals > 0:
            text = text.rstrip("0")
            if text.endswith(","):
                text += "0"
        return text

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip())

    @classmethod
    def _first_sentence(cls, text: str, fallback: str) -> str:
        cleaned = cls._clean_text(text)
        if not cleaned:
            return fallback
        cleaned = re.sub(r"^[\s:;,-]+", "", cleaned)
        match = re.match(r".*?[\.!?](?:\s|$)", cleaned)
        return (match.group(0).strip() if match else cleaned) or fallback

    @classmethod
    def _observation_text(cls, text: str) -> str:
        cleaned = cls._clean_text(text)
        if cleaned:
            return cleaned
        return (
            "Esta página funciona como devolutiva sintética, com linguagem clara e tecnicamente controlada. "
            "A BFP descreve tendências de personalidade e deve ser integrada aos demais dados do processo avaliativo."
        )

    @classmethod
    def _factor_radar_svg(cls, factors: dict) -> str:
        width = 360.0
        height = 320.0
        cx = 180.0
        cy = 160.0
        radius = 110.0
        rings = [100, 80, 60, 40, 20]
        actual_values = [float((factors.get(code) or {}).get("percentile") or 0.0) for code in cls.FACTOR_ORDER]
        norm_values = [50.0] * len(cls.FACTOR_ORDER)

        ring_polygons = "".join(
            f'<polygon fill="none" stroke="#e4e7eb" stroke-width="1" points="{_polygon_points([ring] * len(cls.FACTOR_ORDER), 0, 0, radius)}" />' for ring in rings
        )
        spokes = "".join(
            f'<line stroke="#e4e7eb" stroke-width="1" x1="0" y1="0" x2="{_polar_point(0, 0, radius, (-math.pi / 2) + (index / len(cls.FACTOR_ORDER)) * math.pi * 2)[0]:.2f}" y2="{_polar_point(0, 0, radius, (-math.pi / 2) + (index / len(cls.FACTOR_ORDER)) * math.pi * 2)[1]:.2f}" />'
            for index, _ in enumerate(cls.FACTOR_ORDER)
        )
        result_dots = "".join(
            f'<circle fill="#0f7f8c" cx="{_polar_point(0, 0, (max(0.0, min(100.0, value)) / 100.0) * radius, (-math.pi / 2) + (index / len(actual_values)) * math.pi * 2)[0]:.2f}" cy="{_polar_point(0, 0, (max(0.0, min(100.0, value)) / 100.0) * radius, (-math.pi / 2) + (index / len(actual_values)) * math.pi * 2)[1]:.2f}" r="4" />'
            for index, value in enumerate(actual_values)
        )
        norm_dots = "".join(
            f'<circle fill="#f39a18" cx="{_polar_point(0, 0, 0.5 * radius, (-math.pi / 2) + (index / len(norm_values)) * math.pi * 2)[0]:.2f}" cy="{_polar_point(0, 0, 0.5 * radius, (-math.pi / 2) + (index / len(norm_values)) * math.pi * 2)[1]:.2f}" r="4" />'
            for index, _ in enumerate(norm_values)
        )
        factor_labels = "".join(
            f'<text x="{_polar_point(cx, cy, radius + 38, (-math.pi / 2) + (index / len(cls.FACTOR_ORDER)) * math.pi * 2)[0]:.2f}" y="{_polar_point(cx, cy, radius + 38, (-math.pi / 2) + (index / len(cls.FACTOR_ORDER)) * math.pi * 2)[1]:.2f}" text-anchor="middle" font-size="11" fill="#25314f">{FACTOR_DEFINITIONS[code]["name"]}</text>'
            for index, code in enumerate(cls.FACTOR_ORDER)
        )

        return f'''
        <svg viewBox="0 0 {width} {height}" class="factor-radar-svg" role="img" aria-label="Gráfico radar dos fatores da BFP" xmlns="http://www.w3.org/2000/svg">
          <g transform="translate({cx},{cy})">
            {ring_polygons}
            {spokes}
            <polygon fill="rgba(242,140,40,0.10)" stroke="#f39a18" stroke-width="2.5" points="{_polygon_points(norm_values, 0, 0, radius)}" />
            <polygon fill="rgba(15,127,140,0.38)" stroke="#0f7f8c" stroke-width="2.5" points="{_polygon_points(actual_values, 0, 0, radius)}" />
            {result_dots}
            {norm_dots}
          </g>
          {factor_labels}
        </svg>
        '''

    @classmethod
    def _facet_radar_svg(cls, facets: dict) -> str:
        width = 520.0
        height = 520.0
        cx = 260.0
        cy = 260.0
        radius = 190.0
        rings = [20, 40, 60, 80, 100]
        actual_values = [float((facets.get(code) or {}).get("percentile") or 0.0) for code in cls.FACET_ORDER]
        norm_values = [50.0] * len(cls.FACET_ORDER)
        ring_polygons = "".join(
            f'<polygon fill="none" stroke="#e4e7eb" stroke-width="1" points="{_polygon_points([ring] * len(cls.FACET_ORDER), 0, 0, radius)}" />' for ring in rings[::-1]
        )

        spokes = "".join(
            f'<line stroke="#e4e7eb" stroke-width="1" x1="0" y1="0" x2="{_polar_point(0, 0, radius, (-math.pi / 2) + (index / len(cls.FACET_ORDER)) * math.pi * 2)[0]:.2f}" y2="{_polar_point(0, 0, radius, (-math.pi / 2) + (index / len(cls.FACET_ORDER)) * math.pi * 2)[1]:.2f}" />'
            for index, _ in enumerate(cls.FACET_ORDER)
        )
        result_dots = "".join(
            f'<circle fill="#0f7f8c" cx="{_polar_point(0, 0, (max(0.0, min(100.0, value)) / 100.0) * radius, (-math.pi / 2) + (index / len(actual_values)) * math.pi * 2)[0]:.2f}" cy="{_polar_point(0, 0, (max(0.0, min(100.0, value)) / 100.0) * radius, (-math.pi / 2) + (index / len(actual_values)) * math.pi * 2)[1]:.2f}" r="4" />'
            for index, value in enumerate(actual_values)
        )
        labels = "".join(
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="10" fill="#777">{label}</text>'
            for x, y, anchor, label in cls.FACET_LABEL_POSITIONS
        )
        ring_labels = "".join(
            f'<text x="260" y="{260 - (radius * ring / 100.0) - 4:.2f}" text-anchor="middle" font-size="9" fill="#8d99ae">{ring}</text>'
            for ring in rings
        )

        return f'''
        <svg viewBox="0 0 {width} {height}" class="facet-radar-svg" role="img" aria-label="Gráfico radar das facetas do BFP" xmlns="http://www.w3.org/2000/svg">
          <g transform="translate({cx},{cy})">
            {ring_polygons}
            {spokes}
            <polygon fill="rgba(242,140,40,0.10)" stroke="#f39a18" stroke-width="2.5" points="{_polygon_points(norm_values, 0, 0, radius)}" />
            <polygon fill="rgba(15,127,140,0.38)" stroke="#0f7f8c" stroke-width="2.5" points="{_polygon_points(actual_values, 0, 0, radius)}" />
            {result_dots}
          </g>
          {ring_labels}
          {labels}
        </svg>
        '''

    @classmethod
    def _grouped_rows(cls, factors: dict, facets: dict) -> list[dict]:
        groups: list[dict] = []
        for factor_code in cls.FACTOR_ORDER:
            factor_definition = FACTOR_DEFINITIONS[factor_code]
            rows: list[dict] = []
            for facet_code in factor_definition["facets"]:
                source = facets.get(facet_code)
                if not source:
                    continue
                rows.append(
                    {
                        "code": facet_code,
                        "name": source.get("name") or FACET_DEFINITIONS[facet_code]["name"],
                        "raw_score": cls._format_value(source.get("raw_score"), 4),
                        "percentile": cls._format_value(source.get("percentile"), 1),
                        "classification": source.get("classification") or "—",
                    }
                )

            factor_result = factors.get(factor_code)
            summary_row = None
            if factor_result:
                summary_row = {
                    "code": factor_code,
                    "name": factor_definition["name"],
                    "raw_score": cls._format_value(factor_result.get("raw_score"), 4),
                    "percentile": cls._format_value(factor_result.get("percentile"), 1),
                    "classification": factor_result.get("classification") or "—",
                }

            if rows or summary_row:
                groups.append(
                    {
                        "code": factor_code,
                        "name": factor_definition["name"],
                        "rows": rows,
                        "summary_row": summary_row,
                    }
                )

        return groups

    @classmethod
    def _factor_interpretation_items(cls, computed: dict, patient_name: str) -> list[dict]:
        payload = build_bfp_interpretation_payload(computed, patient_name=patient_name)
        factor_texts = payload.get("factors") or {}
        facet_texts = payload.get("facets") or {}

        items = []
        for code in cls.FACTOR_ORDER:
            title = FACTOR_DEFINITIONS[code]["name"]
            fallback = cls._factor_summary(title)
            text = cls._clean_text(factor_texts.get(code) or fallback)
            facets = [
                cls._clean_text(facet_texts[facet_code])
                for facet_code in FACTOR_DEFINITIONS[code]["facets"]
                if facet_code in facet_texts
            ]
            items.append(
                {
                    "code": code,
                    "title": title,
                    "text": text,
                    "summary": cls._first_sentence(text, fallback),
                    "facets": facets,
                }
            )
        return items

    @classmethod
    def build_pdf_bytes(cls, application) -> bytes:
        patient = application.evaluation.patient
        computed = application.computed_payload or {}
        factors = computed.get("factors") or {}
        facets = computed.get("facets") or {}
        sample = computed.get("sample") or (application.raw_payload or {}).get("sample") or "geral"
        sample_label = computed.get("sample_label") or SAMPLE_LABELS.get(sample, str(sample).title())
        responsible_professional = "Dra. Jacqueline O. Caires - CRP09/6017"
        age = getattr(patient, "age", None)
        patient_age = str(age) if age is not None else "—"
        factor_interpretations = cls._factor_interpretation_items(computed, patient.full_name)

        context = {
            "application": application,
            "codigo_avaliado": cls._application_code(application),
            "codigo_relatorio": cls._report_code(application),
            "patient_name": patient.full_name,
            "patient_cpf": "",
            "patient_sex": cls._format_sex(patient.sex),
            "patient_age": patient_age,
            "patient_schooling": cls._format_schooling(patient.schooling),
            "patient_state": getattr(patient, "state", None) or "—",
            "patient_email": getattr(patient, "email", None) or "—",
            "responsible_professional": responsible_professional,
            "applied_on": application.applied_on.strftime("%d/%m/%Y") if application.applied_on else "—",
            "sample_label": sample_label,
            "items_valid": len([value for value in (application.raw_payload or {}).get("responses", {}).values() if int(value or 0) > 0]),
            "factor_overview_texts": factor_interpretations,
            "facet_groups": [
                {
                    "code": factor_code,
                    "name": FACTOR_DEFINITIONS[factor_code]["name"],
                    "color": cls.FACTOR_COLORS.get(factor_code, "#1E77A8"),
                    "facets": [FACET_DEFINITIONS[facet_code]["name"] for facet_code in FACTOR_DEFINITIONS[factor_code]["facets"]],
                }
                for factor_code in cls.FACTOR_ORDER
            ],
            "table_groups": cls._grouped_rows(factors, facets),
            "factor_radar_svg": cls._factor_radar_svg(factors),
            "facet_radar_svg": cls._facet_radar_svg(facets),
            "factor_interpretations": factor_interpretations,
        }
        template_source = cls.TEMPLATE_PATH.read_text(encoding="utf-8")
        template = engines["django"].from_string(template_source)
        html = template.render(Context(context).flatten())
        from apps.tests.services.playwright_pdf_service import generate_pdf_from_html
        return generate_pdf_from_html(html)


class RAVLTPdfExporter(BaseTestPdfExporter):
    instrument_code = "ravlt"

    @classmethod
    def build_pdf_bytes(cls, application) -> bytes:
        return RAVLTPdfService.generate_pdf_bytes(application)


class WISC4PdfExporter(BaseTestPdfExporter):
    instrument_code = "wisc4"

    @classmethod
    def build_pdf_bytes(cls, application) -> bytes:
        return WISC4PdfService.generate_pdf_bytes(application)


class WAIS3PdfExporter(BaseTestPdfExporter):
    instrument_code = "wais3"

    @classmethod
    def build_pdf_bytes(cls, application) -> bytes:
        return WAIS3PdfService.generate_pdf_bytes(application)


class SRS2PdfExporter(BaseTestPdfExporter):
    instrument_code = "srs2"

    @classmethod
    def build_pdf_bytes(cls, application, report_type: str = "summary") -> bytes:
        return SRS2PdfService.generate_pdf_bytes(application, report_type=report_type)


class SCAREDPdfExporter(BaseTestPdfExporter):
    instrument_code = "scared"

    @classmethod
    def build_pdf_bytes(cls, application) -> bytes:
        return SCAREDPdfService.generate_pdf_bytes(application)


class TestPdfExportService:
    EXPORTERS: dict[str, type[BaseTestPdfExporter]] = {
        BPA2PdfExporter.instrument_code: BPA2PdfExporter,
        EBADEPAPdfExporter.instrument_code: EBADEPAPdfExporter,
        FDTPdfExporter.instrument_code: FDTPdfExporter,
        BFPPdfExporter.instrument_code: BFPPdfExporter,
        RAVLTPdfExporter.instrument_code: RAVLTPdfExporter,
        SCAREDPdfExporter.instrument_code: SCAREDPdfExporter,
        SRS2PdfExporter.instrument_code: SRS2PdfExporter,
        WAIS3PdfExporter.instrument_code: WAIS3PdfExporter,
        WISC4PdfExporter.instrument_code: WISC4PdfExporter,
        "WISC-IV": WISC4PdfExporter,
        "WISC-4": WISC4PdfExporter,
    }

    @classmethod
    def build_pdf_bytes(cls, application, report_type: str = "summary") -> bytes:
        exporter = cls.EXPORTERS.get(application.instrument.code)
        if not exporter:
            raise ValueError(f"Exportação PDF não disponível para {application.instrument.code}.")
        if application.instrument.code == "srs2":
            return exporter.build_pdf_bytes(application, report_type=report_type)
        return exporter.build_pdf_bytes(application)
