#!/usr/bin/env python3
"""Backups locais do Render; nunca restaura em servidores remotos."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import getpass
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
from urllib.parse import parse_qs, unquote, urlparse

CONFIG = Path.home() / '.config/neuropsi/backup.json'


class ConfigError(ValueError):
    """Mensagem controlada, sem conteúdo copiado da credencial."""


def connection(url):
    if not url:
        raise ConfigError('Nenhuma URL recebida. Cole a External Database URL e pressione Enter.')
    try:
        parsed = urlparse(url)
        parsed.port
    except ValueError:
        raise ConfigError('URL malformada: confira o endereço completo e a porta.') from None
    if parsed.scheme not in ('postgres', 'postgresql') or not parsed.hostname:
        raise ConfigError(
            'Cole a URL completa iniciada por postgresql://, sem aspas, '
            'sem DATABASE_URL= e sem o comando psql.'
        )
    if not parsed.path.strip('/') or not parsed.username or not parsed.password:
        raise ConfigError('URL incompleta: copie o campo External Database URL inteiro, incluindo usuário, senha e banco.')
    return parsed


@contextmanager
def pg_environment(url):
    parsed = connection(url)
    env = {k: v for k, v in os.environ.items() if not k.startswith('PG')}
    env.update(
        PGHOST=parsed.hostname,
        PGPORT=str(parsed.port or 5432),
        PGUSER=unquote(parsed.username),
        PGDATABASE=unquote(parsed.path.lstrip('/')),
        PGCONNECT_TIMEOUT='20',
        PGSSLMODE=parse_qs(parsed.query).get('sslmode', ['require'])[0],
    )
    # Senhas não aparecem nos argumentos dos processos ou no journal.
    with tempfile.NamedTemporaryFile(mode='w', prefix='neuropsi-pgpass-') as password:
        escaped = unquote(parsed.password).replace('\\', '\\\\').replace(':', '\\:')
        password.write(f'*:*:*:*:{escaped}\n')
        password.flush()
        env['PGPASSFILE'] = password.name
        yield env


def run_pg(arguments, url):
    with pg_environment(url) as env:
        result = subprocess.run(arguments, env=env, capture_output=True, text=True)
    if result.returncode:
        # Não imprimir stderr de ferramentas externas: pode conter credenciais.
        raise RuntimeError(
            f'{arguments[0]} falhou (código {result.returncode}). '
            'Confira rede, credenciais, permissões e compatibilidade de versão PostgreSQL.'
        )


def private_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as file:
        file.write(content)


def setup():
    if CONFIG.exists():
        raise ConfigError(f'Configuração já existe: {CONFIG}. Edite-a localmente.')
    url = getpass.getpass('External Database URL atualizada do Render (oculta): ').strip()
    parsed = connection(url)
    if not parsed.hostname.endswith('.render.com'):
        raise ConfigError(
            'O endereço não é o externo do Render. Copie Connections → External Database URL, '
            'não Hostname nem Internal Database URL.'
        )
    password = secrets.token_urlsafe(32)
    root = Path(__file__).resolve().parents[2]
    env_path = root / '.env.recovery'
    if env_path.exists():
        raise ConfigError('.env.recovery já existe; não será sobrescrito. Confira esse arquivo antes de repetir o setup.')
    config = {
        'source_url': url,
        'backup_dir': str(Path.home() / '.local/share/neuropsi/backups'),
        'local_url': f'postgresql://neuro_recovery:{password}@127.0.0.1:55432/neuro_recovery?sslmode=disable',
    }
    private_write(env_path, f'RECOVERY_DB_PASSWORD={password}\n')
    private_write(CONFIG, json.dumps(config, indent=2) + '\n')
    print(f'Configuração privada criada: {CONFIG}')


def backup(config):
    directory = Path(config['backup_dir']).expanduser()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)
    with (directory / '.backup.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Já existe um backup em andamento.') from None
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        target = directory / f'neuropsi-{stamp}.dump'
        temporary = target.with_suffix('.partial')
        try:
            run_pg(['pg_dump', '--no-password', '--format=custom', '--no-owner',
                    '--no-acl', '--file', str(temporary)], config['source_url'])
            run_pg(['pg_restore', '--list', str(temporary)], config['source_url'])
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    print(f'Backup concluído: {target}')


def restore(config, archive):
    url = config['local_url']
    parsed = connection(url)
    if parsed.hostname not in ('127.0.0.1', 'localhost', '::1'):
        raise ConfigError('Restauração permitida somente no banco local.')
    archive = Path(archive).resolve(strict=True)
    print('O destino deve ser um banco local vazio. Nenhum dado existente será apagado.')
    if input('Digite RESTAURAR LOCAL para continuar: ') != 'RESTAURAR LOCAL':
        raise ConfigError('Restauração cancelada.')
    run_pg(['pg_restore', '--no-password', '--exit-on-error', '--single-transaction',
            '--no-owner', '--no-acl', '--dbname', unquote(parsed.path.lstrip('/')),
            str(archive)], url)
    print('Restauração local concluída. Execute as migrações antes de iniciar o sistema.')


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('setup', 'backup', 'restore'))
    parser.add_argument('archive', nargs='?')
    args = parser.parse_args()
    try:
        if args.command == 'setup':
            setup()
            return
        if CONFIG.stat().st_mode & 0o077:
            raise ConfigError(f'Proteja a configuração com chmod 600 {CONFIG}')
        config = json.loads(CONFIG.read_text())
        if args.command == 'backup':
            backup(config)
        elif args.archive:
            restore(config, args.archive)
        else:
            parser.error('restore exige o caminho do arquivo .dump')
    except ConfigError as error:
        parser.exit(1, f'{error}\n')
    except (OSError, ValueError, RuntimeError) as error:
        # Erros de parsing podem conter a URL; não mostrar seu conteúdo.
        if isinstance(error, ValueError):
            parser.exit(1, 'Configuração inválida ou operação cancelada. Confira os dados locais.\n')
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
