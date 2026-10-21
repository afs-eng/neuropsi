# Skill de Implementação do GAI no WAIS-III

## 1. Objetivo da skill

Implementar, no módulo do teste WAIS-III, o cálculo automático do Índice de Capacidade Geral, conhecido como GAI, e dos clusters clínicos derivados das tabelas C.1 a C.9.

O GAI deve ser usado como estimativa alternativa da habilidade intelectual geral quando o QI Total, QIT, apresentar baixa representatividade clínica por discrepâncias relevantes entre os índices fatoriais, especialmente quando Memória Operacional e/ou Velocidade de Processamento reduzem ou distorcem a interpretação global do funcionamento intelectual.

Esta skill deve orientar a IA/desenvolvedor a:

1. validar se o GAI pode ser calculado;
2. calcular a soma dos escores ponderados necessários;
3. consultar a tabela normativa correta;
4. retornar GAI, percentil, intervalo de confiança e classificação qualitativa;
5. emitir alertas interpretativos quando houver discrepâncias importantes;
6. disponibilizar análise por clusters quando QIT e GAI não forem interpretáveis.

## 2. Dados necessários no sistema

O sistema deve ter acesso aos seguintes dados já corrigidos do WAIS-III:

### Subtestes verbais

- Vocabulário, VC
- Semelhanças, SM
- Aritmética, AR
- Dígitos, DG
- Informação, IN
- Compreensão, CO
- Sequência de Números e Letras, SNL

### Subtestes de execução

- Completar Figuras, CF
- Códigos, CD
- Cubos, CB
- Raciocínio Matricial, RM
- Arranjo de Figuras, AF
- Procurar Símbolos, PS
- Armar Objetos, AO

Todos os valores usados no cálculo do GAI e dos clusters devem ser escores ponderados, não escores brutos.

## 3. Regra principal para cálculo do GAI

O GAI só deve ser calculado quando houver condição psicométrica mínima para combinar ICV e IOP.

### Critério obrigatório

Calcular a diferença absoluta entre ICV e IOP:

```python
abs(ICV - IOP)
```

### Decisão

- Se a diferença entre ICV e IOP for menor que 23 pontos, o GAI pode ser calculado e interpretado.
- Se a diferença entre ICV e IOP for igual ou maior que 23 pontos, o GAI não deve ser interpretado como estimativa confiável da habilidade intelectual geral.

Regra operacional:

```python
if abs(ICV - IOP) < 23:
    gai_interpretavel = True
else:
    gai_interpretavel = False
```

## 4. Cálculo do GAI

O GAI é calculado a partir da soma dos escores ponderados de três subtestes do ICV e três subtestes do IOP.

### Subtestes usados no GAI

ICV:

- Vocabulário, VC
- Semelhanças, SM
- Informação, IN

IOP:

- Completar Figuras, CF
- Cubos, CB
- Raciocínio Matricial, RM

### Fórmula da soma

```python
soma_gai = VC + SM + IN + CF + CB + RM
```

Depois de obter a soma, o sistema deve consultar a tabela C.1.

### Saída esperada da tabela C.1

A tabela C.1 deve retornar:

- soma dos 6 escores ponderados;
- GAI;
- percentil;
- intervalo de confiança inferior, 95%;
- intervalo de confiança superior, 95%.

Exemplo de estrutura esperada no banco ou CSV:

```csv
soma_6_ponderados,gai,percentil,ic_95_inferior,ic_95_superior
```

## 5. Tabelas normativas necessárias

O sistema deve carregar as tabelas C.1 a C.9 em arquivos separados ou abas separadas do Excel/XLSM.

### tabela_c1

Nome: WAIS-III General Ability Index, GAI.

Uso:

```python
soma_gai = VC + SM + IN + CF + CB + RM
```

Retorna:

- GAI;
- percentil;
- intervalo de confiança de 95%.

### tabela_c2

Nome: Fluid Reasoning, Gf.

Subtestes:

```python
soma_gf = RM + AF + AR
```

Uso clínico: raciocínio fluido, solução de problemas novos, raciocínio abstrato e análise relacional.

### tabela_c3

Nome: Visual Processing, Gv.

Subtestes:

```python
soma_gv = CB + CF
```

Uso clínico: processamento visual, análise visuoespacial e organização perceptiva.

### tabela_c4

Nome: Nonverbal Fluid Reasoning, Gf-nonverbal.

Subtestes:

```python
soma_gf_nao_verbal = RM + AF
```

Uso clínico: raciocínio fluido não verbal e análise de relações visuais.

### tabela_c5

