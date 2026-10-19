# Preparação do laudo — primeira entrega

- [x] Modelos/migration aditivos: registro de preparação e etapas, sem agendar IA.
- [x] Pré-checagem e manifesto de hashes: todas as aplicações, anamnese,
  dados clínicos e relatório alvo; autorização, limites e idempotência.
- [x] API privada por avaliação: consultar e preparar; stale derivado sem
  reescrever histórico. Flag desligada por padrão.
- [x] Painel na visão geral: botão único, pendências, histórico mais recente e
  etapas explicitamente indisponíveis nesta entrega, sem simular worker ativo.
- [x] Testes offline de isolamento, duplicação, fontes, bloqueios e preservação;
  documentar operação/migration.
- [ ] Atualizar grafo: tentativa bloqueada porque `graphify` não está instalado
  ou disponível no PATH desta sessão. Não substituir/remover o grafo existente.

Não implementar inferência, homologação automática, síntese, integração ao DOCX
ou serviço de inicialização nesta entrega. Nenhuma migration no banco compartilhado.
Rollback: desativar flag e novos consumidores, preservar tabelas/registros; sem
reverter dados nem alterar snapshots ou conteúdo de laudos anteriores.

Operação e limites: `apps/reports/REPORT_PREPARATION.md`. Manifesto armazena hashes,
não cópia dos dados brutos. Etapas posteriores continuam indisponíveis e
`ready_for_execution=false`; nenhuma aprovação ou homologação é inferida.

## Verificação — 19/10/2026

- 33 novos testes backend e 326 regressões existentes passaram com SQLite em
  memória e zero tentativas de conexão à rede. Logs em
  `/tmp/opencode/report-preparation-tests.log` e
  `/tmp/opencode/report-preparation-regressions.log`.
  Execução final conjunta: **359/359**, zero conexões, registrada em
  `/tmp/opencode/report-preparation-all-tests.log`.
- 20 testes frontend passaram (8 de preparação e 12 regressões do painel de
  especialistas); TypeScript e lint dos arquivos envolvidos passaram.
- Migration 0009 → 0010 → 0009 → 0010 em banco em memória preservou relatório e
  seções sintéticos; `makemigrations --check --dry-run` sem divergências.
  A primeira tentativa do script temporário migrou só dependências do app, faltando
  migrations atuais de accounts; corrigido somente o setup do banco em memória.
- `git diff --check` passou. Sem deploy, migration compartilhada, serviço instalado,
  inferência real, commit ou push.
- Pendente: concorrência PostgreSQL real e E2E no navegador/ambiente publicado.
