# skill_wais3_implementacao_django.md

## 1. Objetivo da skill

Implementar no sistema Django um módulo completo para o teste **WAIS-III**, capaz de:

1. Receber escores brutos e/ou escores ponderados dos subtestes.
2. Validar idade, dados obrigatórios e consistência dos campos.
3. Converter escores brutos em escores ponderados quando as tabelas normativas estiverem cadastradas.
4. Somar escores ponderados por escala e índice.
5. Converter somas em QI, índice, percentil e intervalo de confiança.
6. Verificar interpretabilidade do QI Total.
7. Calcular e interpretar o GAI quando necessário.
8. Verificar se cada índice é unitário.
9. Realizar análise por subtestes quando o índice não for unitário.
10. Realizar análise por clusters quando aplicável.
11. Gerar texto técnico automático, em padrão ouro, para a seção de eficiência intelectual do laudo.
12. Integrar o resultado ao `ReportAIService` e ao fluxo de regeneração de seções do laudo.

---

## 2. Estrutura recomendada de pastas

```text
apps/tests/
  registry.py
  services/
    scoring_service.py
    interpretation_service.py

  norms/
    wais3/
      raw_to_scaled/
        tabela_a1.csv
        tabela_a2.csv
        tabela_a3.csv
        tabela_a4.csv
        tabela_a5.csv
      composites/
        verbal_qi.csv
        performance_qi.csv
        qit.csv
        icv.csv
        iop.csv
        imo.csv
        ivp.csv
        gai_c1.csv
      clusters/
        tabela_c2_gf.csv
        tabela_c3_gv.csv
        tabela_c4_gf_nonverbal.csv
        tabela_c5_gf_verbal.csv
        tabela_c6_gc_vl.csv
        tabela_c7_gc_k0.csv
        tabela_c8_gc_ltm.csv
        tabela_c9_gsm_wm.csv

  wais3/
    __init__.py
    config.py
    constants.py
    schemas.py
    validators.py
    loaders.py
    calculators.py
    classifiers.py
    interpreters.py
```

---

## 3. Siglas padronizadas dos subtestes

```python
WAIS3_SUBTESTS = {
    "VC": "Vocabulário",
    "SM": "Semelhanças",
    "IN": "Informação",
    "CO": "Compreensão",
    "AR": "Aritmética",
    "DG": "Dígitos",
    "SNL": "Sequência de Números e Letras",
    "CF": "Completar Figuras",
    "CD": "Códigos",
    "CB": "Cubos",
    "RM": "Raciocínio Matricial",
    "AF": "Arranjo de Figuras",
    "AO": "Armar Objetos",
    "PS": "Procurar Símbolos"
}
```

---

## 4. Composição das escalas e índices

### 4.1 Escala Verbal

```python
VERBAL_SCALE = ["VC", "SM", "AR", "DG", "IN"]
```

### 4.2 Escala de Execução

```python
PERFORMANCE_SCALE = ["CF", "CD", "CB", "RM", "AF"]
```

### 4.3 Índice de Compreensão Verbal, ICV

```python
ICV = ["VC", "SM", "IN"]
```

### 4.4 Índice de Organização Perceptual, IOP

```python
IOP = ["CF", "CB", "RM"]
```

### 4.5 Índice de Memória Operacional, IMO

```python
IMO = ["AR", "DG", "SNL"]
```

### 4.6 Índice de Velocidade de Processamento, IVP

```python
IVP = ["CD", "PS"]
```

### 4.7 GAI

```python
GAI_SUBTESTS = ["VC", "SM", "IN", "CF", "CB", "RM"]
```

---

## 5. `schemas.py`

O schema deve aceitar escores brutos, escores ponderados ou ambos.

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class WAIS3RawScores(BaseModel):
    VC: Optional[int] = None
    SM: Optional[int] = None
    IN: Optional[int] = None
    CO: Optional[int] = None
    AR: Optional[int] = None
    DG: Optional[int] = None
    SNL: Optional[int] = None
    CF: Optional[int] = None
    CD: Optional[int] = None
    CB: Optional[int] = None
    RM: Optional[int] = None
    AF: Optional[int] = None
    AO: Optional[int] = None
    PS: Optional[int] = None


