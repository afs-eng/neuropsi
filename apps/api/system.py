from ninja import Router
from django.db import connection
from django.conf import settings
import os

from apps.common.security import rate_limit

router = Router(tags=["system"])


@router.get("/status")
def system_status(request, setup: bool = False):
    db_ok = False
    db_error = None
    tables = []
    setup_result = "Nenhum setup executado"

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_ok = True

            # Check if User table exists
            cursor.execute(
                "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"
            )
            tables = [row[0] for row in cursor.fetchall()]

        # Setup logic is disabled by default and only allowed in local/dev.
        if setup:
            rate_limit(request, "system-setup", limit=2, window_seconds=3600)
            setup_token = request.headers.get("X-System-Setup-Token", "")
            if not settings.DEBUG or not settings.ENABLE_SYSTEM_SETUP:
                return 403, {
                    "status": "forbidden",
                    "message": "System setup is disabled.",
                }
            if not settings.SYSTEM_BOOTSTRAP_PASSWORD:
                return 400, {
                    "status": "forbidden",
                    "message": "Bootstrap password not configured.",
                }
            if not setup_token or setup_token != settings.SYSTEM_BOOTSTRAP_PASSWORD:
                return 403, {
                    "status": "forbidden",
                    "message": "Invalid setup token.",
                }

        if setup and db_ok:
            from django.contrib.auth import get_user_model
            from django.core.management import call_command

            User = get_user_model()

            # Force trigger migrations just in case
            try:
                call_command("migrate", interactive=False)
            except Exception as e:
                setup_result = f"Erro nas migrações: {str(e)}"

            # Create or update admin user
            user, created = User.objects.get_or_create(
                email="admin@neuroavalia.com",
                defaults={
                    "username": "admin",
                    "full_name": "Administrador do Sistema",
                    "role": "admin",
                    "is_superuser": True,
                    "is_staff": True,
                },
            )
            user.set_password(settings.SYSTEM_BOOTSTRAP_PASSWORD)
            user.save()

            # Seed Instruments
            from apps.tests.models.instruments import Instrument

            standard_tests = [
                {"code": "fdt", "name": "FDT", "category": "Funções Executivas"},
                {"code": "ravlt", "name": "RAVLT", "category": "Memória"},
                {"code": "srs2", "name": "SRS-2", "category": "Autismo"},
                {"code": "ssrs", "name": "SSRS", "category": "Social / Comportamento"},
                {"code": "wisc4", "name": "WISC-IV", "category": "Inteligência"},
                {"code": "bpa2", "name": "BPA-2", "category": "Atenção"},
                {"code": "ebadep_a", "name": "EBADEP-A", "category": "Depressão"},
                {"code": "ebadep_ij", "name": "EBADEP-IJ", "category": "Depressão"},
                {"code": "epq_j", "name": "EPQ-J", "category": "Personalidade"},
                {"code": "etdah_ad", "name": "ETDAH-AD", "category": "TDAH"},
                {"code": "etdah_pais", "name": "ETDAH-PAIS", "category": "TDAH"},
            ]

            seeded_count = 0
            for test in standard_tests:
                _, created_i = Instrument.objects.get_or_create(
                    code=test["code"],
                    defaults={
                        "name": test["name"],
                        "category": test["category"],
                        "is_active": True,
                    },
                )
                if created_i:
                    seeded_count += 1

            if created:
                setup_result = (
                    f"Admin CRIADO e {seeded_count} instrumentos semeados com sucesso!"
                )
            else:
                setup_result = (
                    f"Admin ATUALIZADO e {seeded_count} novos instrumentos semeados!"
                )

    except Exception as e:
        db_error = str(e) if settings.DEBUG else "Erro ao consultar o banco de dados"

    response = {
        "status": "online",
        "database": {
            "connected": db_ok,
            "error": db_error,
        },
    }

    if settings.DEBUG:
        response["setup_result"] = setup_result
        response["database"]["has_users_table"] = "accounts_user" in tables
        response["database"]["tables_count"] = len(tables)
        response["environment"] = {
            "debug": settings.DEBUG,
            "render_hostname": os.getenv("RENDER_EXTERNAL_HOSTNAME", "local"),
            "allowed_hosts": settings.ALLOWED_HOSTS,
        }

    return response
