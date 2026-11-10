# Tabelas normativas Vineland-3 — CSV

Organização equivalente ao WISC4: diretório `tabelas/`, separado por famílias de tabelas e, nas conversões, por faixa etária. Os dados continuam sendo **normas americanas do Vineland-3**, nunca normas WISC4.

**Cobertura:** 21 tabelas, 509 páginas normativas dos quatro apêndices, **573 CSVs de dados / 167.713 registros**, mais `catalogo.csv` e `fontes.csv` (575 CSVs no total). Células sem norma são preservadas como campos vazios, não como zeros. Não há marcas d'água, dados pessoais, macros ou texto do paciente nos arquivos.

## Estrutura

```text
tabelas/
├── catalogo.csv              # Localização, formulário, tipo, idade, páginas, linhas e SHA-256 de cada CSV
├── fontes.csv                # Nome e SHA-256 dos quatro PDFs originais
├── tabelas-b/                # Entrevista
│   ├── b1/extensivo/idade_*.csv
│   ├── b2/equivalentes.csv
│   ├── b3/extensivo/idade_*.csv
│   ├── b3/niveis_dominio/idade_*.csv
│   ├── b3/ic/{extensivo,niveis_dominio}/idade_*.csv
│   └── {b4,b5,b6}/estatisticas.csv
├── tabelas-c/                # Pais/Cuidadores: mesma estrutura c1–c6
├── tabelas-d/                # Professores: mesma estrutura d1–d6
└── tabelas-e/
    ├── e1/comportamento.csv  # Entrevista
    ├── e2/comportamento.csv  # Pais/Cuidadores
    └── e3/comportamento.csv  # Professores
```

Os arquivos usam UTF-8, separador vírgula, ponto decimal e quebras LF. O CSV tem formato longo: uma linha por escala/escore ou comparação, evitando cabeçalhos mesclados de PDF/Excel. Os limites etários estão em **meses completos e são inclusivos**. Por exemplo, `idade_0072_0077.csv` corresponde a 6:0–6:5. `mais` e limite máximo vazio indicam intervalo superior aberto conforme a fonte.

## Famílias e campos

| Tabelas | Conteúdo | Campos dos dados |
|---|---|---|
| B.1 / C.1 / D.1 | Bruto dos subdomínios → escala-v, extensivos | `escala, entrada_min, entrada_max, escore, percentil, pagina`; percentil fica vazio porque a tabela não o fornece |
| B.2 / C.2 / D.2 | Equivalentes etários e Valores de Escala de Crescimento dos subdomínios extensivos | `escala, bruto, equivalente_idade, vec, pagina` |
| B.3 / C.3 / D.3 | Domínios/CCA → escore padrão e percentil, em blocos extensivo e níveis de domínio separados | `escala, entrada_min, entrada_max, escore, percentil, pagina` |
| B.3 / C.3 / D.3, subdiretório `ic/` | Margens de IC 85%, 90% e 95% por idade/formulário | `escala, confianca, margem, pagina` |
| B.4 / C.4 / D.4 | Análise de forças/fraquezas de domínios e subdomínios, com blocos extensivos e níveis de domínio | `nivel, categoria, idade_min_meses, idade_max_meses, idade_texto, escala`, estatísticas e `pagina` |
| B.5 / C.5 / D.5 | Comparações entre pares de domínios | Campos etários/de nível, `escala, direcao, outra_escala`, estatísticas e `pagina` |
| B.6 / C.6 / D.6 | Comparações entre pares de subdomínios extensivos | Mesmos campos de pares, com `categoria=subdominio` |
| E.1 / E.2 / E.3 | Bruto Internalizante/Externalizante → escala-v | Campos etários, `escala, bruto_min, bruto_max, escala_v, pagina` |

As estatísticas são `critico_p10, critico_p05, base_2, base_5, base_10, base_15, base_25`. As colunas `base_*` contêm **magnitudes críticas de diferença**, não percentuais calculados do paciente. Campos vazios representam células sem conversão/valor publicado; não interpolar. A direção `>`/`<` das tabelas de pares é obrigatória.

