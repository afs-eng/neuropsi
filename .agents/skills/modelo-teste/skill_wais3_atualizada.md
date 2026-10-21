# Skill de Implementação do WAIS-III no Sistema Neuropsicológico

## Objetivo da skill

Implementar a correção do WAIS-III de forma automatizada, segura e auditável dentro do sistema, garantindo que os escores brutos sejam convertidos corretamente em escores ponderados por idade, que as somas fatoriais sejam calculadas sem incluir subtestes opcionais entre parênteses, e que os resultados sejam salvos em um `computed_payload` estruturado para posterior geração do laudo.

Esta skill deve ser usada pela IA/desenvolvedor sempre que for necessário implementar, corrigir, revisar ou auditar o módulo WAIS-III no sistema.

## Regra principal da correção

A correção do WAIS-III deve seguir esta sequência obrigatória:

1. Receber os escores brutos de cada subteste.
2. Identificar a idade cronológica do examinando.
3. Selecionar a tabela normativa `tabela_a1` correspondente à faixa etária do examinando.
4. Converter cada escore bruto em Escore Ponderado ajustado por idade.
5. Inserir cada Escore Ponderado no domínio correto.
6. Somar os Escores Ponderados por escala e por índice.
7. Calcular a Escala Total a partir da soma da Escala Verbal + Escala de Execução.
8. Calcular as médias dos escores ponderados quando necessário.
9. Nunca incluir nas somas os valores opcionais anotados entre parênteses.
10. Salvar o resultado final no `computed_payload`.

## Estrutura recomendada do módulo

O módulo WAIS-III deve seguir a mesma lógica modular já planejada para os demais testes do sistema, com CSVs separados em pasta normativa e lógica própria em pasta do instrumento.

```text
apps/tests/
  norms/
    wais3/
      tabela_a1/
        idade_16-0_17-11.csv
        idade_18-0_19-11.csv
        idade_20-0_24-11.csv
        idade_25-0_29-11.csv
        idade_30-0_34-11.csv
        idade_35-0_44-11.csv
        idade_45-0_54-11.csv
        idade_55-0_64-11.csv
        idade_65-0_69-11.csv
        idade_70-0_74-11.csv
        idade_75-0_79-11.csv
        idade_80-0_84-11.csv
        idade_85-0_89-11.csv

  wais3/
    __init__.py
    config.py
    schemas.py
    validators.py
    loaders.py
    norm_utils.py
    calculators.py
    classifiers.py
    interpreters.py
    constants.py
```

A arquitetura deve manter CSVs normativos separados da lógica do teste, seguindo o padrão modular já usado no sistema para testes, com `norms/`, `calculators.py`, `classifiers.py`, `interpreters.py` e registro global em `registry.py`.

## Subtestes do WAIS-III

Os subtestes que podem aparecer no protocolo são:

```text
Completar Figuras
Vocabulário
Códigos
Semelhanças
Cubos
Aritmética
Raciocínio Matricial
Dígitos
Informação
Arranjo de Figuras
Compreensão
Procurar Símbolos
Sequência Números-Letras
Armar Objetos
```

## Nomes internos padronizados

Usar nomes internos estáveis para evitar erro de digitação:

```python
SUBTEST_KEYS = {
    "completar_figuras": "Completar Figuras",
    "vocabulario": "Vocabulário",
    "codigos": "Códigos",
    "semelhancas": "Semelhanças",
    "cubos": "Cubos",
    "aritmetica": "Aritmética",
    "raciocinio_matricial": "Raciocínio Matricial",
    "digitos": "Dígitos",
    "informacao": "Informação",
    "arranjo_figuras": "Arranjo de Figuras",
    "compreensao": "Compreensão",
    "procurar_simbolos": "Procurar Símbolos",
    "sequencia_numeros_letras": "Sequência Números-Letras",
    "armar_objetos": "Armar Objetos",
}
```

## Entrada esperada no raw_payload

O `raw_payload` deve receber idade, data de nascimento, data da avaliação e escores brutos por subteste.

