from ninja import NinjaAPI
from django.conf import settings

from apps.accounts.api.router import router as accounts_router
from apps.ai.api.router import router as ai_router
from apps.patients.api.router import router as patients_router
from apps.evaluations.api.router import router as evaluations_router
from apps.documents.api.router import router as documents_router
from apps.anamnesis.api.router import (
    router as anamnesis_router,
    public_router as public_anamnesis_router,
)
from apps.tests.api.router import router as tests_router
from apps.reports.api.router import router as reports_router
from apps.reports.api.template_endpoints import router as report_templates_router

from apps.api.system import router as system_router

api = NinjaAPI(
    title="Laudos AI API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

api.add_router("/system", system_router)
api.add_router("/accounts", accounts_router)
api.add_router("/ai", ai_router)
api.add_router("/patients", patients_router)
api.add_router("/evaluations", evaluations_router)
api.add_router("/documents", documents_router)
api.add_router("/anamnesis", anamnesis_router)
api.add_router("/tests", tests_router)
api.add_router("/reports", reports_router)
api.add_router("/report-templates", report_templates_router)
api.add_router("/public/anamnesis", public_anamnesis_router)
