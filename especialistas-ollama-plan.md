# Especialistas com Ollama no Windows

- [x] Separar configuração dos especialistas do provedor legado; persistir provedor na fila.
- [x] Usar compatibilidade OpenAI do Ollama com JSON estruturado e raciocínio desativado.
- [x] Testar transporte offline, isolamento de provedores e ausência de fallback.
- [x] Documentar configuração WSL/Render e validar regressões e migration.
- [x] Executar atualização do grafo (AST); sem forçar sobrescrita do grafo existente.

Sem alterar credenciais, ativar o piloto ou enviar dados clínicos ao modelo.

257 testes direcionados passaram, além de TypeScript, ESLint do componente,
consistência de migrations e Ruff do código do piloto. `base.py` tem E402 anterior
na linha 74; a checagem desse arquivo passou ignorando somente essa regra.
Não houve deploy, ativação, chamada real ou início do worker. A migration `0009`
foi gerada, não aplicada ao banco de uso. Falta teste sintético de ponta a ponta
no Ollama real, validação de contexto e homologação clínica.
`graphify update .` atualizou relatório/cache, mas recusou reduzir `graph.json`
de 9030 para 7568 nós. Não foi forçada a sobrescrita.
