# BPA-2: referências inexistentes na saída local

Falhas #10/#11: `evidence_not_found`. A saída rejeitada não foi persistida;
não é possível afirmar qual ID foi usado nessas execuções.

Fragilidade reproduzível: schema nativo permite qualquer string e a correção
informa apenas que a evidência não existe, sem indicar o conjunto permitido.

- [x] Restringir schema nativo BPA-2 aos IDs da aplicação, sem cache global.
- [x] Orientar cópia exata de facts, não caminhos de reading_guide ou abreviações.
- [x] Corrigir mensagem de retry, sem persistir saída rejeitada nem afrouxar validação.
- [x] Versionar para solicitação explícita nova; preservar sucessos compatíveis e histórico.
- [x] Testar transporte sintético, enum, retry, bloqueio e compatibilidade; documentar e atualizar grafo.

Sem inferência real, mudanças de credenciais, novos limites, repetição automática,
commit ou deploy. O comportamento real do modelo ainda exige homologação.

Verificado: 313 testes direcionados (7 novos), Ruff, diff-check e consistência
de migrations; nenhuma migration nova. Transporte mockado confirma o enum no
schema enviado, recuperação no segundo pedido e bloqueio de IDs inválidos quando
o provedor ignora o schema. Mesmos limites de tokens, tempo e requisições.

Graphify executado: relatório/cache atualizados; recusou reduzir graph.json de
9030 para 7666 nós. Não foi forçada sobrescrita. Publicar backend e atualizar o
worker antes da nova solicitação sintética `pydantic-bpa2-4-ollama-4k`.
