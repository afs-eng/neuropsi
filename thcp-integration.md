# Integração THCP

Implementar o Teste de Habilidades e Conhecimento Pré-Alfabetização usando exclusivamente as normas de `aux/CORRECAO.xlsm`.

- [x] Extrair normas de 4–7 anos e amostra geral, preservando intervalos de T-score e a origem dos dados.
- [x] Criar `apps/tests/thcp/` com validação, cálculo, classificação, interpretação e payload de laudo; testar limites e fórmulas.
- [x] Registrar instrumento, faixa etária e endpoints de aplicação/resultado com edição e permissões existentes.
- [x] Integrar formulário, resultados, PDF e inclusão do THCP no laudo.
- [x] Executar testes backend, verificação frontend e `graphify update .`; registrar limitações verificadas.

Escores censurados (ex.: `< 27`) não serão convertidos em valores pontuais ou percentis fictícios.

## Validação

- 205 testes passando (25 THCP, mais regressões de testes existentes e laudos).
- Build Next.js, TypeScript e ESLint das novas telas passando; Ruff sem novos erros e Bandit sem achados no módulo.
- PDFs reais gerados para resultados pontuais e censurados; fluxo de navegador testado com APIs fictícias, preservando dados existentes.
- `npm audit`: 11 vulnerabilidades preexistentes (10 altas, 1 crítica), sem atualização de dependências nesta tarefa.
- Graphify executado, mas recusou sobrescrever `graph.json`: grafo extraído com 7.144 nós contra 9.030 existentes. Não foi forçada substituição nem perda de dados do grafo.
- Nenhuma migração foi aplicada ao banco existente; cadastro THCP será criado pela migração 0005 no deploy.
