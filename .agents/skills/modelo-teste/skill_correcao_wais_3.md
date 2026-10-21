# Skill de Correção do WAIS-III para Implementação no Sistema

## Análise do material WAIS-III 2020

O material **WAIS-III - Revisão das Normas Brasileiras 2020** funciona como base normativa para correção psicométrica do instrumento. Para implementação no sistema, ele deve ser tratado principalmente como um conjunto de tabelas normativas para:

1. Converter resultados brutos em escores ponderados.
2. Somar escores ponderados conforme as escalas e índices.
3. Converter somas em QI, índices fatoriais, percentis e intervalos de confiança.
4. Realizar análises complementares de discrepância, significância estatística, dispersão e confiabilidade.

O sistema não deve automatizar aplicação clínica, pontuação item a item, decisão diagnóstica ou interpretação isolada sem supervisão profissional. A implementação deve automatizar apenas a correção normativa e a organização psicométrica dos resultados.

## Objetivo da skill

Implementar o módulo de correção automatizada do **WAIS-III, Revisão das Normas Brasileiras 2020**, dentro do sistema neuropsicológico, permitindo que o profissional insira os resultados brutos dos subtestes, selecione ou calcule automaticamente a idade do paciente, converta os resultados para escores ponderados, calcule QI Verbal, QI de Execução, QI Total, índices fatoriais e análises complementares.

A IA deve implementar apenas a **correção normativa e cálculo psicométrico**. A aplicação, pontuação item a item, regras de início, reversão, interrupção e critérios qualitativos devem permanecer sob responsabilidade do profissional habilitado.

## Base normativa

Usar as tabelas brasileiras de atualização normativa do WAIS-III 2020.

O instrumento é composto por 14 subtestes. Os escores se organizam em quatro índices:

- Índice de Compreensão Verbal, ICV.
- Índice de Organização Perceptual, IOP.
- Índice de Memória Operacional, IMO.
- Índice de Velocidade de Processamento, IVP.

A Escala Verbal deriva dos subtestes verbais principais. A Escala de Execução deriva dos subtestes de execução principais. O QI Total representa a estimativa global da capacidade intelectual a partir da soma dos subtestes principais.

## Subtestes do WAIS-III

O sistema deve cadastrar os 14 subtestes:

1. Completar Figuras.
2. Vocabulário.
3. Códigos.
4. Semelhanças.
5. Cubos.
6. Aritmética.
7. Raciocínio Matricial.
8. Dígitos.
9. Informação.
10. Arranjo de Figuras.
11. Compreensão.
12. Procurar Símbolos.
13. Sequência de Números e Letras.
14. Armar Objetos.

## Fluxo oficial de correção no sistema

### 1. Calcular idade cronológica

O sistema deve calcular a idade do paciente na data da avaliação.

Campos necessários:

```text
data_nascimento
data_avaliacao
idade_anos
idade_meses
faixa_etaria_normativa
```

Faixas normativas:

```text
16-17
18-19
20-29
30-39
40-49
50-59
60-64
65-89
```

Regra:

```text
Se idade entre 16 anos e 0 meses até 17 anos e 11 meses, usar faixa 16-17.
Se idade entre 18 anos e 0 meses até 19 anos e 11 meses, usar faixa 18-19.
Se idade entre 20 anos e 0 meses até 29 anos e 11 meses, usar faixa 20-29.
Se idade entre 30 anos e 0 meses até 39 anos e 11 meses, usar faixa 30-39.
Se idade entre 40 anos e 0 meses até 49 anos e 11 meses, usar faixa 40-49.
Se idade entre 50 anos e 0 meses até 59 anos e 11 meses, usar faixa 50-59.
Se idade entre 60 anos e 0 meses até 64 anos e 11 meses, usar faixa 60-64.
Se idade entre 65 anos e 0 meses até 89 anos e 11 meses, usar faixa 65-89.
```

Validação especial:

