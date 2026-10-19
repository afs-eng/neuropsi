# BPA-2 — modelo de redação aprovado com percentis

Escopo autorizado: adaptar o estilo fornecido pela profissional, mantendo os
percentis por componente. Não executar as demais fases do plano clínico.

- [x] Atualizar instruções: introdução com perfil, definição/resultado/interpretação
  por modalidade e síntese em três parágrafos, sem repetir números.
- [x] Validar os três parágrafos apenas nas novas gerações; preservar leitura e
  revisão de rascunhos antigos sem aplicar retroativamente formato novo.
- [x] Preservar parágrafos na interface, sem HTML fornecido pelo modelo.
- [x] Testar perfis diferentes, percentis obrigatórios, correção limitada, falha
  segura, compatibilidade e renderização; documentar e atualizar grafo.

Arquivos: bpa2_specialist.py, specialist_agent_service.py, specialist_errors.py,
testes BPA-2/diagnósticos, componente de texto do painel e documentação.
Manter contrato de seis findings e limite de 2.000 caracteres por statement;
sem migration, mudança de cálculos, budgets, modelos ou integração ao laudo.

Riscos: resposta maior pode exceder limite; evitar exemplo completo redundante
no prompt e não ampliar orçamento. Estilo não equivale a validação semântica
completa. A exigência de três parágrafos é editorial, não homologação clínica.
Rollback: retornar instruções/geração ao estilo anterior, sem reescrever jobs,
revisões ou artefatos; não fazer retry de falhas nem remover histórico.

Verificação: 326 testes backend (7 novos) com SQLite em memória, rede bloqueada e
zero tentativas de conexão; 12 frontend (2 novos), TypeScript, Ruff, lint dos
componentes e diff-check passaram. Testes estáticos/transportes sintéticos não
comprovam a qualidade da redação no modelo real. Não houve inferência, deploy,
commit, migração ou instalação de serviço.

Versão nova: `pydantic-bpa2-6-ollama-4k`. Atualizar backend/frontend e código do
worker, reiniciá-lo e solicitar explicitamente um caso sintético. Sucessos
anteriores permanecem revisáveis; nenhuma execução falha é reativada.
Graphify executado sem force: relatório/cache atualizados; recusou reduzir
graph.json de 9030 para 7685 nós. Demais entregas do plano clínico não executadas.
