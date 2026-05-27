import re
import csv
from pathlib import Path

from .paths import TABELAS_A8, TABELAS_CD, TABELAS_NCP, TABELAS_EQUIVALENTES


WISC4_CODE = "wisc4"
WISC4_NAME = "WISC-IV - Escala de Inteligência Wechsler para Crianças"
WISC4_VERSION = "4"

WISC4_SUBTESTS = {
    "semelhancas": {"name": "Semelhanças", "code": "SM", "max": 44},
    "vocabulario": {"name": "Vocabulário", "code": "VC", "max": 68},
    "compreensao": {"name": "Compreensão", "code": "CO", "max": 47},
    "cubos": {"name": "Cubos", "code": "CB", "max": 68},
    "conceitos": {"name": "Conceitos Figurativos", "code": "CN", "max": 28},
    "matricial": {"name": "Raciocínio Matricial", "code": "RM", "max": 41},
    "digitos": {"name": "Dígitos", "code": "DG", "max": 32},
    "sequencias": {"name": "Seq. Letras e Números", "code": "SNL", "max": 30},
    "codigos": {"name": "Códigos", "code": "CD", "max": 119},
    "procura_simbolos": {"name": "Procura de Símbolos", "code": "PS", "max": 60},
}

WISC4_SUPPLEMENTAL_SUBTESTS = {
    "cf": {"name": "Completar Figuras", "code": "CF", "max": 38},
    "ca": {"name": "Cancelamento", "code": "CA", "max": 60},
    "in": {"name": "Informação", "code": "IN", "max": 30},
    "ar": {"name": "Aritmética", "code": "AR", "max": 34},
    "rp": {"name": "Raciocínio com Palavras", "code": "RP", "max": 32},
}

WISC4_INDICES = {
    "icv": {
        "name": "Índice de Compreensão Verbal",
        "subtests": ["semelhancas", "vocabulario", "compreensao"],
        "supplemental": ["in", "rp"],
    },
    "iop": {
        "name": "Índice de Organização Perceptual",
        "subtests": ["cubos", "conceitos", "matricial"],
        "supplemental": ["cf"],
    },
    "imt": {
        "name": "Índice de Memória de Trabalho",
        "subtests": ["digitos", "sequencias"],
        "supplemental": ["ar"],
    },
    "ivp": {
        "name": "Índice de Velocidade de Processamento",
        "subtests": ["codigos", "procura_simbolos"],
        "supplemental": ["ca"],
    },
}

INDEX_CONVERSION = {
    69: (2, "Extremamente Baixo"),
    79: (5, "Limítrofe"),
    89: (16, "Média Inferior"),
    109: (50, "Média"),
    119: (84, "Média Superior"),
    129: (95, "Superior"),
}

# Conversão de Ponto Ponderado (1-19) → Percentil (WISC-IV, média=10, DP=3)
PP_TO_PERCENTIL: dict[int, float] = {
    1: 0.1, 2: 0.4, 3: 1.0, 4: 2.0, 5: 5.0,
    6: 9.0, 7: 16.0, 8: 25.0, 9: 37.0, 10: 50.0,
    11: 63.0, 12: 75.0, 13: 84.0, 14: 91.0, 15: 95.0,
    16: 98.0, 17: 99.0, 18: 99.6, 19: 99.9,
}

# SEM médio por subteste (escala de ponto ponderado)
# Baseado nas confiabilidades publicadas no manual técnico do WISC-IV
SUBTEST_SEM: dict[str, float] = {
    "SM": 1.22, "VC": 1.00, "CO": 1.36,
    "CB": 1.36, "CN": 1.50, "RM": 1.22,
    "DG": 1.00, "SNL": 1.22,
    "CD": 1.22, "PS": 1.36,
}

PROCESS_SCORE_CONFIG = {
    "cusb": {"name": "Cubos sem Tempo de Bônus", "code": "CUSB"},
    "diod": {"name": "Dígitos Ordem Direta", "code": "DIOD"},
    "dioi": {"name": "Dígitos Ordem Inversa", "code": "DIOI"},
    "caa": {"name": "Cancelamento Aleatório", "code": "CAA"},
    "cae": {"name": "Cancelamento Estruturado", "code": "CAE"},
}