```text
Se idade for menor que 16 anos, bloquear correção pelo WAIS-III.
Se idade for maior que 89 anos e 11 meses, bloquear correção normativa.
Se idade for 16 anos, emitir alerta clínico sobre possível decisão entre WISC e WAIS conforme objetivo avaliativo.
```

### 2. Entrada dos resultados brutos

A tela deve permitir lançar o resultado bruto de cada subteste.

Modelo de campos:

```json
{
  "vocabulario_bruto": null,
  "semelhancas_bruto": null,
  "aritmetica_bruto": null,
  "digitos_bruto": null,
  "informacao_bruto": null,
  "compreensao_bruto": null,
  "sequencia_numeros_letras_bruto": null,
  "completar_figuras_bruto": null,
  "codigos_bruto": null,
  "cubos_bruto": null,
  "raciocinio_matricial_bruto": null,
  "arranjo_figuras_bruto": null,
  "procurar_simbolos_bruto": null,
  "armar_objetos_bruto": null
}
```

### 3. Converter bruto em escore ponderado

Usar a **Tabela A.1** conforme a faixa etária do paciente.

Estrutura recomendada do arquivo normativo:

```text
wais3_a1_bruto_para_ponderado.csv
```

Colunas:

```text
faixa_etaria
subteste
bruto_min
bruto_max
escore_ponderado
```

Exemplo de lógica:

```python
def converter_bruto_para_ponderado(faixa_etaria, subteste, bruto):
    linha = buscar_linha(
        tabela="A1",
        faixa_etaria=faixa_etaria,
        subteste=subteste,
        bruto_min__lte=bruto,
        bruto_max__gte=bruto
    )
    if not linha:
        raise ValueError("Resultado bruto fora da faixa normativa para este subteste e idade.")
    return linha.escore_ponderado
```

Regras obrigatórias:

```text
Intervalos devem ser tratados como inclusivos.
Exemplo: 10-13 significa bruto mínimo 10 e bruto máximo 13.
Células com travessão devem ser tratadas como valor inexistente ou não aplicável.
Nunca transformar travessão em zero.
```

### 4. Calcular somas de escores ponderados

Depois de converter todos os resultados brutos, calcular as somas.

#### Escala Verbal

```text
QI Verbal = soma dos escores ponderados de:
Vocabulário
Semelhanças
Aritmética
Dígitos
Informação
Compreensão
```

Depois converter a soma pela **Tabela A.3**.

#### Escala de Execução

```text
QI Execução = soma dos escores ponderados de:
Completar Figuras
Códigos
Cubos
Raciocínio Matricial
Arranjo de Figuras
```

Depois converter a soma pela **Tabela A.4**.

#### Escala Total

```text
QI Total = soma dos 11 subtestes principais:
Vocabulário
Semelhanças
Aritmética
Dígitos
Informação
Compreensão
Completar Figuras
Códigos
Cubos
Raciocínio Matricial
Arranjo de Figuras
```

Depois converter a soma pela **Tabela A.5**.

### 5. Calcular índices fatoriais

#### Índice de Compreensão Verbal, ICV

```text
ICV = Vocabulário + Semelhanças + Informação
```

Converter pela **Tabela A.6**.

#### Índice de Organização Perceptual, IOP

```text
IOP = Completar Figuras + Cubos + Raciocínio Matricial
```

Converter pela **Tabela A.7**.

#### Índice de Memória Operacional, IMO

```text
IMO = Aritmética + Dígitos + Sequência de Números e Letras
```

Converter pela **Tabela A.8**.

#### Índice de Velocidade de Processamento, IVP

```text
IVP = Códigos + Procurar Símbolos
```

Converter pela **Tabela A.9**.

### 6. Estrutura dos arquivos A.3 até A.9

Para as tabelas A.3 até A.9, usar a estrutura:

```text
tabela
soma_escores_ponderados
escore_composto
percentil
ic_90_min
ic_90_max
ic_95_min
ic_95_max
```

Exemplo:

