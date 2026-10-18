# Segurança e integração dos laudos

- [x] Isolar pacientes, avaliações, testes, documentos, anamneses e laudos nas APIs e views legadas.
- [x] Separar edição da aprovação clínica; testar acesso cruzado inclusive para admins.
- [x] Corrigir dependências e falhas abertas da auditoria, mantendo a ordem visual dos capítulos.
- [x] Preservar dados, textos, identidade e exportações nas novas aprovações; criar revisões separadas.
- [x] Exibir aplicações/informantes separadamente, sem deduplicar pelo nome do instrumento.
- [x] Conectar interface/revisão experimental dos especialistas sem perder edições humanas (sem integração automática ao texto).
- [ ] Homologar modelo/worker e referências (depende de operação e avaliação clínica).
- [ ] Integrar síntese e versões homologadas dos modelos privados ao DOCX.

Executar na ordem. Não ativar provedores ou serviços pagos automaticamente.
Não redistribuir cadastros antigos com responsáveis divergentes sem revisão.
Verificar cada etapa com testes antes de avançar.

## Entrega intermediária

- Aplicar `python manage.py migrate` no deploy: nova migration `reports.0007_reportapprovalsnapshot`.
- Aprovação exige CRP, revisão sem pendências, auditoria válida vinculada ao conteúdo e exportação DOCX bem-sucedida.
- O snapshot guarda contexto, textos, identidade, checksum do modelo do sistema e bytes DOCX/HTML no banco. Não ativa modelos privados em rascunho.
- O fluxo de nova revisão copia textos humanos, mas exige nova auditoria/aprovação. O documento original não é alterado.
- Laudos finalizados anteriormente não recebem retroativamente um snapshot confiável; devem passar por uma nova revisão para usar essa garantia.
- Downloads de anexos usam API autenticada. Infraestrutura externa/CDN/bucket deve negar acesso público direto a `documents/`; essa configuração não foi verificada aqui.
- `.venv/bin/graphify update .` executado: relatório/cache atualizados. A ferramenta recusou reduzir o `graph.json` de 9.030 para 7.499 nós; não foi usado `force` para preservar o grafo existente.
- Verificação: 224 testes direcionados passaram; TypeScript, Ruff dos novos serviços/testes, `git diff --check` e consistência da migration passaram. Renderização Word/LibreOffice e operação em produção continuam não verificadas.
- Próxima entrega: revisão auditável dos especialistas (aprovar/rejeitar/repetir), interface e integração apenas de resultados aprovados.