class WAIS3ScaledScores(BaseModel):
    VC: Optional[int] = Field(None, ge=1, le=19)
    SM: Optional[int] = Field(None, ge=1, le=19)
    IN: Optional[int] = Field(None, ge=1, le=19)
    CO: Optional[int] = Field(None, ge=1, le=19)
    AR: Optional[int] = Field(None, ge=1, le=19)
    DG: Optional[int] = Field(None, ge=1, le=19)
    SNL: Optional[int] = Field(None, ge=1, le=19)
    CF: Optional[int] = Field(None, ge=1, le=19)
    CD: Optional[int] = Field(None, ge=1, le=19)
    CB: Optional[int] = Field(None, ge=1, le=19)
    RM: Optional[int] = Field(None, ge=1, le=19)
    AF: Optional[int] = Field(None, ge=1, le=19)
    AO: Optional[int] = Field(None, ge=1, le=19)
    PS: Optional[int] = Field(None, ge=1, le=19)


class WAIS3Input(BaseModel):
    patient_name: str
    age_years: int = Field(..., ge=16, le=89)
    age_months: Optional[int] = Field(0, ge=0, le=11)
    raw_scores: Optional[WAIS3RawScores] = None
    scaled_scores: Optional[WAIS3ScaledScores] = None
    observations: Optional[Dict[str, Any]] = None
```

---

## 6. `constants.py`

```python
INDEX_COMPOSITION = {
    "ICV": ["VC", "SM", "IN"],
    "IOP": ["CF", "CB", "RM"],
    "IMO": ["AR", "DG", "SNL"],
    "IVP": ["CD", "PS"],
}

SCALE_COMPOSITION = {
    "QIV": ["VC", "SM", "AR", "DG", "IN"],
    "QIE": ["CF", "CD", "CB", "RM", "AF"],
    "QIT": ["VC", "SM", "AR", "DG", "IN", "CF", "CD", "CB", "RM", "AF"],
}

GAI_SUBTESTS = ["VC", "SM", "IN", "CF", "CB", "RM"]

CLUSTERS = {
    "Gf": ["RM", "AF", "AR"],
    "Gv": ["CB", "CF"],
    "Gf_nonverbal": ["RM", "AF"],
    "Gf_verbal": ["SM", "CO"],
    "Gc_VL": ["VC", "SM"],
    "Gc_K0": ["CO", "IN"],
    "Gc_LTM": ["VC", "IN"],
    "Gsm_WM": ["SNL", "DG"],
}

CLUSTER_CRITICAL_VALUES = {
    ("Gf", "Gv"): 21,
    ("Gf_nonverbal", "Gv"): 21,
    ("Gf_nonverbal", "Gf_verbal"): 21,
    ("Gc_VL", "Gc_K0"): 16,
    ("Gc_LTM", "Gsm_WM"): 24,
    ("Gc_LTM", "Gf_verbal"): 16,
}

COMPOSITE_CLASSIFICATION = [
    (130, 999, "Muito Superior"),
    (120, 129, "Superior"),
    (110, 119, "Média Superior"),
    (90, 109, "Média"),
    (80, 89, "Média Inferior"),
    (70, 79, "Limítrofe"),
    (0, 69, "Extremamente Baixo"),
]

SCALED_CLASSIFICATION = [
    (16, 19, "Muito Superior"),
    (14, 15, "Superior"),
    (12, 13, "Média Superior"),
    (8, 11, "Média"),
    (6, 7, "Média Inferior"),
    (4, 5, "Limítrofe"),
    (1, 3, "Extremamente Baixo"),
]
```

---

## 7. `loaders.py`

Responsável por carregar CSVs normativos.

```python
from pathlib import Path
import pandas as pd
from functools import lru_cache