```json
{
  "tabela": "A6",
  "soma_escores_ponderados": 30,
  "escore_composto": 100,
  "percentil": "50",
  "ic_90_min": 95,
  "ic_90_max": 105,
  "ic_95_min": 94,
  "ic_95_max": 106
}
```

O sistema deve preservar percentis como texto quando forem apresentados como:

```text
<0,1
99,9
>99,9
```

### 7. Classificação qualitativa dos escores compostos

Criar função configurável:

```python
def classificar_escore_composto(valor):
    if valor <= 69:
        return "Extremamente Baixo"
    if 70 <= valor <= 79:
        return "Limítrofe"
    if 80 <= valor <= 89:
        return "Média Inferior"
    if 90 <= valor <= 109:
        return "Média"
    if 110 <= valor <= 119:
        return "Média Superior"
    if 120 <= valor <= 129:
        return "Superior"
    if valor >= 130:
        return "Muito Superior"
```

Aplicar essa classificação para:

```text
QI Verbal
QI Execução
QI Total
ICV
IOP
IMO
IVP
```

### 8. Resultado final esperado da correção

O backend deve retornar:

```json
{
  "idade": {
    "anos": 30,
    "meses": 4,
    "faixa_etaria": "30-39"
  },
  "subtestes": {
    "vocabulario": {
      "bruto": 45,
      "ponderado": 14
    }
  },
  "somas": {
    "soma_verbal": null,
    "soma_execucao": null,
    "soma_total": null,
    "soma_icv": null,
    "soma_iop": null,
    "soma_imo": null,
    "soma_ivp": null
  },
  "resultados_compostos": {
    "qi_verbal": {
      "soma": null,
      "escore": null,
      "percentil": null,
      "ic_90": null,
      "ic_95": null,
      "classificacao": null
    },
    "qi_execucao": {},
    "qi_total": {},
    "icv": {},
    "iop": {},
    "imo": {},
    "ivp": {}
  }
}
```

## Análises complementares

### Tabela B.1

Usar para verificar se a diferença entre QIs ou índices é estatisticamente significativa por idade e nível de significância.

Comparações:

```text
QIV-QIE
Compreensão Verbal - Organização Perceptual
Compreensão Verbal - Memória Operacional
Organização Perceptual - Velocidade de Processamento
Compreensão Verbal - Velocidade de Processamento
Organização Perceptual - Memória Operacional
Memória Operacional - Velocidade de Processamento
```

Regra:

```python
diferenca = abs(valor_1 - valor_2)
significativo = diferenca >= valor_critico_tabela_b1
```

### Tabela B.2

Usar para verificar a frequência acumulada das discrepâncias entre os índices. Isso permite informar se uma diferença é comum ou rara na amostra normativa.

### Tabela B.3

Usar para comparar o escore ponderado de um único subteste com a média ponderada do conjunto.

O sistema deve calcular:

```python
media_conjunto = soma_escores_ponderados / quantidade_subtestes
diferenca = escore_ponderado_subteste - media_conjunto
diferenca_absoluta = abs(diferenca)
```

Manter o sinal da diferença para interpretação clínica:

```text
positivo = subteste acima da média do conjunto
negativo = subteste abaixo da média do conjunto
```

### Tabela B.4

Usar para comparar pares de subtestes e verificar diferença estatisticamente significativa.

A matriz possui duas áreas:

```text
Diagonal inferior / área branca: alfa = 0,05
Diagonal superior / área cinza: alfa = 0,15
```

O sistema deve preservar essa lógica.

### Tabela B.5

Usar para analisar dispersão entre subtestes.

```python
dispersao = maior_escore_ponderado - menor_escore_ponderado
```

Calcular para:

```text
6 subtestes verbais
5 subtestes de execução
7 subtestes verbais
7 subtestes de execução
11 subtestes para QI
11 subtestes fatoriais
13 subtestes
14 subtestes
```

### Tabela B.6

Usar para análise de Dígitos Ordem Direta e Dígitos Ordem Inversa.

