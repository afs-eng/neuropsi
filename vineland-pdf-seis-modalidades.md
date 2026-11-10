# PDF Vineland — seis modalidades

Escopo: completar os três Extensivos e preservar os três Níveis de Domínio, no padrão visual WISC-IV/NeuroAvalia. Sem novos indicadores clínicos, publicação ou alteração de registros reais.

- [x] Recalcular os Extensivos com dados atuais e bloquear registros inválidos, sem gravar ou confiar em resultados em cache.
- [x] Compartilhar o estilo do PDF existente; incluir identificação, subdomínios, domínios/CCA, gráficos separados e síntese com limitações/fontes.
- [x] Disponibilizar download autenticado na tela de resultados extensivos, com estado de carregamento e erro.
- [x] Verificar seis modalidades, segurança, dados obsoletos, omissões e PDFs reais; rodar regressões, lint e tipos.
- [x] Executar atualização do grafo e registrar eventual proteção contra substituição parcial.

## Evidências locais

- 211 testes backend e 36 de interface passando. Incluem regressões Vineland, CSVs, revisão/DOCX, WISC4 PDF e relatórios; seis novos testes de PDF verificam fontes, recálculo, segurança, ausência de motor, dados inválidos e escape de texto.
- PDFs reais gerados pela rota autenticada, em banco SQLite sintético isolado: seis modalidades com quatro páginas usuais; caso Extensivo sem motor com observações extensas produziu seis páginas, preservando o marcador final. Imagens/pdfs em `/tmp/opencode/vineland-pdf-all/`.
- Chromium real abriu as seis telas de resultados e baixou os seis PDFs pelo botão da interface, sem erros JavaScript. Evidências em `/tmp/opencode/vineland-pdf-browser/`.
- Indicadores não calculados no fluxo Extensivo permanecem explicitamente indisponíveis, sem inventar IC, classificações, comparações ou diagnósticos. O questionário e as normas de domínio permanecem separados.
- Sem commit, push, deploy ou alteração de pacientes reais. Dependências de inspeção/PDF usadas somente em `/tmp/opencode`; servidores temporários encerrados e artefatos rastreados `.next` restaurados.
- Ruff, ESLint, TypeScript, Bandit e `git diff --check` passaram. `npm audit` mantém 15 vulnerabilidades preexistentes (7 moderadas, 7 altas, 1 crítica); dependências do projeto não foram alteradas.
- `graphify update .` executado; a ferramenta recusou substituir o grafo maior de 9.030 nós pela extração parcial de 8.156 nós. Sem sobrescrita forçada.
