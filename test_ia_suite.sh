#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  . "$ROOT_DIR/.env"
  set +a
fi

LOCAL_PYTHON="$ROOT_DIR/.venv/bin/python"
LOCAL_OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
DOCKER_OLLAMA_URL="${DOCKER_OLLAMA_BASE_URL:-http://host.docker.internal:11434}"
DOCKER_COMPOSE_SERVICE="${DOCKER_BACKEND_SERVICE:-backend}"
REPORT_ID="${REPORT_ID:-1}"

if [ ! -x "$LOCAL_PYTHON" ]; then
  printf 'Virtualenv nao encontrado em .venv\n' >&2
  exit 1
fi

printf '\n[1/6] Verificando Ollama local...\n'
curl -fsS "$LOCAL_OLLAMA_URL/api/tags"

printf '\n\n[2/6] Verificando Django local e aliases...\n'
"$LOCAL_PYTHON" "$ROOT_DIR/manage.py" check
"$LOCAL_PYTHON" "$ROOT_DIR/manage.py" shell -c "from apps.reports.builders.section_builder import normalize_section_key; print({k: normalize_section_key(k) for k in ['epqj','historia_pessoal_anamnese','eficiencia_cognitiva','encaminhamentos','demanda']})"

printf '\n[3/6] Executando teste local rapido (FDT)...\n'
"$ROOT_DIR/test_ia_local.sh"

printf '\n[4/6] Verificando Docker e Ollama no container...\n'
docker compose exec -T "$DOCKER_COMPOSE_SERVICE" python manage.py check
docker compose exec -T "$DOCKER_COMPOSE_SERVICE" python manage.py shell -c "import requests; r = requests.get('$DOCKER_OLLAMA_URL/api/tags', timeout=30); r.raise_for_status(); print(r.json())"

printf '\n[5/6] Validando cobertura das chaves suportadas no Docker...\n'
docker compose exec -T "$DOCKER_COMPOSE_SERVICE" python manage.py shell -c "from pathlib import Path; from apps.reports.models import Report; from apps.reports.services.report_ai_service import ReportAIService; from apps.ai.services.text_generation_service import TextGenerationService; report=Report.objects.get(id=$REPORT_ID); context=report.context_payload or {}; tests={item.get('instrument_code') for item in context.get('validated_tests') or []}; base=Path(TextGenerationService.PROMPTS_DIR); summary=[]; 
for key in sorted(ReportAIService.SUPPORTED_SECTIONS):
    config=ReportAIService._generator_config(key)
    summary.append({'key': key, 'kind': config['kind'], 'prompt_exists': (base / config['prompt']).is_file(), 'has_data': bool(tests & set(config['codes']))})
print(summary)"

printf '\n[6/6] Rodando suite completa de geracao no Docker...\n'
docker compose exec -T "$DOCKER_COMPOSE_SERVICE" python manage.py shell -c "import json; from apps.reports.models import Report; from apps.reports.services.report_ai_service import ReportAIService; report=Report.objects.get(id=$REPORT_ID); context=report.context_payload or {}; tests={item.get('instrument_code') for item in context.get('validated_tests') or []}; results=[]; 
for key in sorted(ReportAIService.SUPPORTED_SECTIONS):
    config=ReportAIService._generator_config(key)
    has_data=bool(tests & set(config['codes']))
    entry={'key': key, 'kind': config['kind'], 'has_data': has_data}
    if not has_data:
        entry['status']='skipped'
        entry['reason']='no_data'
        results.append(entry)
        continue
    try:
        result=ReportAIService.generate_section(report, key, context)
        entry['status']='ok'
        entry['provider']=result['metadata'].get('provider')
        entry['model']=result['metadata'].get('model')
        entry['preview']=(result['content'] or '')[:140]
    except Exception as exc:
        entry['status']='error'
        entry['error']=str(exc)
    results.append(entry)
print(json.dumps(results, ensure_ascii=False, indent=2))"

printf '\nSuite concluida.\n'
