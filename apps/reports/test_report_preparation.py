import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from ninja.testing import TestClient

from apps.accounts.models import hash_api_token
from apps.anamnesis.models import AnamnesisResponse, AnamnesisTemplate
from apps.documents.models import EvaluationDocument
from apps.evaluations.models import Evaluation, EvaluationProgressEntry
from apps.patients.models import Patient
from apps.reports.api.preparation_endpoints import router
from apps.reports.models import Report, ReportPreparation, ReportPreparationStep, ReportSection, SpecialistRun
from apps.reports.services.report_preparation_service import ReportPreparationService as Service
from apps.tests.models import Instrument, TestApplication


@override_settings(
    REPORT_PREPARATION_ENABLED=True, SPECIALIST_AI_ENABLED=True,
    SPECIALIST_AI_PROVIDER="ollama", SPECIALIST_AI_MODEL="synthetic-local-model",
    SPECIALIST_OLLAMA_BASE_URL="http://127.0.0.1:11434/v1", SPECIALIST_AI_INSTRUMENTS=["wasi"],
)
class ReportPreparationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create(username="prep-owner", email="prep-owner@example.test", role="neuropsychologist", api_token_hash=hash_api_token("owner-prep-token"))
        self.other = User.objects.create(username="prep-other", email="prep-other@example.test", role="admin", api_token_hash=hash_api_token("other-prep-token"))
        self.patient = Patient.objects.create(full_name="Paciente Sintético Privado", created_by=self.owner, birth_date=date(1990, 1, 1))
        self.evaluation = Evaluation.objects.create(patient=self.patient, examiner=self.owner, start_date=date(2026, 1, 1), referral_reason="Motivo clínico sintético privado")
        self.report = Report.objects.create(evaluation=self.evaluation, patient=self.patient, author=self.owner, edited_text="Texto humano preservado")
        self.section = ReportSection.objects.create(report=self.report, key="atencao", title="Atenção", content_edited="Seção editada privada", is_locked=True)
        instrument, _ = Instrument.objects.get_or_create(code="wasi", defaults={"name": "WASI"})
        self.application = TestApplication.objects.create(evaluation=self.evaluation, instrument=instrument, is_validated=True, computed_payload={"qi": 100}, raw_payload={"form": "self", "respondent_name": "Informante Sintético Privado"})
        template, _ = AnamnesisTemplate.objects.get_or_create(code="preparation-synthetic", defaults={"name": "Sintético", "target_type": "adult"})
        self.anamnesis = AnamnesisResponse.objects.create(evaluation=self.evaluation, patient=self.patient, template=template, status="reviewed", reviewed_by=self.owner, reviewed_at=timezone.now(), answers_payload={"history": "História sintética privada"})
        self.client = TestClient(router)
        self.headers = {"Authorization": "Bearer owner-prep-token"}
        self.other_headers = {"Authorization": "Bearer other-prep-token"}
        self.path = f"/evaluations/{self.evaluation.pk}"

    def start(self, payload=None):
        return self.client.post(self.path, json=payload or {}, headers=self.headers)

    def status(self, suffix=""):
        response = self.client.get(self.path + suffix, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")
        return response.json()

    def test_start_and_status_are_private_including_foreign_admin(self):
        for method in ("get", "post"):
            with self.subTest(method=method):
                args = {"json": {}} if method == "post" else {}
                self.assertEqual(getattr(self.client, method)(self.path, **args).status_code, 401)
                self.assertEqual(getattr(self.client, method)(self.path, headers=self.other_headers, **args).status_code, 404)
        self.assertFalse(ReportPreparation.objects.exists())

    def test_flag_off_hides_feature_and_never_writes(self):
        with override_settings(REPORT_PREPARATION_ENABLED=False):
            self.assertEqual(self.status(), {"enabled": False})
            self.assertEqual(self.start().status_code, 403)
        self.assertFalse(ReportPreparation.objects.exists())

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_routes_are_registered_on_the_main_api(self):
        client = Client()
        path = f"/api/report-preparations/evaluations/{self.evaluation.pk}"
        response = client.get(path, HTTP_AUTHORIZATION=self.headers["Authorization"])
        self.assertEqual(response.status_code, 200, response.content)
        response = client.post(path, data="{}", content_type="application/json", HTTP_AUTHORIZATION=self.headers["Authorization"])
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")

    def test_start_is_idempotent_and_never_calls_ai_or_changes_report(self):
        before = list(Report.objects.filter(pk=self.report.pk).values())
        sections = list(self.report.sections.values())
        with patch("apps.reports.services.specialist_run_service.SpecialistRunService.enqueue") as enqueue, patch("apps.reports.services.specialist_agent_service.SpecialistAgentService.generate") as generate:
            first = self.start()
            second = self.start()
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(second.status_code, 200, second.content)
        self.assertEqual(first.json()["preparation"]["id"], second.json()["preparation"]["id"])
        enqueue.assert_not_called()
        generate.assert_not_called()
        self.assertFalse(SpecialistRun.objects.exists())
        self.assertEqual(before, list(Report.objects.filter(pk=self.report.pk).values()))
        self.assertEqual(sections, list(self.report.sections.values()))
        self.assertEqual(ReportPreparation.objects.count(), 1)

    def test_inventory_completion_is_not_clinical_or_execution_approval(self):
        response = self.start()
        self.assertEqual(response.json()["preparation"]["status"], "prepared")
        self.assertFalse(response.json()["ready_for_execution"])
        self.assertFalse(self.status()["ready_for_execution"])
        self.assertEqual(ReportPreparationStep.objects.filter(status="completed").count(), 1)
        self.assertEqual(ReportPreparationStep.objects.filter(status="unavailable").count(), 6)

    def test_get_is_read_only_even_without_report(self):
        self.report.delete()
        self.assertTrue(self.status()["can_prepare"])
        self.assertFalse(Report.objects.exists())
        self.assertFalse(ReportPreparation.objects.exists())

    def test_first_click_creates_only_an_empty_draft_target(self):
        self.report.delete()
        self.assertEqual(self.start().status_code, 201)
        self.assertEqual(self.start().status_code, 200)
        report = Report.objects.get()
        self.assertEqual(report.status, "draft")
        self.assertEqual(report.context_payload, {})
        self.assertEqual(report.generated_text, "")
        self.assertFalse(report.sections.exists())

    def test_manifest_omits_clinical_text_and_credentials(self):
        self.start()
        data = json.dumps(ReportPreparation.objects.get().manifest)
        for private in (self.patient.full_name, self.evaluation.referral_reason, self.report.edited_text, self.section.content_edited, "História sintética privada", "Informante Sintético Privado", "owner-prep-token", "OPENAI_API_KEY"):
            self.assertNotIn(private, data)
        self.assertEqual(len(ReportPreparation.objects.get().source_sha256), 64)

    def test_all_applications_and_informants_remain_separate(self):
        unsupported = Instrument.objects.create(code="prep-unsupported", name="Outro instrumento")
        app2 = TestApplication.objects.create(evaluation=self.evaluation, instrument=self.application.instrument, computed_payload={"qi": 110}, is_validated=True, raw_payload={"form": "parent"})
        app3 = TestApplication.objects.create(evaluation=self.evaluation, instrument=unsupported)
        checked = self.status()
        self.assertEqual({a["application_id"] for a in checked["applications"]}, {self.application.pk, app2.pk, app3.pk})
        self.assertEqual({b["code"] for b in checked["blockers"]}, {"instrument_unsupported", "application_not_validated"})
        self.assertEqual(self.start().json()["preparation"]["status"], "blocked")

    def test_unusable_results_block_but_do_not_crash_or_validate_test(self):
        TestApplication.objects.filter(pk=self.application.pk).update(computed_payload={}, classified_payload={})
        self.assertIn("results_invalid", {b["code"] for b in self.status()["blockers"]})
        self.start()
        self.application.refresh_from_db()
        self.assertEqual(self.application.computed_payload, {})

    def test_missing_clinical_data_and_anamnesis_are_explicit(self):
        Patient.objects.filter(pk=self.patient.pk).update(birth_date=None)
        Evaluation.objects.filter(pk=self.evaluation.pk).update(start_date=None, referral_reason="")
        self.anamnesis.delete()
        self.application.delete()
        codes = {b["code"] for b in self.status()["blockers"]}
        self.assertTrue({"birth_date_missing", "start_date_missing", "purpose_missing", "anamnesis_review_missing", "applications_missing"} <= codes)

    def test_malformed_raw_payload_is_a_safe_blocker(self):
        TestApplication.objects.filter(pk=self.application.pk).update(raw_payload=["invalid"])
        self.assertIn("results_invalid", {b["code"] for b in self.status()["blockers"]})
        self.assertEqual(self.start().status_code, 201)

    def test_new_editable_revision_does_not_change_finalized_report(self):
        Report.objects.filter(pk=self.report.pk).update(status="finalized", final_text="Bytes históricos não modificados")
        original = list(Report.objects.filter(pk=self.report.pk).values())
        revision = Report.objects.create(evaluation=self.evaluation, patient=self.patient, author=self.owner)
        response = self.start()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["preparation"]["report_id"], revision.pk)
        self.assertEqual(original, list(Report.objects.filter(pk=self.report.pk).values()))

    def test_anamnesis_review_by_another_professional_does_not_pass(self):
        AnamnesisResponse.objects.filter(pk=self.anamnesis.pk).update(reviewed_by=self.other)
        self.assertIn("anamnesis_review_missing", {b["code"] for b in self.status()["blockers"]})

    def test_divergent_patient_source_is_blocked_without_disclosure(self):
        foreign = Patient.objects.create(full_name="Não divulgar", created_by=self.other)
        AnamnesisResponse.objects.filter(pk=self.anamnesis.pk).update(patient=foreign, answers_payload={"private": "Não divulgar história"})
        checked = self.status()
        self.assertIn("source_patient_mismatch", {b["code"] for b in checked["blockers"]})
        self.assertNotIn("Não divulgar", json.dumps(checked))

    def test_clinical_source_edit_marks_history_stale_without_rewriting_it(self):
        self.start()
        original = ReportPreparation.objects.get()
        AnamnesisResponse.objects.filter(pk=self.anamnesis.pk).update(answers_payload={"history": "Novo"})
        self.assertEqual(self.status()["latest"]["status"], "stale")
        original.refresh_from_db()
        self.assertEqual(original.status, "prepared")
        self.assertEqual(self.start().status_code, 201)
        self.assertEqual(ReportPreparation.objects.count(), 2)
        self.assertTrue(self.status()["latest"]["is_current"])

    def test_test_text_and_validation_changes_mark_sources_stale(self):
        self.start()
        TestApplication.objects.filter(pk=self.application.pk).update(interpretation_text="Alteração humana", is_validated=False)
        checked = self.status()
        self.assertEqual(checked["latest"]["status"], "stale")
        self.assertIn("application_not_validated", {b["code"] for b in checked["blockers"]})

    def test_added_or_deleted_application_marks_sources_stale(self):
        self.start()
        self.application.delete()
        self.assertEqual(self.status()["latest"]["status"], "stale")

    def test_edited_section_and_report_are_preserved_and_detected(self):
        self.start()
        ReportSection.objects.filter(pk=self.section.pk).update(content_edited="Nova edição humana")
        self.assertEqual(self.status()["latest"]["status"], "stale")
        self.start()
        self.section.refresh_from_db()
        self.assertEqual(self.section.content_edited, "Nova edição humana")
        self.assertTrue(self.section.is_locked)

    def test_progress_documents_and_patient_changes_are_in_manifest(self):
        self.start()
        entry = EvaluationProgressEntry.objects.create(evaluation=self.evaluation, patient=self.patient, professional=self.owner, entry_date=date(2026, 1, 1), clinical_notes="Privado")
        self.assertEqual(self.status()["latest"]["status"], "stale")
        self.start()
        doc = EvaluationDocument.objects.create(evaluation=self.evaluation, patient=self.patient, title="Documento", file="synthetic/not-opened.pdf")
        self.assertEqual(self.status()["latest"]["status"], "stale")
        self.start()
        Patient.objects.filter(pk=self.patient.pk).update(schooling="higher")
        self.assertEqual(self.status()["latest"]["status"], "stale")
        manifest = ReportPreparation.objects.first().manifest
        self.assertEqual(manifest["clinical_sources"]["documents"][0]["id"], doc.pk)
        self.assertEqual(manifest["clinical_sources"]["progress_entries"][0]["id"], entry.pk)

    def test_model_policy_and_workflow_changes_invalidate_sources(self):
        self.start()
        for override in ({"SPECIALIST_AI_MODEL": "another-local-model"}, {"SPECIALIST_AI_INSTRUMENTS": []}):
            with override_settings(**override):
                self.assertEqual(self.status()["latest"]["status"], "stale")
        with patch.object(Service, "VERSION", "preparation-inventory-next"):
            self.assertEqual(self.status()["latest"]["status"], "stale")

    def test_professional_identity_and_anamnesis_template_are_versioned(self):
        self.start()
        get_user_model().objects.filter(pk=self.owner.pk).update(full_name="Nova identidade profissional")
        self.assertEqual(self.status()["latest"]["status"], "stale")
        self.start()
        AnamnesisTemplate.objects.filter(pk=self.anamnesis.template_id).update(schema_payload={"new": "schema"})
        self.assertEqual(self.status()["latest"]["status"], "stale")

    def test_configuration_is_safe_and_no_external_provider_is_enabled(self):
        with override_settings(SPECIALIST_AI_PROVIDER="openai", OPENAI_API_KEY="never-in-manifest"):
            checked = self.status()
            self.assertIn("local_provider_required", {b["code"] for b in checked["blockers"]})
            self.start()
            self.assertNotIn("never-in-manifest", json.dumps(ReportPreparation.objects.get().manifest))

    def test_invalid_provider_url_is_not_stored_or_exposed(self):
        with override_settings(SPECIALIST_OLLAMA_BASE_URL="https://secret-user:secret-pass@example.test/v1?token=secret"):
            checked = self.status()
            self.assertIn("specialist_configuration", {b["code"] for b in checked["blockers"]})
            self.start()
            self.assertNotIn("secret-pass", json.dumps(ReportPreparation.objects.get().manifest))

    def test_finalized_sent_and_generating_reports_are_never_changed(self):
        for status in ("finalized", "sent", "generating"):
            with self.subTest(status=status):
                Report.objects.filter(pk=self.report.pk).update(status=status, final_text="Histórico imutável")
                before = list(Report.objects.values())
                self.assertFalse(self.status()["can_prepare"])
                self.assertEqual(self.start().status_code, 409)
                self.assertEqual(before, list(Report.objects.values()))
        self.assertFalse(ReportPreparation.objects.exists())

    def test_archived_or_approved_evaluations_block_even_without_report(self):
        self.report.delete()
        for status in ("archived", "approved"):
            Evaluation.objects.filter(pk=self.evaluation.pk).update(status=status)
            self.assertEqual(self.start().status_code, 409)
            self.assertFalse(Report.objects.exists())

    def test_ambiguous_target_requires_selection(self):
        report2 = Report.objects.create(evaluation=self.evaluation, patient=self.patient, author=self.owner)
        self.assertFalse(self.status()["can_prepare"])
        self.assertEqual(self.start().status_code, 409)
        self.assertEqual(self.start({"report_id": report2.pk}).status_code, 201)
        self.assertEqual(self.status(f"?report_id={report2.pk}")["target_report_id"], report2.pk)

    def test_foreign_and_mismatched_report_ids_are_not_found(self):
        other_report = Report.objects.create(evaluation=self.evaluation, patient=self.patient, author=self.other)
        other_patient = Patient.objects.create(full_name="Outro", created_by=self.owner)
        mismatch = Report.objects.create(evaluation=self.evaluation, patient=other_patient, author=self.owner)
        for report in (other_report, mismatch):
            self.assertEqual(self.start({"report_id": report.pk}).status_code, 404)
            self.assertEqual(self.client.get(self.path + f"?report_id={report.pk}", headers=self.headers).status_code, 404)

    def test_owner_and_examiner_changes_revoke_status_and_start(self):
        self.start()
        Evaluation.objects.filter(pk=self.evaluation.pk).update(examiner=self.other)
        self.assertEqual(self.client.get(self.path, headers=self.headers).status_code, 404)
        self.assertEqual(self.start().status_code, 404)

    def test_readonly_and_inactive_accounts_cannot_prepare(self):
        get_user_model().objects.filter(pk=self.owner.pk).update(role="readonly")
        self.assertFalse(self.status()["can_prepare"])
        self.assertEqual(self.start().status_code, 403)
        get_user_model().objects.filter(pk=self.owner.pk).update(is_active=False)
        self.assertEqual(self.start().status_code, 401)

    def test_database_constraint_defends_duplicate_manifests(self):
        self.start()
        preparation = ReportPreparation.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            ReportPreparation.objects.create(report=self.report, evaluation=self.evaluation, requested_by=self.owner, workflow_version=preparation.workflow_version, source_sha256=preparation.source_sha256, status="prepared")

    def test_more_than_thirty_applications_are_visible_and_blocked(self):
        TestApplication.objects.bulk_create([TestApplication(evaluation=self.evaluation, instrument=self.application.instrument) for _ in range(30)])
        checked = self.status()
        self.assertEqual(len(checked["applications"]), 31)
        self.assertIn("applications_limit", {b["code"] for b in checked["blockers"]})

    def test_failure_rolls_back_empty_report_and_preparation(self):
        self.report.delete()
        with patch.object(ReportPreparationStep.objects, "bulk_create", side_effect=RuntimeError("synthetic failure")):
            with self.assertRaises(RuntimeError):
                Service.start(user=self.owner, evaluation_id=self.evaluation.pk)
        self.assertFalse(Report.objects.exists())
        self.assertFalse(ReportPreparation.objects.exists())
