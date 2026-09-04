# ============================================================
# NeuroAvalia — Docker Compose Instructions
# ============================================================

## Desenvolvimento Local

```bash
# 1. Copie o arquivo de exemplo
# ja deixei um .env de desenvolvimento pronto no projeto
# se quiser recriar do zero, use:
# cp .env.example .env

# 2. Suba todos os servicos
docker compose up --build

# 3. Baixe o modelo da Ollama (primeira vez)
docker compose exec ollama ollama pull qwen3.5:27b

# 4. Crie superusuario
docker compose exec backend uv run python manage.py createsuperuser

# 5. Crie instrumentos de teste
docker compose exec backend uv run python manage.py create_instruments
```

Apos iniciar:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api
- **Django Admin:** http://localhost:8000/admin
- **API Docs (Swagger):** http://localhost:8000/api/docs
- **Ollama API:** http://localhost:11434

## Producao Self-Hosted (VPS)

```bash
# 1. Copie o arquivo de exemplo
cp .env.example.prod .env.prod

# 2. Edite as variaveis de producao
nano .env.prod

# 3. Suba todos os servicos
docker compose -f docker-compose.prod.yml up -d --build

# 4. Rode as migracoes
docker compose -f docker-compose.prod.yml exec backend uv run python manage.py migrate

# 5. Crie superusuario
docker compose -f docker-compose.prod.yml exec backend uv run python manage.py createsuperuser
```

Apos iniciar em producao:
- **Frontend:** https://seu-dominio.com
- **Backend API:** https://seu-dominio.com/api
- **Django Admin:** https://seu-dominio.com/admin

## DigitalOcean (Droplet + Managed PostgreSQL)

```bash
# 1. Copie o arquivo de exemplo
cp .env.example.digitalocean .env.digitalocean

# 2. Edite as variaveis de producao
nano .env.digitalocean

# 3. Suba a stack do DigitalOcean
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml up -d --build

# 4. Crie superusuario
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml exec backend uv run python manage.py createsuperuser

# 5. Carregue os instrumentos
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml exec backend uv run python manage.py create_instruments
```

Apos iniciar no DigitalOcean:
- **Sistema:** `https://seu-dominio.com`
- **Backend API:** `https://seu-dominio.com/api`
- **Django Admin:** `https://seu-dominio.com/admin`
- **Healthcheck:** `https://seu-dominio.com/healthz/`

Guia detalhado: `DEPLOY_DIGITALOCEAN.md`

## Comandos Uteis

```bash
# Ver logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f ollama

# Parar servicos
docker compose down

# Parar e remover volumes (cuidado: apaga dados!)
docker compose down -v

# Reconstruir apenas um servico
docker compose up -d --build backend

# Executar comando no container
docker compose exec backend uv run python manage.py shell
docker compose exec backend uv run python manage.py test
```