Nome: Verbal Fluid Reasoning, Gf-verbal.

Subtestes:

```python
soma_gf_verbal = SM + CO
```

Uso clínico: raciocínio verbal, julgamento conceitual e abstração verbal.

### tabela_c6

Nome: Lexical Knowledge, Gc-LK.

Subtestes:

```python
soma_gc_lk = VC + SM
```

Uso clínico: conhecimento lexical, repertório verbal e formação de conceitos.

### tabela_c7

Nome: General Information, Gc-K0.

Subtestes:

```python
soma_gc_k0 = IN + CO
```

Uso clínico: conhecimento geral, julgamento prático e informações adquiridas.

### tabela_c8

Nome: Long-Term Memory, Gc-LTM.

Subtestes:

```python
soma_gc_ltm = VC + IN
```

Uso clínico: acesso a conhecimentos previamente aprendidos e recuperação de informações de longo prazo.

### tabela_c9

Nome: Short-Term Memory, Gsm-WM.

Subtestes:

```python
soma_gsm_wm = DG + SNL
```

Uso clínico: memória de curto prazo, memória operacional verbal, atenção sustentada e manipulação mental.

## 6. Classificação qualitativa

Após obter GAI ou cluster, o sistema deve classificar o escore padrão usando a mesma lógica dos índices Wechsler.

```python
def classificar_wechsler(valor: int) -> str:
    if valor <= 69:
        return "Extremamente Baixo"
    elif valor <= 79:
        return "Limítrofe"
    elif valor <= 89:
        return "Média Inferior"
    elif valor <= 109:
        return "Média"
    elif valor <= 119:
        return "Média Superior"
    elif valor <= 129:
        return "Superior"
    else:
        return "Muito Superior"
```

## 7. Validação de índices unitários e não unitários

O sistema deve verificar se cada índice é unitário. Um índice é considerado não unitário quando há diferença maior que 5 pontos ponderados entre os subtestes que o compõem.

### Exemplo para ICV

```python
subtestes_icv = [VC, SM, IN]
diferenca_icv = max(subtestes_icv) - min(subtestes_icv)
icv_unitario = diferenca_icv <= 5
```

### Exemplo para IOP

```python
subtestes_iop = [CF, CB, RM]
diferenca_iop = max(subtestes_iop) - min(subtestes_iop)
iop_unitario = diferenca_iop <= 5
```

### Regra interpretativa

- Diferença até 5 pontos ponderados: índice unitário.
- Diferença maior que 5 pontos ponderados: índice não unitário.
- Se houver três ou mais índices não unitários, o sistema deve recomendar análise por clusters e/ou análise por subtestes.

## 8. Quando calcular o GAI

O sistema deve calcular o GAI especialmente quando:

1. o QIT estiver disponível, mas houver discrepância clinicamente relevante entre índices;
2. ICV e IOP estiverem preservados ou próximos entre si;
3. IMO e/ou IVP estiverem significativamente inferiores a ICV e IOP;
4. o avaliador quiser uma estimativa menos influenciada por memória operacional e velocidade de processamento.

## 9. Quando não interpretar o GAI

O sistema deve bloquear ou sinalizar cautela quando:

1. a diferença entre ICV e IOP for igual ou maior que 23 pontos;
2. houver discrepância interna importante nos subtestes que formam o ICV ou IOP;
3. houver muitos índices não unitários;
4. os dados de algum subteste obrigatório estiverem ausentes;
5. o cálculo estiver sendo feito com escore bruto em vez de escore ponderado.

Mensagem sugerida:

> O GAI não deve ser interpretado como estimativa confiável da habilidade intelectual geral, pois a discrepância entre ICV e IOP é igual ou superior a 23 pontos. Recomenda-se análise por índices, clusters e subtestes.

## 10. Fluxo de implementação no sistema

### Entrada esperada

```json
{
  "VC": 13,
  "SM": 12,
  "IN": 11,
  "CF": 12,
  "CB": 13,
  "RM": 12,
  "AR": 10,
  "DG": 9,
  "SNL": 8,
  "CO": 11,
  "AF": 10,
  "ICV": 120,
  "IOP": 121,
  "IMO": 109,
  "IVP": 98,
  "QIT": 115
}
```

### Processamento