BASE_NORMS_PATH = Path(__file__).resolve().parents[1] / "norms" / "wais3"


@lru_cache(maxsize=64)
def load_norm_table(relative_path: str) -> pd.DataFrame:
    path = BASE_NORMS_PATH / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Tabela normativa não encontrada: {path}")

    return pd.read_csv(path)


def lookup_conversion(
    table_path: str,
    sum_score: int,
    sum_column: str = "soma",
) -> dict:
    df = load_norm_table(table_path)

    row = df[df[sum_column] == sum_score]
    if row.empty:
        raise ValueError(f"Soma {sum_score} não encontrada em {table_path}")

    return row.iloc[0].to_dict()
```

---

## 8. `classifiers.py`

```python
from .constants import COMPOSITE_CLASSIFICATION, SCALED_CLASSIFICATION


def classify_composite(score: int) -> str:
    for low, high, label in COMPOSITE_CLASSIFICATION:
        if low <= score <= high:
            return label
    return "Classificação não encontrada"


def classify_scaled(score: int) -> str:
    for low, high, label in SCALED_CLASSIFICATION:
        if low <= score <= high:
            return label
    return "Classificação não encontrada"
```

---

## 9. `calculators.py`

Este é o núcleo determinístico do WAIS-III.

```python
from typing import Dict, Any, Optional
from .constants import (
    INDEX_COMPOSITION,
    SCALE_COMPOSITION,
    GAI_SUBTESTS,
    CLUSTERS,
    CLUSTER_CRITICAL_VALUES,
)
from .classifiers import classify_composite, classify_scaled
from .loaders import lookup_conversion


class WAIS3CalculationError(Exception):
    pass


def require_scores(scaled_scores: Dict[str, Optional[int]], keys: list[str], label: str) -> None:
    missing = [key for key in keys if scaled_scores.get(key) is None]
    if missing:
        raise WAIS3CalculationError(
            f"Não é possível calcular {label}. Subtestes ausentes: {', '.join(missing)}"
        )


def sum_scores(scaled_scores: Dict[str, Optional[int]], keys: list[str], label: str) -> int:
    require_scores(scaled_scores, keys, label)
    return sum(int(scaled_scores[key]) for key in keys)


def is_unitary(scaled_scores: Dict[str, Optional[int]], keys: list[str]) -> dict:
    available = [int(scaled_scores[key]) for key in keys if scaled_scores.get(key) is not None]

    if len(available) != len(keys):
        return {
            "unitary": False,
            "difference": None,
            "reason": "Subtestes ausentes",
        }

    difference = max(available) - min(available)

    return {
        "unitary": difference < 5,
        "difference": difference,
        "max": max(available),
        "min": min(available),
    }


def calculate_composites(scaled_scores: Dict[str, Optional[int]]) -> Dict[str, Any]:
    output = {
        "sums": {},
        "composites": {},
        "indices_unitarity": {},
    }

    # QIV, QIE, QIT
    for composite, keys in SCALE_COMPOSITION.items():
        try:
            total = sum_scores(scaled_scores, keys, composite)
            output["sums"][composite] = total

            table_map = {
                "QIV": "composites/verbal_qi.csv",
                "QIE": "composites/performance_qi.csv",
                "QIT": "composites/qit.csv",
            }

            converted = lookup_conversion(table_map[composite], total)
            score = int(converted["score"])

            output["composites"][composite] = {
                "sum": total,
                "score": score,
                "classification": classify_composite(score),
                "percentile": converted.get("percentile"),
                "ci_95": converted.get("ci_95"),
            }
        except Exception as exc:
            output["composites"][composite] = {
                "error": str(exc)
            }

    # ICV, IOP, IMO, IVP
    for index, keys in INDEX_COMPOSITION.items():
        output["indices_unitarity"][index] = is_unitary(scaled_scores, keys)

        try:
            total = sum_scores(scaled_scores, keys, index)
            output["sums"][index] = total

            table_map = {
                "ICV": "composites/icv.csv",
                "IOP": "composites/iop.csv",
                "IMO": "composites/imo.csv",
                "IVP": "composites/ivp.csv",
            }

            converted = lookup_conversion(table_map[index], total)
            score = int(converted["score"])

            output["composites"][index] = {
                "sum": total,
                "score": score,
                "classification": classify_composite(score),
                "percentile": converted.get("percentile"),
                "ci_95": converted.get("ci_95"),
                "unitarity": output["indices_unitarity"][index],
            }
        except Exception as exc:
            output["composites"][index] = {
                "error": str(exc),
                "unitarity": output["indices_unitarity"][index],
            }

    return output


