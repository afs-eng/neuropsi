from datetime import date
from typing import Any, Optional

from ninja import Schema


class InstrumentOut(Schema):
    id: int
    code: str
    name: str
    category: str
    version: str
    description: Optional[str] = None
    is_active: bool
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    age_message: Optional[str] = ""


class InstrumentCreateIn(Schema):
    code: str
    name: str
    category: Optional[str] = ""
    version: Optional[str] = ""
    is_active: bool = True


class InstrumentUpdateIn(Schema):
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None


class TestApplicationOut(Schema):
    id: int
    evaluation_id: int
    patient_name: str
    patient_sex: Optional[str] = None
    patient_schooling: Optional[str] = None
    instrument_id: int
    instrument_code: str
    instrument_name: str
    applied_on: Optional[date] = None
    raw_payload: dict[str, Any]
    computed_payload: dict[str, Any]
    classified_payload: dict[str, Any]
    reviewed_payload: dict[str, Any]
    interpretation_text: str
    report_payload: dict[str, Any] = {}
    is_validated: bool
    status: str
    status_display: str


class TestApplicationCreateIn(Schema):
    evaluation_id: int
    instrument_id: int
    applied_on: Optional[date] = None
    raw_payload: dict[str, Any] = {}
    reviewed_payload: dict[str, Any] = {}
    interpretation_text: Optional[str] = ""
    is_validated: bool = False
    status: Optional[str] = None


class TestApplicationUpdateIn(Schema):
    evaluation_id: Optional[int] = None
    instrument_id: Optional[int] = None
    applied_on: Optional[date] = None
    raw_payload: Optional[dict[str, Any]] = None
    computed_payload: Optional[dict[str, Any]] = None
    classified_payload: Optional[dict[str, Any]] = None
    reviewed_payload: Optional[dict[str, Any]] = None
    interpretation_text: Optional[str] = None
    is_validated: Optional[bool] = None
    status: Optional[str] = None


class MessageOut(Schema):
    message: str


class BFPSubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    sample: Optional[str] = "geral"
    responses: dict[str, int]


class WASISubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    confidence_level: Optional[str] = "95"
    vc: int
    sm: int
    cb: int
    rm: int


# --- EBADEP-A ---


class EBADEPASubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    item_01: int = 0
    item_02: int = 0
    item_03: int = 0
    item_04: int = 0
    item_05: int = 0
    item_06: int = 0
    item_07: int = 0
    item_08: int = 0
    item_09: int = 0
    item_10: int = 0
    item_11: int = 0
    item_12: int = 0
    item_13: int = 0
    item_14: int = 0
    item_15: int = 0
    item_16: int = 0
    item_17: int = 0
    item_18: int = 0
    item_19: int = 0
    item_20: int = 0
    item_21: int = 0
    item_22: int = 0
    item_23: int = 0
    item_24: int = 0
    item_25: int = 0
    item_26: int = 0
    item_27: int = 0
    item_28: int = 0
    item_29: int = 0
    item_30: int = 0
    item_31: int = 0
    item_32: int = 0
    item_33: int = 0
    item_34: int = 0
    item_35: int = 0
    item_36: int = 0
    item_37: int = 0
    item_38: int = 0
    item_39: int = 0
    item_40: int = 0
    item_41: int = 0
    item_42: int = 0
    item_43: int = 0
    item_44: int = 0
    item_45: int = 0


# --- EBADEP-IJ ---


class EBADEPIJSubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    item_01: int = 0
    item_02: int = 0
    item_03: int = 0
    item_04: int = 0
    item_05: int = 0
    item_06: int = 0
    item_07: int = 0
    item_08: int = 0
    item_09: int = 0
    item_10: int = 0
    item_11: int = 0
    item_12: int = 0
    item_13: int = 0
    item_14: int = 0
    item_15: int = 0
    item_16: int = 0
    item_17: int = 0
    item_18: int = 0
    item_19: int = 0
    item_20: int = 0
    item_21: int = 0
    item_22: int = 0
    item_23: int = 0
    item_24: int = 0
    item_25: int = 0
    item_26: int = 0
    item_27: int = 0


# --- FDT ---


class FDTStageIn(Schema):
    tempo: float = 0
    erros: int = 0


class FDTSubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    leitura: FDTStageIn
    contagem: FDTStageIn
    escolha: FDTStageIn
    alternancia: FDTStageIn


# --- BPA-2 ---


class BPA2SubtestIn(Schema):
    brutos: int = 0
    erros: int = 0
    omissoes: int = 0


class BPA2SubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    norm_type: Optional[str] = "idade"
    ac: BPA2SubtestIn
    ad: BPA2SubtestIn
    aa: BPA2SubtestIn


# --- M-CHAT ---


class MCHATResponseItem(Schema):
    answer: str


class MCHATSubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    patient_name: Optional[str] = None
    evaluation_date: Optional[str] = None
    birth_date: Optional[str] = None
    age_months: Optional[int] = None
    respondent_name: Optional[str] = None
    respondent_relationship: Optional[str] = None
    items: dict[str, MCHATResponseItem]


# --- CARS2-HF ---


class CARS2HFItemIn(Schema):
    score: float = 0
    observations: Optional[str] = ""


class CARS2HFSubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    patient_name: Optional[str] = None
    examiner_name: Optional[str] = None
    birth_date: Optional[str] = None
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    informant: Optional[str] = None
    items: dict[str, CARS2HFItemIn]


# --- WISC-IV ---


class WISC4SubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    cb: Optional[str] = ""
    sm: Optional[str] = ""
    dg: Optional[str] = ""
    cn: Optional[str] = ""
    cd: Optional[str] = ""
    vc: Optional[str] = ""
    snl: Optional[str] = ""
    rm: Optional[str] = ""
    co: Optional[str] = ""
    ps: Optional[str] = ""
    cf: Optional[str] = ""
    ca: Optional[str] = ""
    in_: Optional[str] = ""
    ar: Optional[str] = ""
    rp: Optional[str] = ""
    cusb: Optional[str] = ""
    diod: Optional[str] = ""
    dioi: Optional[str] = ""
    caa: Optional[str] = ""
    cae: Optional[str] = ""
    udiod: Optional[str] = ""
    udioi: Optional[str] = ""


class WAIS3SubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    vocabulario: Optional[str] = ""
    semelhancas: Optional[str] = ""
    aritmetica: Optional[str] = ""
    digitos: Optional[str] = ""
    informacao: Optional[str] = ""
    compreensao: Optional[str] = ""
    sequencia_numeros_letras: Optional[str] = ""
    completar_figuras: Optional[str] = ""
    codigos: Optional[str] = ""
    cubos: Optional[str] = ""
    raciocinio_matricial: Optional[str] = ""
    arranjo_figuras: Optional[str] = ""
    procurar_simbolos: Optional[str] = ""
    armar_objetos: Optional[str] = ""
    digitos_ordem_direta: Optional[str] = ""
    digitos_ordem_inversa: Optional[str] = ""
    maior_sequencia_digitos_direta: Optional[str] = ""
    maior_sequencia_digitos_inversa: Optional[str] = ""


# --- EPQ-J ---


class EPQJSubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    sexo: str = "M"
    item_01: Optional[int] = 0
    item_02: Optional[int] = 0
    item_03: Optional[int] = 0
    item_04: Optional[int] = 0
    item_05: Optional[int] = 0
    item_06: Optional[int] = 0
    item_07: Optional[int] = 0
    item_08: Optional[int] = 0
    item_09: Optional[int] = 0
    item_10: Optional[int] = 0
    item_11: Optional[int] = 0
    item_12: Optional[int] = 0
    item_13: Optional[int] = 0
    item_14: Optional[int] = 0
    item_15: Optional[int] = 0
    item_16: Optional[int] = 0
    item_17: Optional[int] = 0
    item_18: Optional[int] = 0
    item_19: Optional[int] = 0
    item_20: Optional[int] = 0
    item_21: Optional[int] = 0
    item_22: Optional[int] = 0
    item_23: Optional[int] = 0
    item_24: Optional[int] = 0
    item_25: Optional[int] = 0
    item_26: Optional[int] = 0
    item_27: Optional[int] = 0
    item_28: Optional[int] = 0
    item_29: Optional[int] = 0
    item_30: Optional[int] = 0
    item_31: Optional[int] = 0
    item_32: Optional[int] = 0
    item_33: Optional[int] = 0
    item_34: Optional[int] = 0
    item_35: Optional[int] = 0
    item_36: Optional[int] = 0
    item_37: Optional[int] = 0
    item_38: Optional[int] = 0
    item_39: Optional[int] = 0
    item_40: Optional[int] = 0
    item_41: Optional[int] = 0
    item_42: Optional[int] = 0
    item_43: Optional[int] = 0
    item_44: Optional[int] = 0
    item_45: Optional[int] = 0
    item_46: Optional[int] = 0
    item_47: Optional[int] = 0
    item_48: Optional[int] = 0
    item_49: Optional[int] = 0
    item_50: Optional[int] = 0
    item_51: Optional[int] = 0
    item_52: Optional[int] = 0
    item_53: Optional[int] = 0
    item_54: Optional[int] = 0
    item_55: Optional[int] = 0
    item_56: Optional[int] = 0
    item_57: Optional[int] = 0
    item_58: Optional[int] = 0
    item_59: Optional[int] = 0
    item_60: Optional[int] = 0


# --- ETDAH-AD ---


class ETDAHADSubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    item_01: int = 0
    item_02: int = 0
    item_03: int = 0
    item_04: int = 0
    item_05: int = 0
    item_06: int = 0
    item_07: int = 0
    item_08: int = 0
    item_09: int = 0
    item_10: int = 0
    item_11: int = 0
    item_12: int = 0
    item_13: int = 0
    item_14: int = 0
    item_15: int = 0
    item_16: int = 0
    item_17: int = 0
    item_18: int = 0
    item_19: int = 0
    item_20: int = 0
    item_21: int = 0
    item_22: int = 0
    item_23: int = 0
    item_24: int = 0
    item_25: int = 0
    item_26: int = 0
    item_27: int = 0
    item_28: int = 0
    item_29: int = 0
    item_30: int = 0
    item_31: int = 0
    item_32: int = 0
    item_33: int = 0
    item_34: int = 0
    item_35: int = 0
    item_36: int = 0
    item_37: int = 0
    item_38: int = 0
    item_39: int = 0
    item_40: int = 0
    item_41: int = 0
    item_42: int = 0
    item_43: int = 0
    item_44: int = 0
    item_45: int = 0
    item_46: int = 0
    item_47: int = 0
    item_48: int = 0
    item_49: int = 0
    item_50: int = 0
    item_51: int = 0
    item_52: int = 0
    item_53: int = 0
    item_54: int = 0
    item_55: int = 0
    item_56: int = 0
    item_57: int = 0
    item_58: int = 0
    item_59: int = 0
    item_60: int = 0
    item_61: int = 0
    item_62: int = 0
    item_63: int = 0
    item_64: int = 0
    item_65: int = 0
    item_66: int = 0
    item_67: int = 0
    item_68: int = 0
    item_69: int = 0


# --- ETDAH-PAIS ---


class ETDAHPAISSubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    sex: str = "M"
    item_01: int = 0
    item_02: int = 0
    item_03: int = 0
    item_04: int = 0
    item_05: int = 0
    item_06: int = 0
    item_07: int = 0
    item_08: int = 0
    item_09: int = 0
    item_10: int = 0
    item_11: int = 0
    item_12: int = 0
    item_13: int = 0
    item_14: int = 0
    item_15: int = 0
    item_16: int = 0
    item_17: int = 0
    item_18: int = 0
    item_19: int = 0
    item_20: int = 0
    item_21: int = 0
    item_22: int = 0
    item_23: int = 0
    item_24: int = 0
    item_25: int = 0
    item_26: int = 0
    item_27: int = 0
    item_28: int = 0
    item_29: int = 0
    item_30: int = 0
    item_31: int = 0
    item_32: int = 0
    item_33: int = 0
    item_34: int = 0
    item_35: int = 0
    item_36: int = 0
    item_37: int = 0
    item_38: int = 0
    item_39: int = 0
    item_40: int = 0
    item_41: int = 0
    item_42: int = 0
    item_43: int = 0
    item_44: int = 0
    item_45: int = 0
    item_46: int = 0
    item_47: int = 0
    item_48: int = 0
    item_49: int = 0
    item_50: int = 0
    item_51: int = 0
    item_52: int = 0
    item_53: int = 0
    item_54: int = 0
    item_55: int = 0
    item_56: int = 0
    item_57: int = 0
    item_58: int = 0


# --- RAVLT ---


class RAVLTSubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    a1: Optional[int] = 0
    a2: Optional[int] = 0
    a3: Optional[int] = 0
    a4: Optional[int] = 0
    a5: Optional[int] = 0
    b: Optional[int] = 0
    a6: Optional[int] = 0
    a7: Optional[int] = 0
    reconhecimento: Optional[int] = 0


# --- SRS-2 ---


class SRS2SubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    form: str = "idade_escolar"
    gender: Optional[str] = "M"
    age: Optional[int] = 10
    respondent_name: Optional[str] = ""
    responses: Optional[dict[str, int]] = {}


# --- SCARED ---


class SCAREDSubmitIn(Schema):
    application_id: Optional[int] = None
    evaluation_id: int
    applied_on: Optional[date] = None
    form: str = "child"  # child or parent
    gender: Optional[str] = "M"
    age: Optional[int] = 10
    responses: Optional[dict[str, int]] = {}


# --- BAI ---


class BAISubmitIn(Schema):
    evaluation_id: int
    applied_on: Optional[date] = None
    item_01: int = 0
    item_02: int = 0
    item_03: int = 0
    item_04: int = 0
    item_05: int = 0
    item_06: int = 0
    item_07: int = 0
    item_08: int = 0
    item_09: int = 0
    item_10: int = 0
    item_11: int = 0
    item_12: int = 0
    item_13: int = 0
    item_14: int = 0
    item_15: int = 0
    item_16: int = 0
    item_17: int = 0
    item_18: int = 0
    item_19: int = 0
    item_20: int = 0
    item_21: int = 0
