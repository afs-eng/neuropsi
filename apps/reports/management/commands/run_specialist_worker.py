import time

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from apps.reports.services.specialist_run_service import SpecialistRunService


class Command(BaseCommand):
    help = "Processa a fila persistente de especialistas, sem alterar textos do laudo."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Processar no máximo uma execução e sair.")
        parser.add_argument("--poll-interval", type=float, default=5)

    def handle(self, *args, **options):
        if options["poll_interval"] < 1:
            raise CommandError("Intervalo mínimo: 1 segundo.")
        try:
            SpecialistRunService.configuration()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        try:
            while True:
                close_old_connections()
                run = SpecialistRunService.process_next()
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
