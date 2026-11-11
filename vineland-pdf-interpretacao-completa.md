# Vineland Extensivo — PDF analítico e interpretação

Escopo confirmado: PDF individual dos três Extensivos; interpretação automática descritiva preliminar, sem diagnóstico. Sem deploy, alteração de pacientes reais, mudança nas normas ou nas aprovações existentes.

- [x] Gerar interpretação determinística de CCA, domínios, subdomínios e diferenças significativas a partir da correção atual, sem texto salvo ou inferência de itens.
- [x] Incluir síntese interpretativa e páginas por domínio com tabelas, gráficos e leitura dos subdomínios; manter análises estatísticas e anexo.
- [x] Cobrir referência, três informantes, ausência de Motor, empates, falta de normas, direção das diferenças, segurança e revisão não automática.
- [x] Executar regressões/lint/segurança, renderizar PDFs reais e conferir paginação/legibilidade; tentar atualizar o grafo sem sobrescrita forçada.

## Resultado e limites

- `extensive_interpretation.py` usa exclusivamente os resultados atuais; não altera correção, registros, assinaturas de revisão ou interpretação salva. O texto automático permanece preliminar, inclusive quando há nota de revisão dos resultados.
- Diferencia posição normativa (referência escala-v 15) de força/fraqueza relativa à média pessoal global. Usa a decisão de significância calculada antes de arredondar; não transforma indisponibilidade em ausência de diferença ou escore zero.
- PDFs autenticados de dados sintéticos em SQLite em memória: três Extensivos com 13 páginas e três Níveis de Domínio com quatro. Caso sem Motor e observações longas com 14 páginas preservou o final do texto. Artefatos locais em `/tmp/opencode/vineland-complete-pdfs/`.
- Páginas por domínio incluem tabela analítica, gráfico com referência normativa e média pessoal, leitura individual de cada subdomínio e diferenças direcionais; tabelas emparelhadas completas continuam na análise estatística e no anexo.
- Sem novas faixas qualitativas de escala-v, inferência de respostas, idade global de desenvolvimento ou diagnóstico. Homologação clínica e publicação continuam fora desta etapa.
- Verificação final: 226 testes de backend passaram, Ruff sem erros nos arquivos Python alterados, Bandit sem achados e `git diff --check` limpo. Não houve mudança no frontend ou nas dependências do projeto.
- `graphify update .` executado: extração de 8.195 nós; preservou o grafo existente de 9.030 nós por proteção contra sobrescrita parcial. Nenhuma atualização forçada.