SEQUENCE_SCORE_CONFIG = {
    "udiod": {"name": "Sequência Maior de Dígitos Ordem Direta", "code": "UDIOD", "column": "Direta"},
    "udioi": {"name": "Sequência Maior de Dígitos Ordem Inversa", "code": "UDIOI", "column": "Inversa"},
}


def _idade_em_meses(anos: int, meses: int) -> int:
    return anos * 12 + meses


def _calcular_idade(birth_date, evaluation_date) -> tuple[int, int]:
    anos = evaluation_date.year - birth_date.year
    meses = evaluation_date.month - birth_date.month
    if evaluation_date.day < birth_date.day:
        meses -= 1
    if meses < 0:
        anos -= 1
        meses += 12
    return anos, meses


def _obter_arquivo_ncp(anos: int, meses: int) -> Path:
    idade_meses = _idade_em_meses(anos, meses)
    faixas = []
    for arquivo in TABELAS_NCP.glob("idade_*.csv"):
        match = re.match(r"idade_(\d+)-(\d+)-(\d+)-(\d+)$", arquivo.stem)
        if not match:
            match = re.match(r"idade_(\d+)-(\d+)_(\d+)-(\d+)$", arquivo.stem)
        if not match:
            continue
        a1, m1, a2, m2 = map(int, match.groups())
        min_meses = _idade_em_meses(a1, m1)
        max_exclusivo = _idade_em_meses(a2, m2) + 1
        faixas.append({"min": min_meses, "max": max_exclusivo, "arquivo": arquivo})

    faixas.sort(key=lambda f: f["min"])
    for faixa in faixas:
        if faixa["min"] <= idade_meses < faixa["max"]:
            return faixa["arquivo"]

    raise ValueError(f"Idade fora das faixas WISC-IV: {anos}a {meses}m")


