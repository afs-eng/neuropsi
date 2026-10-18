from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.reports.models import Report, ReportStatus, SpecialistRun
from apps.tests.models import TestApplication

from .specialist_agent_service import SpecialistAgentService
from .specialist_contracts import SpecialistOutput, validate_evidence
from .specialist_input_service import SpecialistInputService
from .specialist_instructions import INSTRUMENT_INSTRUCTIONS


class SpecialistRunService:
    VERSION = "pydantic-specialist-1"
    CLINICAL_ROLES = {UserRole.ADMIN, UserRole.NEUROPSYCHOLOGIST}

    @staticmethod
    def provider_name() -> str:
        return settings.SPECIALIST_AI_PROVIDER or settings.AI_PROVIDER

    @classmethod
    def configuration(cls) -> tuple[str, str]:
        if not settings.SPECIALIST_AI_ENABLED:
            raise ValueError("Especialistas desabilitados neste ambiente.")
        provider = cls.provider_name()
        if provider not in {"openai", "ollama"}:
            raise ValueError("Provedor dos especialistas inválido: use openai ou ollama.")
        if provider == "openai" and not settings.OPENAI_API_KEY:
            raise ValueError("Configure o provedor OpenAI/OpenRouter dos especialistas.")
        model = settings.SPECIALIST_AI_MODEL.strip()
        if not model or len(model) > 255:
            raise ValueError("Configure SPECIALIST_AI_MODEL explicitamente.")
        base_url = (
            settings.SPECIALIST_OLLAMA_BASE_URL if provider == "ollama"
            else (settings.OPENAI_BASE_URL or "https://api.openai.com/v1")
        ).rstrip("/")
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or len(base_url) > 500:
            raise ValueError("URL do provedor inválida.")
        if provider == "ollama":
            if parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.path != "/v1":
                raise ValueError("Ollama dos especialistas exige endpoint loopback com caminho /v1.")
            if "cloud" in model.lower() or "/" in model:
                raise ValueError("Use um modelo local explícito, sem cloud ou namespace remoto.")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Use HTTPS para transmitir resultados ao provedor.")
        return model, base_url

    @classmethod
    def enqueue(cls, *, user, report_id: int, application_ids: list[int] | None = None):
        if user.role not in cls.CLINICAL_ROLES:
            raise PermissionError("Somente profissionais autorizados podem solicitar interpretações.")
        model, base_url = cls.configuration()
        with transaction.atomic():
            from apps.common.clinical_access import owned_reports

            report = owned_reports(Report.objects.select_for_update(), user).get(pk=report_id)
            if report.status in {ReportStatus.FINALIZED, ReportStatus.SENT}:
                raise ValueError("Laudo finalizado: abra uma nova revisão antes de solicitar especialistas.")
            applications = TestApplication.objects.with_details().filter(
                evaluation_id=report.evaluation_id, is_validated=True,
            )
            if application_ids is not None:
                applications = applications.filter(pk__in=application_ids)
            applications = list(applications.order_by("id"))
            if application_ids is not None and {a.pk for a in applications} != set(application_ids):
                raise ValueError("Uma aplicação não pertence à avaliação ou não está validada.")
            if not applications or len(applications) > 30:
                raise ValueError("Selecione entre 1 e 30 aplicações validadas.")
            runs, skipped = [], []
            for application in applications:
                if application.evaluation.patient_id != report.patient_id:
                    raise ValueError("Paciente do laudo diverge da avaliação.")
                code = application.instrument.code
                if code not in settings.SPECIALIST_AI_INSTRUMENTS or code not in INSTRUMENT_INSTRUCTIONS:
                    skipped.append({"application_id": application.pk, "instrument_code": code, "reason": "not_enabled"})
                    continue
                payload = SpecialistInputService.build(application)
                run, _ = SpecialistRun.objects.get_or_create(
                    report=report, application=application,
                    source_sha256=SpecialistInputService.fingerprint(application),
                    specialist_version=cls.VERSION, model_name=model, provider_base_url=base_url,
                    provider_name=cls.provider_name(),
                    defaults={"requested_by": user, "instrument_code": code, "input_payload": payload},
                )
                runs.append(run)
            return runs, skipped

    @classmethod
    def is_current(cls, run) -> bool:
        app = run.application
        return (
            app.is_validated
            and run.report.evaluation_id == app.evaluation_id
            and run.report.patient_id == app.evaluation.patient_id
            and run.report.author_id == run.requested_by_id
            and app.evaluation.patient.created_by_id == run.requested_by_id
            and app.evaluation.examiner_id in (None, run.requested_by_id)
            and run.specialist_version == cls.VERSION
            and run.source_sha256 == SpecialistInputService.fingerprint(app)
        )

    @classmethod
    def recover_interrupted(cls, report_id=None) -> int:
        # Sem repetição automática: o provedor pode já ter cobrado a chamada.
        runs = SpecialistRun.objects.filter(
            status=SpecialistRun.Status.RUNNING,
            started_at__lt=timezone.now() - timedelta(minutes=10),
        )
        if report_id is not None:
            runs = runs.filter(report_id=report_id)
        return runs.update(status=SpecialistRun.Status.FAILED, error_code="worker_interrupted", finished_at=timezone.now())

    @staticmethod
    def _load(run_id):
        return SpecialistRun.objects.select_related(
            "report", "requested_by", "application__evaluation__patient", "application__instrument",
        ).get(pk=run_id)

    @staticmethod
    def _claim(report_id=None):
        # Compare-and-swap: só um worker pode alterar queued -> running.
        runs = SpecialistRun.objects.filter(status=SpecialistRun.Status.QUEUED)
        if report_id is not None:
            runs = runs.filter(report_id=report_id)
        for run_id in runs.values_list("pk", flat=True)[:50]:
            if SpecialistRun.objects.filter(pk=run_id, status=SpecialistRun.Status.QUEUED).update(
                status=SpecialistRun.Status.RUNNING, started_at=timezone.now(), error_code="",
            ):
                return run_id
        return None

    @classmethod
    def process_next(cls, *, generator=None, report_id=None):
        cls.configuration()
        cls.recover_interrupted(report_id=report_id)
        run_id = cls._claim(report_id=report_id)
        if run_id is None:
            return None
        try:
            run = cls._load(run_id)
        except SpecialistRun.DoesNotExist:
            return None
        output, usage, error = {}, {}, ""
        status = SpecialistRun.Status.FAILED
        try:
            model, base_url = cls.configuration()
            if not run.requested_by.is_active or run.requested_by.role not in cls.CLINICAL_ROLES:
                error = "permission_revoked"
            elif run.report.status in {ReportStatus.FINALIZED, ReportStatus.SENT}:
                error = "report_closed"
            elif run.instrument_code not in settings.SPECIALIST_AI_INSTRUMENTS:
                error = "instrument_disabled"
            elif model != run.model_name or base_url != run.provider_base_url or cls.provider_name() != run.provider_name:
                error = "configuration_changed"
            elif not cls.is_current(run):
                status = SpecialistRun.Status.STALE
            else:
                output, usage = (generator or SpecialistAgentService.generate)(run)
                parsed = SpecialistOutput.model_validate(output)
                validate_evidence(parsed, run.input_payload["facts"], run.instrument_code)
                output = parsed.model_dump()
                status = SpecialistRun.Status.NEEDS_REVIEW if cls.is_current(cls._load(run_id)) else SpecialistRun.Status.STALE
        except Exception:
            # Exceções do SDK podem conter dados clínicos ou credenciais: não persistir/logar o texto.
            error = "generation_failed"
            output = {}
        SpecialistRun.objects.filter(pk=run_id, status=SpecialistRun.Status.RUNNING).update(
            status=status, output_payload=output, usage_payload=usage,
            error_code=error, finished_at=timezone.now(),
        )
        try:
            return cls._load(run_id)
        except SpecialistRun.DoesNotExist:
            return None
