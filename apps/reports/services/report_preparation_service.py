"""Pré-checagem e inventário de fontes. Não executa agentes ou modifica conteúdo."""
import hashlib
import json

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

from apps.accounts.models import UserRole
from apps.anamnesis.models import AnamnesisTemplate
from apps.anamnesis.selectors import get_current_anamnesis_response_by_evaluation
from apps.common.clinical_access import owned_evaluations, owned_reports
from apps.evaluations.models import Evaluation, EvaluationStatus
from apps.reports.models import Report, ReportPreparation, ReportPreparationStep, ReportStatus
from .specialist_input_service import SpecialistInputService
from .specialist_instructions import INSTRUMENT_INSTRUCTIONS
from .specialist_run_service import SpecialistRunService


class PreparationConflict(ValueError):
    pass


class ReportPreparationService:
    VERSION = "preparation-inventory-1"
    STEPS = (
        ("preflight", "Pré-checagem e manifesto"),
        ("interpretations", "Interpretações por aplicação"),
        ("interpretation_review", "Revisão consolidada das interpretações"),
        ("synthesis", "Síntese e conclusão"),
        ("composition", "Composição do laudo"),
        ("audit", "Auditoria"),
        ("final_review", "Revisão e aprovação final"),
    )
    ROLES = {UserRole.ADMIN, UserRole.NEUROPSYCHOLOGIST}

    @staticmethod
    def digest(value):
        data = json.dumps(value, cls=DjangoJSONEncoder, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()

    @classmethod
    def model_digest(cls, instance):
        return cls.digest({field.attname: getattr(instance, field.attname) for field in instance._meta.concrete_fields})

    @staticmethod
    def evaluation(user, evaluation_id, *, lock=False):
        qs = owned_evaluations(Evaluation.objects.all(), user)
        if lock:
            qs = qs.select_for_update()
        return qs.select_related("patient").get(pk=evaluation_id)

    @staticmethod
    def targets(evaluation, user):
        return list(owned_reports(Report.objects.all(), user).filter(
            evaluation=evaluation,
        ).order_by("id"))

    @classmethod
    def target(cls, evaluation, user, report_id=None):
        reports = cls.targets(evaluation, user)
        if report_id is not None:
            report = owned_reports(Report.objects.all(), user).get(pk=report_id, evaluation=evaluation)
            return report
        editable = [r for r in reports if r.status in {ReportStatus.DRAFT, ReportStatus.IN_REVIEW}]
        if len(editable) == 1:
            return editable[0]
        if len(editable) > 1:
            raise PreparationConflict("Há mais de um laudo editável. Selecione o laudo alvo.")
        if any(r.status == ReportStatus.GENERATING for r in reports):
            raise PreparationConflict("Aguarde a geração em andamento antes de preparar o laudo.")
        if reports:
            raise PreparationConflict("Não há laudo editável. Abra uma nova revisão antes de preparar.")
        return None

    @classmethod
    def inspect(cls, evaluation, user, report=None):
        blockers = []

        def block(code, message, application_id=None):
            blockers.append({"code": code, "message": message, "application_id": application_id})

        if evaluation.is_archived or evaluation.status in {EvaluationStatus.ARCHIVED, EvaluationStatus.APPROVED}:
            block("evaluation_closed", "Avaliação encerrada ou arquivada; revise o processo antes de preparar.")
        if report and report.status not in {ReportStatus.DRAFT, ReportStatus.IN_REVIEW}:
            block("report_not_editable", "O laudo alvo não está editável. Abra uma nova revisão ou aguarde a geração atual.")
        if not evaluation.patient.birth_date:
            block("birth_date_missing", "Informe a data de nascimento para conferir as fontes normativas.")
        if not evaluation.start_date:
            block("start_date_missing", "Informe a data de início da avaliação.")
        if not (evaluation.referral_reason.strip() or evaluation.evaluation_purpose.strip()):
            block("purpose_missing", "Informe o motivo do encaminhamento ou a finalidade da avaliação.")

        applications = list(evaluation.test_applications.with_details().order_by("id"))
        if not applications:
            block("applications_missing", "Nenhuma aplicação foi registrada nesta avaliação.")
        if len(applications) > 30:
            block("applications_limit", "A avaliação excede o limite atual de 30 aplicações; nenhuma foi omitida do inventário.")
        coverage = []
        for app in applications:
            code = app.instrument.code
            issues = []
            if not app.is_validated:
                issues.append("not_validated")
                block("application_not_validated", "A aplicação precisa de validação profissional.", app.pk)
            supported = code in INSTRUMENT_INSTRUCTIONS
            enabled = supported and code in settings.SPECIALIST_AI_INSTRUMENTS
            if not supported:
                issues.append("unsupported")
                block("instrument_unsupported", "O instrumento ainda não possui especialista executável.", app.pk)
            elif not enabled:
                issues.append("not_enabled")
                block("instrument_disabled", "O especialista não está habilitado neste ambiente.", app.pk)
            if app.is_validated:
                try:
                    if not all(isinstance(getattr(app, name), dict) for name in (
                        "raw_payload", "computed_payload", "classified_payload", "reviewed_payload",
                    )):
                        raise ValueError("Formato de resultados inválido.")
                    SpecialistInputService.build(app)
                except ValueError:
                    issues.append("results_invalid")
                    block("results_invalid", "Resultados ausentes, inconsistentes ou acima dos limites do especialista.", app.pk)
            coverage.append({
                "application_id": app.pk, "instrument_code": code, "instrument_name": app.instrument.name,
                "validated": app.is_validated, "supported": supported, "enabled": enabled,
                "issues": issues,
                "source_sha256": cls.model_digest(app),
                "specialist_source_sha256": SpecialistInputService.fingerprint(app),
                "specialist_version": SpecialistRunService.version_for(code),
            })

        sources = {}
        for key in ("anamnesis_responses", "progress_entries", "documents"):
            related = getattr(evaluation, key)
            if related.exclude(patient_id=evaluation.patient_id).exists():
                block("source_patient_mismatch", "Há uma fonte com paciente divergente; corrija o vínculo antes de continuar.")
            rows = list(related.filter(patient_id=evaluation.patient_id).order_by("id").values())
            sources[key] = [{"id": row["id"], "sha256": cls.digest(row)} for row in rows]
        sources["anamnesis_templates"] = [
            {"id": row["id"], "sha256": cls.digest(row)}
            for row in AnamnesisTemplate.objects.filter(
                responses__evaluation=evaluation, responses__patient_id=evaluation.patient_id,
            ).distinct().order_by("id").values()
        ]
        anamnesis = get_current_anamnesis_response_by_evaluation(evaluation.pk)
        if not (anamnesis and anamnesis.patient_id == evaluation.patient_id
                and anamnesis.status == "reviewed" and anamnesis.reviewed_by_id == user.pk and anamnesis.reviewed_at):
            block("anamnesis_review_missing", "A anamnese selecionada precisa de revisão da profissional responsável.")
        sources["selected_anamnesis_id"] = anamnesis.pk if anamnesis and anamnesis.patient_id == evaluation.patient_id else None

        configuration = {
            "provider": SpecialistRunService.provider_name(), "model": settings.SPECIALIST_AI_MODEL,
            "enabled_instruments": sorted(settings.SPECIALIST_AI_INSTRUMENTS),
            "specialists_enabled": settings.SPECIALIST_AI_ENABLED,
            "max_output_tokens": settings.SPECIALIST_OLLAMA_MAX_TOKENS,
            "timeout_seconds": settings.SPECIALIST_AI_TIMEOUT,
        }
        try:
            _, url = SpecialistRunService.configuration()
            configuration["endpoint"] = url
        except ValueError:
            block("specialist_configuration", "A configuração dos especialistas está indisponível ou inválida.")
        if configuration["provider"] != "ollama":
            block("local_provider_required", "A nova esteira exige Ollama local, sem fallback para provedor externo.")

        # Apenas hashes de dados clínicos: não guardar respostas, nomes, notas ou prompts.
        manifest = {
            "workflow_version": cls.VERSION, "evaluation_id": evaluation.pk,
            "patient_id": evaluation.patient_id, "owner_id": user.pk,
            "evaluation_sha256": cls.model_digest(evaluation),
            "patient_sha256": cls.model_digest(evaluation.patient),
            "professional_sha256": cls.digest({name: getattr(user, name) for name in (
                "id", "username", "full_name", "first_name", "last_name", "crp", "specialty", "role",
            )}),
            "report_id": report.pk if report else None,
            "report_sha256": cls.digest({
                "report": cls.model_digest(report),
                "sections": list(report.sections.order_by("id").values()),
            }) if report else None,
            "applications": coverage, "clinical_sources": sources, "configuration": configuration,
            "template": {"status": "selection_not_implemented"},
            "preflight_blockers": blockers,
        }
        return {
            "manifest": manifest, "source_sha256": cls.digest(manifest), "blockers": blockers,
            "can_prepare": bool(user.is_active and user.role in cls.ROLES and not any(
                item["code"] in {"evaluation_closed", "report_not_editable"} for item in blockers
            )),
            "ready_for_execution": False,
            "limitations": [
                "Esta entrega registra fontes e pendências; não agenda nem chama a IA.",
                "Homologação clínica, seleção de template, worker e integração ao laudo ainda não estão conectados à preparação.",
                "Anexos são inventariados por metadados; os bytes dos arquivos não foram validados ou interpretados.",
            ],
        }

    @classmethod
    def serialize(cls, preparation, current_sha256):
        return {
            "id": preparation.pk, "report_id": preparation.report_id,
            "status": preparation.status if preparation.source_sha256 == current_sha256 else "stale",
            "stored_status": preparation.status,
            "is_current": preparation.source_sha256 == current_sha256,
            "source_sha256": preparation.source_sha256,
            "created_at": preparation.created_at.isoformat(), "blockers": preparation.blockers,
            "applications": preparation.manifest["applications"],
            "steps": [{"key": s.key, "title": dict(cls.STEPS)[s.key], "status": s.status} for s in preparation.steps.all()],
        }

    @classmethod
    def status(cls, *, user, evaluation_id, report_id=None):
        evaluation = cls.evaluation(user, evaluation_id)
        if not settings.REPORT_PREPARATION_ENABLED:
            return {"enabled": False}
        targets = cls.targets(evaluation, user)
        target_issue = ""
        try:
            report = cls.target(evaluation, user, report_id)
        except PreparationConflict as exc:
            report, target_issue = None, str(exc)
        checked = cls.inspect(evaluation, user, report)
        if target_issue:
            checked["can_prepare"] = False
            checked["blockers"].insert(0, {"code": "target_required", "message": target_issue, "application_id": None})
        preparations = ReportPreparation.objects.filter(
            evaluation=evaluation, requested_by=user,
            report__in=owned_reports(Report.objects.all(), user),
        ).prefetch_related("steps")
        if report:
            preparations = preparations.filter(report=report)
        latest = preparations.filter(source_sha256=checked["source_sha256"]).first() or preparations.first()
        return {
            "enabled": True, "can_prepare": checked["can_prepare"],
            "ready_for_execution": False, "blockers": checked["blockers"],
            "limitations": checked["limitations"], "applications": checked["manifest"]["applications"],
            "source_sha256": checked["source_sha256"], "target_report_id": report.pk if report else None,
            "targets": [{"id": r.pk, "status": r.status, "title": r.title} for r in targets],
            "latest": cls.serialize(latest, checked["source_sha256"]) if latest else None,
        }

    @classmethod
    def start(cls, *, user, evaluation_id, report_id=None):
        if not settings.REPORT_PREPARATION_ENABLED:
            raise PermissionError("A preparação automatizada ainda não foi habilitada neste ambiente.")
        if not user.is_active or user.role not in cls.ROLES:
            raise PermissionError("Somente profissionais responsáveis podem preparar o laudo.")
        with transaction.atomic():
            evaluation = cls.evaluation(user, evaluation_id, lock=True)
            report = cls.target(evaluation, user, report_id)
            checked = cls.inspect(evaluation, user, report)
            if not checked["can_prepare"]:
                raise PreparationConflict("Avaliação ou laudo indisponível para preparação.")
            if report is None:
                report = Report.objects.create(evaluation=evaluation, patient=evaluation.patient, author=user)
            else:
                report = owned_reports(Report.objects.select_for_update(), user).get(pk=report.pk)
            checked = cls.inspect(cls.evaluation(user, evaluation_id), user, report)
            if not checked["can_prepare"]:
                raise PreparationConflict("A avaliação ou o laudo mudou; consulte novamente.")
            preparation, created = ReportPreparation.objects.get_or_create(
                report=report, workflow_version=cls.VERSION, source_sha256=checked["source_sha256"],
                defaults={"evaluation": evaluation, "requested_by": user, "manifest": checked["manifest"],
                          "blockers": checked["blockers"], "status": "blocked" if checked["blockers"] else "prepared"},
            )
            if created:
                ReportPreparationStep.objects.bulk_create([
                    ReportPreparationStep(preparation=preparation, key=key, order=index,
                                          status="completed" if index == 0 else "unavailable")
                    for index, (key, _) in enumerate(cls.STEPS)
                ])
            return preparation, checked, created
