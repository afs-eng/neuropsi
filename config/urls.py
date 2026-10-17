from django.contrib import admin
from django.http import JsonResponse, HttpResponseNotFound
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.api.router import api
from apps.patients import views as patient_views
from apps.evaluations import views as eval_views
from apps.tests import views as test_views
from apps.reports import views as report_views


urlpatterns = [
    path("healthz/", lambda request: JsonResponse({"status": "ok"}), name="healthz"),
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    # Dashboard
    path("", patient_views.dashboard_view, name="dashboard"),
    # Pacientes
    path("pacientes/", include("apps.patients.urls")),
    # Avaliações
    path("avaliacoes/", include("apps.evaluations.urls")),
    # Testes
    path("testes/", include("apps.tests.urls")),
    # Relatórios
    path("relatorios/", include("apps.reports.urls")),
]

if settings.DEBUG:
    # Documentos clínicos só podem ser baixados pela API autenticada.
    urlpatterns += [
        path(f"{settings.MEDIA_URL.lstrip('/')}documents/<path:path>", lambda request, path: HttpResponseNotFound()),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
