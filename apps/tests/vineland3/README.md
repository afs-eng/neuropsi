# Vineland-3 — primeiro incremento

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

## Fonte e rastreabilidade

Os apêndices fornecidos são explicitamente **normas americanas**, não uma amostra normativa brasileira.
`norms.json` contém apenas tabelas numéricas extensivas extraídas dos PDFs, sem dados pessoais das marcas d'água.
Cada resultado identifica arquivo, SHA-256 e páginas físicas do PDF.

Reimportação (dependência somente de desenvolvimento, sem alteração do ambiente da aplicação):

```bash
uv run --no-project --with pymupdf python apps/tests/vineland3/import_norms.py
```

O importador confere cabeçalhos, marcadores laterais, continuidade dos intervalos e três páginas por tabela de escores padrão. Não executa macros da planilha.

## Bloqueios / próximo incremento

Os arquivos disponíveis não incluem os protocolos completos nem as regras de início, basal, teto, estimativas, respostas especiais e omissões. **Não inferir contagem de itens pelo máximo bruto nem usar soma simples.** O modo `items` é explicitamente rejeitado na API e na correção genérica.

As faixas de classificação qualitativa precisam de uma referência do manual confirmada. `classification_status=pending_manual_verification`; nenhuma classificação clínica é inventada. A interpretação atual é quantitativa e determinística.

Ainda pendentes: item a item; classificação qualitativa; IC; equivalentes etários/VEC; comportamento mal adaptado (apêndice E); comparações inferenciais entre informantes; homologação clínica dos casos de referência. Esses recursos não devem ser apresentados como concluídos.
