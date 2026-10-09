# Padrão WAIS-III — modelo aprovado

Referência: `aux/Laudo-Eric-Jhonn-Mascarenhas-CORRIGIDO.docx`.
Escopo confirmado: apenas WAIS-III; apresentação e organização clínica; informantes apresentados em conjunto.

- [x] Criar ativo reutilizável com estilos, timbre e gráficos do modelo, removendo dados clínicos, imagens de resultados e vínculos antigos.
- [x] Construir os DOCX WAIS-III na ordem do modelo, com numeração contínua de tabelas/gráficos e fechamento completo; preservar conteúdos revisados.
- [x] Manter todas as aplicações SRS-2, identificar respondentes e comparar somente domínios/formulários compatíveis com escores disponíveis.
- [x] Alinhar a organização das interpretações e do contexto de geração, sem copiar diagnósticos ou criar dados ausentes.
- [x] Verificar exportação, isolamento WISC-IV/WASI, identidade, dados dos gráficos e ausência de dados de Eric no ativo; executar atualização graphify.

Nota: BDEFS e IPHEXA aparecem no documento, mas não possuem módulos especializados neste checkout. Não implementar correção normativa nova nem reutilizar os números do modelo; apresentar resultados estruturados salvos quando disponíveis.

## Verificação

- `manage.py test apps.reports.tests apps.reports.test_wais3_docx_model --noinput`: 93 testes aprovados.
- Ruff aprovado nos arquivos novos/modificados; no exportador, ignorados apenas E402/F401 preexistentes.
- `git diff --check`: aprovado.
- `graphify update .`: executado; preservou o `graph.json` maior existente por segurança, sem atualização forçada.
- Paginação visual no Word/LibreOffice pendente: LibreOffice não está instalado neste ambiente. A estrutura XML, margens, timbre e resultados foram verificados automaticamente; não foi confirmada equivalência visual página a página.
- Descoberta ampla por `manage.py test apps.reports` falhou por pacote namespace (`__file__` ausente); a execução com os dois módulos explícitos acima foi aprovada.