```json
{
  "idade_anos": 40,
  "idade_meses": 0,
  "data_avaliacao": "2026-04-25",
  "data_nascimento": "1986-04-25",
  "raw_scores": {
    "completar_figuras": 11,
    "vocabulario": 35,
    "codigos": 39,
    "semelhancas": 24,
    "cubos": 26,
    "aritmetica": 8,
    "raciocinio_matricial": 15,
    "digitos": 8,
    "informacao": 15,
    "arranjo_figuras": 9,
    "compreensao": 24,
    "procurar_simbolos": 14,
    "sequencia_numeros_letras": 3,
    "armar_objetos": 20
  }
}
```

## Seleção da tabela normativa por idade

A IA deve selecionar automaticamente a tabela `tabela_a1` correta com base na idade do examinando.

Exemplo:

```text
Paciente com 40 anos → usar tabela_a1 da faixa etária 35-0 a 44-11.
```

Regra:

```python
idade_total_meses = idade_anos * 12 + idade_meses
```

A tabela correta é aquela em que:

```python
idade_min_meses <= idade_total_meses <= idade_max_meses
```

## Conversão de escore bruto para Escore Ponderado

Depois de selecionada a tabela correta, cada escore bruto deve ser convertido no Escore Ponderado correspondente.

Exemplo obrigatório de validação:

```text
Paciente de 40 anos.
Subteste Semelhanças.
Escore Bruto = 24.
Tabela usada = tabela_a1 da faixa etária correspondente a 40 anos.
Resultado esperado: Escore Ponderado = 13.
```

Esse exemplo deve ser usado como teste unitário obrigatório. Se o sistema retornar valor diferente de 13 para esse caso, a conversão normativa está incorreta.

## Formato esperado dos CSVs da tabela_a1

Cada CSV da `tabela_a1` deve conter uma coluna de escore bruto e uma coluna para cada subteste disponível naquela tabela.

Exemplo:

```csv
escore_bruto,completar_figuras,vocabulario,codigos,semelhancas,cubos,aritmetica,raciocinio_matricial,digitos,informacao,arranjo_figuras,compreensao,procurar_simbolos,sequencia_numeros_letras,armar_objetos
0,,,,,,,,,,,,,,
1,,,,,,,,,,,,,,
2,,,,,,,,,,,,,,
...
24,,,,13,,,,,,,,,
```

A conversão deve procurar o escore bruto informado na linha `escore_bruto` e retornar o valor da coluna do subteste correspondente.

## Regra para valores ausentes

Se o escore bruto não existir na tabela ou a célula normativa estiver vazia:

1. O sistema não deve inventar valor.
2. O sistema deve retornar erro de validação.
3. O erro deve indicar subteste, escore bruto e tabela usada.

Exemplo:

```json
{
  "error": "Conversão normativa não encontrada",
  "subtest": "semelhancas",
  "raw_score": 24,
  "norm_table": "idade_35-0_44-11.csv"
}
```

## Regra crítica: não incluir notas entre parênteses

No protocolo do WAIS-III, alguns subtestes podem aparecer com valores entre parênteses, como:

```text
Procurar Símbolos = (9)
Sequência Números-Letras = (6)
Armar Objetos = (10)
```

Esses valores indicam subtestes opcionais/substitutos ou complementares conforme o protocolo. Eles não devem entrar automaticamente nas somas principais, exceto se houver regra explícita de substituição autorizada.

Regra prática para o sistema:

```text
Valor marcado como parenthetical = true → não entra nas somas principais.
Valor marcado como parenthetical = false → entra nas somas, se pertencer ao domínio obrigatório.
```

Exemplo de estrutura:

```json
{
  "scaled_scores": {
    "procurar_simbolos": {
      "value": 9,
      "parenthetical": true,
      "included_in_primary_sum": false
    },
    "sequencia_numeros_letras": {
      "value": 6,
      "parenthetical": true,
      "included_in_primary_sum": false
    },
    "armar_objetos": {
      "value": 10,
      "parenthetical": true,
      "included_in_primary_sum": false
    }
  }
}
```

## Somas obrigatórias dos Escores Ponderados

As somas devem ser calculadas apenas com Escores Ponderados válidos e incluídos.

### Escala Verbal

```text
Escala Verbal = Vocabulário + Semelhanças + Aritmética + Dígitos + Informação
```

Em código:

```python
verbal_sum = (
    vocabulario +
    semelhancas +
    aritmetica +
    digitos +
    informacao
)
```

