from copy import deepcopy
from datetime import date
import json
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from apps.reports.builders.tests_builder import build_validated_tests_snapshot
from apps.tests.models import TestApplication
from apps.tests import test_vineland_pdf as pdf_tests
from apps.tests.test_vineland3 import raw
from apps.tests.vineland3.calculators import compute_scores
from apps.tests.vineland3.csv_tables import load_table
from apps.tests.vineland3.extensive_analysis import base_rate_range, pairs, strengths
from apps.tests.vineland3.review import EXTENSIVE_CORRECTION_VERSION, review_state
from apps.tests.vineland3.pdf_service import Vineland3PdfService


REFERENCE_SCORES = {"rec": 45, "exp": 55, "esc": 48, "pes": 53, "dom": 36, "com": 58,
                    "rin": 41, "bri": 33, "enf": 32, "cmg": 36, "cmf": 39}


class ExtensiveAnalysisTests(SimpleTestCase):
    def test_pdf90_reference_uses_extensive_ic_and_classification(self):
        result = compute_scores({**raw("entrevista", birth="2020-01-15"), "raw_scores": REFERENCE_SCORES})
        analysis = result["analysis"]
        self.assertEqual([r["v_scale"] for r in analysis["subdomains"]], [7, 4, 19, 7, 18, 19, 8, 9, 12, 1, 8])
        rows = analysis["adaptive"] + [analysis["cca"]]
        self.assertEqual([r["standard_score"] for r in rows], [73, 98, 72, 49, 78])
        self.assertEqual([r["confidence_interval"] for r in rows], [[67, 79], [92, 104], [66, 78], [41, 57], [74, 82]])
        self.assertEqual([r["classification"] for r in rows], ["Moderadamente baixo", "Adequado", "Moderadamente baixo", "Baixo", "Moderadamente baixo"])
        self.assertEqual(analysis["mean_standard_score"], 73)
        self.assertEqual(analysis["mean_domain_count"], 4)
        self.assertEqual(analysis["subdomain_count"], 11)
        self.assertEqual(len(analysis["subdomain_pairs"]), 55)
        self.assertEqual(sum(p["within_domain"] for p in analysis["subdomain_pairs"]), 10)
        self.assertEqual(analysis["pairs"][0]["difference"], -25)
        self.assertEqual(analysis["pairs"][0]["base_rate"], "> 5% a ≤ 10%")
        self.assertEqual(analysis["pairs"][0]["source_page"], 196)

    def test_specific_form_and_age_norms_and_equivalents_match_published_rows(self):
        for form, appendix in (("entrevista", "B"), ("pais_cuidadores", "C"), ("professores", "D")):
            for age in (3, 6, 7, 10, 18):
                with self.subTest(form=form, age=age):
                    data = raw(form, birth=f"{2026-age}-01-15")
                    original = deepcopy(data)
                    analysis = compute_scores(data)["analysis"]
                    self.assertEqual(data, original)
                    ci = {r["escala"]: r for r in load_table(f"{appendix}.3", kind="ic", level="extensivo", months=age*12) if r["confianca"] == "95"}
                    for row in analysis["adaptive"] + [analysis["cca"]]:
                        if row["standard_score"] is not None:
                            margin = int(ci[row["scale"]]["margem"])
                            self.assertEqual(row["confidence_interval"], [row["standard_score"] - margin, row["standard_score"] + margin])
                    norms = {(r["escala"], r["bruto"]): r for r in load_table(f"{appendix}.2", level="extensivo")}
                    for row in analysis["subdomains"]:
                        norm = norms[row["scale"], str(row["raw_score"])]
                        self.assertEqual(row["age_equivalent"], norm["equivalente_idade"] or None)
                        self.assertEqual(row["growth_value"], int(norm["vec"]) if norm["vec"] else None)
                    if form == "professores":
                        self.assertIn("num", {r["scale"] for r in analysis["subdomains"]})
                        self.assertNotIn("com", {r["scale"] for r in analysis["subdomains"]})

    def test_missing_motor_has_no_score_and_does_not_enter_means_or_cca(self):
        data = raw("entrevista", birth="2020-01-15")
        full = compute_scores(data)["analysis"]
        for code in ("cmg", "cmf"):
            data["raw_scores"].pop(code)
        analysis = compute_scores(data)["analysis"]
        self.assertEqual(analysis["cca"], full["cca"])
        self.assertEqual(analysis["mean_domain_count"], 3)
        self.assertEqual(analysis["subdomain_count"], 9)
        self.assertIsNone(analysis["adaptive"][-1]["standard_score"])
        self.assertEqual(analysis["adaptive"][-1]["unavailable_reason"], "Não informado")
        self.assertTrue(all(p["difference"] is None and p["significant"] is None and p["base_rate"] is None for p in analysis["pairs"] if p["second"] == "HMOT"))
        self.assertTrue(all(r["v_scale"] is not None for r in analysis["subdomains"]))

    def test_signed_pair_selects_directional_rates_and_preserves_zero(self):
        norms = {(r["escala"], r["outra_escala"], r["direcao"]): r for r in load_table("B.5", level="extensivo", months=72)}
        for first, second, direction, expected in ((100, 75, ">", "> 2% a ≤ 5%"), (75, 100, "<", "> 5% a ≤ 10%"), (100, 100, "=", "> 25%")):
            row = pairs([{"scale": "COM", "label": "Comunicação", "score": first}, {"scale": "AVD", "label": "Vida diária", "score": second}], norms)[0]
            self.assertEqual(row["relation"], direction)
            self.assertEqual(row["difference"], first-second)
            self.assertEqual(row["base_rate"], expected)

    def test_base_rates_bound_only_by_available_thresholds(self):
        norms = {f"base_{p}": str(c) for p, c in zip((2, 5, 10, 15, 25), (30, 22, 18, 15, 13))}
        for value, expected in ((30, "≤ 2%"), (22, "> 2% a ≤ 5%"), (13, "> 15% a ≤ 25%"), (0, "> 25%")):
            self.assertEqual(base_rate_range(value, norms), expected)
        self.assertIsNone(base_rate_range(5, {}))
        self.assertEqual(base_rate_range(4, {"base_2": "7", "base_5": "5", "base_10": "", "base_15": "4", "base_25": "3"}), "> 5% a ≤ 15%")

    def test_significance_is_decided_before_rounding_difference(self):
        rows = [{"scale": key, "label": key, "score": score} for key, score in (("A", 1), ("B", 1), ("C", 2))]
        output, mean, count = strengths(rows, {"A": {"critico_p05": "0.331", "pagina": "1"}})
        self.assertEqual((mean, count), (1.33, 3))
        self.assertEqual(output[0]["difference"], -.33)
        self.assertTrue(output[0]["significant"])