def determine_qit_interpretability(composites: Dict[str, Any]) -> Dict[str, Any]:
    required_indices = ["ICV", "IOP", "IMO", "IVP"]

    scores = []
    for index in required_indices:
        data = composites.get(index, {})
        if "score" not in data:
            return {
                "interpretable": False,
                "difference": None,
                "reason": f"Índice {index} ausente ou inválido",
            }
        scores.append(int(data["score"]))

    difference = max(scores) - min(scores)

    return {
        "interpretable": difference < 23,
        "difference": difference,
        "criterion": 23,
    }


def calculate_gai_if_needed(
    scaled_scores: Dict[str, Optional[int]],
    composites: Dict[str, Any],
    qit_interpretability: Dict[str, Any],
) -> Dict[str, Any]:
    icv = composites.get("ICV", {}).get("score")
    iop = composites.get("IOP", {}).get("score")

    if icv is None or iop is None:
        return {
            "calculated": False,
            "valid": False,
            "reason": "ICV ou IOP ausente",
        }

    icv_iop_difference = abs(int(icv) - int(iop))

    if qit_interpretability.get("interpretable") is True:
        return {
            "calculated": False,
            "valid": False,
            "reason": "QIT interpretável; GAI não é necessário",
            "icv_iop_difference": icv_iop_difference,
        }

    if icv_iop_difference >= 23:
        return {
            "calculated": False,
            "valid": False,
            "reason": "Diferença entre ICV e IOP igual ou superior a 23 pontos",
            "icv_iop_difference": icv_iop_difference,
        }

    total = sum_scores(scaled_scores, GAI_SUBTESTS, "GAI")
    converted = lookup_conversion("composites/gai_c1.csv", total)
    score = int(converted["score"])

    return {
        "calculated": True,
        "valid": True,
        "sum": total,
        "score": score,
        "classification": classify_composite(score),
        "percentile": converted.get("percentile"),
        "ci_95": converted.get("ci_95"),
        "icv_iop_difference": icv_iop_difference,
    }


def calculate_clusters(scaled_scores: Dict[str, Optional[int]]) -> Dict[str, Any]:
    clusters = {}

    table_map = {
        "Gf": "clusters/tabela_c2_gf.csv",
        "Gv": "clusters/tabela_c3_gv.csv",
        "Gf_nonverbal": "clusters/tabela_c4_gf_nonverbal.csv",
        "Gf_verbal": "clusters/tabela_c5_gf_verbal.csv",
        "Gc_VL": "clusters/tabela_c6_gc_vl.csv",
        "Gc_K0": "clusters/tabela_c7_gc_k0.csv",
        "Gc_LTM": "clusters/tabela_c8_gc_ltm.csv",
        "Gsm_WM": "clusters/tabela_c9_gsm_wm.csv",
    }

    for cluster_name, keys in CLUSTERS.items():
        unit = is_unitary(scaled_scores, keys)

        if not unit["unitary"]:
            clusters[cluster_name] = {
                "valid": False,
                "unitarity": unit,
                "reason": "Cluster não unitário ou com subtestes ausentes",
            }
            continue

        try:
            total = sum_scores(scaled_scores, keys, cluster_name)
            converted = lookup_conversion(table_map[cluster_name], total)
            score = int(converted["score"])

            clusters[cluster_name] = {
                "valid": True,
                "sum": total,
                "score": score,
                "classification": classify_composite(score),
                "percentile": converted.get("percentile"),
                "ci_95": converted.get("ci_95"),
                "unitarity": unit,
            }
        except Exception as exc:
            clusters[cluster_name] = {
                "valid": False,
                "unitarity": unit,
                "error": str(exc),
            }

    return clusters


