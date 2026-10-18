# Acompanhamento dos rascunhos no painel

- [x] Mostrar fila, geração/validação, conclusão e falha fora dos detalhes recolhidos.
- [x] Exibir tempo decorrido e barra indeterminada, sem inventar percentual/previsão.
- [x] Atualizar a consulta automaticamente enquanto houver pendências, sem chamadas de IA.
- [x] Tratar falhas de conexão, consulta lenta e desmontagem sem apagar notas humanas.
- [x] Testar estados, duração, polling, TypeScript/lint e regressões; atualizar grafo.

Usar timestamps/status existentes. Sem prometer monitoramento de worker (não há
heartbeat), aumentar limites, iniciar jobs automaticamente ou alterar aprovação.

Validação: 10 testes frontend (lógica e renderização estática), 72 regressões
backend, TypeScript sem erros, lint dos arquivos TS/TSX alterados e diff-check.
Não foi realizado teste em navegador, inferência real, commit ou deploy.
Graphify executado sem forçar redução: relatório/cache atualizados; sobrescrita
de graph.json recusada (9030 nós existentes, 7657 na extração atual).
