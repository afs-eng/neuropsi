# Vineland — fechamento técnico do questionário atual

Escopo confirmado: Pais/Cuidadores — Níveis de Domínio (180 itens), revisão profissional explícita e integração ao laudo; somente verificação local, sem deploy ou dados reais.

- [x] Auditar elegibilidade, recalculação, erros e consistência dos resultados.
- [x] Implementar revisão explícita com identidade do profissional e impressão digital dos dados/normas; invalidar após alteração.
- [x] Integrar somente resultados finalizados, normativamente disponíveis e revisados ao contexto/laudo DOCX.
- [x] Expor ação e situação de revisão na tela, sem confundir finalização com validação.
- [x] Verificar permissões, edição, dados obsoletos, API, DOCX e regressões; atualizar documentação e grafo.

Homologação clínica independente e verificação autenticada em produção permanecem externas a esta etapa. Não declarar 100% clínico com base apenas nos testes automatizados.

## Evidências locais

- Revisão autenticada com confirmação explícita, nota, profissional/CRP e assinatura vinculada aos dados atuais; permissões individuais e por papel; bloqueio de versões antigas, falsificação de flag/JSON, reaproveitamento em outro ID e alterações após revisão.
- Retirada de aprovação sem alterar respostas; novas edições/refinalizações exigem nova revisão. O banco legado continua separado. Laudos já finalizados conservam os snapshots históricos, sem alterações retroativas.
- DOCX: tabelas adaptativa/CCA, comportamento, forças/fraquezas e diferenças; gráfico com IC95%; síntese normativa, itens críticos individuais e nota profissional. PDF próprio informa situação de revisão. Corrigidos avisos obsoletos da tela que diziam não haver correção normativa.
- Navegador Chromium real, Next + Django locais e SQLite isolado `/tmp/opencode/vineland-review-e2e.sqlite3`, apenas paciente/profissional fictícios: abriu resultado autenticado, conferiu IC95/itens críticos/estimativas históricas, aprovou, baixou PDF servidor de quatro páginas, retirou validação, editou/refinalizou e renderizou em tela móvel; sem erros JavaScript. Evidências em `/tmp/opencode/vineland-review-browser/`; script `/tmp/opencode/vineland-review-browser.py`.
- PDFs sintéticos normais/opcionais vazios: 4 páginas; observações longas: 7 páginas, sem truncamento. Nenhum acesso ou alteração de registro real, migração do banco da aplicação, commit, push ou deploy.
- Regressão: 193 testes backend (Vineland, corpus, revisão, WISC4 PDF e `apps.reports.tests`) e 34 testes de interface. Ruff, ESLint, TypeScript e Bandit verificados. Dependências não alteradas; `npm audit` mantém os problemas preexistentes, registrados separadamente.
- `npm audit`: 15 vulnerabilidades preexistentes (7 moderadas, 7 altas e 1 crítica); não houve alteração de dependências neste escopo. Precisam de atualização coordenada antes de se declarar o sistema inteiro pronto para produção.
- `graphify update .` executado; a ferramenta recusou substituir o grafo maior de 9.030 nós pelo parcial de 8.115. Não foi forçada a sobrescrita. `git diff --check` passou; artefatos `.next` produzidos pelo teste local foram restaurados ao estado anterior, sem alteração de fontes de outras funcionalidades.

## Antes do uso clínico publicado

1. Homologar de forma independente casos de referência e limites etários/formulário, incluindo preenchimentos estimados e interpretação dos itens críticos. As normas continuam americanas.
2. Após autorização de publicação, publicar frontend/backend juntos e repetir o fluxo autenticado na infraestrutura real, inclusive Chromium/PDF, revisão, DOCX e edição/refinalização.
3. Manter a revisão profissional de cada aplicação; não confundir finalização, homologação do sistema e aprovação do caso.