### Escala de Execução

```text
Escala de Execução = Completar Figuras + Códigos + Cubos + Raciocínio Matricial + Arranjo de Figuras
```

Em código:

```python
execution_sum = (
    completar_figuras +
    codigos +
    cubos +
    raciocinio_matricial +
    arranjo_figuras
)
```

### ICV - Índice de Compreensão Verbal

```text
ICV = Vocabulário + Semelhanças + Informação
```

Em código:

```python
icv_sum = vocabulario + semelhancas + informacao
```

### IOP - Índice de Organização Perceptual

```text
IOP = Completar Figuras + Cubos + Raciocínio Matricial
```

Em código:

```python
iop_sum = completar_figuras + cubos + raciocinio_matricial
```

### IMO - Índice de Memória Operacional

```text
IMO = Aritmética + Dígitos + Sequência Números-Letras
```

Em código:

```python
imo_sum = aritmetica + digitos + sequencia_numeros_letras
```

Atenção: se `sequencia_numeros_letras` estiver entre parênteses e não tiver sido aplicada como subteste incluído no índice, ela não deve entrar na soma.

### IVP - Índice de Velocidade de Processamento

```text
IVP = Códigos + Procurar Símbolos
```

Em código:

```python
ivp_sum = codigos + procurar_simbolos
```

Atenção: se `procurar_simbolos` estiver entre parênteses e não tiver sido aplicado como subteste incluído no índice, ele não deve entrar na soma.

## Escala Total

A Escala Total deve ser calculada assim:

```text
Escala Total = Escala Verbal + Escala de Execução
```

Em código:

```python
total_sum = verbal_sum + execution_sum
```

Não calcular Escala Total somando todos os subtestes da tabela indiscriminadamente. A Escala Total é a soma da Escala Verbal e da Escala de Execução.

## Cálculo da média dos Escores Ponderados

Quando o protocolo solicitar a média:

```text
Média = Soma dos Escores Ponderados / Número de subtestes incluídos
```

### Média da Escala Verbal

```python
verbal_mean = verbal_sum / 5
```

### Média da Escala de Execução

```python
execution_mean = execution_sum / 5
```

### Média Total

```python
total_mean = total_sum / 10
```

A média deve considerar apenas os subtestes incluídos na soma principal. Não incluir subtestes entre parênteses.

## Exemplo com os valores da imagem fornecida

Considerando os Escores Ponderados visíveis no exemplo:

```text
Vocabulário = 11
Semelhanças = 13
Aritmética = 8
Dígitos = 7
Informação = 13

Completar Figuras = 12
Códigos = 10
Cubos = 11
Raciocínio Matricial = 13
Arranjo de Figuras = 12

Procurar Símbolos = (9), não incluir na soma principal da Escala de Execução.
Sequência Números-Letras = (6), não incluir na soma principal se estiver apenas como opcional.
Armar Objetos = (10), não incluir na soma principal.
```

### Resultado esperado

```text
Escala Verbal = 11 + 13 + 8 + 7 + 13 = 52
Escala de Execução = 12 + 10 + 11 + 13 + 12 = 58
Escala Total = 52 + 58 = 110
```

Observação: os valores acima seguem a regra informada nesta skill. Caso o protocolo físico apresente outro total manuscrito, o sistema deve priorizar a regra formal configurada e sinalizar divergência para revisão humana.

## Validações obrigatórias

O sistema deve validar:

1. Se a idade foi informada.
2. Se existe tabela normativa para a idade.
3. Se todos os subtestes obrigatórios foram preenchidos.
4. Se cada escore bruto foi convertido corretamente.
5. Se nenhum valor entre parênteses entrou indevidamente nas somas principais.
6. Se a Escala Total foi calculada como Verbal + Execução.
7. Se os índices ICV, IOP, IMO e IVP foram calculados com os subtestes corretos.
8. Se há divergência entre soma calculada e soma digitada manualmente, quando existir campo manual.

## Subtestes obrigatórios por domínio