def compare_clusters(clusters: Dict[str, Any]) -> list[dict]:
    results = []

    for (c1, c2), critical_value in CLUSTER_CRITICAL_VALUES.items():
        first = clusters.get(c1, {})
        second = clusters.get(c2, {})

        if not first.get("valid") or not second.get("valid"):
            results.append({
                "comparison": f"{c1} x {c2}",
                "valid": False,
                "reason": "Um ou ambos os clusters não são válidos/unitários",
                "critical_value": critical_value,
            })
            continue

        difference = abs(int(first["score"]) - int(second["score"]))

        results.append({
            "comparison": f"{c1} x {c2}",
            "valid": True,
            "difference": difference,
            "critical_value": critical_value,
            "result": "Incomum" if difference >= critical_value else "Não incomum",
        })

    return results


def calculate_wais3(payload: dict) -> dict:
    scaled_model = payload.get("scaled_scores") or {}
    scaled_scores = dict(scaled_model)

    composites_output = calculate_composites(scaled_scores)
    qit_interpretability = determine_qit_interpretability(composites_output["composites"])
    gai = calculate_gai_if_needed(
        scaled_scores=scaled_scores,
        composites=composites_output["composites"],
        qit_interpretability=qit_interpretability,
    )
    clusters = calculate_clusters(scaled_scores)
    cluster_comparisons = compare_clusters(clusters)

    return {
        "test": "WAIS-III",
        "scaled_scores": scaled_scores,
        "sums": composites_output["sums"],
        "composites": composites_output["composites"],
        "qit_interpretability": qit_interpretability,
        "gai": gai,
        "clusters": clusters,
        "cluster_comparisons": cluster_comparisons,
    }
```

---

## 10. `interpreters.py`

Gera o texto automático padrão ouro.

```python
from typing import Dict, Any


def _fmt_score(data: Dict[str, Any]) -> str:
    if not data or "score" not in data:
        return "resultado indisponível"
    return f'{data["score"]} ({data.get("classification", "sem classificação")})'


def interpret_qit(patient_name: str, result: Dict[str, Any]) -> str:
    composites = result["composites"]
    qit = composites.get("QIT", {})
    qit_interp = result["qit_interpretability"]

    if qit_interp.get("interpretable"):
        return (
            f"{patient_name} apresentou funcionamento intelectual global situado na faixa "
            f"{qit.get('classification', '').lower()}, com QI Total = {qit.get('score')}. "
            f"A diferença entre o maior e o menor índice fatorial foi de "
            f"{qit_interp.get('difference')} pontos, inferior ao critério de 23 pontos, "
            f"indicando que o QI Total pode ser interpretado como estimativa válida "
            f"e representativa da capacidade intelectual global."
        )

    gai = result.get("gai", {})

    if gai.get("valid"):
        return (
            f"{patient_name} apresentou QI Total = {qit.get('score')}, classificado como "
            f"{qit.get('classification', '').lower()}. Contudo, a diferença entre o maior "
            f"e o menor índice fatorial foi de {qit_interp.get('difference')} pontos, "
            f"igual ou superior ao critério técnico de 23 pontos, indicando que o QI Total "
            f"não deve ser utilizado como estimativa única e plenamente representativa "
            f"da capacidade intelectual global. Nessa condição, foi calculado o Índice de "
            f"Capacidade Geral, GAI = {gai.get('score')}, classificado como "
            f"{gai.get('classification', '').lower()}, por apresentar diferença entre ICV "
            f"e IOP inferior a 23 pontos. O GAI representa uma estimativa mais estável "
            f"das habilidades intelectuais gerais, com menor interferência da memória "
            f"operacional e da velocidade de processamento."
        )

    return (
        f"{patient_name} apresentou perfil cognitivo heterogêneo, com discrepâncias "
        f"clinicamente significativas entre os índices fatoriais. A diferença entre o maior "
        f"e o menor índice foi de {qit_interp.get('difference')} pontos, tornando o QI Total "
        f"pouco representativo como medida global. Além disso, o GAI não se mostrou "
        f"tecnicamente apropriado, pois a diferença entre ICV e IOP foi igual ou superior "
        f"ao critério de 23 pontos ou houve ausência de dados necessários. Dessa forma, "
        f"a interpretação deve priorizar os índices, subtestes e clusters clinicamente válidos."
    )


