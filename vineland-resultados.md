# Finalização e resultados do Vineland

Objetivo: oferecer salvamento parcial e finalização com resultados no padrão visual do WISC4, sem reutilizar normas de outro formulário.

- [x] Validar no servidor COM, AVD e SOC completos; seções opcionais vazias ficam não aplicadas, se iniciadas exigem todas as respostas. Testar zero, binários e preservação de rascunhos.
- [x] Gerar resumo descritivo por seção e itens críticos individuais, sem soma da seção C, escores normativos ou inclusão no laudo.
- [x] Adicionar finalização e página de resultados com identificação, tabelas, perfil bruto, edição e impressão no modelo WISC4; reabrir aplicações finalizadas no resultado.
- [x] Verificar testes Django, renderização/navegação, TypeScript, ESLint, Ruff e executar atualização graphify.

Limites: `computed_payload`/`classified_payload` continuam vazios no modo item a item. O resumo descritivo gerado pelo servidor é salvo em `raw_payload.item_summary`, acompanhado de `completion_status`. Não há migração de respostas ou homologação normativa.

Verificação: 46 testes Django e 26 testes de interface/renderização passaram; TypeScript, ESLint e Ruff passaram. `npm audit` apontou as 15 vulnerabilidades já existentes (7 moderadas, 7 altas, 1 crítica); dependências não alteradas. Não houve acesso autenticado ao ambiente publicado. Frontend e backend precisam ser publicados juntos.

`graphify update .` executado; a ferramenta recusou sobrescrever `graph.json` porque a extração atual tem menos nós que o grafo existente. Não foi forçada a substituição.
