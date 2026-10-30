# Ajustes Vineland a partir dos novos materiais

- [x] Conferir o Markdown e o PDF: banco parcial com edição não confirmada; PDF contém normas, não regras de aplicação.
- [x] Registrar o banco transcrito com origem e versão, sem mapear itens a subdomínios por suposição.
- [x] Salvar respostas e observações como registro parcial, sem cálculo normativo nem inclusão no laudo.
- [x] Exibir tabelas por domínio, inputs de um caractere, legenda acima do domínio ativo e pendências.
- [x] Verificar as tabelas existentes contra o PDF inglês: 309 tabelas conferidas, sem divergências.
- [x] Rodar testes de persistência, validação, isolamento e regressão: 156 testes Django e 6 testes do componente passaram; TypeScript, Ruff, ESLint e Bandit passaram.
- [x] Executar `graphify update .`: relatório regenerado; `graph.json` preservado pela ferramenta devido ao alerta de redução de nós. Não foi usada atualização forçada.

## Ressalvas

- `npm audit` aponta vulnerabilidades em dependências existentes, incluindo Next.js; nenhuma dependência foi adicionada ou alterada neste ajuste.
- Testes do componente cobrem estrutura e eventos; não substituem homologação clínica nem validação visual em navegador.
