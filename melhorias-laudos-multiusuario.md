# Laudos multiusuário e especialistas

- [x] Cadastro privado de modelos por proprietário, sem sobrescrita de versões pela API.
- [x] API autenticada para cadastro, envio e download privado; uploads permanecem rascunhos.
- [x] Autoria e assinatura dinâmicas no texto; cabeçalhos/imagens ainda são os dos modelos atuais.
- [x] Registro de especialistas e planejamento por aplicação validada, sem chamadas extras à IA.
- [x] Verificação: 117 testes passando, arquivos novos sem alertas Ruff; migração consistente.

Próximas entregas: interface de modelos, homologação/mapeamento dos templates,
execuções persistentes dos especialistas, worker, integração clínica e aprovação
vinculada ao snapshot. Esta primeira entrega não ativa templates arbitrários nem
substitui silenciosamente o pipeline clínico atual.

Lint global: pendências anteriores ao trabalho e mypy indisponível; não corrigidos
fora do escopo. Graphify executado, mas recusou substituir o graph.json maior
existente. Migração criada e testada em banco de testes, sem deploy ou migração de
produção. Detalhes e endpoints: `apps/reports/PRIVATE_TEMPLATES.md`.
