# Especialistas com PydanticAI

- [x] Fixar dependência slim/OpenAI e definir contratos com evidências verificáveis.
- [x] Preparar entradas minimizadas, sem cadastro/anamnese e separadas por aplicação.
- [x] Persistir fila e resultados sem sobrescrever laudos ou interpretações existentes.
- [x] Disponibilizar API privada para solicitar e acompanhar execuções.
- [x] Implementar worker sequencial, limites e tratamento de interrupções.
- [x] Verificar: 155 testes passando sem chamadas externas, incluindo regressão DOCX.

Ativação explícita por ambiente e instrumento. Não adicionar serviços pagos ao
Render automaticamente. Resultados são rascunhos para revisão, não laudos
aprovados. Integração clínica, interface e aplicação ao DOCX ficam para etapa
posterior, após validação dos especialistas pela profissional.

Verificação: dependências compatíveis, migração `0006` consistente, diff sem erros
de whitespace e arquivos novos sem alertas Ruff. Lint global mantém pendências
anteriores; mypy não está instalado. Graphify executado, mas não substituiu o
graph.json maior existente. Testes de fila executados no SQLite do ambiente de
teste; worker em produção e concorrência real em PostgreSQL ainda não exercitados.
Não houve deploy nem migração do banco real.

Operação e limitações: `apps/reports/SPECIALIST_AGENTS.md`.
