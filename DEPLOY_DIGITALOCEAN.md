# Deploy no DigitalOcean

## Arquitetura

- Droplet Ubuntu rodando Docker Compose
- PostgreSQL gerenciado pelo DigitalOcean
- Caddy fazendo HTTPS automatico e proxy reverso
- Frontend Next.js e backend Django no mesmo dominio

## Arquivos usados

- `docker-compose.digitalocean.yml`
- `.env.digitalocean`
- `infra/caddy/Caddyfile`

## 1. Preparar infraestrutura no DigitalOcean

1. Crie um Droplet Ubuntu 24.04 com pelo menos 2 vCPU e 4 GB RAM.
2. Crie um banco `Managed PostgreSQL`.
3. Aponte o DNS do dominio para o IP publico do Droplet com um registro `A`.
4. Libere no firewall as portas `22`, `80` e `443`.

## 2. Preparar o servidor

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Abra nova sessao SSH depois do `usermod`.

## 3. Configurar o projeto

```bash
git clone <seu-repositorio> neuropsi
cd neuropsi
cp .env.example.digitalocean .env.digitalocean
```

Edite `.env.digitalocean` e preencha pelo menos:

- `APP_DOMAIN`
- `ACME_EMAIL`
- `SECRET_KEY`
- `DATABASE_URL`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `CORS_ALLOWED_ORIGINS`
- `FRONTEND_BASE_URL`
- `BACKEND_PUBLIC_URL`
- credenciais de IA/e-mail que usar em producao

## 4. Subir a stack

```bash
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml up -d --build
```

## 5. Inicializacao obrigatoria

Crie o superusuario e carregue os instrumentos:

```bash
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml exec backend python manage.py createsuperuser
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml exec backend python manage.py create_instruments
```

## 6. Validacoes

Verifique:

```bash
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml logs -f caddy
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml logs -f backend
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml logs -f frontend
```

URLs esperadas:

- `https://seu-dominio/healthz/`
- `https://seu-dominio/admin`
- `https://seu-dominio/login`
- `https://seu-dominio/api/docs`

## 7. Operacao diaria

Deploy de atualizacao:

```bash
git pull
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml up -d --build
```

Reiniciar apenas backend:

```bash
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml up -d --build backend
```

Abrir shell do Django:

```bash
docker compose --env-file .env.digitalocean -f docker-compose.digitalocean.yml exec backend python manage.py shell
```

## 8. Recomendacoes de producao

- Ative backups automaticos do banco gerenciado.
- Use um dominio dedicado para o sistema.
- Guarde `.env.digitalocean` fora do Git.
- Monitore logs do `backend` e do `caddy` nas primeiras horas apos deploy.
- Se quiser cache compartilhado, adicione `Managed Redis` e configure `REDIS_URL`.
