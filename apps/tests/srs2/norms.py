import os
import csv
from typing import Optional, Dict, Tuple

from .paths import TABLES_DIR

NormTable = Dict[int, Tuple[float, float]]

NORMS: Dict[str, Dict[str, Dict[str, NormTable]]] = {
    "idade_escolar": {
        "M": {},
        "F": {}
    },
    "pre_escola": {
        "default": {}
    },
    "adulto_autorrelato": {
        "default": {}
    },
    "adulto_heterorrelato": {
        "default": {}
    }
}


def _normalize_column_name(name: str) -> str:
    normalized = name.lstrip("\ufeff").strip().lower()
    return normalized.replace("escoret", "escore_t")

def load_norm_data():
    base_dir = TABLES_DIR
    
    # Mapeamento dos arquivos CSV para Formulário e Gênero
    file_mapping = {
        "adulto_autorrelato_score_total.csv": ("adulto_autorrelato", "default"),
        "adulto_autorrelato_subescalas.csv": ("adulto_autorrelato", "default"),
        "adulto_heterorrelato_score_total.csv": ("adulto_heterorrelato", "default"),
        "adulto_heterorrelato_subescalas.csv": ("adulto_heterorrelato", "default"),
        "idade_escolar_feminino_score_total.csv": ("idade_escolar", "F"),
        "idade_escolar_feminino_subescalas.csv": ("idade_escolar", "F"),
        "idade_escolar_masculino_score_total.csv": ("idade_escolar", "M"),
        "idade_escolar_masculino_subescalas_intervencao.csv": ("idade_escolar", "M"),
        "pre_escolar_subescalas_intervencao.csv": ("pre_escola", "default"),
        "score_total_pre_escolar.csv": ("pre_escola", "default"),
    }
    
    # Mapeamento flexível de nomes de coluna em vários arquivos para o fator interno
    factor_mapping = {
        "percepção_social": ["percepcao_social", "ps"],
        "cognição_social": ["cognicao_social", "cs"],
        "comunicação_social": ["comunicacao_social", "coms"],
        "motivação_social": ["motivacao_social", "ms"],
        "padrões_restritos": ["padroes_restritos_repetitivos", "prr"],
        "cis": ["comunicacao_interacao_social", "cis"],
        "total": ["pontuacao_srs2_total", "total", "srs2_total"]
    }

    # Inicializar os dicionários dos fatores
    for form in NORMS:
        for gender in NORMS[form]:
            for factor in factor_mapping.keys():
                NORMS[form][gender][factor] = {}

    for filename, (form, gender) in file_mapping.items():
        filepath = os.path.join(base_dir, filename)
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                normalized_row = {
                    _normalize_column_name(key): (value or "")
                    for key, value in row.items()
                    if key is not None
                }
                try:
                    bruto_str = normalized_row.get("pontuacao_bruta", "").strip()
                    if not bruto_str: 
                        continue
                    bruto = int(bruto_str)
                except ValueError:
                    continue

                for factor, possible_names in factor_mapping.items():
                    for name in possible_names:
                        key_t = f"{name}_escore_t"
                        key_p = f"{name}_percentil"
                        
                        if key_t in normalized_row and key_p in normalized_row:
                            val_t = normalized_row[key_t].strip()
                            val_p = normalized_row[key_p].strip()
                            
                            if not val_t or val_t == "-":
                                continue
                            
                            try:
                                tscore_val = float(val_t)
                            except ValueError:
                                continue
                                
                            if not val_p or val_p == "-":
                                continue
                                
                            # Remover sinais matemáticos que denotam os limites das curvas >=99 ou <=1
                            p_clean = val_p.replace(">", "").replace("<", "").replace(",", ".")
                            try:
                                pct_val = float(p_clean)
                            except ValueError:
                                continue
                                
                            NORMS[form][gender][factor][bruto] = (tscore_val, pct_val)

# Carrega os dados na memória no startup
load_norm_data()

def get_norm_data(raw: int, form: str, gender: str, factor: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Procura na tabela normativa o T-Score e Percentil exatos para o Ponto Bruto. 
    Se o Ponto Bruto exceder ou faltar, ancora limites de teto, borda ou interpola.
    """
    if form == "idade_escolar":
        key = gender
    else:
        key = "default"

    table = NORMS.get(form, {}).get(key, {}).get(factor, {})
    
    if raw in table:
        return table[raw]

    # Lógica auxiliar iterativa para interpolações
    valid_points = []
    for k, tuple_vals in table.items():
        if isinstance(k, int):
            valid_points.append((k, tuple_vals[0], tuple_vals[1]))

    if not valid_points:
        return None, None

    valid_points.sort(key=lambda x: x[0])

    # Teto inferior
    if raw <= valid_points[0][0]:
        return valid_points[0][1], valid_points[0][2]

    # Teto superior
    if raw >= valid_points[-1][0]:
        return valid_points[-1][1], valid_points[-1][2]

    # Interpolação linear arredondando para garantir o piso
    for i in range(len(valid_points) - 1):
        r1, t1, p1 = valid_points[i]
        r2, t2, p2 = valid_points[i+1]
        
        if r1 < raw < r2:
            return float(round(t1)), float(round(p1))

    return None, None

def classify_tscore(t: Optional[float]) -> str:
    if t is None:
        return "Norma não localizada"
    
    # Regras universais de classificação para SRS-2 com base no T-Score
    if t <= 59:
        return "Dentro dos limites normais"
    elif 60 <= t <= 65:
        return "Leve"
    elif 66 <= t <= 75:
        return "Moderado"
    else:
        return "Severo"

def get_age_band(age: int, form: str) -> str:
    if form == "pre_escola":
        return "4 a 5 anos"
    elif form == "idade_escolar":
        return "6 a 18 anos"
    else:
        return "> 18 anos"
