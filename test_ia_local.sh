#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  . "$ROOT_DIR/.env"
  set +a
fi

if [ ! -x "$ROOT_DIR/.venv/bin/python" ]; then
  printf 'Virtualenv nao encontrado em .venv\n' >&2
  exit 1
fi

printf '\n[1/4] Verificando Ollama...\n'
curl -fsS "${OLLAMA_BASE_URL:-http://localhost:11434}/api/tags"

printf '\n\n[2/4] Verificando Django...\n'
"$ROOT_DIR/.venv/bin/python" "$ROOT_DIR/manage.py" check

printf '\n[3/4] Testando geracao local no service de laudo...\n'
"$ROOT_DIR/.venv/bin/python" "$ROOT_DIR/manage.py" shell -c "from apps.reports.models import Report; from apps.accounts.models import User; from apps.reports.services.report_section_service import ReportSectionService; report=Report.objects.get(id=1); user=User.objects.get(id=1); section=ReportSectionService.regenerate_section(report, 'fdt', user=user); print({'section_id': section.id, 'section_key': section.key, 'provider': section.generation_metadata.get('provider'), 'model': section.generation_metadata.get('model'), 'warnings': section.warnings_payload, 'preview': (section.content_generated or '')[:400]})"

printf '\n[4/4] Comandos uteis para teste HTTP manual\n'
printf 'Suba o backend: .venv/bin/python manage.py runserver\n'
printf 'Depois use um token valido e chame:\n'
printf 'curl -X POST http://127.0.0.1:8000/api/reports/1/regenerate-section/fdt -H "Authorization: Bearer <TOKEN>"\n'
