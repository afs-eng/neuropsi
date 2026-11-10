# Vineland: Extensivo × Níveis de Domínio

Escopo confirmado: seis combinações por totais, duas seleções (tipo e informante), uma aplicação por vez. Preservar questionário Pais/Cuidadores de 180 itens, legados e aplicações existentes; sem publicar.

- [x] Mapear entradas das seis abas de `aux/CORRECAO.xlsm` e confrontar com CSVs/manuais; não executar macros/copiar fórmulas defeituosas.
- [x] Acrescentar nível explícito ao contrato, mantendo totais antigos como extensivos e impedindo mudança de modalidade no mesmo registro.
- [x] Implementar totais de domínio para Entrevista, Pais/Cuidadores e Professores com normas específicas, limites etários e sem subdomínios fictícios.
- [x] Organizar seleção de tipo, informante e modo de entrada; mostrar resultados e preservar revisão/PDF/laudo dos fluxos compatíveis.
- [x] Testar seis combinações, rejeição de misturas, reabertura/edição e regressões; atualizar documentação e executar atualização do grafo (ressalva abaixo).

A planilha serve como referência de organização e campos. Normas continuam nos CSVs validados contra manuais; sem uso de cortes de idade em dias fixos, fórmulas Excel ou dados pessoais de exemplo. Não cria bancos de perguntas não fornecidos nem comparações entre informantes.

## Evidências de conclusão local

- 205 testes backend passando, incluindo 12 testes novos em `apps.tests.test_vineland_forms`; 34 testes de interface, Ruff, ESLint, TypeScript e Bandit passando.
- Chromium real com Next/Django e banco SQLite sintético isolado: seleção, preenchimento e salvamento nas seis combinações; revisão explícita, PDF servidor de quatro páginas, edição, invalidação e reabertura para os três Níveis de Domínio; tela móvel e nenhum erro JavaScript. Evidências: `/tmp/opencode/vineland-six-browser/`; script: `/tmp/opencode/vineland-six-browser.py`.
- PDF/DOCX distinguem B.3/B.4/B.5/E.1, C.3/C.4/C.5/E.2 e D.3/D.4/D.5/E.3. Totais não inventam perguntas ou indicam ausência de itens críticos.
- `graphify update .` executado, mas manteve a proteção contra substituir o grafo maior (9.030 nós) pelo AST parcial (8.143); sem sobrescrita forçada.
- `npm audit` continua com 15 vulnerabilidades preexistentes (7 moderadas, 7 altas, 1 crítica); nenhuma dependência alterada. Homologação clínica independente e verificação em produção continuam pendentes.
- Sem commit, push, deploy ou alteração de pacientes reais. Servidores temporários encerrados e artefatos rastreados `.next` restaurados ao estado anterior aos testes.