class ExtensiveReviewTests(TestCase):
    setUp = pdf_tests.VinelandExtensivePdfTests.setUp
    application = pdf_tests.VinelandExtensivePdfTests.application

    def approve(self, app):
        response = self.client.post(f"/api/tests/vineland3/applications/{app.pk}/review",
                                    data=json.dumps({"fingerprint": review_state(app)["fingerprint"], "confirmed": True,
                                                     "clinical_note": "Conferência das normas extensivas e do protocolo original."}),
                                    content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 200, response.content)
        app.refresh_from_db()
        return response.json()

    def test_extensive_review_rebuilds_stale_scores_and_invalidates_after_edits(self):
        for form in ("entrevista", "pais_cuidadores", "professores"):
            app = self.application(form)
            original = deepcopy(app.raw_payload)
            self.assertFalse(review_state(app)["validated"])
            self.approve(app)
            with patch("apps.tests.vineland3.review.EXTENSIVE_CORRECTION_VERSION", EXTENSIVE_CORRECTION_VERSION + 1):
                self.assertFalse(review_state(app)["validated"])
            snapshot = next(t for t in build_validated_tests_snapshot(self.evaluation) if t["application_id"] == app.pk)
            self.assertEqual(snapshot["computed_payload"]["normative_results"], compute_scores(original)["analysis"])
            self.assertNotIn("999", snapshot["clinical_interpretation"])
            self.assertFalse(snapshot["computed_payload"]["domain_level"])
            self.assertIn("Revisão profissional registrada", Vineland3PdfService.render_html(app))
            before = deepcopy(app.raw_payload)
            for field, value in (("general_observations", "Observação alterada"), ("respondent", "Outro informante")):
                app.raw_payload[field] = value
                self.assertFalse(review_state(app)["validated"])
                app.raw_payload = deepcopy(before)
            app.applied_on = date(2026, 1, 16)
            self.assertFalse(review_state(app)["validated"])
            app.applied_on = date(2026, 1, 15)
            app.raw_payload["raw_scores"]["rec"] += 1
            self.assertFalse(review_state(app)["validated"])
            app.save()
            self.assertFalse(any(t["application_id"] == app.pk for t in build_validated_tests_snapshot(self.evaluation)))

    def test_extensive_generic_update_cannot_forge_approval_and_submit_keeps_notes(self):
        app = self.application()
        response = self.client.patch(f"/api/tests/applications/{app.pk}", data=json.dumps({"is_validated": True}),
                                     content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 403)
        self.approve(app)
        response = self.client.post("/api/tests/vineland3/submit", data=json.dumps({"evaluation_id": self.evaluation.pk,
                                    "application_id": app.pk, "applied_on": "2026-01-15", "form": "entrevista",
                                    "form_level": "extensivo", "respondent": "Informante", "raw_scores": app.raw_payload["raw_scores"],
                                    "general_observations": "Observação dos totais preservada."}),
                                    content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 200, response.content)
        app.refresh_from_db()
        self.assertFalse(app.is_validated)
        self.assertEqual(app.reviewed_payload, {})
        self.assertIn("Observação dos totais preservada.", Vineland3PdfService.render_html(app))
        self.assertEqual(TestApplication.objects.filter(pk=app.pk).count(), 1)
