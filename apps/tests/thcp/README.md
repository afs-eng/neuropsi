# THCP

Teste de Habilidades e Conhecimento Pré-Alfabetização, integrado ao registro de testes, API, frontend, PDF e laudo DOCX.

## Aplicação

Na avaliação, adicionar **THCP** e preencher:

| Campo | Intervalo |
|---|---|
| Habilidades Percepto-Motoras — total dos exercícios I e II | 0–30 |
| Linguagem | 0–12 |
| Pensamento Quantitativo | 0–11 |
| Memória | 0–10 |
| Atenção — acertos | 0–28 |
| Atenção — erros | 0–62 |

A atenção é `max(0, acertos − erros)`; o total é a soma das cinco escalas (0–91). Todos os escores são inteiros obrigatórios. Campos vazios não equivalem a zero.

A idade é calculada na data de aplicação, com fallback para a data inicial/final da avaliação. É obrigatória a data de nascimento. Somente idades completas de 4, 5, 6 e 7 anos são aceitas, inclusive na amostra geral.

## Normas e interpretação

Fonte: `aux/CORRECAO.xlsm`, abas `THCP` e `THCP-Normas`. A transcrição está em `norms.py`, com SHA256 da fonte. O deploy **não depende** da presença da planilha nem de um leitor de Excel.

- Subescalas: quartis/classificações do manual e médias/desvios por idade ou amostra geral.
- Total por idade: T-score/classificação do manual. Z = `(T − 50) / 10` somente quando T é pontual.
- Total na amostra geral: média 64,1, DP 15,6; Z = `(bruto − média) / DP`.
- Subescalas: Z = `(bruto − média) / DP`, T = `max(0, 50 + 10 × Z)`.
- Ponderado = `10 + 3 × Z`; percentil estimado = `100 × Φ(Z)`.
- Classificação por Z (Guilmette) é independente da classificação do manual; usa os cortes exatos da planilha antes do arredondamento.
- T-score censurado (`< 27`, `> 73`, etc.) é preservado: sem Z, ponderado, percentil ou classificação Z pontuais para o total. Gráficos não substituem indisponibilidade por zero.
- A fonte traz `T < 28` para total 49 aos 6 anos (`THCP-Normas!E206/B206`). A inconsistência é preservada e gera aviso para conferência do manual.
- A amostra geral não fornece classificação manual do total no protocolo; esse campo permanece indisponível.

A interpretação é determinística, sem chamadas de IA, e precisa da revisão do profissional; não estabelece diagnóstico isoladamente.

## Integração e deploy

- `POST /api/tests/thcp/submit`: escores acima, `norm_type` (`idade` ou `geral`), `evaluation_id`, `applied_on` opcional e `application_id` opcional para edição.
- `GET /api/tests/thcp/result/{id}`: resultado, interpretação e payload estruturado.
- `GET /api/tests/applications/{id}/export-pdf`: PDF com tabelas, perfil e notas técnicas, usando o mesmo Chromium/Playwright dos outros testes.
- Frontend: `/dashboard/tests/thcp` e `/dashboard/tests/thcp/{id}/result`.
- `0005_add_thcp_instrument` cadastra o instrumento com `python manage.py migrate`; o catálogo e `create_instruments` também o incluem sem reativar instrumentos desativados.
- Aplicações travadas não podem ser editadas. Auth e permissões seguem os outros testes.
- O laudo inclui as seis linhas, gráfico e interpretação antes da conclusão/referências, usando os mesmos payloads da correção.

## Verificação

```bash
uv run python manage.py test apps.tests.test_thcp
```

Os testes cobrem fórmulas, limites, intervalos de T, faixas normativas, edição, permissões, idade na aplicação, recorreção, PDF e DOCX. Quando a planilha fonte está presente, também conferem todas as células normativas de subescalas e total.
