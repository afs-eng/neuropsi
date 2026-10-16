# Modelo DOCX WISC-IV

- [x] Incluir cópia do modelo de `aux` nos assets versionados do backend.
- [x] Usar o modelo e seu cabeçalho/rodapé em todas as exportações WISC-IV.
- [x] Ajustar vínculos dos gráficos à ordem do novo modelo, sem dados de exemplo.
- [x] Testar seleção, exportação completa, gráficos e isolamento dos demais testes.
- [x] Executar graphify update após as alterações.

Validação: 85 testes passaram. Ruff sem novos alertas (35 preexistentes no
serviço de exportação). Graphify executado sem forçar a substituição do grafo
maior existente. Não houve deploy nem conferência visual no Word.