```python
def calcular_gai(dados, tabela_c1):
    obrigatorios = ["VC", "SM", "IN", "CF", "CB", "RM", "ICV", "IOP"]

    for campo in obrigatorios:
        if campo not in dados or dados[campo] is None:
            return {
                "calculado": False,
                "interpretavel": False,
                "erro": f"Campo obrigatório ausente: {campo}"
            }

    diferenca_icv_iop = abs(dados["ICV"] - dados["IOP"])

    soma_gai = (
        dados["VC"] + dados["SM"] + dados["IN"] +
        dados["CF"] + dados["CB"] + dados["RM"]
    )

    linha = tabela_c1.get(soma_gai)

    if linha is None:
        return {
            "calculado": False,
            "interpretavel": False,
            "erro": f"Soma GAI fora da tabela C.1: {soma_gai}"
        }

    gai = linha["gai"]

    return {
        "calculado": True,
        "soma_gai": soma_gai,
        "gai": gai,
        "percentil": linha["percentil"],
        "ic_95_inferior": linha["ic_95_inferior"],
        "ic_95_superior": linha["ic_95_superior"],
        "classificacao": classificar_wechsler(gai),
        "diferenca_icv_iop": diferenca_icv_iop,
        "interpretavel": diferenca_icv_iop < 23,
        "alerta": None if diferenca_icv_iop < 23 else "Diferença entre ICV e IOP igual ou superior a 23 pontos. GAI não interpretável."
    }
```

## 11. Cálculo dos clusters clínicos

Criar uma função genérica para consultar qualquer cluster.

```python
def consultar_cluster(nome_cluster, soma, tabela):
    linha = tabela.get(soma)

    if linha is None:
        return {
            "cluster": nome_cluster,
            "calculado": False,
            "erro": f"Soma fora da tabela normativa: {soma}"
        }

    escore = linha["escore"]

    return {
        "cluster": nome_cluster,
        "calculado": True,
        "soma": soma,
        "escore": escore,
        "percentil": linha["percentil"],
        "intervalo_confianca_95": linha["ic_95"],
        "classificacao": classificar_wechsler(escore)
    }
```

### Função principal para clusters

```python
def calcular_clusters(dados, tabelas):
    clusters = {}

    clusters["Gf"] = consultar_cluster(
        "Raciocínio Fluido - Gf",
        dados["RM"] + dados["AF"] + dados["AR"],
        tabelas["tabela_c2"]
    )

    clusters["Gv"] = consultar_cluster(
        "Processamento Visual - Gv",
        dados["CB"] + dados["CF"],
        tabelas["tabela_c3"]
    )

    clusters["Gf_nonverbal"] = consultar_cluster(
        "Raciocínio Fluido Não Verbal - Gf-nonverbal",
        dados["RM"] + dados["AF"],
        tabelas["tabela_c4"]
    )

    clusters["Gf_verbal"] = consultar_cluster(
        "Raciocínio Fluido Verbal - Gf-verbal",
        dados["SM"] + dados["CO"],
        tabelas["tabela_c5"]
    )

    clusters["Gc_LK"] = consultar_cluster(
        "Conhecimento Lexical - Gc-LK",
        dados["VC"] + dados["SM"],
        tabelas["tabela_c6"]
    )

    clusters["Gc_K0"] = consultar_cluster(
        "Informação Geral - Gc-K0",
        dados["IN"] + dados["CO"],
        tabelas["tabela_c7"]
    )

    clusters["Gc_LTM"] = consultar_cluster(
        "Memória de Longo Prazo - Gc-LTM",
        dados["VC"] + dados["IN"],
        tabelas["tabela_c8"]
    )

    clusters["Gsm_WM"] = consultar_cluster(
        "Memória de Curto Prazo / Memória Operacional - Gsm-WM",
        dados["DG"] + dados["SNL"],
        tabelas["tabela_c9"]
    )

    return clusters
```

## 12. Modelo de saída para o frontend

```json
{
  "gai": {
    "calculado": true,
    "soma_gai": 73,
    "valor": 114,
    "percentil": 82,
    "ic_95": {
      "inferior": 109,
      "superior": 119
    },
    "classificacao": "Média Superior",
    "interpretavel": true,
    "diferenca_icv_iop": 8,
    "alertas": []
  },
  "clusters": {
    "Gf": {
      "soma": 31,
      "valor": 102,
      "classificacao": "Média",
      "percentil": 55,
      "ic_95": "94-110"
    }
  }
}
```

## 13. Texto automático para o laudo quando o GAI for interpretável

Modelo:

