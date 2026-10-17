from unittest.mock import patch

from django.test import TestCase
from ninja.testing import TestClient

from apps.common import test_clinical_access
from apps.reports.api.endpoints import router
from apps.reports.models import ReportApprovalSnapshot, ReportStatus
from apps.reports.services.report_export_service import ReportExportService
from apps.reports.services.clinical_consistency_audit_service import ClinicalConsistencyAuditService
from apps.reports.services.report_approval_service import ReportApprovalService
from apps.reports.services.report_context_service import ReportContextService
from apps.reports.services.professional_identity_service import ProfessionalIdentityService


class ReportApprovalTests(TestCase):
    setUp = test_clinical_access.ClinicalAccessTests.setUp

    def valid_audit(self, **overrides):
        self.report.context_payload = ReportContextService.build_context(self.evaluation)
        self.report.ai_metadata = {"audit": {
            "status": "ok", "alerts": [],
            "source_sha256": ReportApprovalService.fingerprint(self.report), **overrides,
        }}
        self.report.save(update_fields=["ai_metadata", "context_payload"])

    def finalize(self):
        return TestClient(router).post(f"/{self.report.pk}/finalize", headers=self.owner_headers)

    def test_approval_requires_successful_audit(self):
        self.assertEqual(self.finalize().status_code, 400)
        self.report.refresh_from_db()
        self.assertNotEqual(self.report.status, ReportStatus.FINALIZED)
        self.assertEqual(self.report.final_text, "")

    def test_critical_or_failed_audit_blocks_approval(self):
        for audit in [
            {"status": "error"}, {"alerts": None},
            {"status": "flagged", "alerts": [{"severity": "high", "issue": "Divergência"}]},
        ]:
            with self.subTest(audit=audit):
                self.valid_audit(**audit)
                self.assertEqual(self.finalize().status_code, 400)

    def test_content_edits_require_new_audit(self):
        self.valid_audit()
        self.section.content_edited = "Texto alterado"
        self.section.save(update_fields=["content_edited"])
        self.assertEqual(self.finalize().status_code, 400)

    def test_review_warnings_block_approval(self):
        self.section.warnings_payload = ["Verificar informante"]
        self.section.save(update_fields=["warnings_payload"])
        self.valid_audit()
        self.assertEqual(self.finalize().status_code, 400)

    def test_valid_approval_records_professional_and_rejects_later_edits(self):
        self.valid_audit()
        self.assertEqual(self.finalize().status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.FINALIZED)
        self.assertIn("Texto privado", self.report.final_text)
        self.assertEqual(self.report.ai_metadata["finalization"]["approved_by"], self.owner.pk)
        self.assertTrue(self.report.versions.exists())
        client = TestClient(router)
        for path, payload in [
            (f"/{self.report.pk}", {"title": "Alterado"}),
            (f"/sections/{self.section.pk}", {"edited_text": "Alterado"}),
        ]:
            method = client.put if path == f"/{self.report.pk}" else client.patch
            self.assertEqual(method(path, json=payload, headers=self.owner_headers).status_code, 403)
        self.assertEqual(client.post(f"/{self.report.pk}/regenerate-tests", headers=self.owner_headers).status_code, 403)

    def test_empty_and_malformed_audit_never_pass_as_ok(self):
        for content in ["", "[]", "null", "{}", '{"alerts":null}', '{"alerts":{}}', '{"alerts":[{}]}', "not json"]:
            with self.subTest(content=content), patch.object(ClinicalConsistencyAuditService, "_call_ai", return_value={"content": content}):
                result = ClinicalConsistencyAuditService.audit_report(self.report, {})
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["alerts"][0]["severity"], "high")

    def test_explicit_audit_endpoint_binds_result_to_content(self):
        with patch.object(ClinicalConsistencyAuditService, "_call_ai", return_value={"content": '{"alerts": []}'}):
            response = TestClient(router).post(f"/{self.report.pk}/audit", headers=self.owner_headers)
        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(response.json()["source_sha256"], ReportApprovalService.fingerprint(self.report))
        self.assertEqual(self.finalize().status_code, 200)

    def test_changed_clinical_results_require_a_new_audit(self):
        self.valid_audit()
        self.patient.schooling = "Escolaridade corrigida"
        self.patient.save(update_fields=["schooling"])
        self.assertEqual(self.finalize().status_code, 400)

    def test_approval_keeps_context_and_professional_identity_after_source_changes(self):
        self.valid_audit()
        self.assertEqual(self.finalize().status_code, 200)
        self.report.refresh_from_db()
        original_context = self.report.context_payload
        original_identity = ProfessionalIdentityService.author_label(self.report)
        self.patient.full_name = "Nome corrigido depois da aprovação"
        self.patient.save(update_fields=["full_name"])
        self.owner.crp = "99/99999"
        self.owner.save(update_fields=["crp"])
        self.report.refresh_from_db()
        self.assertEqual(ReportContextService.sync_report_context(self.report), original_context)
        self.assertEqual(ProfessionalIdentityService.author_label(self.report), original_identity)

    def test_approved_export_uses_preserved_bytes_not_current_template(self):
        self.valid_audit()
        self.assertEqual(self.finalize().status_code, 200)
        self.report.refresh_from_db()
        snapshot = ReportApprovalSnapshot.objects.get(report=self.report)
        self.assertTrue(bytes(snapshot.document).startswith(b"PK"))
        self.assertEqual(snapshot.payload["context"], self.report.context_payload)
        self.assertEqual(snapshot.payload["sections"][0]["content_edited"], "Texto privado")
        with patch.object(ReportExportService, "_select_template_path", side_effect=AssertionError("Must not reload template")):
            self.assertEqual(ReportExportService.generate_docx_bytes(self.report), bytes(snapshot.document))
            self.assertEqual(ReportExportService.generate_html(self.report), snapshot.html)

    def test_failed_export_does_not_partially_approve(self):
        self.valid_audit()
        with patch.object(ReportExportService, "generate_docx_bytes", side_effect=ValueError("Invalid document")):
            self.assertEqual(self.finalize().status_code, 400)
        self.report.refresh_from_db()
        self.assertNotEqual(self.report.status, ReportStatus.FINALIZED)
        self.assertEqual(self.report.final_text, "")
        self.assertFalse(ReportApprovalSnapshot.objects.filter(report=self.report).exists())
        self.assertFalse(self.report.versions.exists())

    def test_revision_is_a_new_draft_with_current_sources_and_human_text(self):
        self.valid_audit()
        self.assertEqual(self.finalize().status_code, 200)
        self.patient.schooling = "Dados corrigidos"
        self.patient.save(update_fields=["schooling"])
        client = TestClient(router)
        url = f"/{self.report.pk}/revisions"
        self.assertIn(client.post(url, headers=self.other_headers).status_code, (403, 404))
        response = client.post(url, headers=self.owner_headers)
        self.assertEqual(response.status_code, 201)
        revision = self.report.__class__.objects.get(pk=response.json()["id"])
        self.assertNotEqual(revision.pk, self.report.pk)
        self.assertEqual(revision.status, ReportStatus.IN_REVIEW)
        self.assertEqual(revision.context_payload["patient"]["schooling"], "Dados corrigidos")
        self.assertEqual(revision.sections.get(key=self.section.key).content_edited, "Texto privado")
        self.assertEqual(revision.ai_metadata, {"revision_of": self.report.pk})
        self.assertEqual(revision.final_text, "")
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.FINALIZED)
        self.assertNotEqual(self.report.context_payload["patient"]["schooling"], "Dados corrigidos")

    def test_approved_record_cannot_be_deleted_through_parent_endpoints(self):
        from apps.evaluations.api.endpoints import router as evaluations_router
        from apps.patients.api.endpoints import router as patients_router

        self.valid_audit()
        self.assertEqual(self.finalize().status_code, 200)
        for endpoint_router, path in [
            (router, f"/{self.report.pk}"),
            (evaluations_router, f"/{self.evaluation.pk}"),
            (patients_router, f"/{self.patient.pk}"),
        ]:
            with self.subTest(path=path):
                response = TestClient(endpoint_router).delete(path, headers=self.owner_headers)
                self.assertEqual(response.status_code, 403)
        self.assertTrue(ReportApprovalSnapshot.objects.filter(report=self.report).exists())

    def test_corrupt_approved_document_is_not_exported(self):
        self.valid_audit()
        self.assertEqual(self.finalize().status_code, 200)
        self.report.refresh_from_db()
        ReportApprovalSnapshot.objects.filter(report=self.report).update(document=b"corrupted")
        with self.assertRaisesMessage(ValueError, "integridade"):
            ReportExportService.generate_docx_bytes(self.report)
