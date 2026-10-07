# Tela de correção THCP

## Objetivo
Aplicar a referência visual de `aux/Dashboard NeuroAvalia para Correção do THCP.png`, com campos por item e totais automáticos, preservando sidebar, limites, normas e cálculos existentes.

## Tarefas
- [x] Conferir os campos persistidos e a fórmula da atenção no módulo THCP.
- [x] Reorganizar a tela em resumo de cinco domínios, dados da aplicação e painéis de pontuação responsivos.
- [x] Conferir 42 casos de limites/vazios, totais 74/91 e mínimo zero da atenção; verificar que carregamento e envio permanecem idênticos ao código anterior.
- [x] Executar TypeScript, lint e os 25 testes THCP, todos aprovados.
- [x] Validar visualmente no navegador: bibliotecas temporárias extraídas em `/tmp/opencode`, sem instalar pacotes no sistema.
- [ ] Atualizar o graphify: `graphify update .` tentado, mas o executável não está instalado.

## Critérios
- Sidebar e normas intactas; backend aceita/valida opcionalmente os itens sem alterar cálculos normativos.
- Campos vazios permanecem distintos de zero; erros de atenção mantêm limite 62.
- Persistir respostas por item e pontuações, sem inventar gabaritos.

## Revisão solicitada
- [x] Conferir campos, opções e fórmulas na aba THCP da planilha (incluindo VBA, sem gabarito de alternativas).
- [x] Criar validação/persistência opcional dos itens, mantendo compatibilidade com totais antigos.
- [x] Substituir os cards informativos pelos campos detalhados e seleção de alternativas/pontos.
- [x] Verificar somas, limites, consistência no backend, restauração e compatibilidade das aplicações antigas.

## Verificação da revisão
- 33 testes backend aprovados, incluindo comparação das alternativas com as células da planilha, consistência de totais, persistência, recorreção e bloqueio.
- TypeScript, ESLint e Ruff aprovados.
- Playwright com APIs fictícias: 47 itens reais, totais 91/90/62, resposta ausente explícita, limite de 62 erros, envio/restauração, bloqueio e totais antigos preservados.
- Sem rolagem horizontal nas larguras 375, 768, 1024 e 1280; capturas desktop/mobile em `/tmp/opencode/thcp-items-*.png`.
- Graphify continua indisponível (`command not found`); não houve substituição ou remoção de arquivos do grafo.
