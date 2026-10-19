# Especialistas de IA — BFP e E-TDAH-AD

Escopo aprovado: adicionar os dois especialistas ausentes usando
`aux/neuro_skills/{bfp,etdah_ad}/SKILL.md`, sem modificar os nove atuais.
Narrativa sem percentis; validação somente com dados sintéticos e sem inferência.

- [x] Mapear os payloads reais, isolando resultados de respostas/itens e textos antigos.
- [x] Implementar instruções versionadas, guia de evidências e contratos específicos.
- [x] Validar classificações, lacunas, referências e redação sem percentis; bloquear fontes divergentes.
- [x] Integrar à fila, revisão e painel existentes, mantendo ativação explícita por allowlist.
- [x] Testar entradas, geração simulada, transporte Ollama simulado, privacidade, revisão e preservação do legado.
- [x] Executar regressões, Ruff, checagens disponíveis e diff-check.
- [ ] Atualizar grafo: `graphify update .` executado, mas o CLI não está disponível.

Sem deploy, migration, chamada real ao Ollama ou edição dos arquivos fornecidos em
`aux`. Especialistas experimentais: revisão profissional não equivale a homologação.

## Verificação

- 32 testes novos; suíte completa de laudos: **341 testes aprovados**, SQLite em
  memória, sem carregar dotenv e com sockets de rede bloqueados.
- Testados também os payloads dos módulos determinísticos reais com respostas
  inteiramente sintéticas; BFP com cinco fatores/17 facetas e E-TDAH-AD com cinco
  fatores (agregado opcional, nunca criado pela IA).
- **Zero tentativas de rede** no runner. FunctionModel e MockTransport exercitam
  a geração estruturada, schema nativo, retry limitado e diagnósticos seguros,
  sem chamar o Ollama real. Log: `/tmp/opencode/self-report-all-reports.log`.
- Frontend: 30 testes aprovados, TypeScript e lint do painel sem erros.
- Ruff dos arquivos Python alterados: aprovado. Bandit dos serviços alterados:
  nenhum achado. MyPy do módulo novo, com imports externos ignorados: aprovado.
  Ferramentas Bandit/MyPy executadas via `uv tool run`, sem mudar dependências.
- `git diff --check`: aprovado. Sem alteração de modelos/migrations ou allowlist.
- O grafo existente foi preservado. `aux/neuro_skills/` e `aux/wisc_iv/` continuam
  como arquivos fornecidos pelo usuário, sem modificações nesta entrega.

Operação e limitações clínicas em `apps/reports/SPECIALIST_AGENTS.md`. Para usar
após publicação e revisão de configuração, incluir `bfp` e `etdah_ad` na allowlist
do backend e do worker. Ainda pendentes: teste autorizado com o modelo real e
homologação clínica; nenhum rascunho é integrado automaticamente ao laudo/DOCX.
