# Tela de correção THCP

## Objetivo
Aplicar a referência visual de `aux/Dashboard NeuroAvalia para Correção do THCP.png`, preservando sidebar, payload, limites, normas e cálculos existentes.

## Tarefas
- [x] Conferir os campos persistidos e a fórmula da atenção no módulo THCP.
- [x] Reorganizar a tela em resumo de cinco domínios, dados da aplicação e painéis de pontuação responsivos.
- [x] Conferir 42 casos de limites/vazios, totais 74/91 e mínimo zero da atenção; verificar que carregamento e envio permanecem idênticos ao código anterior.
- [x] Executar TypeScript, lint e os 25 testes THCP, todos aprovados.
- [ ] Validar visualmente no navegador: Chromium bloqueado pela ausência de `libnspr4.so` no ambiente.
- [ ] Atualizar o graphify: `graphify update .` tentado, mas o executável não está instalado.

## Critérios
- Nenhuma alteração em backend, sidebar ou normas.
- Campos vazios permanecem distintos de zero; erros de atenção mantêm limite 62.
- Não criar respostas por item ou gabaritos que o sistema não persiste.
