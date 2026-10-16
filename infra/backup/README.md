# Backup Render e recuperação no WSL

O backend de produção continua no Render. Não se altera a Vercel nem se faz
replicação automática: a recuperação é manual, usando a última cópia concluída.

## Ativar

Pré-requisitos: Python 3, clientes PostgreSQL 18 (ou versão compatível com o
servidor), systemd de usuário ativo. Docker Desktop com integração WSL para
executar o banco de recuperação.

Neste ambiente, o cliente PostgreSQL 18 está disponível, mas a integração
Docker/WSL ainda não está ativa. No Docker Desktop, abra **Settings → Resources
→ WSL Integration**, habilite esta distribuição e aplique. Confirme com
`docker info` antes de tentar subir o banco de recuperação. O backup remoto
com `pg_dump` não depende do Docker.

Na raiz do projeto:

```bash
python3 infra/backup/backup.py setup
bash infra/backup/install-timer.sh
```

O setup pede a **External Database URL** sem mostrá-la na tela. Use uma senha
nova, pois a anterior foi exposta. Permita a conexão do seu IP nas regras de
acesso externo do banco Render. A URL interna não funciona no computador.

A credencial fica em `~/.config/neuropsi/backup.json` (permissão 600), fora do
Git. A senha aleatória do banco local fica em `.env.recovery`, ignorado pelo Git.
O instalador só ativa o timer depois de um primeiro backup bem-sucedido.

## Conferir

```bash
systemctl --user list-timers neuropsi-backup.timer
journalctl --user -u neuropsi-backup.service -n 30 --no-pager
ls -lh ~/.local/share/neuropsi/backups/
```

Os dumps são publicados após `pg_dump` e leitura do catálogo com `pg_restore`.
Isso não substitui um teste completo de restauração. Arquivos incompletos são
removidos. Não há exclusão automática de cópias: monitore espaço em disco.

**WSL/computador desligado não faz backup.** `Persistent=true` tenta executar
uma cópia ao voltar, mas não recupera alterações de um banco já apagado. Confira
regularmente a data da última cópia e os logs. O timer de usuário depende da
sessão de usuário ativa; não é garantia de execução com Windows ligado e WSL parado.

## Restaurar sem tocar na produção

```bash
docker compose --env-file .env.recovery -f infra/backup/compose.yaml up -d --wait
python3 infra/backup/backup.py restore /caminho/para/neuropsi-DATA.dump
```

O destino é um banco novo, separado, acessível somente pelo loopback na porta
55432. A ferramenta recusa destino remoto e exige confirmação. Não apaga
tabelas: se o banco já tiver dados, use outro banco vazio. A restauração é
transacional. Não use `docker compose down -v`: isso apaga o volume local.

Para executar o backend no WSL, em um terminal Python com as dependências do
projeto, carregue a URL **local** da configuração sem imprimi-la:

```bash
export DATABASE_URL="$(python3 -c 'import json,pathlib; print(json.loads((pathlib.Path.home()/".config/neuropsi/backup.json").read_text())["local_url"])')"
export DJANGO_ENV=local DATABASE_SSL_REQUIRE=False DEBUG=True
export FRONTEND_BASE_URL=http://localhost:3000
export BACKEND_PUBLIC_URL=http://localhost:8000
uv run python manage.py migrate
uv run python manage.py runserver 127.0.0.1:8000
```

Em outro terminal:

```bash
cd neuro-frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 INTERNAL_API_BASE_URL=http://localhost:8000 NEXT_PUBLIC_APP_URL=http://localhost:3000 npm run dev
```

Abra `http://localhost:3000` e valide login e registros conhecidos. O frontend
da Vercel **não muda automaticamente** para este banco. Integrações de IA e
outros serviços externos podem exigir configuração adicional/internet.
Alterações feitas localmente não são reenviadas automaticamente ao Render.

## Anexos e dados clínicos

**Este procedimento cobre somente o PostgreSQL.** O projeto grava arquivos em
`MEDIA_ROOT` (normalmente `media/`); dumps não incluem esses arquivos. É preciso
copiar os anexos da produção separadamente ou configurar armazenamento externo
durável. Uma cópia da pasta `media/` deste computador não comprova que os anexos
do Render foram salvos. Não considere a recuperação completa sem resolver isso.

Backups contêm dados clínicos e hashes de senhas. São privados, mas **não são
criptografados por este script**. Use disco criptografado, controle de acesso
e uma segunda cópia criptografada fora deste computador. Não os envie ao Git,
chats ou pastas públicas. Banco local não substitui backup independente.

Para suspender: `systemctl --user disable --now neuropsi-backup.timer`.