### Não misturar entradas

- `.1`: entrada é bruto de **subdomínio**; saída é escala-v.
- `.3/extensivo`: entrada de COM/AVD/SOC/HMOT é a **soma das escalas-v dos subdomínios**; entrada do CCA é a soma dos escores padrão de COM + AVD + SOC.
- `.3/niveis_dominio`: entrada de COM/AVD/SOC/HMOT é o **bruto do domínio**; entrada do CCA continua sendo a soma dos escores padrão de COM + AVD + SOC.
- `CCA` é o código normalizado de `ABC` nas tabelas. Os carregadores extensivos existentes recebem `ABC` por compatibilidade.
- Equivalentes etários preservam sinais e limites (`<3:0`, `22:0+`). Não converter em números decimais nem atribuí-los aos totais de níveis de domínio.
- E.2 preserva a faixa original `70–90+`, aberta no corpus. O cálculo atual do questionário de níveis de domínio mantém seu limite específico C.3, até 90:11; a conversão para CSV não amplia automaticamente a faixa etária clínica.
- Índices e CSVs são recursos internos do backend. A API não disponibiliza o corpus normativo completo.

## Uso no código

`apps/tests/vineland3/paths.py` centraliza os caminhos, como no WISC4. `csv_tables.py` indexa os arquivos, verifica SHA-256/contagem na leitura e oferece filtros:

```python
from apps.tests.vineland3.csv_tables import load_table

# C.3 de Pais/Cuidadores — Níveis de Domínio, aos 6:0.
scores = load_table("C.3", level="niveis_dominio", months=72, kind="dominios")
intervals = load_table("C.3", level="niveis_dominio", months=72, kind="ic")
strengths = load_table("C.4", level="niveis_dominio", months=72)
domain_pairs = load_table("C.5", level="niveis_dominio", months=72)
subdomain_pairs = load_table("B.6", level="extensivo", months=84)
equivalents = load_table("C.2", level="extensivo")
behavior = load_table("E.2", months=72)
```

O leitor genérico retorna cópias dos valores como strings, além de metadados do catálogo; vazio continua vazio. `kind` distingue conversões e ICs da tabela `.3`. Os carregadores `extensive_norms_from_csv()` e `domain_norms_from_csv()` montam os tipos numéricos usados pelos cálculos existentes, preservando **exatamente** o contrato e os resultados dos JSONs anteriores.

O cálculo em produção passa a ler os CSVs, com cache. `norms.json` e `domain_norms.json` permanecem somente como snapshots de regressão/rastreabilidade: não são fallback de runtime. A importação de B.2/C.2/D.2 ou B.6/C.6/D.6 não habilita implicitamente novos cálculos, interpretação clínica ou inclusão no laudo.

## Extração e conferência

Fontes originais: `aux/vineland/Vineland3_AppMan_APX_{B,C,D,E}.pdf`. O importador trata páginas com texto rotacionado, confere os dois marcadores laterais das conversões, número de linhas/páginas, cabeçalhos, ICs e campos numéricos. Os arquivos são determinísticos e não incluem data de geração.

```bash
# Regerar os CSVs e índices a partir dos quatro PDFs.
uv run --no-project --with pymupdf python -m apps.tests.vineland3.import_csv_tables

# Sem sobrescrever arquivos: conferir TODOS os CSVs e índices contra os PDFs
# portugueses e comparar as 21 tabelas com o apêndice inglês fornecido.
uv run --no-project --with pymupdf python -m apps.tests.vineland3.import_csv_tables --verify-english

# Regressão e integridade, sem precisar dos PDFs nem de PyMuPDF.
DATABASE_URL=sqlite:///:memory: DJANGO_ENV=local .venv/bin/python manage.py test \
  apps.tests.test_vineland_csv_tables apps.tests.test_vineland3 --noinput
```

Conferência concluída: **21 tabelas, 573 arquivos e 167.713 registros coincidentes**, comparando os valores das versões portuguesa/inglesa e desconsiderando apenas tradução dos rótulos e numeração física distinta das páginas. Não foram usadas fórmulas do Excel nem executadas macros.