def _carregar_tabela_ncp(anos: int, meses: int) -> list[dict]:
    arquivo = _obter_arquivo_ncp(anos, meses)
    with open(arquivo, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _obter_arquivo_a8(anos: int, meses: int) -> Path:
    idade_meses = _idade_em_meses(anos, meses)
    faixas = []
    for arquivo in TABELAS_A8.glob("*.csv"):
        age_range = _parse_a8_age_range(arquivo.stem)
        if not age_range:
            continue
        a1, m1, a2, m2 = age_range
        min_meses = _idade_em_meses(a1, m1)
        max_exclusivo = _idade_em_meses(a2, m2) + 1
        faixas.append({"min": min_meses, "max": max_exclusivo, "arquivo": arquivo})

    faixas.sort(key=lambda faixa: faixa["min"])
    for faixa in faixas:
        if faixa["min"] <= idade_meses < faixa["max"]:
            return faixa["arquivo"]

    raise ValueError(f"Tabela A8 não encontrada para idade WISC-IV: {anos}a {meses}m")


def _parse_a8_age_range(stem: str) -> tuple[int, int, int, int] | None:
    patterns = [
        r"(\d+)_(\d+)[_-]a[_-](\d+)_(\d+)$",
        r"(\d+)_(\d+)-(\d+)_(\d+)$",
        r"(\d+)_(\d+)a(\d+)_(\d+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, stem)
        if match:
            return tuple(map(int, match.groups()))

    match = re.search(r"(\d+)_(\d+)a(\d+)$", stem)
    if match:
        year, start_month, end_month = map(int, match.groups())
        return year, start_month, year, end_month
    return None


def _carregar_tabela_a8(anos: int, meses: int) -> list[dict]:
    arquivo = _obter_arquivo_a8(anos, meses)
    with open(arquivo, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            normalized = {("PP" if key in {"PontoP", "Ponto Ponderado"} else key): value for key, value in row.items()}
            rows.append(normalized)
        return rows


def _valor_no_intervalo(valor: int, celula: str) -> bool:
    if not celula or celula.strip() in ("", "-"):
        return False
    celula = celula.strip().replace(":", "-")
    if "-" in celula:
        try:
            inicio, fim = celula.split("-", 1)
            return int(inicio) <= valor <= int(fim)
        except (ValueError,):
            return False
    try:
        return valor == int(celula)
    except (ValueError,):
        return False


def buscar_ponderado(tabela: list[dict], coluna: str, valor_bruto: int) -> int:
    for linha in tabela:
        celula = linha.get(coluna, "")
        if _valor_no_intervalo(valor_bruto, celula):
            pp = linha.get("PP", "")
            if pp and pp.strip().isdigit():
                return int(pp.strip())
    raise ValueError(f"Valor bruto {valor_bruto} não encontrado para {coluna}")


def _parse_float(value) -> float | None:
    if value in (None, "", ".", "-"):
        return None
    try:
        number = float(str(value).strip().replace(",", "."))
    except ValueError:
        return None
    if number > 50:
        number = number / 100
    return number


def _format_process_number(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(round(value, 2)).replace(".", ",")


def _b7_column_indexes(anos: int) -> tuple[int, int]:
    if anos <= 7:
        return 1, 2
    if anos <= 9:
        return 3, 4
    if anos <= 11:
        return 5, 6
    if anos <= 13:
        return 7, 8
    if anos <= 15:
        return 9, 10
    return 11, 12


def _b8_column_name(anos: int) -> str:
    if anos <= 6:
        return "6:0-6:11"
    if anos <= 16:
        return f"{anos}:0-{anos}:11"
    return "Todas as idades"


def _load_csv_rows(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))


def _lookup_b7_frequency(raw_score: int | None, column_index: int) -> float | None:
    if raw_score is None:
        return None
    for row in _load_csv_rows(TABELAS_CD / "tabela_B7_1.csv"):
        if not row or not row[0].strip().isdigit():
            continue
        if int(row[0]) == raw_score and column_index < len(row):
            return _parse_float(row[column_index])
    return None


def _lookup_b8_frequency(difference: int | None, anos: int) -> float | None:
    if difference is None:
        return None
    with (TABELAS_CD / "tabela_B8.csv").open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        column = _b8_column_name(anos)
        for row in reader:
            if row.get("Tamanho da Discrepância") == str(difference):
                return _parse_float(row.get(column) or row.get("Todas as idades"))
    return None


def _lookup_b9_critical(first_code: str, second_code: str, significance: str = "0.05") -> float | None:
    fallback = None
    with (TABELAS_CD / "tabela_B9.csv").open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_code = row.get("")
            if row_code != first_code:
                continue
            value = _parse_float(row.get(second_code))
            if row.get("Nível de Significância") == significance and value is not None:
                return value
            if value is not None and fallback is None:
                fallback = value
    return fallback


def _lookup_b10_frequency(first_code: str, second_code: str, difference: int | None) -> float | None:
    if difference is None:
        return None
    direction = "<" if difference < 0 else ">"
    column = f"{first_code} {direction} {second_code} ({'-' if direction == '<' else '+'})"
    abs_difference = abs(difference)
    with (TABELAS_CD / "tabela_B10.csv").open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get("Tamanho da\nDiscrepância") or row.get("Tamanho da Discrepância")
            if key == str(abs_difference):
                return _parse_float(row.get(column))
    return None


def build_process_scores(raw_scores: dict, anos: int, meses: int, computed_data: dict) -> dict:
    a8_table = _carregar_tabela_a8(anos, meses)
    scaled_rows = []
    process_by_code = {}
    for raw_key, config in PROCESS_SCORE_CONFIG.items():
        raw_value = raw_scores.get(raw_key)
        scaled_score = None
        if raw_value is not None:
            try:
                scaled_score = buscar_ponderado(a8_table, config["code"], raw_value)
            except ValueError:
                scaled_score = None
        row = {
            "name": config["name"],
            "code": config["code"],
            "raw_score": raw_value,
            "scaled_score": scaled_score,
        }
        scaled_rows.append(row)
        process_by_code[config["code"]] = row

    direct_col, inverse_col = _b7_column_indexes(anos)
    sequence_rows = []
    sequence_by_code = {}
    for raw_key, config in SEQUENCE_SCORE_CONFIG.items():
        raw_value = raw_scores.get(raw_key)
        frequency = _lookup_b7_frequency(raw_value, direct_col if config["column"] == "Direta" else inverse_col)
        row = {
            "name": config["name"],
            "code": config["code"],
            "raw_score": raw_value,
            "frequency": frequency,
        }
        sequence_rows.append(row)
        sequence_by_code[config["code"]] = row

    udiod = sequence_by_code.get("UDIOD", {}).get("raw_score")
    udioi = sequence_by_code.get("UDIOI", {}).get("raw_score")
    raw_difference = udiod - udioi if udiod is not None and udioi is not None else None
    raw_discrepancy_rows = [
        {
            "label": "UDIOD - UDIOI",
            "first": udiod,
            "second": udioi,
            "difference": raw_difference,
            "frequency": _lookup_b8_frequency(raw_difference, anos),
        }
    ]

    subtest_scores = {
        "CB": (computed_data.get("cubos") or {}).get("escore_padrao"),
        "DIOD": process_by_code.get("DIOD", {}).get("scaled_score"),
        "CAA": process_by_code.get("CAA", {}).get("scaled_score"),
    }
    discrepancy_pairs = [
        ("Cubos - Cubos sem Tempo de Bônus", "CB", "CUSB", subtest_scores.get("CB"), process_by_code.get("CUSB", {}).get("scaled_score")),
        ("Dígitos Ordem Direta - Dígitos Ordem Inversa", "DIOD", "DIOI", subtest_scores.get("DIOD"), process_by_code.get("DIOI", {}).get("scaled_score")),
        ("Cancelamento Aleatório - Estruturado", "CAA", "CAE", subtest_scores.get("CAA"), process_by_code.get("CAE", {}).get("scaled_score")),
    ]
    process_discrepancy_rows = []
    for label, first_code, second_code, first_value, second_value in discrepancy_pairs:
        difference = first_value - second_value if first_value is not None and second_value is not None else None
        critical = _lookup_b9_critical(first_code, second_code)
        process_discrepancy_rows.append(
            {
                "label": label,
                "first_code": first_code,
                "second_code": second_code,
                "first": first_value,
                "second": second_value,
                "difference": difference,
                "critical": critical,
                "significant": abs(difference) >= critical if difference is not None and critical is not None else None,
                "frequency": _lookup_b10_frequency(first_code, second_code, difference),
            }
        )

    return {
        "scaled_rows": scaled_rows,
        "sequence_frequency_rows": sequence_rows,
        "raw_discrepancy_rows": raw_discrepancy_rows,
        "process_discrepancy_rows": process_discrepancy_rows,
    }


def get_classification_padrao(escore_padrao: int) -> str:
    if escore_padrao <= 2:
        return "Dificuldade Grave"
    elif escore_padrao <= 4:
        return "Dificuldade Moderada"
    elif escore_padrao <= 7:
        return "Dificuldade Leve"
    elif escore_padrao <= 12:
        return "Média"
    elif escore_padrao <= 15:
        return "Média Superior"
    elif escore_padrao <= 17:
        return "Superior"
    else:
        return "Muito Superior"


def get_classification_composto(escore: int) -> tuple[int, str]:
    keys = sorted(INDEX_CONVERSION.keys())
    for key in keys:
        if escore <= key:
            return INDEX_CONVERSION[key]
    return (50, "Muito Superior")


def calculate_index_score(standard_scores: list[int]) -> int:
    if not standard_scores:
        return 0
    return sum(standard_scores)


def calculate_qi_total(soma_total_pp: int) -> int:
    """
    Estimativa de fallback do QIT quando a soma está fora do range da tabela.
    A soma dos PPs dos 10 subtestes mapeia aproximadamente 1:1 ao QIT no lookup
    (soma ~100 → QIT ~100). Retorna valor clampado ao range válido [40, 160].
    NOTA: Este valor NÃO é normativamente válido — use lookup_composite_score sempre que possível.
    """
    return max(40, min(160, soma_total_pp))


def get_percentil_subteste(pp: int) -> float:
    """Converte ponto ponderado (1-19) em percentil usando tabela normativa do WISC-IV."""
    return PP_TO_PERCENTIL.get(max(1, min(19, pp)), 50.0)


def calculate_confidence_interval(
    escore: int, sem: float = 1.22, nivel: float = 1.96
) -> tuple[int, int]:
    """IC para escore ponderado de subteste (IC 95% por padrão)."""
    lower = int(round(escore - nivel * sem))
    upper = int(round(escore + nivel * sem))
    return (lower, upper)


EQUIVALENCE_TABLE_FILES = {
    "icv": "tabela A2.csv",
    "iop": "tabela A3.csv",
    "imt": "tabela A4.csv",
    "ivp": "tabela A5.csv",
    "qit": "Tabela A6.csv",
}

EQUIVALENCE_TABLE_COLUMNS = {
    "icv": "ICV",
    "iop": "IOP",
    "imt": "IMO",
    "ivp": "IVP",
    "qit": "QIT",
}


def _carregar_tabela_equivalente(index_code: str) -> list[dict]:
    arquivo = TABELAS_EQUIVALENTES / EQUIVALENCE_TABLE_FILES[index_code]
    with open(arquivo, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _parse_percentile(percentil_str: str) -> float:
    percentil_str = percentil_str.strip().replace(",", ".")
    if percentil_str.startswith("<"):
        return 0.01
    if percentil_str.startswith(">"):
        return 99.9
    try:
        return float(percentil_str)
    except (ValueError,):
        return 0.0


def _parse_interval(interval_str: str) -> tuple[int, int]:
    interval_str = interval_str.strip()
    if not interval_str or interval_str == "-":
        return (0, 0)
    parts = interval_str.split("-")
    if len(parts) == 2:
        return (int(parts[0]), int(parts[1]))
    return (0, 0)


def lookup_composite_score(index_code: str, soma_ponderados: int) -> dict:
    """
    Lookup composite score, percentile, and confidence intervals from equivalence table.
    index_code: 'icv', 'iop', 'imt', 'ivp', 'qit'
    Returns: {'escore': int, 'percentil': float, 'ic_90': tuple, 'ic_95': tuple}
    """
    tabela = _carregar_tabela_equivalente(index_code)
    score_column = EQUIVALENCE_TABLE_COLUMNS.get(index_code, index_code.upper())
    for linha in tabela:
        soma_col = linha.get("Soma dos pontos ponderados", "").strip()
        if not soma_col:
            continue
        try:
            if int(soma_col) == soma_ponderados:
                escore = int(linha.get(score_column, "0").strip())
                percentil = _parse_percentile(linha.get("Rank Percentil", "0"))
                ic_90 = _parse_interval(linha.get("90%", "0-0"))
                ic_95 = _parse_interval(linha.get("95%", "0-0"))
                return {
                    "escore": escore,
                    "percentil": percentil,
                    "ic_90": ic_90,
                    "ic_95": ic_95,
                }
        except (ValueError, KeyError):
            continue
    raise ValueError(f"Soma {soma_ponderados} não encontrada para {index_code}")


def lookup_gai_score(soma_ponderados: int) -> dict:
    """
    Lookup GAI (General Ability Index) from Tabela-GAI.csv.
    Returns: {'escore': int, 'percentil': float, 'ic_95': tuple, 'classificacao': str}
    """
    arquivo = TABELAS_EQUIVALENTES / "Tabela-GAI.csv"
    with open(arquivo, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for linha in reader:
            soma_col = linha.get("Soma de Escalado Pontuações", "").strip()
            if not soma_col:
                continue
            try:
                if int(soma_col) == soma_ponderados:
                    escore = int(linha.get("GAI", "0").strip())
                    percentil = _parse_percentile(linha.get("Percentil", "0"))
                    ic_95 = _parse_interval(linha.get("Nível de Confiança 95%", "0-0"))
                    _, classificacao = get_classification_composto(escore)
                    return {
                        "escore": escore,
                        "percentil": percentil,
                        "ic_95": ic_95,
                        "classificacao": classificacao,
                    }
            except (ValueError, KeyError):
                continue
    raise ValueError(f"Soma {soma_ponderados} não encontrada para GAI")


def lookup_cpi_score(soma_ponderados: int) -> dict:
    """
    Lookup CPI (Cognitive Proficiency Index) from Tabela-CPI.csv.
    Returns: {'escore': int, 'percentil': float, 'ic_95': tuple, 'classificacao': str}
    """
    arquivo = TABELAS_EQUIVALENTES / "Tabela-CPI.csv"
    with open(arquivo, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for linha in reader:
            soma_col = linha.get("Soma de Escalas", "").strip()
            if not soma_col:
                continue
            try:
                if int(soma_col) == soma_ponderados:
                    escore = int(linha.get("CPI", "0").strip())
                    percentil = _parse_percentile(linha.get("Percentil", "0"))
                    ic_95 = _parse_interval(linha.get("IC 95%", "0-0"))
                    _, classificacao = get_classification_composto(escore)
                    return {
                        "escore": escore,
                        "percentil": percentil,
                        "ic_95": ic_95,
                        "classificacao": classificacao,
                    }
            except (ValueError, KeyError):
                continue
    raise ValueError(f"Soma {soma_ponderados} não encontrada para CPI")
