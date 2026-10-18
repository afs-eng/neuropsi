# Worker contínuo por conta

- [x] Acrescentar --username, mantendo o filtro opcional por laudo.
- [x] Restringir consulta, claim e recuperação de interrompidos ao solicitante.
- [x] Informar início e espera da fila, sem logar dados clínicos.
- [x] Testar isolamento entre contas/laudos, filtros combinados e regressões; documentar.
- [x] Executar atualização AST do grafo, sem forçar sobrescrita.

Não iniciar serviço em background, configurar inicialização automática ou fazer
chamadas reais. A solicitação continua explícita no sistema, sem informar o ID no
terminal para cada laudo. Sem filtro, a fila global antiga continua disponível
com aviso; não recomendada em computador pessoal conectado a banco multiusuário.

Verificação: 306 testes direcionados passaram (8 novos), Ruff, consistência de
migrations e `git diff --check`. Sem migration nova, deploy, inferência real ou
serviço instalado. O uso por username depende da atualização do código local;
não altera o frontend nem gera especialistas automaticamente ao abrir o laudo.
Graphify atualizou relatório/cache, mas recusou reduzir `graph.json` de 9030 para
7645 nós. Não foi forçada a sobrescrita.