```python
WAIS3_DOMAINS = {
    "verbal": [
        "vocabulario",
        "semelhancas",
        "aritmetica",
        "digitos",
        "informacao",
    ],
    "execucao": [
        "completar_figuras",
        "codigos",
        "cubos",
        "raciocinio_matricial",
        "arranjo_figuras",
    ],
    "icv": [
        "vocabulario",
        "semelhancas",
        "informacao",
    ],
    "iop": [
        "completar_figuras",
        "cubos",
        "raciocinio_matricial",
    ],
    "imo": [
        "aritmetica",
        "digitos",
        "sequencia_numeros_letras",
    ],
    "ivp": [
        "codigos",
        "procurar_simbolos",
    ],
}
```

## Função base para soma segura

```python
def sum_scaled_scores(scaled_scores: dict, subtests: list[str]) -> int:
    total = 0
    missing = []

    for subtest in subtests:
        item = scaled_scores.get(subtest)

        if item is None:
            missing.append(subtest)
            continue

        if item.get("parenthetical") is True:
            continue

        if item.get("included_in_primary_sum") is False:
            continue

        value = item.get("value")
        if value is None:
            missing.append(subtest)
            continue

        total += int(value)

    if missing:
        raise ValueError(f"Subtestes obrigatórios ausentes: {missing}")

    return total
```

## Conversor de escore bruto para Escore Ponderado

```python
def convert_raw_to_scaled(norm_df, subtest_key: str, raw_score: int) -> int:
    row = norm_df.loc[norm_df["escore_bruto"] == raw_score]

    if row.empty:
        raise ValueError(
            f"Escore bruto {raw_score} não encontrado na tabela normativa para {subtest_key}."
        )

    value = row.iloc[0].get(subtest_key)

    if value is None or str(value).strip() == "" or str(value).lower() == "nan":
        raise ValueError(
            f"Escore ponderado não encontrado para subteste {subtest_key}, escore bruto {raw_score}."
        )

    return int(value)
```

## Estrutura esperada do computed_payload

```json
{
  "test": "WAIS-III",
  "age": {
    "years": 40,
    "months": 0,
    "total_months": 480,
    "norm_table": "idade_35-0_44-11.csv"
  },
  "raw_scores": {
    "semelhancas": 24
  },
  "scaled_scores": {
    "semelhancas": {
      "value": 13,
      "parenthetical": false,
      "included_in_primary_sum": true
    }
  },
  "sums": {
    "verbal": 52,
    "execucao": 58,
    "escala_total": 110,
    "icv": 37,
    "iop": 36,
    "imo": 21,
    "ivp": 19
  },
  "means": {
    "verbal": 10.4,
    "execucao": 11.6,
    "total": 11.0
  },
  "warnings": []
}
```

## Regras para o frontend

A tela do WAIS-III deve conter:

1. Campo para idade ou cálculo automático pela data de nascimento.
2. Campo de escore bruto para cada subteste.
3. Exibição automática do Escore Ponderado após salvar/calcular.
4. Indicação visual dos subtestes opcionais.
5. Checkbox ou seletor para indicar se um subteste opcional deve entrar ou não em alguma substituição autorizada.
6. Campo bloqueado para as somas automáticas.
7. Campo bloqueado para médias automáticas.
8. Alerta quando houver divergência entre soma esperada e soma manual.

## Regra de segurança clínica

O sistema não deve permitir que a IA altere os valores normativos. A IA pode:

1. Ler tabelas normativas.
2. Aplicar regras de cálculo.
3. Gerar interpretações textuais.
4. Sinalizar inconsistências.

A IA não pode:

1. Inventar escore ponderado.
2. Corrigir manualmente tabela normativa sem autorização.
3. Substituir subteste opcional sem regra explícita.
4. Gerar QI ou índice composto sem consultar a tabela de conversão correspondente.

## Testes unitários obrigatórios

### Teste 1: conversão normativa

```python
def test_semelhancas_40_anos_raw_24_scaled_13():
    result = convert_wais3_raw_to_scaled(
        age_years=40,
        age_months=0,
        subtest_key="semelhancas",
        raw_score=24,
    )
    assert result == 13
```

### Teste 2: soma verbal