Campos adicionais:

```text
maximo_digitos_ordem_direta
maximo_digitos_ordem_inversa
```

### Tabela B.7

Usar para analisar a diferença entre máximo de dígitos na ordem direta e inversa.

```python
diferenca_digitos = maximo_direta - maximo_inversa
```

### Tabela 5.7

Usar como tabela psicométrica de consistência interna, Alfa de Cronbach, dos subtestes, QI e índices fatoriais.

### Tabela 5.8a e 5.8b

Usar como referência de estabilidade teste-reteste e distribuição da amostra submetida ao reteste.

### Tabela 5.9

Usar como tabela de erro padrão de medida por grupo etário. Pode ser exibida no relatório técnico ou usada para análises adicionais, mas os intervalos de confiança principais já vêm nas tabelas A.3 até A.9.

## Regras de validação obrigatórias

A IA deve implementar estas validações:

```text
1. Não calcular QI ou índice se algum subteste obrigatório estiver ausente.
2. Não transformar travessão em zero.
3. Não usar Tabela A.2 para cálculo formal de QI ou índices.
4. Não aceitar resultado bruto fora da faixa prevista na tabela normativa.
5. Não arredondar escores ponderados, pois eles são inteiros obtidos por tabela.
6. Não arredondar percentis textuais como <0,1 ou >99,9.
7. Preservar vírgula decimal na interface brasileira, mas usar ponto decimal internamente no backend.
8. Registrar qual tabela foi usada em cada conversão.
9. Registrar a faixa etária normativa usada.
10. Exibir alerta quando a idade for 16 anos, pois pode haver decisão clínica entre WISC e WAIS conforme objetivo da avaliação.
```

## Modelo de implementação no backend

### Entidades sugeridas

```python
class WAIS3Evaluation:
    patient
    evaluation_date
    age_years
    age_months
    age_band
    status

class WAIS3SubtestScore:
    evaluation
    subtest
    raw_score
    scaled_score

class WAIS3CompositeScore:
    evaluation
    composite_type
    sum_scaled_scores
    standard_score
    percentile
    ci90_low
    ci90_high
    ci95_low
    ci95_high
    classification

class WAIS3DiscrepancyAnalysis:
    evaluation
    comparison_type
    score_a
    score_b
    difference
    critical_15
    significant_15
    critical_05
    significant_05
    cumulative_frequency
```

### Arquivos normativos recomendados

```text
wais3_a1_raw_to_scaled.csv
wais3_a2_reference_group.csv
wais3_a3_verbal_iq.csv
wais3_a4_performance_iq.csv
wais3_a5_full_scale_iq.csv
wais3_a6_vci.csv
wais3_a7_poi.csv
wais3_a8_wmi.csv
wais3_a9_psi.csv
wais3_b1_critical_values.csv
wais3_b2_cumulative_discrepancies.csv
wais3_b3_subtest_mean_differences.csv
wais3_b4_pairwise_subtest_differences.csv
wais3_b5_subtest_dispersion.csv
wais3_b6_digits_direct_inverse.csv
wais3_b7_digits_difference.csv
wais3_5_7_internal_consistency.csv
wais3_5_8a_stability.csv
wais3_5_8b_retest_sample.csv
wais3_5_9_sem.csv
```

## Prompt pronto para a IA da IDE

