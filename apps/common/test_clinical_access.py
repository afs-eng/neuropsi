from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase
from ninja.testing import TestClient

from apps.accounts.models import hash_api_token
from apps.anamnesis.api.endpoints import router as anamnesis_router
from apps.documents.api.endpoints import router as documents_router
from apps.documents.models import EvaluationDocument
from apps.evaluations.api.endpoints import router as evaluations_router
from apps.evaluations.models import Evaluation
from apps.patients.api.endpoints import router as patients_router
from apps.patients.models import Patient
from apps.reports.api.endpoints import router as reports_router
from apps.reports.models import Report, ReportSection
from apps.tests.api.endpoints import router as tests_router
from apps.tests.models import Instrument, TestApplication


class ClinicalAccessTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="clinical-owner", email="owner@example.com", role="neuropsychologist",
            crp="00/12345", api_token_hash=hash_api_token("owner-secret"),
        )
        self.other = get_user_model().objects.create_superuser(
            username="clinical-admin", email="admin@example.com", password="unused",
            role="admin", api_token_hash=hash_api_token("other-secret"),
        )
        self.patient = Patient.objects.create(full_name="Paciente privado", created_by=self.owner)
        self.evaluation = Evaluation.objects.create(
            patient=self.patient, examiner=self.owner, start_date=date(2026, 10, 16),
        )
        self.report = Report.objects.create(patient=self.patient, evaluation=self.evaluation, author=self.owner)
        self.section = ReportSection.objects.create(report=self.report, key="conclusao", content_edited="Texto privado")
        instrument, _ = Instrument.objects.get_or_create(code="wisc4", defaults={"name": "WISC-IV"})
        self.application = TestApplication.objects.create(evaluation=self.evaluation, instrument=instrument)
        self.document = EvaluationDocument.objects.create(
            patient=self.patient, evaluation=self.evaluation, title="Anexo privado", file="documents/private.pdf",
        )
        self.owner_headers = {"Authorization": "Bearer owner-secret"}
        self.other_headers = {"Authorization": "Bearer other-secret"}

    def test_superuser_cannot_list_another_professionals_data(self):
        for router, path in [
            (patients_router, "/"), (evaluations_router, "/"), (reports_router, "/"),
            (tests_router, "/applications"),
            (documents_router, f"list?evaluation_id={self.evaluation.pk}"),
            (anamnesis_router, f"/invites?evaluation_id={self.evaluation.pk}"),
        ]:
            with self.subTest(path=path):
                response = TestClient(router).get(path, headers=self.other_headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), [])

    def test_foreign_detail_is_hidden_even_for_superuser(self):
        for router, path in [
            (patients_router, f"/{self.patient.pk}"),
            (evaluations_router, f"/{self.evaluation.pk}"),
            (reports_router, f"/{self.report.pk}"),
            (tests_router, f"/applications/{self.application.pk}"),
            (documents_router, f"get/{self.document.pk}"),
        ]:
            with self.subTest(path=path):
                self.assertEqual(TestClient(router).get(path, headers=self.other_headers).status_code, 404)

    def test_owner_can_read_detail(self):
        for router, path in [
            (patients_router, f"/{self.patient.pk}"),
            (evaluations_router, f"/{self.evaluation.pk}"),
            (tests_router, f"/applications/{self.application.pk}"),
            (documents_router, f"get/{self.document.pk}"),
        ]:
            with self.subTest(path=path):
                self.assertEqual(TestClient(router).get(path, headers=self.owner_headers).status_code, 200)

    def test_report_generation_and_export_cannot_cross_users(self):
        client = TestClient(reports_router)
        with patch("apps.reports.api.endpoints.ReportGenerationService.generate_full_report") as generate:
            self.assertEqual(client.post(f"/{self.report.pk}/build", headers=self.other_headers).status_code, 404)
            generate.assert_not_called()
        for path in ["export-html", "export-docx", "finalize", "regenerate-tests"]:
            with self.subTest(path=path):
                response = client.post(f"/{self.report.pk}/{path}", headers=self.other_headers)
                self.assertIn(response.status_code, (403, 404))

    def test_foreign_patient_cannot_be_used_to_create_evaluation(self):
        response = TestClient(evaluations_router).post("/", headers=self.other_headers, json={
            "patient_id": self.patient.pk,
        })
        self.assertEqual(response.status_code, 404)

    def test_examiner_cannot_be_assigned_to_another_user(self):
        response = TestClient(evaluations_router).patch(f"/{self.evaluation.pk}", headers=self.owner_headers, json={
            "examiner_id": self.other.pk,
        })
        self.assertEqual(response.status_code, 403)
        self.evaluation.refresh_from_db()
        self.assertEqual(self.evaluation.examiner_id, self.owner.pk)

    def test_report_status_and_final_text_cannot_bypass_approval(self):
        for payload in [{"status": "finalized"}, {"final_text": "Sem aprovação"}]:
            response = TestClient(reports_router).put(f"/{self.report.pk}", headers=self.owner_headers, json=payload)
            self.assertEqual(response.status_code, 403)

    def test_assistant_cannot_finalize(self):
        self.owner.role = "assistant"
        self.owner.save(update_fields=["role"])
        response = TestClient(reports_router).post(f"/{self.report.pk}/finalize", headers=self.owner_headers)
        self.assertEqual(response.status_code, 403)

    def test_mismatched_legacy_ownership_is_not_silently_shared(self):
        self.evaluation.examiner = self.other
        self.evaluation.save(update_fields=["examiner"])
        for headers in [self.owner_headers, self.other_headers]:
            response = TestClient(evaluations_router).get(f"/{self.evaluation.pk}", headers=headers)
            self.assertEqual(response.status_code, 404)

    def test_legacy_views_require_login_and_scope_records(self):
        self.assertEqual(self.client.get("/pacientes/").status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/pacientes/").json(), {"patients": []})
        for path in [f"/pacientes/{self.patient.pk}/", f"/avaliacoes/{self.evaluation.pk}/", f"/testes/wisc4/{self.application.pk}/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_legacy_readonly_user_cannot_write(self):
        self.owner.role = "readonly"
        self.owner.save(update_fields=["role"])
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(f"/pacientes/{self.patient.pk}/editar/", {"full_name": "Alterado"}).status_code, 403)

    def test_document_download_requires_owner_and_does_not_expose_storage_url(self):
        client = TestClient(documents_router)
        path = f"download/{self.document.pk}"
        self.assertEqual(client.get(path).status_code, 401)
        self.assertEqual(client.get(path, headers=self.other_headers).status_code, 404)
        with patch.object(type(self.document.file), "open", return_value=ContentFile(b"private bytes")):
            response = client.get(path, headers=self.owner_headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b"private bytes")
            self.assertEqual(response["Cache-Control"], "private, no-store")
        detail = client.get(f"get/{self.document.pk}", headers=self.owner_headers).json()
        self.assertEqual(detail["file_url"], f"/api/documents/{path}")

    def test_document_with_divergent_patient_is_hidden(self):
        another = Patient.objects.create(full_name="Outro paciente", created_by=self.other)
        self.document.patient = another
        self.document.save(update_fields=["patient"])
        response = TestClient(documents_router).get(f"get/{self.document.pk}", headers=self.owner_headers)
        self.assertEqual(response.status_code, 404)
