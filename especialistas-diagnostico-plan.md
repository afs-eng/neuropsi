# Diagnóstico seguro de falhas dos especialistas

- [x] Reproduzir rejeições falsas de evidência equivalente e redação de percentil.
- [x] Corrigir esses casos sem aceitar escores divergentes nem afrouxar o contrato.
- [x] Preservar códigos de erro, contagens e término da resposta, sem conteúdo clínico.
- [x] Testar truncamento, validação, rede, privacidade e regressões.
- [x] Executar atualização AST do grafo (sem forçar sobrescrita).

HTTP 200 não identifica a causa da execução #5. Não repetir jobs automaticamente,
não aumentar limites nem habilitar tracing. Sem chamadas reais durante esta tarefa.

291 testes direcionados passaram; Ruff, TypeScript, ESLint do componente,
consistência de migrations e `git diff --check` passaram. Nenhuma migration nova.
O BPA-2 passa a `pydantic-bpa2-3`; nova solicitação cria novo job, preservando #5.
A causa real de #5 não pode ser recuperada: sua versão descartou a resposta e
a exceção sem diagnóstico. O teste ponta a ponta no Ollama real continua pendente.
`graphify update .` atualizou relatório/cache, mas recusou reduzir `graph.json`
de 9030 para 7633 nós; nenhuma sobrescrita foi forçada.
