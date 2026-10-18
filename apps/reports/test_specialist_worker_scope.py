from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.evaluations.models import Evaluation
from apps.patients.models import Patient
from apps.reports import test_specialist_runs
from apps.reports.models import Report, SpecialistRun
from apps.reports.services.specialist_agent_service import SpecialistAgentService
from apps.reports.services.specialist_run_service import SpecialistRunService
from apps.tests.models import TestApplication


@override_settings(
    SPECIALIST_AI_ENABLED=True, SPECIALIST_AI_INSTRUMENTS=["wisc4"],
    SPECIALIST_AI_PROVIDER="openai", SPECIALIST_AI_MODEL="test-model",
    AI_PROVIDER="openai", OPENAI_API_KEY="not-real", OPENAI_BASE_URL="https://offline.example/v1",
)
class SpecialistWorkerScopeTests(TestCase):
    def setUp(self):
        test_specialist_runs.SpecialistRunTests.setUp(self)
        patient = Patient.objects.create(full_name="Outro paciente fictício", created_by=self.other)
        evaluation = Evaluation.objects.create(patient=patient, examiner=self.other, start_date=self.evaluation.start_date)
        TestApplication.objects.create(
            evaluation=evaluation, instrument=self.instrument, is_validated=True,
            computed_payload={"qi": 100}, classified_payload={"classificacao": "Média"},
        )
        self.other_report = Report.objects.create(patient=patient, evaluation=evaluation, author=self.other)
        self.second_report = Report.objects.create(patient=self.patient, evaluation=self.evaluation, author=self.owner)

    def enqueue(self, report, user):
        return SpecialistRunService.enqueue(user=user, report_id=report.pk)[0][0]

    def test_username_processes_different_reports_without_claiming_other_users_jobs(self):
        other_run = self.enqueue(self.other_report, self.other)
        first = self.enqueue(self.report, self.owner)
        second = self.enqueue(self.second_report, self.owner)
        stdout = StringIO()
        with patch.object(SpecialistAgentService, "generate", side_effect=test_specialist_runs.SpecialistRunTests.valid_generator) as generate:
            for _ in range(2):
                call_command("run_specialist_worker", username=self.owner.username, once=True, stdout=stdout)
        self.assertEqual(generate.call_count, 2)
        for run in (first, second):
            run.refresh_from_db()
            self.assertEqual(run.status, "needs_review")
        other_run.refresh_from_db()
        self.assertEqual(other_run.status, "queued")
        self.assertIn("todos os laudos", stdout.getvalue())
        self.assertNotIn(self.patient.full_name, stdout.getvalue())

    def test_check_counts_only_selected_account_and_never_claims_jobs(self):
        self.enqueue(self.other_report, self.other)
        stdout = StringIO()
        with patch.object(SpecialistAgentService, "generate") as generate, patch.object(SpecialistRunService, "_claim") as claim:
            call_command("run_specialist_worker", username=self.owner.username, check=True, stdout=stdout)
        self.assertIn("queued=0", stdout.getvalue())
        generate.assert_not_called()
        claim.assert_not_called()
        self.assertEqual(SpecialistRun.objects.get().status, "queued")

    def test_username_and_report_filters_are_intersected(self):
        own_run = self.enqueue(self.report, self.owner)
        other_run = self.enqueue(self.other_report, self.other)
        with patch.object(SpecialistAgentService, "generate") as generate:
            call_command("run_specialist_worker", username=self.owner.username, report_id=self.other_report.pk, once=True, stdout=StringIO())
        generate.assert_not_called()
        for run in (own_run, other_run):
            run.refresh_from_db()
            self.assertEqual(run.status, "queued")

    def test_interrupted_recovery_cannot_modify_other_accounts_runs(self):
        own_run = self.enqueue(self.report, self.owner)
        other_run = self.enqueue(self.other_report, self.other)
        SpecialistRun.objects.filter(pk__in=[own_run.pk, other_run.pk]).update(
            status="running", started_at=timezone.now() - timedelta(minutes=11),
        )
        recovered = SpecialistRunService.recover_interrupted(requested_by_id=self.owner.pk)
        self.assertEqual(recovered, 1)
        own_run.refresh_from_db()
        other_run.refresh_from_db()
        self.assertEqual(own_run.error_code, "worker_interrupted")
        self.assertEqual(other_run.status, "running")

    def test_combined_recovery_filters_do_not_touch_other_reports_of_same_account(self):
        own_run = self.enqueue(self.report, self.owner)
        second = self.enqueue(self.second_report, self.owner)
        SpecialistRun.objects.filter(pk__in=[own_run.pk, second.pk]).update(
            status="running", started_at=timezone.now() - timedelta(minutes=11),
        )
        recovered = SpecialistRunService.recover_interrupted(requested_by_id=self.owner.pk, report_id=self.report.pk)
        self.assertEqual(recovered, 1)
        second.refresh_from_db()
        self.assertEqual(second.status, "running")

    def test_invalid_or_unauthorized_username_cannot_start_processing(self):
        for username in ("missing-account", ""):
            with self.subTest(username=username), patch.object(SpecialistRunService, "process_next") as process:
                with self.assertRaises(CommandError):
                    call_command("run_specialist_worker", username=username, once=True, stdout=StringIO())
                process.assert_not_called()
        for role, active in (("assistant", True), ("neuropsychologist", False)):
            self.owner.role, self.owner.is_active = role, active
            self.owner.save(update_fields=["role", "is_active"])
            with self.subTest(role=role, active=active), self.assertRaises(CommandError):
                call_command("run_specialist_worker", username=self.owner.username, once=True, stdout=StringIO())

    def test_idle_feedback_is_not_repeated_on_every_poll(self):
        run = self.enqueue(self.report, self.owner)
        run.status = "needs_review"
        stdout = StringIO()
        with patch.object(SpecialistRunService, "process_next", side_effect=[None, None, run, None]) as process:
            with patch("apps.reports.management.commands.run_specialist_worker.time.sleep", side_effect=[None, None, KeyboardInterrupt]):
                call_command("run_specialist_worker", username=self.owner.username, stdout=stdout)
        self.assertEqual(stdout.getvalue().count("Aguardando novas solicitações"), 2)
        self.assertIn("Worker ativo", stdout.getvalue())
        self.assertIn("Worker interrompido", stdout.getvalue())
        self.assertEqual(process.call_args.kwargs["requested_by_id"], self.owner.pk)
        self.assertIsNone(process.call_args.kwargs["report_id"])

    def test_unfiltered_worker_warns_about_shared_queue(self):
        stderr = StringIO()
        call_command("run_specialist_worker", once=True, stdout=StringIO(), stderr=stderr)
        self.assertIn("fila compartilhada de todas as contas", stderr.getvalue())