```python
def test_verbal_sum():
    scaled_scores = {
        "vocabulario": {"value": 11, "parenthetical": False, "included_in_primary_sum": True},
        "semelhancas": {"value": 13, "parenthetical": False, "included_in_primary_sum": True},
        "aritmetica": {"value": 8, "parenthetical": False, "included_in_primary_sum": True},
        "digitos": {"value": 7, "parenthetical": False, "included_in_primary_sum": True},
        "informacao": {"value": 13, "parenthetical": False, "included_in_primary_sum": True},
    }
    assert sum_scaled_scores(scaled_scores, WAIS3_DOMAINS["verbal"]) == 52
```

### Teste 3: não incluir parênteses

```python
def test_parenthetical_values_are_not_included():
    scaled_scores = {
        "codigos": {"value": 10, "parenthetical": False, "included_in_primary_sum": True},
        "procurar_simbolos": {"value": 9, "parenthetical": True, "included_in_primary_sum": False},
    }
    assert sum_scaled_scores(scaled_scores, WAIS3_DOMAINS["ivp"]) == 10
```

### Teste 4: escala total

```python
def test_total_sum():
    verbal_sum = 52
    execution_sum = 58
    assert verbal_sum + execution_sum == 110
```

## Prompt para a IA implementar o WAIS-III

Use o seguinte prompt quando for pedir para a IA da IDE implementar o módulo:

```text
Implemente o módulo WAIS-III no app de testes do sistema Django, seguindo arquitetura modular em apps/tests/wais3/ e normas em apps/tests/norms/wais3/tabela_a1/.

O módulo deve:
1. Receber escores brutos por subteste no raw_payload.
2. Calcular idade em anos, meses e total de meses.
3. Selecionar automaticamente o CSV normativo tabela_a1 adequado à idade.
4. Converter escores brutos em Escores Ponderados por idade.
5. Usar como validação obrigatória: paciente de 40 anos, Semelhanças bruto 24 deve resultar em Escore Ponderado 13.
6. Calcular as somas:
   - Escala Verbal = Vocabulário + Semelhanças + Aritmética + Dígitos + Informação.
   - Escala de Execução = Completar Figuras + Códigos + Cubos + Raciocínio Matricial + Arranjo de Figuras.
   - ICV = Vocabulário + Semelhanças + Informação.
   - IOP = Completar Figuras + Cubos + Raciocínio Matricial.
   - IMO = Aritmética + Dígitos + Sequência Números-Letras.
   - IVP = Códigos + Procurar Símbolos.
7. Calcular Escala Total = Escala Verbal + Escala de Execução.
8. Calcular médias: verbal, execução e total, considerando apenas os subtestes incluídos.
9. Não incluir nas somas principais valores entre parênteses, exceto se houver regra explícita de substituição autorizada.
10. Salvar tudo em computed_payload com raw_scores, scaled_scores, sums, means, norm_table e warnings.
11. Criar validators.py, loaders.py, norm_utils.py, calculators.py, classifiers.py, interpreters.py, constants.py e config.py.
12. Criar testes unitários para conversão normativa, somas, exclusão de parênteses e Escala Total.
13. Nunca inventar valor normativo; se não encontrar valor na tabela, retornar erro de validação claro.
```

## Checklist de auditoria

Antes de considerar o WAIS-III pronto, conferir:

```text
[ ] A idade seleciona a tabela_a1 correta.
[ ] A conversão bruto → ponderado está funcionando.
[ ] Semelhanças bruto 24 em paciente de 40 anos retorna ponderado 13.
[ ] Escala Verbal usa apenas os 5 subtestes corretos.
[ ] Escala de Execução usa apenas os 5 subtestes corretos.
[ ] ICV usa os 3 subtestes corretos.
[ ] IOP usa os 3 subtestes corretos.
[ ] IMO usa os 3 subtestes corretos.
[ ] IVP usa os 2 subtestes corretos.
[ ] Valores entre parênteses não entram nas somas principais.
[ ] Escala Total é Verbal + Execução.
[ ] O computed_payload está completo.
[ ] Existem testes unitários.
[ ] O frontend mostra os campos calculados como bloqueados.
[ ] O sistema emite warnings em caso de divergência.
```

## Conversão das somas ponderadas em QIs e Índices Fatoriais

Após calcular as somas dos Escores Ponderados, o WAIS-III exige uma segunda etapa de correção: converter essas somas em QI, Índice Fatorial, percentil e intervalo de confiança. Essa conversão não deve ser feita por fórmula, média, regra de três ou estimativa. Ela deve consultar obrigatoriamente as tabelas normativas A.3 a A.9.