def interpret_indices(patient_name: str, result: Dict[str, Any]) -> str:
    composites = result["composites"]
    parts = []

    index_labels = {
        "ICV": "Índice de Compreensão Verbal",
        "IOP": "Índice de Organização Perceptual",
        "IMO": "Índice de Memória Operacional",
        "IVP": "Índice de Velocidade de Processamento",
    }

    index_functions = {
        "ICV": "habilidades de inteligência cristalizada, formação de conceitos verbais, repertório lexical, raciocínio verbal e acesso à memória semântica",
        "IOP": "raciocínio fluido não verbal, organização visuoespacial, análise perceptual e resolução de problemas novos",
        "IMO": "atenção sustentada, retenção temporária e manipulação mental de informações",
        "IVP": "rapidez de processamento visual, atenção visual sob limite de tempo, coordenação visuomotora e eficiência grafomotora",
    }

    for index, label in index_labels.items():
        data = composites.get(index, {})
        if "score" not in data:
            continue

        unit = data.get("unitarity", {})
        unit_text = (
            "unitário, permitindo interpretação do índice como medida relativamente homogênea"
            if unit.get("unitary")
            else "não unitário, exigindo cautela interpretativa e análise complementar por subtestes"
        )

        parts.append(
            f"O {label} apresentou escore {data['score']}, classificação "
            f"{data.get('classification', '').lower()}, sendo considerado {unit_text}. "
            f"Esse índice avalia principalmente {index_functions[index]}."
        )

    return "\n\n".join(parts)


def interpret_clusters(result: Dict[str, Any]) -> str:
    comparisons = result.get("cluster_comparisons", [])
    valid_comparisons = [c for c in comparisons if c.get("valid")]

    if not valid_comparisons:
        return (
            "A análise por clusters não foi interpretada, pois não houve pares de clusters "
            "simultaneamente válidos e unitários para comparação clínica segura."
        )

    uncommon = [c for c in valid_comparisons if c.get("result") == "Incomum"]

    if not uncommon:
        return (
            "As comparações clínicas por clusters não evidenciaram discrepâncias incomuns. "
            "Esse padrão sugere ausência de dissociações clinicamente relevantes entre os "
            "agrupamentos cognitivos analisados, devendo a interpretação permanecer centrada "
            "nos índices fatoriais e nos subtestes mais informativos."
        )

    descriptions = []
    for item in uncommon:
        descriptions.append(
            f"{item['comparison']} apresentou diferença de {item['difference']} pontos, "
            f"atingindo ou superando o valor crítico de {item['critical_value']}, sendo "
            f"classificada como discrepância incomum."
        )

    return (
        "A análise por clusters evidenciou discrepâncias clinicamente relevantes. "
        + " ".join(descriptions)
        + " Tais achados devem ser integrados aos dados de anamnese, observação clínica "
          "e demais instrumentos neuropsicológicos, não devendo ser utilizados isoladamente "
          "para definição diagnóstica."
    )


