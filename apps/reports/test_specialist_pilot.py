from datetime import timedelta
from io import StringIO
import os
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from apps.reports import test_specialist_runs
from apps.reports.models import Report, SpecialistReview, SpecialistRun
from apps.reports.services.specialist_agent_service import SpecialistAgentService
from apps.reports.services.specialist_review_service import SpecialistReviewService
from apps.reports.services.specialist_run_service import SpecialistRunService
from apps.tests.models import TestApplication


@override_settings(
    SPECIALIST_AI_ENABLED=True, SPECIALIST_AI_INSTRUMENTS=["wisc4", "scared"],
    SPECIALIST_AI_MODEL="test-model", AI_PROVIDER="openai", OPENAI_API_KEY="not-real",
    OPENAI_BASE_URL="https://provider.example/v1",
)
class SpecialistPilotTests(TestCase):
    def setUp(self):
        test_specialist_runs.SpecialistRunTests.setUp(self)
        self.owner.crp = "00/12345"
        self.owner.save(update_fields=["crp"])

    def ready_run(self):
        runs, _ = SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)
        SpecialistRunService.process_next(generator=test_specialist_runs.SpecialistRunTests.valid_generator, report_id=self.report.pk)
        return SpecialistRun.objects.get(pk=runs[0].pk)

    def review(self, run, decision="approved", notes="", **overrides):
        return self.client.post(f"/{self.report.pk}/specialist-runs/{run.pk}/reviews", headers=self.headers, json={
            "decision": decision, "notes": notes, "source_sha256": run.source_sha256,
            "output_sha256": SpecialistReviewService.output_fingerprint(run), **overrides,
        })

    def test_status_is_private_and_makes_no_model_calls(self):
        with patch.object(SpecialistAgentService, "generate") as generate:
            url = f"/{self.report.pk}/specialist-status"
            self.assertEqual(self.client.get(url).status_code, 401)
            self.assertEqual(self.client.get(url, headers=self.other_headers).status_code, 404)
            response = self.client.get(url, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Cache-Control"], "private, no-store")
            self.assertEqual(response.json()["worker_status"], "not_monitored")
            self.assertTrue(response.json()["can_request"])
            self.assertTrue(response.json()["legacy_unchanged"])
            self.assertNotIn("not-real", response.content.decode())
            generate.assert_not_called()

    def test_status_keeps_separate_applications_and_informants(self):
        second = TestApplication.objects.create(
            evaluation=self.evaluation, instrument=self.instrument, is_validated=True,
            raw_payload={"respondent_name": "Outro informante"}, computed_payload={"qi": 100},
        )
        data = self.client.get(f"/{self.report.pk}/specialist-status", headers=self.headers).json()
        self.assertEqual([app["id"] for app in data["applications"]], [self.application.pk, second.pk])
        self.assertEqual(data["applications"][1]["respondent"], "Outro informante")

    @override_settings(SPECIALIST_AI_ENABLED=False)
    def test_disabled_pilot_reports_configuration_without_breaking_report(self):
        response = self.client.get(f"/{self.report.pk}/specialist-status", headers=self.headers)
        self.assertFalse(response.json()["configured"])
        self.assertFalse(response.json()["can_request"])

    @override_settings(SPECIALIST_AI_MODEL="")
    def test_missing_explicit_model_cannot_activate_pilot(self):
        response = self.client.get(f"/{self.report.pk}/specialist-status", headers=self.headers)
        self.assertFalse(response.json()["configured"])
        self.assertIn("SPECIALIST_AI_MODEL", response.json()["configuration_message"])

    def test_review_records_history_without_replacing_human_content(self):
        run = self.ready_run()
        self.assertEqual(self.review(run).status_code, 201)
        self.assertEqual(self.review(run, decision="rejected", notes="Exige revisão clínica adicional").status_code, 201)
        self.assertEqual(SpecialistReview.objects.filter(run=run).count(), 2)
        self.report.refresh_from_db()
        self.section.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(self.report.edited_text, "Texto revisado que deve ser preservado.")
        self.assertEqual(self.section.content_edited, "Revisão humana.")
        self.assertEqual(self.application.interpretation_text, "Texto antigo: QI 120.")
        self.assertEqual(self.report.status, "draft")
        results = self.client.get(f"/{self.report.pk}/specialist-runs", headers=self.headers).json()
        self.assertEqual(results[0]["reviews"][0]["decision"], "rejected")
        self.assertTrue(results[0]["review_is_current"])

    def test_approved_review_is_not_valid_after_result_correction(self):
        run = self.ready_run()
        self.assertEqual(self.review(run).status_code, 201)
        results = self.client.get(f"/{self.report.pk}/specialist-runs", headers=self.headers).json()
        self.assertFalse(results[0]["requires_professional_review"])
        self.application.computed_payload = {"qi": 110}
        self.application.save(update_fields=["computed_payload"])
        self.assertEqual(self.review(run).status_code, 400)
        results = self.client.get(f"/{self.report.pk}/specialist-runs", headers=self.headers).json()
        self.assertFalse(results[0]["review_is_current"])
        self.assertTrue(results[0]["requires_professional_review"])
        self.assertEqual(results[0]["status"], "stale")

    def test_stale_browser_content_cannot_be_approved(self):
        run = self.ready_run()
        self.assertEqual(self.review(run, output_sha256="a" * 64).status_code, 400)
        self.assertFalse(SpecialistReview.objects.exists())

    def test_other_user_or_assistant_or_missing_crp_cannot_review(self):
        run = self.ready_run()
        body = {"decision": "approved", "source_sha256": run.source_sha256, "output_sha256": SpecialistReviewService.output_fingerprint(run)}
        url = f"/{self.report.pk}/specialist-runs/{run.pk}/reviews"
        self.assertEqual(self.client.post(url, headers=self.other_headers, json=body).status_code, 404)
        for role, crp in [("assistant", "00/12345"), ("neuropsychologist", "")]:
            self.owner.role, self.owner.crp = role, crp
            self.owner.save(update_fields=["role", "crp"])
            self.assertEqual(self.client.post(url, headers=self.headers, json=body).status_code, 403)

    def test_rejection_requires_reason_and_finalized_report_blocks_review(self):
        run = self.ready_run()
        self.assertEqual(self.review(run, decision="rejected", notes="  ").status_code, 400)
        self.report.status = "finalized"
        self.report.save(update_fields=["status"])
        self.assertEqual(self.review(run).status_code, 400)

    def test_invalid_evidence_cannot_be_approved(self):
        run = self.ready_run()
        run.output_payload["findings"][0]["evidence_ids"] = ["/unknown"]
        run.save(update_fields=["output_payload"])
        self.assertEqual(self.review(run).status_code, 400)

    def test_local_worker_filter_leaves_other_reports_queued(self):
        other_report = Report.objects.create(patient=self.patient, evaluation=self.evaluation, author=self.owner)
        other_runs, _ = SpecialistRunService.enqueue(user=self.owner, report_id=other_report.pk)
        runs, _ = SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)
        output = StringIO()
        with patch.object(SpecialistAgentService, "generate", side_effect=test_specialist_runs.SpecialistRunTests.valid_generator):
            call_command("run_specialist_worker", once=True, report_id=self.report.pk, stdout=output)
        other_runs[0].refresh_from_db()
        runs[0].refresh_from_db()
        self.assertEqual(other_runs[0].status, "queued")
        self.assertEqual(runs[0].status, "needs_review")

    def test_worker_check_does_not_claim_or_call_ai(self):
        runs, _ = SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)
        with patch.object(SpecialistAgentService, "generate") as generate, patch.object(SpecialistRunService, "_claim") as claim:
            output = StringIO()
            call_command("run_specialist_worker", check=True, report_id=self.report.pk, stdout=output)
            generate.assert_not_called()
            claim.assert_not_called()
            self.assertIn("queued=1", output.getvalue())
        runs[0].refresh_from_db()
        self.assertEqual(runs[0].status, "queued")

    def test_interrupted_recovery_respects_report_filter(self):
        other = Report.objects.create(patient=self.patient, evaluation=self.evaluation, author=self.owner)
        other_runs, _ = SpecialistRunService.enqueue(user=self.owner, report_id=other.pk)
        SpecialistRun.objects.filter(pk=other_runs[0].pk).update(status="running", started_at=timezone.now() - timedelta(minutes=11))
        self.assertEqual(SpecialistRunService.recover_interrupted(report_id=self.report.pk), 0)
        other_runs[0].refresh_from_db()
        self.assertEqual(other_runs[0].status, "running")


class WorkerEnvironmentFileTests(SimpleTestCase):
    def test_explicit_env_file_is_loaded_without_running_management_command(self):
        with TemporaryDirectory(prefix="specialist-env-") as folder:
            path = Path(folder) / "worker.env"
            path.write_text("SPECIALIST_ENV_FILE_TEST=from-worker-file\n", encoding="utf-8")
            with patch.dict(os.environ, {"NEUROPSI_ENV_FILE": str(path)}):
                os.environ.pop("SPECIALIST_ENV_FILE_TEST", None)
                runpy.run_path(str(settings.BASE_DIR / "manage.py"), run_name="worker_env_test")
                self.assertEqual(os.environ["SPECIALIST_ENV_FILE_TEST"], "from-worker-file")

    def test_missing_explicit_file_does_not_silently_load_default_env(self):
        with TemporaryDirectory(prefix="specialist-env-") as folder:
            with patch.dict(os.environ, {"NEUROPSI_ENV_FILE": str(Path(folder) / "missing.env")}):
                with self.assertRaisesMessage(SystemExit, "arquivo inexistente"):
                    runpy.run_path(str(settings.BASE_DIR / "manage.py"), run_name="worker_env_test")
