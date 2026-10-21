# Agentes e skills do projeto

Este é o diretório canônico dos arquivos de apoio aos agentes do Neuropsi.

```text
.agents/
├── agents/          # Definições dos agentes especialistas
├── skills/          # Skills, referências e materiais clínicos
├── scripts/         # Scripts de apoio e validação
├── rules/           # Regras do kit de agentes
├── workflows/       # Procedimentos reutilizáveis
├── .shared/         # Recursos compartilhados de UI/UX
├── ARCHITECTURE.md  # Documentação do kit original
└── mcp_config.json  # Configuração MCP preservada do kit
```

## OpenCode

O OpenCode descobre as skills em `.agents/skills/`. Para solicitar uma skill, mencione seu ID, por exemplo: `Use @security-audit para auditar este projeto`.

As configurações, os plugins e os arquivos de dependências específicos do OpenCode continuam em `.opencode/`. Os arquivos em `agents/`, `rules/` e `workflows/` são materiais de apoio: sua presença aqui não os registra automaticamente como agentes, instruções globais ou comandos do OpenCode.

## Novas skills

Instale a partir da raiz do projeto, sem `--global`, para mantê-las neste repositório. Exemplo:

```bash
npx skills add https://github.com/cloudflare/security-audit-skill \
  --skill security-audit --agent opencode
```

Mantenha `skills-lock.json` na raiz para registrar a origem e a versão das skills instaladas pelo CLI. Não recrie cópias das skills em outros diretórios.

Os materiais clínicos adicionais ficam em `skills/interpretacoes_testes/`, `skills/modelo-teste/` e `skills/skill-systema/`. Eles foram preservados com seus nomes originais; documentos sem o formato de entrada de uma skill devem ser consultados pelo caminho, sem presumir descoberta automática.

## Scripts de apoio

Execute os scripts a partir da raiz do projeto, por exemplo:

```bash
python3 .agents/scripts/session_manager.py info
python3 .agents/scripts/auto_preview.py status
```

O conteúdo foi consolidado sem descartar arquivos exclusivos. Apenas cópias byte a byte idênticas foram removidas.
