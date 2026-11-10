import json
from copy import deepcopy
from datetime import date
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from docx import Document

from apps.accounts.models import UserRole
from apps.accounts.services import issue_api_token
from apps.evaluations.models import Evaluation
from apps.patients.models import Patient
from apps.reports.builders.tests_builder import build_validated_tests_snapshot
from apps.reports.services.report_export_service import ReportExportService
from apps.tests.api.serializers import serialize_test_application
from apps.tests.models import TestApplication
from apps.tests.test_vineland3 import domain_items, items_with_totals
from apps.tests.vineland3.pdf_service import Vineland3PdfService
from apps.tests.vineland3.domain_protocol import PROTOCOL_ID
from apps.tests.vineland3.review import review_state


class VinelandClinicalReviewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="review-vineland", role=UserRole.NEUROPSYCHOLOGIST)
        self.token = issue_api_token(self.user)
        self.patient = Patient.objects.create(full_name="Paciente fictício", birth_date=date(2020, 1, 15), created_by=self.user)
        self.evaluation = Evaluation.objects.create(patient=self.patient, examiner=self.user, start_date=date(2026, 1, 15))
        self.answers = items_with_totals({"comunicacao": 72, "vida_diaria": 54, "socializacao": 48,
                                         "atividade_fisica": 37, "comportamento_a": 13, "comportamento_b": 15})
        self.answers["comportamento_c"]["3"]["response"] = "2"
        self.payload = {"evaluation_id": self.evaluation.pk, "applied_on": "2026-01-15", "respondent": "Informante fictício",
                        "entry_mode": "items", "item_protocol_id": PROTOCOL_ID, "item_responses": self.answers, "finalize": True}
        response = self.post("/api/tests/vineland3/submit", self.payload)
        self.assertEqual(response.status_code, 200, response.content)
        self.application = TestApplication.objects.get(pk=response.json()["application_id"])
        self.url = f"/api/tests/vineland3/applications/{self.application.pk}/review"

    def post(self, url, data, token=None):
        return self.client.post(url, data=json.dumps(data), content_type="application/json",
                                HTTP_AUTHORIZATION=f"Bearer {token or self.token}")

    def review(self, **overrides):
        self.application.refresh_from_db()
        state = review_state(self.application)
        return self.post(self.url, {"fingerprint": state.get("fingerprint", "x" * 64), "confirmed": True,
                                    "clinical_note": "Resultados, normas e itens críticos conferidos pelo profissional.", **overrides})

    def test_finalization_never_implies_clinical_validation_or_report_inclusion(self):
        self.assertFalse(self.application.is_validated)
        self.assertTrue(review_state(self.application)["eligible"])
        self.assertEqual(build_validated_tests_snapshot(self.evaluation), [])
        self.assertEqual(serialize_test_application(self.application)["report_payload"]["results"], [])

    def test_review_records_professional_and_preserves_answers_and_payload_guards(self):
        before = deepcopy(self.application.raw_payload)
        response = self.review()
        self.assertEqual(response.status_code, 200, response.content)
        self.application.refresh_from_db()
        state = response.json()["clinical_review"]
        self.assertTrue(state["validated"])
        self.assertEqual(state["reviewer"]["id"], self.user.pk)
        self.assertTrue(state["reviewed_at"])
        self.assertEqual(self.application.raw_payload, before)
        self.assertEqual(self.application.computed_payload, {})
        self.assertEqual(self.application.classified_payload, {})
        self.assertEqual(self.application.interpretation_text, "")
        self.assertEqual(self.application.status, TestApplication.Status.REVIEWED)
        self.assertTrue(serialize_test_application(self.application)["is_validated"])

    def test_reviewed_snapshot_contains_recalculated_scores_and_no_extensive_interpretation(self):
        self.assertEqual(self.review().status_code, 200)
        snapshot = build_validated_tests_snapshot(self.evaluation)
        self.assertEqual(len(snapshot), 1)
        data = snapshot[0]["computed_payload"]
        self.assertTrue(data["domain_level"])
        self.assertEqual([r["standard_score"] for r in data["domains"]], [130, 110, 91, 94, 112])
        self.assertIn("IC95% 107–117", snapshot[0]["clinical_interpretation"])
        self.assertIn("Item crítico 3, resposta 2", snapshot[0]["clinical_interpretation"])
        self.assertNotIn("não foi emitida", snapshot[0]["clinical_interpretation"])

    def test_signed_review_cannot_be_forged_by_setting_validated_and_reviewed_fields(self):
        self.application.is_validated = True
        self.application.reviewed_payload = {"fingerprint": review_state(self.application)["fingerprint"],
                                             "vineland_domain_review": "forged", "validated": True}
        self.application.save()
        self.assertFalse(review_state(self.application)["validated"])
        self.assertFalse(serialize_test_application(self.application)["is_validated"])
        self.assertEqual(serialize_test_application(self.application)["status"], "completed")
        self.assertEqual(build_validated_tests_snapshot(self.evaluation), [])

    def test_review_rejects_stale_screen_and_missing_explicit_confirmation(self):
        self.assertEqual(self.review(fingerprint="0" * 64).status_code, 400)
        self.assertEqual(self.review(confirmed=False).status_code, 422)
        self.assertEqual(self.review(clinical_note=" " * 12).status_code, 400)
        self.application.refresh_from_db()
        self.assertFalse(self.application.is_validated)

    def test_authenticated_get_exposes_review_state_and_requires_no_write(self):
        self.assertEqual(self.review().status_code, 200)
        before = TestApplication.objects.values().get(pk=self.application.pk)
        response = self.client.get(f"/api/tests/applications/{self.application.pk}", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["clinical_review"]["validated"])
        self.assertEqual(TestApplication.objects.values().get(pk=self.application.pk), before)

    def test_edit_and_refinalize_clear_review_and_remove_from_report(self):
        self.review()
        response = self.post("/api/tests/vineland3/submit", {**self.payload, "application_id": self.application.pk})
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertFalse(self.application.is_validated)
        self.assertEqual(self.application.reviewed_payload, {})
        self.assertEqual(build_validated_tests_snapshot(self.evaluation), [])

    def test_changed_patient_date_invalidates_old_review_even_when_database_flag_remains_true(self):
        self.review()
        self.patient.birth_date = date(2019, 1, 15)
        self.patient.save()
        self.application.refresh_from_db()
        self.assertTrue(self.application.is_validated)
        self.assertFalse(review_state(self.application)["validated"])
        self.assertFalse(serialize_test_application(self.application)["is_validated"])
        self.assertEqual(build_validated_tests_snapshot(self.evaluation), [])

    def test_changed_raw_scores_observations_or_norms_invalidate_signature(self):
        self.review()
        self.application.refresh_from_db()
        for field, value in [("respondent", "Outro respondente"), ("general_observations", "Nova informação")]:
            with self.subTest(field=field):
                original = deepcopy(self.application.raw_payload)
                self.application.raw_payload[field] = value
                self.assertFalse(review_state(self.application)["validated"])
                self.application.raw_payload = original
        result = serialize_test_application(self.application)["normative_results"]
        result["sources"][0]["sha256"] = "changed"
        self.assertFalse(review_state(self.application, result)["validated"])

    def test_other_application_cannot_reuse_signed_review(self):
        self.review()
        self.application.refresh_from_db()
        other = TestApplication.objects.create(evaluation=self.evaluation, instrument=self.application.instrument,
                                               applied_on=self.application.applied_on, raw_payload=self.application.raw_payload,
                                               reviewed_payload=self.application.reviewed_payload, is_validated=True)
        self.assertFalse(review_state(other)["validated"])

    def test_partial_unsupported_age_and_locked_records_cannot_be_reviewed(self):
        self.application.raw_payload["completion_status"] = "partial"
        self.application.save()
        self.assertEqual(self.review().status_code, 400)
        self.application.raw_payload["completion_status"] = "finalized"
        self.application.save()
        self.patient.birth_date = date(2025, 1, 15)
        self.patient.save()
        self.assertEqual(self.review().status_code, 400)
        self.application.status = TestApplication.Status.LOCKED
        self.application.save()
        self.assertEqual(self.review().status_code, 403)

    def test_assistant_and_readonly_cannot_approve_and_other_clinician_cannot_access(self):
        for role in [UserRole.ASSISTANT, UserRole.READONLY]:
            self.user.role = role
            self.user.save()
            self.assertEqual(self.review().status_code, 403)
        other = get_user_model().objects.create_user(username="review-other", email="review-other@example.test", role=UserRole.NEUROPSYCHOLOGIST)
        state = review_state(self.application)
        response = self.post(self.url, {"fingerprint": state["fingerprint"], "confirmed": True, "clinical_note": "Conferência clínica indevida"}, issue_api_token(other))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.post(self.url, data="{}", content_type="application/json").status_code, 401)

    def test_generic_update_cannot_bypass_dedicated_review_or_change_instrument(self):
        response = self.client.patch(f"/api/tests/applications/{self.application.pk}", data=json.dumps({"is_validated": True}),
                                     content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 403)

    def test_reviewed_docx_contains_adaptive_behavior_and_analysis_tables_and_chart(self):
        self.review()
        document = Document()
        document.add_paragraph("14. CONCLUSÃO")
        ReportExportService._insert_vineland3_results(document, {"validated_tests": build_validated_tests_snapshot(self.evaluation)})
        self.assertEqual(len(document.tables), 4)
        cells = "\n".join(cell.text for table in document.tables for row in table.rows for cell in row.cells)
        self.assertIn("107–117", cells)
        self.assertIn("Alto", cells)
        self.assertIn("Escala-v", cells)
        self.assertIn("21", cells)
        self.assertIn("Força", cells)
        self.assertEqual(len(document.inline_shapes), 1)
        self.assertIn("Item crítico 3", "\n".join(p.text for p in document.paragraphs))
        output = BytesIO()
        document.save(output)
        self.assertEqual(len(Document(BytesIO(output.getvalue())).tables), 4)

    def test_pdf_marks_current_review_and_stale_review_as_pending(self):
        self.assertIn("Revisão profissional pendente", Vineland3PdfService.render_html(self.application))
        self.review()
        self.application.refresh_from_db()
        self.assertIn("Revisão profissional registrada", Vineland3PdfService.render_html(self.application))
        self.application.applied_on = date(2026, 1, 16)
        self.assertIn("Revisão profissional pendente", Vineland3PdfService.render_html(self.application))

    def test_future_or_corrupt_finalized_data_cannot_leak_into_report(self):
        self.review()
        self.application.refresh_from_db()
        self.application.applied_on = date(2099, 1, 15)
        self.assertFalse(review_state(self.application)["eligible"])
        self.application.applied_on = date(2026, 1, 15)
        self.application.raw_payload["item_responses"] = domain_items(core_only=True)
        self.application.raw_payload["item_responses"]["comunicacao"]["1"]["response"] = ""
        self.assertFalse(review_state(self.application)["eligible"])

    def test_signed_approval_rejects_a_changed_algorithm_version(self):
        self.review()
        self.application.refresh_from_db()
        with patch("apps.tests.vineland3.review.CORRECTION_VERSION", 2):
            self.assertFalse(review_state(self.application)["validated"])

    def test_revoking_review_preserves_answers_and_prevents_new_report_inclusion(self):
        self.review()
        self.application.refresh_from_db()
        answers = deepcopy(self.application.raw_payload)
        response = self.post(f"{self.url}/revoke", {})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(response.json()["clinical_review"]["validated"])
        self.application.refresh_from_db()
        self.assertEqual(self.application.raw_payload, answers)
        self.assertEqual(build_validated_tests_snapshot(self.evaluation), [])
