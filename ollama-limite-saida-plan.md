# Aumentar somente a saída dos especialistas Ollama

- [x] Aplicar 4.000 tokens/resposta e 8.000 acumulados em até duas requisições locais.
- [x] Manter limites externos, tempo, validações e bloqueio de truncamento.
- [x] Distinguir a política nova para permitir nova solicitação sem repetir/apagar jobs antigos.
- [x] Testar separação local/externa, limites acumulados, preservação e regressões.
- [x] Executar atualização AST do grafo, sem forçar sobrescrita.

Autorizado pelo usuário. Sem alterar credenciais, contexto do servidor Ollama ou
iniciar inferência real. Rascunhos válidos da mesma versão clínica permanecem revisáveis.

Verificado: 298 testes direcionados (7 novos de orçamento), Ruff dos serviços/testes,
consistência de migrations e `git diff --check`. Ruff de base.py passou ignorando
somente E402 preexistente. Sem migration, deploy ou inferência real. A janela de
contexto do Ollama não foi alterada; truncamento ainda deve ser verificado em
teste sintético real. A versão Ollama recebe `-ollama-4k`; OpenAI não muda.
Graphify atualizou relatório/cache, mas recusou reduzir o grafo de 9030 para 7633
nós. O grafo existente não foi sobrescrito à força.
