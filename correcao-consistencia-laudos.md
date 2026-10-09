# Consistência de gráficos e tabelas DOCX

- [x] Conferir o DOCX informado: gráficos nativos conservam dados do modelo; BFP recebe tabelas aninhadas como linhas.
- [x] Verificar disponibilidade de dados oficiais: Guilherme não existe no banco local; não reconstruir resultados clínicos por suposição.
- [x] Vincular cada gráfico inserido ao instrumento e atualizar por essa identidade, sem depender de idade, ordem ou testes opcionais.
- [x] Corrigir categorias/séries e tabelas BFP; bloquear exportação inconsistente em vez de devolver gráficos antigos.
- [x] Adicionar regressões: WAIS-III adolescente/adulto, WISC-IV, WASI, opcionais ausentes, SCARED pais/autorrelato, BFP, FDT e bloqueio de pacote inválido.
- [x] Validar: 82 testes de laudos passaram; suíte ampliada de 189 teve 186 aprovados e 3 erros PDF por ausência de libnspr4.so no Chromium. Ruff sem erros novos (E402/F401 preexistentes ignorados).
- [x] Executar `.venv/bin/graphify update .`: extração concluída; ferramenta avisou que preservou o graph.json maior para evitar perda de nós (sem forçar sobrescrita).
- [ ] Gerar cópia de Guilherme: depende de exportação dos resultados oficiais, ausentes do banco local. Original preservado.
