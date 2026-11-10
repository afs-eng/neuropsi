from copy import deepcopy
from datetime import date, timedelta
import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import UserRole
from apps.accounts.services import issue_api_token
from apps.evaluations.models import Evaluation
from apps.patients.models import Patient
from apps.tests.api.catalog import ensure_required_instruments
from apps.tests.models import Instrument, TestApplication
from apps.tests.test_vineland3 import raw
from apps.tests.vineland3.calculators import compute_scores
from apps.tests.vineland3.pdf_service import Vineland3PdfService


class VinelandExtensivePdfTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="vineland-pdf", email="vineland-pdf@example.test", role=UserRole.NEUROPSYCHOLOGIST)
        self.token = issue_api_token(self.user)
        self.patient = Patient.objects.create(full_name="Paciente fictício PDF", birth_date=date(2020, 1, 15), created_by=self.user)
        self.evaluation = Evaluation.objects.create(patient=self.patient, examiner=self.user, start_date=date(2026, 1, 15))
        ensure_required_instruments()
        self.instrument = Instrument.objects.get(code="vineland3")

    def application(self, form="entrevista", motor=True):
        payload = raw(form, birth="2020-01-15")
        if not motor:
            payload["raw_scores"] = {k: v for k, v in payload["raw_scores"].items() if k not in {"cmg", "cmf"}}
        return TestApplication.objects.create(evaluation=self.evaluation, instrument=self.instrument,
                                              applied_on=date(2026, 1, 15), raw_payload=payload,
                                              computed_payload={"domains": [{"standard_score": 999}], "form_label": "Modalidade antiga"},
                                              interpretation_text="NOME DE OUTRO PACIENTE, RESULTADO ANTIGO")

    def test_three_extensive_templates_use_fresh_scores_and_identify_sources(self):
        for form, appendix in (("entrevista", "B"), ("pais_cuidadores", "C"), ("professores", "D")):
            with self.subTest(form=form):
                app = self.application(form)
                original = deepcopy(app.raw_payload)
                expected = compute_scores(original)
                context = Vineland3PdfService._build_context(app)
                html = Vineland3PdfService.render_html(app)
                self.assertIn(expected["form_label"], html)
                self.assertIn(f"Tabela {appendix}.1", html)
                self.assertIn(f"Tabela {appendix}.3", html)
                self.assertEqual(context["result"], expected)
                self.assertIn("Resultados por subdomínio", html)
                self.assertIn("Perfil de escala-v", html)
                self.assertIn("Perfil dos escores padrão", html)
                self.assertIn("Síntese e limites de utilização", html)
                self.assertIn("Análise dos domínios", html)
                self.assertIn("Análise dos subdomínios", html)
                self.assertIn("IC95%", html)
                self.assertNotIn("HMOT ausente", html)
                self.assertNotIn("NOME DE OUTRO PACIENTE", html)
                self.assertNotIn("Modalidade antiga", html)
                self.assertNotIn("999", html)
                self.assertNotIn("{%", html)
                for svg in re.findall(r"<svg\b.*?</svg>", html, re.DOTALL):
                    coordinates = re.findall(r'\b(?:x|y|x1|x2|y1|y2|cx|cy)="([^"]+)"', svg)
                    self.assertTrue(coordinates)
                    self.assertTrue(all(re.fullmatch(r"-?\d+(?:\.\d+)?", value) for value in coordinates), coordinates)
                self.assertEqual(html.count('<section class="page">'), 6 + len(context["additional_pages"]))
                self.assertNotIn("Resumo da pontuação adaptativa", html)
                app.refresh_from_db()
                self.assertEqual(app.raw_payload, original)
                self.assertFalse(app.is_validated)

    def test_optional_motor_is_not_fabricated_and_never_enters_cca(self):
        for form in ("entrevista", "pais_cuidadores", "professores"):
            app = self.application(form, motor=False)
            context = Vineland3PdfService._build_context(app)
            motor = context["extensive_domains"][-1]
            self.assertIsNone(motor["standard_score"])
            cca = next(row for row in context["extensive_domains"] if row["display_code"] == "CCA")
            self.assertEqual(cca["sum_standard_scores"], sum(r["standard_score"] for r in context["extensive_domains"][:3]))
            self.assertNotIn("cmg", [r["scale"] for r in context["subdomains"]])
            self.assertIn("HMOT ausente", Vineland3PdfService.render_html(app))

    def test_current_patient_dates_override_saved_dates_and_invalid_data_fail_closed(self):
        app = self.application("professores")
        self.patient.birth_date = date(2000, 1, 15)
        self.patient.save()
        with self.assertRaises(ValueError):
            Vineland3PdfService.render_html(app)
        self.patient.birth_date = date(2020, 1, 15)
        self.patient.save()
        app.applied_on = date.today() + timedelta(days=1)
        with self.assertRaises(ValueError):
            Vineland3PdfService.render_html(app)
        app.applied_on = date(2026, 1, 15)
        del app.raw_payload["raw_scores"]["rec"]
        with self.assertRaises(ValueError):
            Vineland3PdfService.render_html(app)

    def test_mixed_item_bank_is_rejected_and_unrelated_instrument_cannot_use_exporter(self):
        app = self.application()
        app.raw_payload["item_protocol_id"] = "legacy"
        with self.assertRaises(ValueError):
            Vineland3PdfService.render_html(app)
        app.raw_payload.pop("item_protocol_id")
        app.instrument = Instrument.objects.exclude(code="vineland3").first()
        with self.assertRaises(ValueError):
            Vineland3PdfService.render_html(app)

    def test_extensive_route_is_authenticated_owned_and_does_not_validate(self):
        for form in ("entrevista", "pais_cuidadores", "professores"):
            app = self.application(form)
            url = f"/api/tests/applications/{app.pk}/export-pdf"
            self.assertEqual(self.client.get(url).status_code, 401)
            with patch("apps.tests.vineland3.pdf_service.generate_pdf_from_html", return_value=b"%PDF-1.4\n") as renderer:
                response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {self.token}")
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(response["Content-Type"], "application/pdf")
            self.assertIn("Resultados por subdomínio", renderer.call_args.args[0])
            app.refresh_from_db()
            self.assertFalse(app.is_validated)
        other = get_user_model().objects.create_user(username="other-vineland-pdf", email="other-pdf@example.test", role=UserRole.NEUROPSYCHOLOGIST)
        with patch("apps.tests.vineland3.pdf_service.generate_pdf_from_html") as renderer:
            response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {issue_api_token(other)}")
            self.assertEqual(response.status_code, 404)
            renderer.assert_not_called()

    def test_template_escapes_text_and_preserves_long_observations(self):
        app = self.application()
        self.patient.full_name = "Paciente <script>"
        app.raw_payload["respondent"] = '<img src="https://external.test/leak">'
        app.raw_payload["general_observations"] = "<script>TESTE</script>\n" + "Observação fictícia. " * 1500 + "FIM DO TEXTO"
        html = Vineland3PdfService.render_html(app)
        self.assertIn("Paciente &lt;script&gt;", html)
        self.assertIn("&lt;img", html)
        self.assertNotIn('<img src="https://', html)
        self.assertNotIn("<script>", html)
        self.assertIn("FIM DO TEXTO", html)