### Sequência obrigatória da segunda etapa

1. Calcular as somas dos Escores Ponderados.
2. Identificar qual resultado será convertido.
3. Selecionar a tabela correta entre A.3 e A.9.
4. Localizar a linha correspondente à soma dos Escores Ponderados.
5. Retornar o valor padronizado correspondente.
6. Retornar também percentil e intervalo de confiança de 95%, quando a tabela trouxer esses dados.
7. Salvar esses resultados no `computed_payload`.

## Tabelas de conversão A.3 a A.9

Usar as tabelas da seguinte forma:

```text
Tabela A.3 → Conversão da soma da Escala Verbal em QI Verbal (QIV)
Tabela A.4 → Conversão da soma da Escala de Execução em QI de Execução (QIE)
Tabela A.5 → Conversão da soma da Escala Total em QI Total (QIT)
Tabela A.6 → Conversão da soma do ICV em Índice de Compreensão Verbal
Tabela A.7 → Conversão da soma do IOP em Índice de Organização Perceptual
Tabela A.8 → Conversão da soma do IMO em Índice de Memória Operacional
Tabela A.9 → Conversão da soma do IVP em Índice de Velocidade de Processamento
```

A IA deve tratar essas tabelas como tabelas normativas fixas. Não é permitido inferir valores ausentes.

## Estrutura recomendada para as tabelas A.3 a A.9

Adicionar as tabelas de conversão na pasta normativa do WAIS-III:

```text
apps/tests/norms/wais3/
  tabela_a1/
    idade_16-0_17-11.csv
    idade_18-0_19-11.csv
    idade_20-0_24-11.csv
    idade_25-0_29-11.csv
    idade_30-0_34-11.csv
    idade_35-0_44-11.csv
    idade_45-0_54-11.csv
    idade_55-0_64-11.csv
    idade_65-0_69-11.csv
    idade_70-0_74-11.csv
    idade_75-0_79-11.csv
    idade_80-0_84-11.csv
    idade_85-0_89-11.csv

  conversions/
    tabela_a3_qiv.csv
    tabela_a4_qie.csv
    tabela_a5_qit.csv
    tabela_a6_icv.csv
    tabela_a7_iop.csv
    tabela_a8_imo.csv
    tabela_a9_ivp.csv
```

## Formato esperado dos CSVs de conversão

Cada CSV das tabelas A.3 a A.9 deve ter, no mínimo, as seguintes colunas:

```csv
soma_escores_ponderados,score_padronizado,percentil,ic_95_min,ic_95_max
```

Exemplo estrutural:

```csv
soma_escores_ponderados,score_padronizado,percentil,ic_95_min,ic_95_max
65,105,63,99,111
```

Importante: o exemplo acima representa apenas o formato esperado. O sistema deve usar os valores reais das tabelas normativas cadastradas em CSV.

## Mapeamento interno dos índices compostos

Usar nomes internos fixos:

```python
WAIS3_COMPOSITE_TABLES = {
    "qiv": {
        "label": "QI Verbal",
        "sum_key": "verbal",
        "table": "tabela_a3_qiv.csv",
    },
    "qie": {
        "label": "QI de Execução",
        "sum_key": "execucao",
        "table": "tabela_a4_qie.csv",
    },
    "qit": {
        "label": "QI Total",
        "sum_key": "escala_total",
        "table": "tabela_a5_qit.csv",
    },
    "icv": {
        "label": "Índice de Compreensão Verbal",
        "sum_key": "icv",
        "table": "tabela_a6_icv.csv",
    },
    "iop": {
        "label": "Índice de Organização Perceptual",
        "sum_key": "iop",
        "table": "tabela_a7_iop.csv",
    },
    "imo": {
        "label": "Índice de Memória Operacional",
        "sum_key": "imo",
        "table": "tabela_a8_imo.csv",
    },
    "ivp": {
        "label": "Índice de Velocidade de Processamento",
        "sum_key": "ivp",
        "table": "tabela_a9_ivp.csv",
    },
}
```

## Função base para conversão de soma em QI ou Índice Fatorial

