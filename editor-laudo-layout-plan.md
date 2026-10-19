# Editor de laudos — layout clean

Escopo: `/dashboard/reports/[id]`, incluindo o laudo 17. Preservar handlers,
permissões, fontes, textos, avisos, revisão, exportação e fila existentes.

- [x] Cabeçalho compacto com paciente, status e ações principais; secundárias em menu acessível.
- [x] Separar Editor, Dados dos testes e Especialistas em abas; preservar estado e acompanhamento.
- [x] Navegação de capítulos consistente, incluindo domínios WISC; editor amplo, responsivo e rotulado.
- [x] Recolher metadados e comparação de versões sem esconder avisos clínicos; organizar revisão final.
- [x] Validar TypeScript, lint e 30 testes frontend (10 novos); navegador com API inteiramente simulada.
- [x] Executar auditoria de dependências: alertas preexistentes, sem atualizar pacotes neste escopo.
- [ ] Atualizar grafo: `graphify update .` bloqueado por comando indisponível; grafo preservado.

Sem backend, migrations, inferência real ou mudanças nos critérios de aprovação.
Não acessar dados clínicos da produção para testes; usar somente dados sintéticos.

## Resultado da verificação — 19/10/2026

- Editor, seleção de aplicações e painel de especialistas permanecem montados ao
  trocar abas; `?view=editor|tests|specialists` identifica a área na URL. Links
  `#specialist-run-*` abrem a área de especialistas. Capítulos apenas selecionam
  texto; a regeneração permanece em ação explícita, não no menu de navegação.
- 11 handlers existentes de carregamento, gravação, geração, auditoria, aprovação,
  revisão e exportação comparados com HEAD: corpos inalterados.
- Playwright/Chromium local: 1440px e larguras 320/375/390/768/1024px, sem overflow
  horizontal da página; teclado, menus/Escape/foco, texto não salvo entre abas,
  gravação sintética, seleção persistente dos especialistas, avisos e bloqueios
  de laudo aprovado/somente testes. Nenhuma inferência ou requisição à produção.
- Evidências temporárias: `/tmp/opencode/report-editor-browser.log`, screenshots
  em `/tmp/opencode/report-editor/`. Faltavam bibliotecas do Chromium; extraídas
  somente em `/tmp/opencode/report-editor-browser-libs`, sem instalação no sistema.
- O servidor temporário foi encerrado; artefatos `.next` já versionados foram
  restaurados ao estado anterior, removendo apenas alterações geradas por este teste.
- `npm audit --omit=dev`: 1 alerta crítico (Next.js) e 2 altos (PostCSS e
  source-map-js), preexistentes. Relatório em `/tmp/opencode/report-editor-npm-audit.json`.
  Sem alteração de dependências; correção exige entrega própria antes de afirmar
  uma auditoria de segurança aprovada.
- Sem deploy, commit, push, backend ou migrations. A página publicada não foi
  alterada nesta sessão; publicar o frontend para disponibilizar o novo layout.
