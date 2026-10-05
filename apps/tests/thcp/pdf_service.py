from pathlib import Path

from django.template import engines

from apps.tests.services.playwright_pdf_service import generate_pdf_from_html

from .interpreters import interpret_thcp_results
from .presentation import result_rows, technical_notes


class THCPPdfService:
    TEMPLATE_PATH = Path(__file__).parent / "templates" / "tests" / "pdf" / "thcp_report.html"

    @classmethod
    def render_html(cls, application) -> str:
        data = {**(application.computed_payload or {}), **(application.classified_payload or {})}
        context = {
            "patient_name": application.evaluation.patient.full_name,
            "applied_on": application.applied_on,
            "age": data.get("age"), "norm_label": data.get("norm_label"),
            "rows": result_rows(data),
            "notes": technical_notes(data),
            "interpretation": interpret_thcp_results(data, application.evaluation.patient.full_name),
        }
        return engines["django"].from_string(cls.TEMPLATE_PATH.read_text(encoding="utf-8")).render(context)

    @classmethod
    def generate_pdf_bytes(cls, application) -> bytes:
        return generate_pdf_from_html(cls.render_html(application))