def generate_wais3_interpretation(patient_name: str, result: Dict[str, Any]) -> str:
    return "\n\n".join([
        "A Escala Wechsler de Inteligência para Adultos, Terceira Edição, WAIS-III, foi utilizada para avaliar o funcionamento intelectual global e os principais domínios cognitivos do paciente, contemplando habilidades verbais, perceptuais, memória operacional e velocidade de processamento.",
        interpret_qit(patient_name, result),
        interpret_indices(patient_name, result),
        interpret_clusters(result),
        "Em análise clínica, os resultados da WAIS-III devem ser compreendidos de forma integrada, considerando a consistência interna dos índices, a presença de discrepâncias, a qualidade das respostas, o comportamento durante a aplicação e os demais achados da avaliação neuropsicológica."
    ])
```

---

## 11. `config.py`

```python
from .schemas import WAIS3Input
from .calculators import calculate_wais3
from .interpreters import generate_wais3_interpretation


class WAIS3Module:
    key = "WAIS3"
    name = "Escala Wechsler de Inteligência para Adultos - Terceira Edição"

    def validate(self, raw_payload: dict) -> WAIS3Input:
        return WAIS3Input(**raw_payload)

    def calculate(self, raw_payload: dict) -> dict:
        validated = self.validate(raw_payload)
        return calculate_wais3(validated.model_dump())

    def interpret(self, raw_payload: dict, computed_payload: dict) -> str:
        validated = self.validate(raw_payload)
        return generate_wais3_interpretation(
            patient_name=validated.patient_name,
            result=computed_payload,
        )
```

---

## 12. Registro no `registry.py`

```python
from apps.tests.wais3.config import WAIS3Module

TEST_REGISTRY = {
    "WAIS3": WAIS3Module(),
}
```

---

## 13. Integração com `scoring_service.py`

```python
from apps.tests.registry import TEST_REGISTRY


class TestScoringService:
    @staticmethod
    def calculate(test_key: str, raw_payload: dict) -> dict:
        module = TEST_REGISTRY.get(test_key)

        if not module:
            raise ValueError(f"Teste não registrado: {test_key}")

        return module.calculate(raw_payload)

    @staticmethod
    def interpret(test_key: str, raw_payload: dict, computed_payload: dict) -> str:
        module = TEST_REGISTRY.get(test_key)

        if not module:
            raise ValueError(f"Teste não registrado: {test_key}")

        return module.interpret(raw_payload, computed_payload)
```

---

## 14. Integração com `ReportAIService`

A IA não deve refazer os cálculos psicométricos. Ela deve receber o `computed_payload` determinístico e produzir apenas síntese textual quando necessário.

```python
class ReportAIService:
    SUPPORTED_SECTIONS = {
        "wais3",
        "intellectual_efficiency",
        "eficiencia_intelectual",
    }

    @classmethod
    def supports_section(cls, section_key: str) -> bool:
        return section_key in cls.SUPPORTED_SECTIONS

    @classmethod
    def build_wais3_context(cls, snapshot: dict) -> dict:
        tests = snapshot.get("tests", [])
        wais3 = next(
            (test for test in tests if test.get("key") == "WAIS3"),
            None
        )

        if not wais3:
            return {
                "available": False,
                "reason": "WAIS-III não encontrado no snapshot",
            }

        return {
            "available": True,
            "patient": snapshot.get("patient", {}),
            "raw_payload": wais3.get("raw_payload", {}),
            "computed_payload": wais3.get("computed_payload", {}),
            "deterministic_interpretation": wais3.get("interpretation", ""),
        }

    @classmethod
    def generate_wais3_section(cls, snapshot: dict) -> str:
        context = cls.build_wais3_context(snapshot)

        if not context["available"]:
            return ""

        deterministic_text = context.get("deterministic_interpretation", "")

        if deterministic_text:
            return deterministic_text

        return "Resultado WAIS-III disponível, porém sem interpretação determinística gerada."
