# Skill para IA – Módulo WAIS-III no Sistema Neuropsicológico

## 1. Objetivo da skill

Esta skill orienta a IA a implementar, revisar ou melhorar o módulo do teste **WAIS-III – Escala de Inteligência Wechsler para Adultos, Terceira Edição**, dentro do sistema de avaliação neuropsicológica.

O objetivo é permitir que o sistema:

1. registre os dados brutos dos subtestes;
2. converta os pontos brutos em escores ponderados, conforme faixa etária;
3. calcule QI Verbal, QI de Execução, QI Total e índices fatoriais;
4. gere percentis, intervalos de confiança e classificações qualitativas;
5. produza interpretação clínica descritiva para o laudo;
6. integre os resultados nas seções de Eficiência Intelectual, Linguagem, Funções Executivas, Memória Operacional, Gnosias e Praxias, Velocidade de Processamento, Conclusão Geral e Hipótese Diagnóstica.

## 2. Restrições legais e éticas

A IA não deve reproduzir integralmente, copiar, extrair ou reconstruir tabelas normativas protegidas por direitos autorais.

A IA pode:

- criar a estrutura de arquivos CSV;
- criar loaders para leitura das tabelas;
- criar funções de cálculo;
- criar validadores;
- criar interpretadores clínicos;
- criar templates vazios para importação;
- usar dados normativos somente quando fornecidos de forma autorizada pelo usuário e dentro do contexto legítimo de uso profissional.

A IA não deve:

- preencher automaticamente tabelas normativas do manual sem autorização;
- gerar banco normativo completo a partir de material protegido;
- expor tabelas normativas completas em respostas públicas;
- substituir o julgamento clínico do psicólogo.

## 3. Estrutura recomendada do módulo

Criar a seguinte estrutura no projeto Django:

```text
apps/tests/
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

  norms/
    wais3/
      raw_to_scaled/
        verbal/
          idade_16-17.csv
          idade_18-19.csv
          idade_20-29.csv
          idade_30-39.csv
          idade_40-49.csv
          idade_50-59.csv
          idade_60-64.csv
          idade_65-89.csv
          grupo_referencia_20-34.csv

        execucao/
          idade_16-17.csv
          idade_18-19.csv
          idade_20-29.csv
          idade_30-39.csv
          idade_40-49.csv
          idade_50-59.csv
          idade_60-64.csv
          idade_65-89.csv
          grupo_referencia_20-34.csv

      composite_scores/
        qi_verbal.csv
        qi_execucao.csv
        qi_total.csv
        compreensao_verbal.csv
        organizacao_perceptual.csv
        memoria_operacional.csv
        velocidade_processamento.csv

      supplementary/
        b1_diferencas_qi_indices_significancia.csv
        b2_frequencia_diferencas_qi_indices.csv
        b3_diferencas_subteste_media.csv
        b4_diferencas_entre_subtestes.csv
        b5_dispersao_subtestes.csv
        b6_digitos_ordem_direta_inversa.csv
        b7_diferenca_digitos_direta_inversa.csv

      psychometrics/
        consistencia_interna.csv
        estabilidade_teste_reteste.csv
        erro_padrao_medida.csv
```

## 4. Subtestes do WAIS-III

A IA deve considerar os seguintes subtestes:

### Subtestes verbais

```python
WAIS3_VERBAL_SUBTESTS = {
    "vocabulario": "Vocabulário",
    "semelhancas": "Semelhanças",
    "aritmetica": "Aritmética",
    "digitos": "Dígitos",
    "informacao": "Informação",
    "compreensao": "Compreensão",
    "sequencia_numeros_letras": "Sequência de Números e Letras",
}
```

### Subtestes de execução

```python
WAIS3_EXECUTION_SUBTESTS = {
    "completar_figuras": "Completar Figuras",
    "codigos": "Códigos",
    "cubos": "Cubos",
    "raciocinio_matricial": "Raciocínio Matricial",
    "arranjo_figuras": "Arranjo de Figuras",
    "procurar_simbolos": "Procurar Símbolos",
    "armar_objetos": "Armar Objetos",
}
```

## 5. Índices e composições

A IA deve utilizar a seguinte organização para cálculo dos índices:

```python
WAIS3_INDEXES = {
    "qi_verbal": {
        "label": "QI Verbal",
        "subtests": [
            "vocabulario",
            "semelhancas",
            "aritmetica",
            "digitos",
            "informacao",
            "compreensao",
        ],
    },
    "qi_execucao": {
        "label": "QI de Execução",
        "subtests": [
            "completar_figuras",
            "codigos",
            "cubos",
            "raciocinio_matricial",
            "arranjo_figuras",
        ],
    },
    "qi_total": {
        "label": "QI Total",
        "subtests": [
            "vocabulario",
            "semelhancas",
            "aritmetica",
            "digitos",
            "informacao",
            "compreensao",
            "completar_figuras",
            "codigos",
            "cubos",
            "raciocinio_matricial",
            "arranjo_figuras",
        ],
    },
    "compreensao_verbal": {
        "label": "Índice de Compreensão Verbal",
        "subtests": [
            "vocabulario",
            "semelhancas",
            "informacao",
        ],
    },
    "organizacao_perceptual": {
        "label": "Índice de Organização Perceptual",
        "subtests": [
            "completar_figuras",
            "cubos",
            "raciocinio_matricial",
        ],
    },
    "memoria_operacional": {
        "label": "Índice de Memória Operacional",
        "subtests": [
            "aritmetica",
            "digitos",
            "sequencia_numeros_letras",
        ],
    },
    "velocidade_processamento": {
        "label": "Índice de Velocidade de Processamento",
        "subtests": [
            "codigos",
            "procurar_simbolos",
        ],
    },
}
```

Observação: a IA deve permitir que o sistema diferencie subtestes principais, suplementares e opcionais, sem impedir o registro de todos os subtestes.

## 6. Faixas etárias normativas

A IA deve reconhecer as seguintes faixas:

```python
WAIS3_AGE_RANGES = [
    {"key": "idade_16-17", "min_years": 16, "min_months": 0, "max_years": 17, "max_months": 11},
    {"key": "idade_18-19", "min_years": 18, "min_months": 0, "max_years": 19, "max_months": 11},
    {"key": "idade_20-29", "min_years": 20, "min_months": 0, "max_years": 29, "max_months": 11},
    {"key": "idade_30-39", "min_years": 30, "min_months": 0, "max_years": 39, "max_months": 11},
    {"key": "idade_40-49", "min_years": 40, "min_months": 0, "max_years": 49, "max_months": 11},
    {"key": "idade_50-59", "min_years": 50, "min_months": 0, "max_years": 59, "max_months": 11},
    {"key": "idade_60-64", "min_years": 60, "min_months": 0, "max_years": 64, "max_months": 11},
    {"key": "idade_65-89", "min_years": 65, "min_months": 0, "max_years": 89, "max_months": 11},
]
```

A IA deve validar que a idade esteja dentro do intervalo aceito para o WAIS-III.

## 7. Payload esperado

O sistema deve receber os pontos brutos dos subtestes:

```json
{
  "idade": {
    "anos": 42,
    "meses": 9
  },
  "subtestes": {
    "vocabulario": {"pontos_brutos": 38},
    "semelhancas": {"pontos_brutos": 24},
    "aritmetica": {"pontos_brutos": 14},
    "digitos": {"pontos_brutos": 15},
    "informacao": {"pontos_brutos": 18},
    "compreensao": {"pontos_brutos": 20},
    "sequencia_numeros_letras": {"pontos_brutos": 10},
    "completar_figuras": {"pontos_brutos": 17},
    "codigos": {"pontos_brutos": 55},
    "cubos": {"pontos_brutos": 32},
    "raciocinio_matricial": {"pontos_brutos": 21},
    "arranjo_figuras": {"pontos_brutos": 14},
    "procurar_simbolos": {"pontos_brutos": 28},
    "armar_objetos": {"pontos_brutos": 25}
  }
}
```

## 8. Payload computado

O sistema deve gerar:

```json
{
  "idade_normativa": "idade_40-49",
  "subtestes": {
    "vocabulario": {
      "pontos_brutos": 38,
      "escore_ponderado": 11,
      "classificacao": "Média"
    }
  },
  "indices": {
    "qi_verbal": {
      "soma_ponderada": 68,
      "pontuacao_composta": 107,
      "percentil": 68,
      "ic_90": "103-111",
      "ic_95": "102-112",
      "classificacao": "Média"
    }
  }
}
```

## 9. Classificação qualitativa

### Pontuação composta, QIs e índices

```python
def classify_composite_score(score: int) -> str:
    if score >= 130:
        return "Muito Superior"
    if score >= 120:
        return "Superior"
    if score >= 110:
        return "Média Superior"
    if score >= 90:
        return "Média"
    if score >= 80:
        return "Média Inferior"
    if score >= 70:
        return "Limítrofe"
    return "Extremamente Baixo"
```

### Escores ponderados dos subtestes

```python
def classify_scaled_score(score: int) -> str:
    if score >= 16:
        return "Muito Superior"
    if score >= 14:
        return "Superior"
    if score >= 12:
        return "Média Superior"
    if score >= 8:
        return "Média"
    if score >= 6:
        return "Média Inferior"
    if score >= 4:
        return "Limítrofe"
    return "Extremamente Baixo"
```

