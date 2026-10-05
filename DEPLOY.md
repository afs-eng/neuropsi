# Deploy de Teste - NeuroAvalia

## Visao Geral

- Frontend: Vercel
- Backend: Render Web Service
- Banco: PostgreSQL no Render

Manter os serviços existentes: frontend `https://neuropsi-eta.vercel.app` e backend
`https://neuropsi-ddag.onrender.com`. Não criar novos projetos/domínios para este deploy.

---

## Backend no Render

### Criar servico

- Tipo: `Web Service`
- Runtime: `Python`
- Root directory: raiz do repositorio

### Build command

```bash
bash infra/render/build.sh
```

O build instala também o Chromium usado pelos PDFs. No plano gratuito, deixar
**Pre-deploy Command vazio**: as migrações são executadas no script de inicialização.

### Start command

```bash
bash infra/render/start.sh
```

O script aplica `migrate --noinput` antes de iniciar o Gunicorn na porta `$PORT`.
Isso inclui a migração `tests.0005_add_thcp_instrument`, cadastrando o THCP
automaticamente. Falhas na migração impedem a abertura do servidor.
Não há download de Chromium a cada reinício.

### Health check

- Path: `/healthz/`

### Variaveis de ambiente do backend

- `DJANGO_ENV=production`
- `DEBUG=False`
- `SECRET_KEY=<gerada>`
- `DATABASE_URL=<connection string do PostgreSQL do Render>`
- `DATABASE_SSL_REQUIRE=True`
- `ALLOWED_HOSTS=neuropsi-ddag.onrender.com`
- `CSRF_TRUSTED_ORIGINS=https://neuropsi-ddag.onrender.com,https://neuropsi-eta.vercel.app`
- `CORS_ALLOWED_ORIGINS=https://neuropsi-eta.vercel.app`
- `FRONTEND_BASE_URL=https://neuropsi-eta.vercel.app`
- `BACKEND_PUBLIC_URL=https://neuropsi-ddag.onrender.com`
- `PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/.playwright-browsers`
- `ALLOW_VERCEL_PREVIEWS=True`
- `AI_PROVIDER=openai`
- `OPENAI_API_KEY=<chave-openrouter>`
- `OPENAI_BASE_URL=https://openrouter.ai/api/v1`
- `OPENAI_REFERER=https://<dominio-vercel>`
- `OPENAI_TITLE=NeuroAvalia`
- `OPENAI_MODEL_TEXT=google/gemma-4-31b-it:free`
- `OPENAI_MODEL_REASONING=google/gemma-4-31b-it:free`
- `OPENAI_FALLBACK_MODELS=google/gemma-3-27b-it:free,meta-llama/llama-3.3-70b-instruct:free,openai/gpt-oss-20b:free`
- `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`
- `DJANGO_LOG_LEVEL=INFO`

### Banco PostgreSQL

- Crie um `PostgreSQL` no Render
- Copie a connection string para `DATABASE_URL`

---

## Frontend no Vercel

### Projeto

- Framework: `Next.js`
- Root directory: `neuro-frontend`

### Variaveis de ambiente do frontend

- `NEXT_PUBLIC_API_BASE_URL=https://neuropsi-ddag.onrender.com`
- `INTERNAL_API_BASE_URL=https://neuropsi-ddag.onrender.com`
- `NEXT_PUBLIC_APP_URL=https://neuropsi-eta.vercel.app`

Essas URLs públicas estão em `neuro-frontend/vercel.json` para build e runtime.
Não incluir senhas, tokens ou chaves nesse arquivo.

### Aplicar ao projeto existente

1. Subir o código na branch vinculada aos serviços atuais.
2. Se o Render não estiver gerenciado por Blueprint, ajustar manualmente os comandos
   acima em **Settings** e conferir as variáveis em **Environment**. Um push isolado
   não sincroniza `render.yaml` em serviços criados manualmente.
3. Manter o banco e `SECRET_KEY` atuais. Não recriar banco nem trocar credenciais.
4. Na Vercel, confirmar Root Directory `neuro-frontend` e branch de produção.
5. Conferir nos logs do Render a migração THCP e verificar `/healthz/`, login,
   inclusão do THCP na avaliação, correção e exportação PDF/DOCX.

### Observacoes

- O frontend consome a API publica do Render
- As variaveis do frontend devem apontar para a raiz do backend, sem adicionar `/api` no final
- As rotas publicas de anamnese por token usam a URL do frontend em `FRONTEND_BASE_URL`
- O OpenRouter fica configurado apenas no backend do Render; nenhuma chave de IA deve ir para o Vercel

---

## Checklist Final

- Backend responde em `/healthz/`
- Frontend consegue autenticar e listar dados
- Migrations aplicadas no PostgreSQL
- Arquivos estaticos coletados com sucesso
- Upload de documentos funcionando
- Anamnese publica abrindo por token
- Email/WhatsApp gerando links com URL publica correta
- CORS e CSRF aceitando o frontend hospedado
