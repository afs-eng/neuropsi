from datetime import date as date_cls

from dateutil.relativedelta import relativedelta

from apps.tests.age_rules import get_instrument_age_rule


def get_reference_date(evaluation, applied_on=None):
    return applied_on or evaluation.start_date or evaluation.end_date or date_cls.today()


def calcAge(birth_date, reference_date=None):
    base_date = reference_date or date_cls.today()
    return relativedelta(base_date, birth_date).years


def calc_age_parts(birth_date, reference_date=None) -> dict[str, int]:
    delta = relativedelta(reference_date or date_cls.today(), birth_date)
    return {"anos": delta.years, "meses": delta.months}


def get_faixa_wisc(age):
    if 6 <= age <= 7:
        return "6-7 anos"
    if 8 <= age <= 9:
        return "8-9 anos"
    if 10 <= age <= 11:
        return "10-11 anos"
    if 12 <= age <= 13:
        return "12-13 anos"
    if 14 <= age <= 15:
        return "14-15 anos"
    if age == 16:
        return "16 anos"
    return "6-7 anos"


def validate_instrument_age(evaluation, instrument):
    patient = evaluation.patient
    if not patient or not patient.birth_date:
        return None

    rules = get_instrument_age_rule(instrument.code)
    if not rules:
        return None

    age = calcAge(patient.birth_date, get_reference_date(evaluation))
    min_age = rules.get("min_age")
    max_age = rules.get("max_age")

    if min_age is not None and age < min_age:
        return rules["message"]
    if max_age is not None and age > max_age:
        return rules["message"]
    return None