> Observa-se que o Índice de Compreensão Verbal e o Índice de Organização Perceptual apresentam discrepância inferior ao ponto de corte estabelecido para inviabilizar a interpretação conjunta desses domínios. Dessa forma, essas pontuações podem ser combinadas para a obtenção do Índice de Capacidade Geral, GAI. O GAI difere do QIT por reduzir a influência direta das tarefas que exigem maior velocidade de processamento e memória operacional, refletindo de maneira mais específica as habilidades de raciocínio verbal, abstração conceitual e raciocínio perceptual não verbal.
>
> Neste caso, foi obtido GAI = {{gai}}, classificado como {{classificacao}}, com percentil {{percentil}} e intervalo de confiança de 95% entre {{ic_95_inferior}} e {{ic_95_superior}}. Esse resultado sugere que a habilidade intelectual geral, quando analisada com menor interferência de velocidade de processamento e memória operacional, situa-se na faixa {{classificacao}}.

## 14. Texto automático quando o QIT for frágil, mas o GAI for interpretável

Modelo:

> Embora o QIT tenha sido calculado, sua representatividade como indicador único do funcionamento intelectual global deve ser analisada com cautela, em razão das discrepâncias observadas entre os índices fatoriais. A diferença entre os índices de raciocínio e os índices de eficiência cognitiva pode indicar que variáveis como velocidade de processamento, atenção sustentada e memória operacional interferiram no desempenho global. Nessa condição, o GAI oferece uma estimativa mais estável das habilidades centrais de raciocínio, por ser composto pelos subtestes de Compreensão Verbal e Organização Perceptual.

## 15. Texto automático quando o GAI não for interpretável

Modelo:

> O GAI não foi interpretado como estimativa confiável da habilidade intelectual geral, pois a discrepância entre ICV e IOP foi de {{diferenca_icv_iop}} pontos, valor igual ou superior ao critério de cautela adotado. Nessa condição, recomenda-se a descrição do funcionamento cognitivo por índices, clusters e subtestes, evitando a utilização de um único escore global como síntese do desempenho intelectual.

## 16. Regras de qualidade e segurança dos dados

1. Nunca calcular GAI usando escores brutos.
2. Sempre usar escores ponderados corrigidos por idade antes de consultar as tabelas C.
3. Sempre validar se os seis subtestes obrigatórios do GAI estão preenchidos.
4. Sempre retornar alerta quando ICV e IOP diferirem em 23 pontos ou mais.
5. Sempre calcular classificação qualitativa a partir do escore padrão obtido na tabela.
6. Nunca substituir julgamento clínico por cálculo automático.
7. Sempre exibir no frontend: soma usada, tabela consultada, escore obtido, percentil, intervalo de confiança e classificação.
8. Se o QIT, o GAI e vários índices forem não interpretáveis, priorizar análise por clusters e subtestes.

## 17. Estrutura sugerida de arquivos

```text
backend/
  apps/
    tests/
      wais3/
        data/
          tabela_c1_gai.csv
          tabela_c2_gf.csv
          tabela_c3_gv.csv
          tabela_c4_gf_nonverbal.csv
          tabela_c5_gf_verbal.csv
          tabela_c6_gc_lk.csv
          tabela_c7_gc_k0.csv
          tabela_c8_gc_ltm.csv
          tabela_c9_gsm_wm.csv
        services/
          gai.py
          clusters.py
          classificacao.py
        schemas.py
        api.py
```

## 18. Testes obrigatórios de validação

Criar testes automatizados para:

1. GAI calculado corretamente quando ICV e IOP diferem menos de 23 pontos;
2. GAI bloqueado quando ICV e IOP diferem 23 pontos ou mais;
3. erro quando subteste obrigatório estiver ausente;
4. erro quando soma não existir na tabela C.1;
5. classificação qualitativa correta;
6. clusters C.2 a C.9 calculados corretamente;
7. alerta quando índice for não unitário;
8. recomendação de análise por clusters quando houver três ou mais índices não unitários.

## 19. Prompt para IA implementar no sistema

Use este prompt na IA da IDE:

> Implemente o módulo GAI do WAIS-III no backend Django. O cálculo deve usar exclusivamente escores ponderados dos subtestes. Para o GAI, some Vocabulário, Semelhanças, Informação, Completar Figuras, Cubos e Raciocínio Matricial. Consulte a tabela_c1_gai.csv para retornar GAI, percentil e intervalo de confiança. Antes de interpretar, valide se a diferença absoluta entre ICV e IOP é menor que 23 pontos. Se for igual ou maior que 23, calcule apenas para registro, mas marque como não interpretável e emita alerta. Também implemente os clusters C.2 a C.9 com suas respectivas somas de subtestes e tabelas normativas. Crie funções puras, testes unitários e respostas JSON claras para o frontend. Nunca use escores brutos para esses cálculos. Inclua classificação qualitativa Wechsler para todos os escores padrão.

