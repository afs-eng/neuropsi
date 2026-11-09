# Correção normativa Vineland-3 — Níveis de Domínio

Escopo confirmado: IC 95%; recalcular aplicações finalizadas ao abrir/exportar sem modificar respostas; tela e PDF com CCA, percentis, IC, escala-v e análises disponíveis. Normas americanas; revisão clínica e inclusão no laudo permanecem separadas.

- [x] Extrair C.3 (bloco Níveis de Domínio), IC, C.4, C.5 e E.2; registrar origem e conferir lacunas/idades e valores com PDFs.
- [x] Implementar cálculo único por idade exata, sem reaproveitar fórmulas incorretas de Entrevista ou interpolar lacunas.
- [x] Integrar finalização e recálculo somente de leitura dos resultados existentes, preservando protocolos legados.
- [x] Preencher tela e PDF com os mesmos resultados normativos, gráfico padronizado e limitações específicas.
- [x] Verificar casos de referência, fronteiras etárias, respostas antigas, permissões, renderização do PDF, lint/tipos e atualizar graphify.

## Evidências

- `domain_norms.json` extraído dos PDFs fornecidos C/E, não das fórmulas do Excel. `import_domain_norms.py --verify-english`: 9.777 células C.3, 90 páginas, 30 conjuntos de IC, C.4/C.5/E.2 coincidentes com o apêndice inglês. SHA-256 das fontes registrado nos dados.
- Conferência da planilha: aba de Pais/Cuidadores aponta E.1 em vez de E.2; comparação de conversões da C.3 com PDFs encontrou divergências/lacunas. Os PDFs português/inglês concordantes são a fonte primária.
- Caso de referência aos 6:0, brutos COM/AVD/SOC/HMOT 72/54/48/37: EP 130/110/91/94, percentis 98/75/27/34. Soma EP 331 → CCA 112, percentil 79, IC95 107–117. Brutos A/B 13/15 → escala-v 21/22 na E.2. Usado em teste numérico, sem recriar ou alterar o PDF do paciente.
- 64 testes Vineland e 6 regressões PDF WISC4 passaram; 30 testes de interface passaram. TypeScript, ESLint, Ruff e Bandit passaram.
- PDFs sintéticos renderizados em Chromium: 4 páginas A4 com opcionais preenchidos ou vazios; 7 páginas com observações longas, mantendo o final do texto. Prévia em `/tmp/opencode/vineland-pdf-preview/`, conferida visualmente.
- `graphify update .` executado; recusou sobrescrever o grafo maior existente, sem forçar substituição.
- Auditoria npm mantém 15 vulnerabilidades preexistentes (7 moderadas, 7 altas, 1 crítica); dependências não alteradas.

## Publicação / limites

Publicar frontend e backend juntos. Nenhuma aplicação remota foi modificada, nenhum banco foi migrado e nenhum deploy foi feito. Após publicar, reabrir a aplicação finalizada e baixar novo PDF para receber a correção. Homologação clínica independente e teste autenticado em produção continuam pendentes. Não há diagnóstico por IA, comparação entre informantes ou inclusão automática no laudo.
