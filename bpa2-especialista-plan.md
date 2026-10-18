# BPA-2 — redação por componentes e síntese

- [x] Explicitar significado dos campos e instruções de redação, com exemplos sintéticos contrastantes.
- [x] Exigir introdução, AC, AD, AA, AG e análise clínica com evidências; validar erros conhecidos.
- [x] Versionar apenas o especialista BPA-2, preservando execuções antigas e permitindo nova solicitação.
- [x] Exibir títulos no painel e testar contratos, fila, revisão e regressões offline.

Sem fine-tuning, chamadas reais, alteração de normas/cálculos, credenciais ou integração automática no DOCX.

Verificação: 277 testes direcionados passaram (16 novos para BPA-2), Ruff,
TypeScript, ESLint do componente, consistência de migrations e `git diff --check`.
Sem migration nova. Teste do transporte Ollama usa HTTP simulado, não inferência
real; qualidade da redação com o modelo local e renderização no navegador ainda
precisam de validação. As verificações semânticas cobrem erros conhecidos, não
toda a correção clínica de um texto. O SQLite já estava alterado ao iniciar a tarefa.
`graphify update .` foi executado; relatório/cache atualizados, mas a ferramenta
recusou reduzir `graph.json` de 9030 para 7604 nós. Não foi forçada a sobrescrita.