```text
Você é uma IA desenvolvedora responsável por implementar o módulo de correção do WAIS-III no sistema neuropsicológico.

Implemente a correção normativa do WAIS-III, Revisão das Normas Brasileiras 2020, usando arquivos CSV/XLSX locais já transcritos das tabelas normativas. Não hardcode os valores normativos no código. A correção deve ser inteiramente orientada por tabelas.

Fluxo obrigatório:

1. Calcular idade cronológica do paciente na data da avaliação.
2. Definir faixa etária normativa:
   16-17, 18-19, 20-29, 30-39, 40-49, 50-59, 60-64 ou 65-89.
3. Receber os resultados brutos dos 14 subtestes:
   Vocabulário, Semelhanças, Aritmética, Dígitos, Informação, Compreensão, Sequência de Números e Letras, Completar Figuras, Códigos, Cubos, Raciocínio Matricial, Arranjo de Figuras, Procurar Símbolos e Armar Objetos.
4. Converter cada resultado bruto em escore ponderado usando a Tabela A.1 correspondente à faixa etária do paciente.
5. Calcular:
   QI Verbal = Vocabulário + Semelhanças + Aritmética + Dígitos + Informação + Compreensão.
   QI Execução = Completar Figuras + Códigos + Cubos + Raciocínio Matricial + Arranjo de Figuras.
   QI Total = soma dos 11 subtestes principais usados em QI Verbal e QI Execução.
   ICV = Vocabulário + Semelhanças + Informação.
   IOP = Completar Figuras + Cubos + Raciocínio Matricial.
   IMO = Aritmética + Dígitos + Sequência de Números e Letras.
   IVP = Códigos + Procurar Símbolos.
6. Converter as somas:
   A3 para QI Verbal.
   A4 para QI Execução.
   A5 para QI Total.
   A6 para Índice de Compreensão Verbal.
   A7 para Índice de Organização Perceptual.
   A8 para Índice de Memória Operacional.
   A9 para Índice de Velocidade de Processamento.
7. Retornar escore composto, percentil, intervalo de confiança de 90%, intervalo de confiança de 95% e classificação qualitativa.
8. Implementar análises complementares:
   B1 para diferenças estatisticamente significativas entre QIs e índices.
   B2 para frequência acumulada das discrepâncias.
   B3 para diferença entre subteste e média ponderada.
   B4 para diferença entre pares de subtestes.
   B5 para dispersão entre subtestes.
   B6 para porcentagens cumulativas de Dígitos Ordem Direta e Inversa.
   B7 para diferença entre máximo de dígitos em ordem direta e inversa.
   Tabela 5.7 para consistência interna.
   Tabela 5.8a e 5.8b para estabilidade teste-reteste e amostra de reteste.
   Tabela 5.9 para erro padrão de medida.

Validações obrigatórias:

- Não calcular QI ou índice se faltar subteste obrigatório.
- Não usar a Tabela A.2 para cálculo formal de QI ou índices. A Tabela A.2 deve aparecer apenas como comparação clínica opcional.
- Não converter células com travessão em zero.
- Tratar intervalos de pontuação como inclusivos.
- Preservar percentis textuais como <0,1 e >99,9.
- Registrar no banco qual tabela foi usada em cada conversão.
- Gerar alertas para idade fora da faixa normativa.
- Gerar alerta para paciente de 16 anos, pois pode haver decisão clínica entre WISC e WAIS conforme o objetivo da avaliação.

O resultado final da API deve retornar:
- idade calculada;
- faixa normativa;
- resultados brutos;
- escores ponderados;
- somas dos escores ponderados;
- QI Verbal;
- QI Execução;
- QI Total;
- ICV;
- IOP;
- IMO;
- IVP;
- percentis;
- intervalos de confiança;
- classificações;
- discrepâncias significativas;
- frequências acumuladas;
- dados psicométricos auxiliares quando solicitados.

O sistema deve permitir exportar os resultados para o laudo neuropsicológico com linguagem técnica, sem automatizar diagnóstico. O diagnóstico deve permanecer como hipótese clínica do profissional.
```

## Arquitetura recomendada

A melhor arquitetura é tratar o WAIS-III como **motor de correção por tabelas**, não como fórmula matemática.

Fluxo recomendado:

```text
Entrada clínica
→ Tabela A.1
→ Escores ponderados
→ Somas
→ Tabelas A.3-A.9
→ QI e índices
→ Tabelas B e 5.x
→ Análise complementar
→ Texto interpretativo
```

Esse modelo reduz erro de cálculo, facilita auditoria clínica e permite rastrear exatamente qual tabela foi usada em cada resultado.