## 10. Regras de cálculo

A IA deve implementar o seguinte fluxo:

1. validar idade;
2. identificar faixa etária normativa;
3. validar pontos brutos;
4. carregar CSV correspondente ao subteste e faixa etária;
5. converter ponto bruto em escore ponderado;
6. calcular a soma ponderada de cada escala e índice;
7. consultar a tabela de pontuação composta;
8. retornar pontuação composta, percentil, intervalo de confiança e classificação;
9. gerar interpretação clínica;
10. salvar resultados em `computed_payload`.

## 11. Loader de normas

A IA deve criar funções de leitura com pandas ou csv nativo.

Exemplo de classe:

```python
from pathlib import Path
import pandas as pd


class WAIS3NormLoader:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def get_scaled_score(
        self,
        subtest_key: str,
        raw_score: int,
        age_range_key: str,
        domain: str,
    ) -> int:
        path = self.base_path / "raw_to_scaled" / domain / f"{age_range_key}.csv"
        df = pd.read_csv(path)

        if subtest_key not in df.columns:
            raise ValueError(f"Subteste não encontrado na tabela: {subtest_key}")

        for _, row in df.iterrows():
            interval = str(row[subtest_key]).strip()

            if self._raw_score_matches_interval(raw_score, interval):
                return int(row["escore_ponderado"])

        raise ValueError(
            f"Não foi encontrada conversão para {subtest_key}, bruto={raw_score}, faixa={age_range_key}"
        )

    def get_composite_score(self, index_key: str, scaled_sum: int) -> dict:
        path = self.base_path / "composite_scores" / f"{index_key}.csv"
        df = pd.read_csv(path)

        match = df[df["soma_ponderada"] == scaled_sum]
        if match.empty:
            raise ValueError(f"Soma ponderada não encontrada para {index_key}: {scaled_sum}")

        row = match.iloc[0]

        return {
            "pontuacao_composta": int(row["pontuacao_composta"]),
            "percentil": row["percentil"],
            "ic_90": row.get("ic_90"),
            "ic_95": row.get("ic_95"),
        }

    @staticmethod
    def _raw_score_matches_interval(raw_score: int, interval: str) -> bool:
        if not interval or interval in ["nan", "—", "-", ""]:
            return False

        interval = interval.replace("–", "-").replace("—", "-").strip()

        if "-" in interval:
            start, end = interval.split("-", 1)
            return int(start) <= raw_score <= int(end)

        return raw_score == int(interval)
```

## 12. Validações obrigatórias

A IA deve validar:

- idade mínima e máxima;
- ausência de subtestes obrigatórios para cálculo dos QIs;
- pontos brutos negativos;
- subtestes com campos vazios;
- faixa etária sem tabela correspondente;
- soma ponderada inexistente nas tabelas compostas;
- subteste não encontrado no CSV;
- diferença entre tabela verbal e tabela de execução;
- uso indevido do grupo de referência para cálculo de QIs e índices.

O grupo de referência de 20 a 34 anos pode ser usado apenas para comparação clínica, não para cálculo oficial dos QIs e índices.

## 13. Interpretação clínica para o laudo

A IA deve gerar interpretações em linguagem técnica, descritiva e integrada, seguindo o estilo dos laudos do sistema.

Modelo:

```text
A avaliação da eficiência intelectual foi realizada por meio da Escala de Inteligência Wechsler para Adultos – Terceira Edição (WAIS-III), instrumento destinado à investigação do funcionamento intelectual global e de domínios cognitivos específicos. O desempenho de [nome] indicou funcionamento intelectual global classificado como [classificação], com QI Total de [valor], percentil [percentil] e intervalo de confiança de [IC].

O QI Verbal apresentou classificação [classificação], sugerindo [descrição clínica]. O QI de Execução situou-se em [classificação], indicando [descrição clínica]. A análise dos índices fatoriais revelou desempenho em Compreensão Verbal classificado como [classificação], Organização Perceptual como [classificação], Memória Operacional como [classificação] e Velocidade de Processamento como [classificação].

Em análise clínica, o perfil cognitivo observado deve ser compreendido a partir da relação entre os índices, da presença ou ausência de discrepâncias clinicamente relevantes e da integração com os demais instrumentos da avaliação neuropsicológica. Há hipótese diagnóstica de [preencher somente quando houver sustentação clínica e psicométrica suficiente].
```

## 14. Regras de escrita para o laudo

A IA deve seguir estas regras:

