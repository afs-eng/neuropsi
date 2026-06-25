#!/usr/bin/env bash
# ============================================================
# NeuroAvalia — Backend Entrypoint (Docker)
# Aguarda o DB, roda migrations e inicia o servidor.
# ============================================================
set -e

echo "🔄 [entrypoint] Iniciando verificacao do ambiente..."

# Espera o banco ficar disponivel
retries=30
while ! python manage.py check --database default > /dev/null 2>&1; do
    echo "⏳ Aguardando conexao com o banco de dados..."
    sleep 2
    retries=$((retries - 1))
    if [ $retries -eq 0 ]; then
        echo "❌ Erro: Timeout ao aguardar banco de dados."
        exit 1
    fi
done

echo "✅ Banco de dados disponivel."

# Aplica migrations
echo "🛠️ Rodando migrations..."
python manage.py migrate --noinput

# Collectstatic apenas em producao
if [ "$DJANGO_ENV" = "production" ]; then
    echo "📦 collectstatic..."
    python manage.py collectstatic --noinput
fi

echo "🚀 Iniciando servidor..."
exec "$@"
