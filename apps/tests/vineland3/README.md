# Vineland-3 — correção normativa e registro parcial de itens

Formulários extensivos: `entrevista`, `pais_cuidadores`, `professores`.
Código canônico: `vineland3` (o antigo rótulo genérico `vineland` no exportador não é um módulo de correção).

## Disponível

- Entrada de pontuações brutas já corrigidas no protocolo, por subdomínio.
- Idade em meses completos calculada pelas datas de nascimento e aplicação.
- Tabelas B.1/C.1/D.1: bruto → escala-v; B.3/C.3/D.3: somas → escore padrão e percentil.
- Subdomínios aplicáveis dependem da idade e do formulário; motor é opcional, mas exige os dois subdomínios.
- CCA calculado com COM + AVD + SOC, sem incluir habilidades motoras.
- Aplicações independentes por respondente; atualizações somente por ID explícito.
- API autenticada, telas de entrada/resultado, gráfico e bloco DOCX para aplicações revisadas/validadas.
- Percentis extremos preservam `<1`/`>99`; sem extrapolação ou substituição por curva normal.
- Aplicações salvas **não validadas**, para revisão clínica antes de inclusão no laudo.
- Registro item a item do banco parcial fornecido: 58 perguntas em cinco domínios, respostas digitáveis `2/1/0/N/D`, observações e pendências. Letras minúsculas são convertidas para maiúsculas; zero, vazio, N e D permanecem distintos.
- Este banco tem **edição e formulário não confirmados**: não está associado aos três formulários extensivos e não recebe conversão normativa, classificação, interpretação ou inclusão no laudo, mesmo se marcado como validado.

## Fonte e rastreabilidade

Os apêndices fornecidos são explicitamente **normas americanas**, não uma amostra normativa brasileira.
`norms.json` contém apenas tabelas numéricas extensivas extraídas dos PDFs, sem dados pessoais das marcas d'água.
Cada resultado identifica arquivo, SHA-256 e páginas físicas do PDF.

Reimportação (dependência somente de desenvolvimento, sem alteração do ambiente da aplicação):

```bash
uv run --no-project --with pymupdf python apps/tests/vineland3/import_norms.py
```

O importador confere cabeçalhos, marcadores laterais, continuidade dos intervalos e três páginas por tabela de escores padrão. Não executa macros da planilha.

## Novos materiais conferidos

- `aux/vineland/Vineland3_Instrucoes_Corrigidas.md`: fonte das perguntas e do layout; declara transcrição parcial e edição não comprovada. Banco versionado: `vineland_partial_transcription_v1`. Inputs de texto de um caractere, observações por item, navegação por domínio preservando o estado e descrição/legenda imediatamente acima do domínio ativo.
- `aux/vineland/vineland-3-manual-appendices.pdf`: edição inglesa de 2016, 525 páginas, apêndices B–E. Não contém regras de base/teto nem comprova a edição das perguntas transcritas.
- Conferência automatizada das **309 tabelas por faixa etária** (226 de subdomínios e 83 de domínios) contra esse PDF: **sem divergências** nos intervalos etários, intervalos brutos, escores e percentis. As normas e páginas originais em português foram preservadas.

Para repetir a conferência sem sobrescrever `norms.json`:

```bash
uv run --no-project --with pymupdf python apps/tests/vineland3/import_norms.py --verify-english
```

O modo `items` de `/api/tests/vineland3/submit` exige `item_protocol_id`, `form: null`, `raw_scores: {}` e `item_responses: {dominio: {item: {response, observation}}}`. Salva somente o registro, identificado pela aplicação/paciente/avaliação; respostas vazias são permitidas, valores inválidos não. Modos não podem ser trocados na mesma aplicação para evitar perda ou interpretação indevida dos dados.

## Bloqueios / próximo incremento

Os arquivos disponíveis não incluem os protocolos completos nem as regras de início, basal, teto, estimativas, respostas especiais e omissões. **Não inferir contagem de itens pelo máximo bruto nem usar soma simples.** O modo `items` permite apenas registro; a correção genérica continua rejeitando seu cálculo.

As faixas de classificação qualitativa precisam de uma referência do manual confirmada. `classification_status=pending_manual_verification`; nenhuma classificação clínica é inventada. A interpretação atual é quantitativa e determinística.

Ainda pendentes: correção normativa item a item e protocolos completos/confirmados; classificação qualitativa; IC; equivalentes etários/VEC; correção de comportamento mal adaptado (apêndice E); comparações inferenciais entre informantes; homologação clínica dos casos de referência. Esses recursos não devem ser apresentados como concluídos.
