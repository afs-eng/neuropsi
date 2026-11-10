# Tabelas Vineland-3 em CSV no padrão de organização WISC4

Objetivo: converter integralmente as 21 tabelas B.1–B.6, C.1–C.6, D.1–D.6 e E.1–E.3 dos PDFs fornecidos para `apps/tests/vineland3/tabelas/`, separadas por apêndice, tabela, formulário, nível e idade. Manter IC95 e o comportamento clínico já confirmado.

- [x] Inventariar páginas, cabeçalhos e famílias de tabelas, inclusive páginas com texto rotacionado.
- [x] Criar importador reproduzível, CSVs e índice com SHA-256, páginas e descrição das colunas; não copiar marcas d'água ou dados pessoais.
- [x] Conferir células, continuidade, contagens e resultados contra os dados já validados e os apêndices ingleses.
- [x] Carregar os cálculos existentes a partir dos CSVs, sem mudar resultados ou habilitar funções clínicas novas implicitamente; oferecer leitor para as demais tabelas.
- [x] Testar regressões, rastreabilidade, integridade dos arquivos, lint/tipos e atualizar graphify.

O pedido trata da organização das tabelas normativas para o backend, seguindo o WISC4. Não altera as respostas dos pacientes nem redesenha o PDF neste incremento.

## Resultado e verificação

- 21 tabelas, 509 páginas, 573 CSVs de dados / 167.713 registros; mais catálogo e índice de fontes, total 575 CSVs (~3 MB). Diretório `apps/tests/vineland3/tabelas/`; organização e exemplos no README desse diretório.
- Importador `import_csv_tables.py` cobre todos os tipos, inclusive equivalentes etários/VEC e pares de subdomínios. Campos sem norma preservados vazios, diferentes de zero; fontes e páginas rastreáveis, sem dados pessoais das marcas d'água.
- `--verify-english` confere os arquivos efetivamente gravados e índices contra os PDFs portugueses e todas as tabelas/valores contra o inglês: 21 tabelas / 573 arquivos / 167.713 registros, sem divergências.
- `csv_tables.py` oferece leitura filtrada por tabela, nível, idade e tipo, com validação de SHA-256 e quantidade de linhas. Os carregadores existentes agora leem CSVs; reconstruções coincidem integralmente com `norms.json` e `domain_norms.json`, preservados como snapshots, sem fallback de runtime.
- 83 testes backend (incluindo 13 de corpus CSV e 6 regressões WISC4) + 30 de interface passaram. Ruff, Bandit, TypeScript e `git diff --check` passaram.
- PDFs sintéticos continuam com 4 páginas A4 (opcionais preenchidos/vazios) e 7 com observações longas; mesmos valores e bytes dos PDFs da etapa anterior.
- `graphify update .` executado; preservado o grafo maior quando a ferramenta recusou sobrescrita, sem forçar substituição.
- Nenhum deploy, alteração de banco/respostas ou migração foi realizado. Não altera normas americanas, IC95 ou bloqueios de revisão clínica/inclusão no laudo.