```python
def convert_sum_to_composite(conversion_df, sum_score: int) -> dict:
    row = conversion_df.loc[
        conversion_df["soma_escores_ponderados"] == int(sum_score)
    ]

    if row.empty:
        raise ValueError(
            f"Soma de escores ponderados {sum_score} não encontrada na tabela de conversão."
        )

    selected = row.iloc[0]

    return {
        "sum_score": int(sum_score),
        "standard_score": int(selected["score_padronizado"]),
        "percentile": float(selected["percentil"]),
        "confidence_interval_95": {
            "min": int(selected["ic_95_min"]),
            "max": int(selected["ic_95_max"]),
        },
    }
```

## Função para converter todos os compostos

```python
def compute_wais3_composites(sums: dict, conversion_tables: dict) -> dict:
    composites = {}

    for composite_key, config in WAIS3_COMPOSITE_TABLES.items():
        sum_key = config["sum_key"]
        table_name = config["table"]

        if sum_key not in sums:
            raise ValueError(f"Soma ausente para {composite_key}: {sum_key}")

        conversion_df = conversion_tables[table_name]
        composites[composite_key] = convert_sum_to_composite(
            conversion_df=conversion_df,
            sum_score=sums[sum_key],
        )
        composites[composite_key]["label"] = config["label"]
        composites[composite_key]["conversion_table"] = table_name

    return composites
```

## Exemplo com os valores da imagem fornecida

Considerando a tabela demonstrativa:

```text
Soma QIV = 65 → QIV = 105, Percentil = 63, IC 95% = 99 a 111
Soma QIE = 58 → QIE = 110, Percentil = 75, IC 95% = 99 a 119
Soma QIT = 123 → QIT = 107, Percentil = 68, IC 95% = 102 a 113
Soma ICV = 37 → ICV = 112, Percentil = 79, IC 95% = 104 a 120
Soma IOP = 36 → IOP = 111, Percentil = 77, IC 95% = 99 a 122
Soma IMO = 21 → IMO = 83, Percentil = 13, IC 95% = 74 a 94
Soma IVP = 19 → IVP = 97, Percentil = 47, IC 95% = 87 a 108
```

Esse exemplo deve ser usado como teste de integração da etapa de conversão das somas. Caso as tabelas CSV cadastradas retornem valores diferentes para as mesmas somas, o sistema deve sinalizar divergência para revisão dos CSVs normativos.

## computed_payload atualizado com QIs e Índices Fatoriais

O `computed_payload` final deve incluir as somas e os compostos convertidos:

```json
{
  "test": "WAIS-III",
  "sums": {
    "verbal": 65,
    "execucao": 58,
    "escala_total": 123,
    "icv": 37,
    "iop": 36,
    "imo": 21,
    "ivp": 19
  },
  "composites": {
    "qiv": {
      "label": "QI Verbal",
      "sum_score": 65,
      "standard_score": 105,
      "percentile": 63,
      "confidence_interval_95": {
        "min": 99,
        "max": 111
      },
      "conversion_table": "tabela_a3_qiv.csv"
    },
    "qie": {
      "label": "QI de Execução",
      "sum_score": 58,
      "standard_score": 110,
      "percentile": 75,
      "confidence_interval_95": {
        "min": 99,
        "max": 119
      },
      "conversion_table": "tabela_a4_qie.csv"
    },
    "qit": {
      "label": "QI Total",
      "sum_score": 123,
      "standard_score": 107,
      "percentile": 68,
      "confidence_interval_95": {
        "min": 102,
        "max": 113
      },
      "conversion_table": "tabela_a5_qit.csv"
    },
    "icv": {
      "label": "Índice de Compreensão Verbal",
      "sum_score": 37,
      "standard_score": 112,
      "percentile": 79,
      "confidence_interval_95": {
        "min": 104,
        "max": 120
      },
      "conversion_table": "tabela_a6_icv.csv"
    },
    "iop": {
      "label": "Índice de Organização Perceptual",
      "sum_score": 36,
      "standard_score": 111,
      "percentile": 77,
      "confidence_interval_95": {
        "min": 99,
        "max": 122
      },
      "conversion_table": "tabela_a7_iop.csv"
    },
    "imo": {
      "label": "Índice de Memória Operacional",
      "sum_score": 21,
      "standard_score": 83,
      "percentile": 13,
      "confidence_interval_95": {
        "min": 74,
        "max": 94
      },
      "conversion_table": "tabela_a8_imo.csv"
    },
    "ivp": {
      "label": "Índice de Velocidade de Processamento",
      "sum_score": 19,
      "standard_score": 97,
      "percentile": 47,
      "confidence_interval_95": {
        "min": 87,
        "max": 108
      },
      "conversion_table": "tabela_a9_ivp.csv"
    }
  }
}
```

