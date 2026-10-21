# Organização dos arquivos de agentes

## Objetivo
Centralizar agentes, skills e arquivos de apoio em `.agents/`, sem perder conteúdo nem alterar a aplicação.

## Tarefas
- [x] Mesclar os diretórios de agentes e skills, removendo somente cópias idênticas e preservando os arquivos exclusivos.
- [x] Atualizar caminhos em scripts e documentos e registrar a estrutura canônica em `AGENTS.md`.
- [x] Validar a integridade dos arquivos migrados, a descoberta das skills e os scripts; tentar atualizar o grafo.

## Concluído quando
- `.agent/` e a antiga cópia de skills do OpenCode não existirem mais.
- As skills estiverem em `.agents/skills/`, incluindo `security-audit` e os materiais clínicos adicionais.
- `.opencode/` preservar suas configurações e plugins.

## Verificação
- 478 arquivos únicos preservados; 268 cópias idênticas removidas, com comparação de hashes antes da mesclagem.
- 38 skills reconhecidas pelo CLI para OpenCode, incluindo `security-audit` e `lint-and-validate`.
- Corrigida a descrição YAML da skill de lint, que continha dois-pontos sem aspas.
- Sintaxe dos 23 arquivos Python validada; os quatro scripts de apoio passaram pelo teste de `--help`.
- 65 testes dos validadores de `security-audit` passaram.
- 21 referências de scripts existentes verificadas; dois scripts opcionais já estavam ausentes na estrutura original.
- `git diff --check` passou. Nenhum código da aplicação foi alterado.
- Graphify 0.5.0 disponibilizado no PATH do usuário via `uv tool install --python 3.12 graphifyy==0.5.0`.
- `graphify update .` executado: o relatório foi regenerado, mas a proteção da ferramenta preservou o `graph.json` original de 9.030 nós diante de um resultado menor (7.828 nós), sem forçar sobrescrita. Consulta local ao grafo validada.
