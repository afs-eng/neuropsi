import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from django.db import DatabaseError
from apps.reports.models import SpecialistRun

from apps.reports.services.specialist_run_service import SpecialistRunService
from apps.reports.services.specialist_errors import VALIDATION_CODES, VALIDATION_SECTIONS


class Command(BaseCommand):
    help = "Processa a fila persistente de especialistas, sem alterar textos do laudo."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Processar no máximo uma execução e sair.")
        parser.add_argument("--poll-interval", type=float, default=5)
        parser.add_argument("--report-id", type=int, help="Processar somente a fila de um laudo do piloto.")
        parser.add_argument("--username", help="Acompanhar somente a fila desta conta, em todos os seus laudos.")
        parser.add_argument("--check", action="store_true", help="Verificar configuração e banco sem reclamar execuções ou chamar IA.")

    def handle(self, *args, **options):
        if options["poll_interval"] < 1:
            raise CommandError("Intervalo mínimo: 1 segundo.")
        if options["report_id"] is not None and options["report_id"] < 1:
            raise CommandError("Informe um ID de laudo positivo.")
        try:
            SpecialistRunService.configuration()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        user_id = None
        if options["username"] is not None:
            try:
                user = get_user_model().objects.filter(username=options["username"], is_active=True).first()
            except DatabaseError:
                raise CommandError("Não foi possível consultar a conta no banco configurado.") from None
            if user is None or user.role not in SpecialistRunService.CLINICAL_ROLES:
                raise CommandError("Informe uma conta ativa com perfil clínico autorizado no banco configurado.")
            user_id = user.pk
        if options["check"]:
            try:
                runs = SpecialistRun.objects.all()
                if options["report_id"] is not None:
                    runs = runs.filter(report_id=options["report_id"])
                if user_id is not None:
                    runs = runs.filter(requested_by_id=user_id)
                count = runs.filter(status=SpecialistRun.Status.QUEUED).count()
            except DatabaseError:
                raise CommandError("Não foi possível acessar a fila. Confira o banco e as migrações; nenhuma chamada de IA foi feita.") from None
            self.stdout.write(f"Configuração e fila acessíveis; queued={count}. Sem chamadas de IA. Isso não comprova homologação do modelo nem worker ativo.")
            return
        if user_id is None and options["report_id"] is None:
            self.stderr.write("Atenção: sem --username ou --report-id, o worker acompanha a fila compartilhada de todas as contas.")
        scope = f"conta #{user_id}" if user_id is not None else "todas as contas"
        report_scope = f"laudo #{options['report_id']}" if options["report_id"] is not None else "todos os laudos"
        self.stdout.write(f"Worker ativo: {scope}; {report_scope}. Ctrl+C para encerrar.")
        idle_announced = False
        try:
            while True:
                close_old_connections()
                run = SpecialistRunService.process_next(report_id=options["report_id"], requested_by_id=user_id)
                if run is not None:
                    idle_announced = False
                    details = f" error_code={run.error_code}" if run.error_code else ""
                    validation_code = (run.usage_payload or {}).get("validation_code")
                    if validation_code in VALIDATION_CODES:
                        details += f" validation_code={validation_code}"
                        section = (run.usage_payload or {}).get("validation_section")
                        if isinstance(section, str) and section in VALIDATION_SECTIONS:
                            details += f" validation_section={section}"
                    self.stdout.write(f"specialist_run={run.pk} status={run.status}{details}")
                if options["once"]:
                    return
                if run is None:
                    if not idle_announced:
                        self.stdout.write("Aguardando novas solicitações no escopo selecionado. O worker permanece ativo.")
                        idle_announced = True
                    time.sleep(options["poll_interval"])
        except KeyboardInterrupt:
            self.stdout.write("Worker interrompido; execuções não serão repetidas automaticamente.")
        finally:
            close_old_connections()
