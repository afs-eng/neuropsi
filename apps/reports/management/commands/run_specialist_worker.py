import time

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from django.db import DatabaseError
from apps.reports.models import SpecialistRun

from apps.reports.services.specialist_run_service import SpecialistRunService


class Command(BaseCommand):
    help = "Processa a fila persistente de especialistas, sem alterar textos do laudo."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Processar no máximo uma execução e sair.")
        parser.add_argument("--poll-interval", type=float, default=5)
        parser.add_argument("--report-id", type=int, help="Processar somente a fila de um laudo do piloto.")
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
        if options["check"]:
            try:
                runs = SpecialistRun.objects.all()
                if options["report_id"] is not None:
                    runs = runs.filter(report_id=options["report_id"])
                count = runs.filter(status=SpecialistRun.Status.QUEUED).count()
            except DatabaseError:
                raise CommandError("Não foi possível acessar a fila. Confira o banco e as migrações; nenhuma chamada de IA foi feita.") from None
            self.stdout.write(f"Configuração e fila acessíveis; queued={count}. Sem chamadas de IA. Isso não comprova homologação do modelo nem worker ativo.")
            return
        try:
            while True:
                close_old_connections()
                run = SpecialistRunService.process_next(report_id=options["report_id"])
                if run is not None:
                    self.stdout.write(f"specialist_run={run.pk} status={run.status}")
                if options["once"]:
                    return
                if run is None:
                    time.sleep(options["poll_interval"])
        except KeyboardInterrupt:
            self.stdout.write("Worker interrompido; execuções não serão repetidas automaticamente.")
        finally:
            close_old_connections()
