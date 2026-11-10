import json
from copy import deepcopy
from datetime import date

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from docx import Document

from apps.accounts.models import UserRole
from apps.accounts.services import issue_api_token
from apps.evaluations.models import Evaluation
from apps.patients.models import Patient
from apps.reports.builders.tests_builder import build_validated_tests_snapshot
from apps.reports.services.report_export_service import ReportExportService
from apps.tests.models import TestApplication
from apps.tests.test_vineland3 import raw, domain_items, items_with_totals
from apps.tests.vineland3.calculators import compute_scores
from apps.tests.vineland3.domain_scoring import compute_domain_results
from apps.tests.vineland3.domain_totals import compute_domain_totals, domain_total_scales
from apps.tests.vineland3.domain_protocol import PROTOCOL_ID
from apps.tests.vineland3.pdf_service import Vineland3PdfService
from apps.tests.vineland3.review import review_state


def domain_raw(form="entrevista", scores=None, birth="2020-01-15", reference="2026-01-15"):
    return {"form": form, "form_level": "niveis_dominio", "entry_mode": "totals", "respondent": "Informante fictício",
            "birth_date": birth, "reference_date": reference, "raw_scores": scores if scores is not None else {"COM": 50, "AVD": 50, "SOC": 50}}


class VinelandSixFormCalculationTests(SimpleTestCase):
    def test_domain_totals_reference_rows_from_b3_c3_d3_are_not_interchangeable(self):
        # Raw 50 at 6:0: B.3 page 135, C.3 page 133, D.3 page 79.
        for form, standard, percentiles, cca in [
            ("entrevista", [85, 96, 87], ["16", "39", "19"], 86),
            ("pais_cuidadores", [91, 105, 93], ["27", "63", "32"], 95),
            ("professores", [106, 105, 98], ["66", "63", "45"], 103),
        ]:
            with self.subTest(form=form):
                result = compute_scores(domain_raw(form))
                self.assertEqual([r["standard_score"] for r in result["adaptive"][:3]], standard)
                self.assertEqual([r["percentile"] for r in result["adaptive"][:3]], percentiles)
                self.assertEqual(result["cca"]["standard_score"], cca)
                self.assertEqual(result["form_level"], "niveis_dominio")
                self.assertNotIn("subdomains", result)
                self.assertEqual(result["mean_domain_count"], 3)

    def test_parent_totals_match_the_180_question_result(self):
        totals = {"COM": 72, "AVD": 54, "SOC": 48, "HMOT": 37, "internalizante": 13, "externalizante": 15}
        responses = items_with_totals(dict(zip(("comunicacao", "vida_diaria", "socializacao", "atividade_fisica", "comportamento_a", "comportamento_b"), totals.values())))
        actual = compute_domain_totals(domain_raw("pais_cuidadores", totals))
        questionnaire = compute_domain_results(responses, "2020-01-15", "2026-01-15")
        for key in ("adaptive", "cca", "behavior", "mean_standard_score", "strengths", "pairs"):
            if key == "behavior":
                self.assertEqual([{k: v for k, v in row.items() if k != "label"} for row in actual[key]],
                                 [{k: v for k, v in row.items() if k != "label"} for row in questionnaire[key]], key)
            else:
                self.assertEqual(actual[key], questionnaire[key], key)

    def test_each_form_uses_own_raw_limits_and_motor_does_not_enter_cca(self):
        for form, maximum in [("entrevista", 90), ("pais_cuidadores", 80), ("professores", 64)]:
            self.assertEqual(domain_total_scales(form)[0]["max"], maximum)
            with self.assertRaises(ValueError):
                compute_domain_totals(domain_raw(form, {"COM": maximum + 1, "AVD": 50, "SOC": 50}))
            before = compute_domain_totals(domain_raw(form))
            after = compute_domain_totals(domain_raw(form, {"COM": 50, "AVD": 50, "SOC": 50, "HMOT": 30}))
            self.assertEqual(before["cca"], after["cca"])
            self.assertEqual(after["mean_domain_count"], 4)

    def test_domain_totals_reject_subdomains_boolean_missing_and_invalid_optional_scores(self):
        for scores in [{"rec": 50}, {"COM": True, "AVD": 50, "SOC": 50}, {"COM": 50, "AVD": 50},
                       {"COM": 50, "AVD": 50, "SOC": 50, "internalizante": -1}, {"COM": "50", "AVD": 50, "SOC": 50}]:
            with self.subTest(scores=scores), self.assertRaises(ValueError):
                compute_domain_totals(domain_raw(scores=scores))
        with self.assertRaises(ValueError):
            compute_domain_totals({**domain_raw(), "item_responses": domain_items()})

    def test_extensive_totals_still_work_for_all_three_informants(self):
        for form in ("entrevista", "pais_cuidadores", "professores"):
            result = compute_scores(raw(form))
            self.assertEqual(result["form_level"], "extensivo")
            self.assertTrue(result["subdomains"])
            self.assertEqual(result["domains"][-1]["scale"], "ABC")
            with self.assertRaises(ValueError):
                compute_scores({**raw(form), "raw_scores": {"COM": 50, "AVD": 50, "SOC": 50}})

    def test_domain_age_limits_and_optional_zero_do_not_extrapolate(self):
        for form in ("entrevista", "pais_cuidadores", "professores"):
            with self.assertRaises(ValueError):
                compute_domain_totals(domain_raw(form, birth="2025-01-15"))
            value = compute_domain_totals(domain_raw(form, {"COM": 0, "AVD": 0, "SOC": 0, "internalizante": 0}))
            self.assertIsNotNone(value["adaptive"][0]["standard_score"])
            self.assertIsNotNone(value["behavior"][0]["v_scale"])
            self.assertFalse(value["behavior"][1]["applied"])
            with self.assertRaises(ValueError):
                compute_domain_totals(domain_raw(form, {"COM": 50, "AVD": 50, "SOC": 50, "HMOT": 30}, birth="2016-01-15"))
        self.assertTrue(compute_domain_totals(domain_raw("professores", birth="2007-02-15"))["normative_scoring"])
        with self.assertRaises(ValueError):
            compute_domain_totals(domain_raw("professores", birth="2007-01-15"))


class VinelandSixFormApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="six-forms", email="six-forms@example.test", role=UserRole.NEUROPSYCHOLOGIST)
        self.token = issue_api_token(self.user)
        self.patient = Patient.objects.create(full_name="Fictício seis modalidades", birth_date=date(2020, 1, 15), created_by=self.user)
        self.evaluation = Evaluation.objects.create(patient=self.patient, examiner=self.user, start_date=date(2026, 1, 15))

    def post(self, path, payload):
        return self.client.post(path, data=json.dumps(payload), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def submit(self, form="entrevista", **overrides):
        payload = {"evaluation_id": self.evaluation.pk, "applied_on": "2026-01-15", "form_level": "niveis_dominio",
                   "form": form, "entry_mode": "totals", "raw_scores": {"COM": 50, "AVD": 50, "SOC": 50}, "respondent": "Informante fictício", **overrides}
        return self.post("/api/tests/vineland3/submit", payload)

    def test_protocol_exposes_two_levels_and_all_three_informants_without_normative_corpus(self):
        response = self.client.get("/api/tests/vineland3/protocol", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        data = response.json()
        self.assertEqual(set(data["form_levels"]), {"extensivo", "niveis_dominio"})
        self.assertEqual(set(data["forms"]), set(data["domain_forms"]))
        self.assertEqual(len(data["domain_forms"]), 3)
        for form in data["domain_forms"].values():
            self.assertEqual({r["code"] for r in form["scales"]}, {"COM", "AVD", "SOC", "HMOT", "internalizante", "externalizante"})
        self.assertNotIn("entrada_min", json.dumps(data))

    def test_each_domain_total_application_is_independent_and_requires_signed_review(self):
        ids = []
        for form in ("entrevista", "pais_cuidadores", "professores"):
            response = self.submit(form)
            self.assertEqual(response.status_code, 200, response.content)
            data = response.json()
            ids.append(data["application_id"])
            self.assertEqual(data["raw_payload"]["form_level"], "niveis_dominio")
            self.assertTrue(data["normative_results"]["normative_scoring"])
            self.assertTrue(data["clinical_review"]["eligible"])
            self.assertFalse(data["is_validated"])
            self.assertEqual(data["computed_payload"], {})
            self.assertEqual(data["report_payload"]["results"], [])
        self.assertEqual(len(set(ids)), 3)
        self.assertEqual(build_validated_tests_snapshot(self.evaluation), [])

    def test_existing_application_cannot_switch_level_informant_or_mode(self):
        created = self.submit().json()
        app = TestApplication.objects.get(pk=created["application_id"])
        original = deepcopy(app.raw_payload)
        for changes in [{"form": "professores"}, {"form_level": "extensivo", "raw_scores": raw("entrevista")["raw_scores"]},
                        {"entry_mode": "items", "form": None, "raw_scores": {}, "item_protocol_id": PROTOCOL_ID, "item_responses": domain_items(), "finalize": True}]:
            self.assertEqual(self.submit(application_id=app.pk, **changes).status_code, 400)
        app.refresh_from_db()
        self.assertEqual(app.raw_payload, original)

    def test_old_totals_without_level_remain_extensive_and_questionnaire_does_not_become_extensive(self):
        payload = {"evaluation_id": self.evaluation.pk, "applied_on": "2026-01-15", "form": "entrevista",
                   "entry_mode": "totals", "respondent": "Entrevistado", "raw_scores": raw("entrevista", birth="2020-01-15")["raw_scores"]}
        response = self.post("/api/tests/vineland3/submit", payload)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["computed_payload"]["form_level"], "extensivo")
        response = self.submit(form=None, form_level="extensivo", entry_mode="items", raw_scores={}, item_protocol_id=PROTOCOL_ID, item_responses=domain_items())
        self.assertEqual(response.status_code, 400)

    def test_domain_totals_pdf_and_reviewed_docx_identify_the_correct_modality(self):
        for form, codes in [("entrevista", "B.3, B.4, B.5 e E.1"), ("pais_cuidadores", "C.3, C.4, C.5 e E.2"), ("professores", "D.3, D.4, D.5 e E.3")]:
            data = self.submit(form).json()
            app = TestApplication.objects.get(pk=data["application_id"])
            html = Vineland3PdfService.render_html(app)
            self.assertIn(codes, html)
            self.assertIn("Itens críticos não registrados neste lançamento por totais", html)
            self.assertNotIn("180 itens, sete seções", html)
            self.assertNotIn("0/0 itens", html)
            approved = self.post(f"/api/tests/vineland3/applications/{app.pk}/review", {
                "fingerprint": review_state(app)["fingerprint"], "confirmed": True, "clinical_note": "Protocolo original, totais e modalidade conferidos."})
            self.assertEqual(approved.status_code, 200, approved.content)
        snapshot = build_validated_tests_snapshot(self.evaluation)
        self.assertEqual(len(snapshot), 3)
        document = Document()
        document.add_paragraph("14. CONCLUSÃO")
        ReportExportService._insert_vineland3_results(document, {"validated_tests": snapshot})
        self.assertEqual(len(document.tables), 12)
        text = "\n".join(p.text for p in document.paragraphs)
        for code in ("B.4", "C.4", "D.4", "E.1", "E.2", "E.3"):
            self.assertIn(code, text)

    def test_domain_total_edit_revokes_review_and_invalid_dates_fail_closed(self):
        data = self.submit().json()
        app = TestApplication.objects.get(pk=data["application_id"])
        response = self.post(f"/api/tests/vineland3/applications/{app.pk}/review", {"fingerprint": review_state(app)["fingerprint"], "confirmed": True, "clinical_note": "Conferência fictícia de modalidade e totais."})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.submit(application_id=app.pk).status_code, 200)
        app.refresh_from_db()
        self.assertFalse(app.is_validated)
        self.assertEqual(app.reviewed_payload, {})
        self.patient.birth_date = date(2025, 1, 15)
        self.patient.save()
        response = self.client.get(f"/api/tests/applications/{app.pk}", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.json()["normative_results"])
        self.assertFalse(response.json()["clinical_review"]["eligible"])