## Classificação dos QIs e Índices Fatoriais

Após converter os compostos, classificar cada QI/Índice Fatorial pela tabela de classificação adotada no sistema.

Usar a seguinte classificação padrão para pontos compostos:

```text
≥ 130 → Muito Superior
120 a 129 → Superior
110 a 119 → Média Superior
90 a 109 → Média
80 a 89 → Média Inferior
70 a 79 → Limítrofe
≤ 69 → Extremamente Baixo
```

A classificação deve ser calculada a partir do `standard_score`, não da soma dos Escores Ponderados.

## Testes unitários obrigatórios para as tabelas A.3 a A.9

Adicionar os seguintes testes:

```python
def test_convert_qiv_sum_65_to_standard_score_105():
    result = convert_wais3_sum_to_composite(
        composite_key="qiv",
        sum_score=65,
    )
    assert result["standard_score"] == 105
    assert result["percentile"] == 63
    assert result["confidence_interval_95"] == {"min": 99, "max": 111}


def test_convert_qie_sum_58_to_standard_score_110():
    result = convert_wais3_sum_to_composite(
        composite_key="qie",
        sum_score=58,
    )
    assert result["standard_score"] == 110
    assert result["percentile"] == 75
    assert result["confidence_interval_95"] == {"min": 99, "max": 119}


def test_convert_qit_sum_123_to_standard_score_107():
    result = convert_wais3_sum_to_composite(
        composite_key="qit",
        sum_score=123,
    )
    assert result["standard_score"] == 107
    assert result["percentile"] == 68
    assert result["confidence_interval_95"] == {"min": 102, "max": 113}


def test_convert_factorial_indexes_from_example():
    expected = {
        "icv": {"sum": 37, "standard_score": 112, "percentile": 79, "ci": {"min": 104, "max": 120}},
        "iop": {"sum": 36, "standard_score": 111, "percentile": 77, "ci": {"min": 99, "max": 122}},
        "imo": {"sum": 21, "standard_score": 83, "percentile": 13, "ci": {"min": 74, "max": 94}},
        "ivp": {"sum": 19, "standard_score": 97, "percentile": 47, "ci": {"min": 87, "max": 108}},
    }

    for composite_key, data in expected.items():
        result = convert_wais3_sum_to_composite(
            composite_key=composite_key,
            sum_score=data["sum"],
        )
        assert result["standard_score"] == data["standard_score"]
        assert result["percentile"] == data["percentile"]
        assert result["confidence_interval_95"] == data["ci"]
```

## Regra crítica para evitar erro de implementação

A idade só é usada para converter escore bruto em Escore Ponderado pela tabela A.1. Depois que as somas dos Escores Ponderados são obtidas, a conversão para QIV, QIE, QIT, ICV, IOP, IMO e IVP deve usar as tabelas A.3 a A.9, conforme cada composto.

Não usar a tabela A.1 para gerar QI ou Índice Fatorial.
Não usar as tabelas A.3 a A.9 para converter escore bruto em Escore Ponderado.
Não calcular QI por média dos escores ponderados.
Não calcular percentil por fórmula no sistema.
Não calcular intervalo de confiança por fórmula, a menos que essa regra estatística seja explicitamente cadastrada e validada. Priorizar o valor já presente na tabela normativa.

## Observação final

Esta skill cobre o fluxo completo de correção quantitativa do WAIS-III: conversão de escores brutos em Escores Ponderados pela tabela A.1, cálculo das somas por escala/índice e conversão das somas em QIV, QIE, QIT, ICV, IOP, IMO e IVP pelas tabelas A.3 a A.9. Nenhuma etapa normativa deve ser estimada ou inferida pela IA.