```

---

## 15. Integração com `ReportSectionService`

```python
class ReportSectionService:
    @staticmethod
    def regenerate_section(report, section_key: str, user=None):
        section = report.sections.filter(key=section_key).first()

        if not section:
            raise ValueError("Seção não encontrada")

        if section.is_locked:
            raise ValueError("Seção bloqueada")

        snapshot = build_report_snapshot(report.evaluation)

        if section_key in ["wais3", "intellectual_efficiency", "eficiencia_intelectual"]:
            content = ReportAIService.generate_wais3_section(snapshot)
            section.content = content
            section.save(update_fields=["content", "updated_at"])
            return section

        if ReportAIService.supports_section(section_key):
            content = ReportAIService.generate_section(section_key, snapshot)
            section.content = content
            section.save(update_fields=["content", "updated_at"])
            return section

        content = DeterministicReportGenerator.generate(section_key, snapshot)
        section.content = content
        section.save(update_fields=["content", "updated_at"])
        return section
```

---

## 16. Regra crítica para IA

A IA nunca deve:

1. Inventar QI, índice, percentil ou intervalo de confiança.
2. Interpretar QIT quando ele estiver marcado como não interpretável.
3. Interpretar índice não unitário como habilidade homogênea.
4. Calcular GAI se a diferença entre ICV e IOP for igual ou superior a 23.
5. Fazer análise de cluster se o cluster não for unitário.
6. Fechar diagnóstico com base apenas na WAIS-III.
7. Ignorar observações clínicas da aplicação.

---

## 17. Prompt interno recomendado para IA

```text
Você é um assistente técnico especializado em avaliação neuropsicológica.
Use exclusivamente os dados calculados no computed_payload.
Não recalcule tabelas normativas.
Não invente escores.
Não interprete QIT se qit_interpretability.interpretable for false.
Se houver GAI válido, explique por que ele foi utilizado.
Se índice não for unitário, informe cautela e priorize análise por subtestes.
Se houver clusters válidos, integre as discrepâncias incomuns.
Use linguagem técnica, clara, auditável e sem conclusões diagnósticas isoladas.
```

---

## 18. Exemplo de payload salvo no banco

```json
{
  "key": "WAIS3",
  "raw_payload": {
    "patient_name": "Paciente",
    "age_years": 40,
    "scaled_scores": {
      "VC": 13,
      "SM": 12,
      "IN": 11,
      "CO": 10,
      "AR": 9,
      "DG": 8,
      "SNL": 9,
      "CF": 12,
      "CD": 7,
      "CB": 13,
      "RM": 14,
      "AF": 10,
      "PS": 8
    }
  },
  "computed_payload": {
    "test": "WAIS-III",
    "qit_interpretability": {
      "interpretable": false,
      "difference": 25,
      "criterion": 23
    },
    "gai": {
      "valid": true,
      "score": 120,
      "classification": "Superior"
    }
  }
}
```

---

## 19. Checklist de validação antes de produção

- [ ] CSVs normativos conferidos linha a linha.
- [ ] Conversão bruto para ponderado testada por idade.
- [ ] Conversão das somas para QI/índices testada.
- [ ] GAI testado com casos válidos e inválidos.
- [ ] QIT interpretável testado com diferença menor que 23.
- [ ] QIT não interpretável testado com diferença igual ou maior que 23.
- [ ] Índices unitários testados com diferença menor que 5.
- [ ] Índices não unitários testados com diferença igual ou maior que 5.
- [ ] Clusters válidos testados.
- [ ] Clusters inválidos testados.
- [ ] Comparações clínicas testadas com valores críticos.
- [ ] Texto final revisado para não conter diagnóstico isolado.
- [ ] Integração com `ReportAIService` validada.
- [ ] Integração com `ReportSectionService` validada.
- [ ] Snapshot do laudo trazendo `raw_payload`, `computed_payload` e `interpretation`.

---

## 20. Resultado esperado no sistema

Ao finalizar a implementação, o sistema deverá:

1. Receber os dados do WAIS-III.
2. Calcular resultados psicométricos de forma determinística.
3. Armazenar os cálculos no `computed_payload`.
4. Gerar interpretação técnica no `interpretation`.
5. Disponibilizar o texto para o laudo.
6. Permitir que a IA apenas refine a redação, sem alterar os cálculos.
7. Manter rastreabilidade total para auditoria clínica.
