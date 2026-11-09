# PDF Vineland no padrão WISC4

Referências: `aux/vineland/modelo-wisc4.pdf` (arquivo fornecido) e imagens do relatório de pontuação Vineland. Manter identidade visual NeuroAvalia azul, capa, tabelas, gráfico, análise e síntese em A4.

- [x] Criar serviço/template próprios do Vineland; revalidar a finalização e recalcular as somas a partir das respostas, sem confiar no resumo salvo.
- [x] Registrar exportador na rota autenticada existente e conectar o botão PDF da tela de resultados, com carregamento e erro.
- [x] Testar identidade, somas, zero, opcionais, itens críticos, HTML escapado, controle de acesso e recusa de rascunhos/legado.
- [x] Gerar PDF sintético, conferir paginação/layout e executar testes, TypeScript, lint e graphify.

Não importar dados do paciente do PDF modelo; não copiar nomes profissionais fixos do WISC4. Usar paciente/examinador da avaliação. Sem conversão normativa: escores padrão, CCA, percentis, IC, forças/fraquezas e diferenças estatísticas ficam explicitamente não calculados.

Prévia sintética em `/tmp/opencode/vineland-pdf-preview/`: relatório completo e somente domínios centrais têm quatro páginas A4; observações com quase 10 mil caracteres geram páginas adicionais com o final do texto preservado. Chromium renderizado e páginas examinadas visualmente. Bibliotecas de conferência e bibliotecas de sistema ausentes do Chromium foram isoladas em `/tmp/opencode/vineland-pdf-review/`, sem alteração de dependências do projeto ou do sistema.

Validação: 52 testes Vineland + 6 testes do serviço PDF WISC4 + 28 testes de interface passaram. TypeScript, ESLint e Ruff dos arquivos específicos passaram. `endpoints.py` contém 11 apontamentos Ruff preexistentes, idênticos ao HEAD (comparação automatizada); não foram alterados trechos alheios à tarefa. `graphify update .` executado, sem forçar sobrescrita do grafo maior existente. Sem publicação ou acesso autenticado ao ambiente remoto; publicar frontend e backend juntos.