- usar apenas o primeiro nome do paciente nas análises;
- não iniciar conclusões com “Diante da análise integrada”;
- usar a expressão “Em análise clínica”;
- não usar travessões longos;
- não usar tabelas quando o usuário solicitar texto interpretativo;
- incluir “Hipótese Diagnóstica” dentro da conclusão;
- usar DSM-5-TR™ quando mencionar DSM;
- usar “hipótese diagnóstica” quando houver indicadores clínicos;
- manter linguagem técnica, clara e compatível com avaliação neuropsicológica.

## 15. Integração com o sistema

O módulo WAIS-III deve se integrar ao registry global:

```python
from apps.tests.wais3.config import WAIS3Module

TEST_REGISTRY = {
    "WAIS3": WAIS3Module(),
}
```

A classe `WAIS3Module` deve expor:

```python
class WAIS3Module:
    key = "WAIS3"
    name = "Escala de Inteligência Wechsler para Adultos – Terceira Edição"

    def validate(self, raw_payload: dict) -> None:
        ...

    def calculate(self, raw_payload: dict) -> dict:
        ...

    def interpret(self, computed_payload: dict, context: dict) -> str:
        ...
```

## 16. Integração com o laudo

O resultado do WAIS-III deve alimentar:

- Eficiência Intelectual;
- Linguagem;
- Funções Executivas;
- Gnosias e Praxias;
- Memória e Aprendizagem;
- Velocidade de Processamento;
- Conclusão Geral;
- Hipótese Diagnóstica.

A IA deve interpretar o WAIS-III como perfil cognitivo, e não apenas como “teste de QI”.

## 17. Interface recomendada

A tela do WAIS-III deve conter:

1. dados do paciente;
2. idade em anos e meses;
3. card de subtestes verbais;
4. card de subtestes de execução;
5. botão “Calcular”;
6. tabela de resultados por subteste;
7. tabela de QIs e índices;
8. campo de interpretação gerada;
9. botão “Enviar para o laudo”.

### Campos de entrada

Cada subteste deve ter:

- nome do subteste;
- ponto bruto;
- escore ponderado calculado;
- classificação;
- observações clínicas opcionais.

## 18. Saída visual recomendada

O sistema deve apresentar os resultados assim:

```text
Subteste | Ponto Bruto | Escore Ponderado | Classificação
```

E para os índices:

```text
Índice | Soma Ponderada | Pontuação Composta | Percentil | IC 90% | IC 95% | Classificação
```

## 19. Testes automatizados

A IA deve criar testes automatizados para:

- identificar faixa etária;
- converter intervalos de pontuação;
- classificar escore ponderado;
- classificar pontuação composta;
- calcular somas dos índices;
- impedir uso do grupo de referência em cálculo oficial;
- retornar erro quando CSV estiver ausente;
- retornar erro quando subteste obrigatório não estiver preenchido;
- validar payload mínimo.

## 20. Prompt operacional para a IA da IDE

Use este prompt para pedir a implementação:

```text
Implemente o módulo WAIS-III no sistema Django, seguindo a arquitetura modular de apps/tests. Crie a pasta apps/tests/wais3 com config.py, schemas.py, validators.py, loaders.py, norm_utils.py, calculators.py, classifiers.py, interpreters.py e constants.py. Crie também a estrutura apps/tests/norms/wais3 com raw_to_scaled, composite_scores, supplementary e psychometrics.

Não transcreva nem invente dados normativos. Use apenas CSVs já existentes ou templates vazios. O sistema deve receber pontos brutos dos subtestes, identificar a faixa etária, converter pontos brutos em escores ponderados a partir dos CSVs, calcular QI Verbal, QI de Execução, QI Total, Índice de Compreensão Verbal, Índice de Organização Perceptual, Índice de Memória Operacional e Índice de Velocidade de Processamento. Deve retornar pontuação composta, percentil, IC 90%, IC 95% e classificação qualitativa.

Implemente validadores robustos, loaders seguros, tratamento de erros, testes automatizados e interpretador clínico em linguagem técnica para laudo neuropsicológico. O texto deve usar “Em análise clínica”, evitar travessões longos e incluir hipótese diagnóstica apenas quando houver sustentação clínica e psicométrica.
```

## 21. Critério de qualidade

A implementação será considerada adequada quando:

- calcular corretamente os subtestes a partir dos CSVs;
- separar normas por faixa etária;
- calcular QIs e índices;
- gerar percentis e intervalos de confiança;
- impedir uso inadequado do grupo de referência;
- gerar interpretação clínica compatível com laudo neuropsicológico;
- não reproduzir material protegido;
- possuir testes automatizados;
- ser facilmente integrável ao fluxo de avaliação e laudo.
