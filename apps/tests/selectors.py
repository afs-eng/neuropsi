from typing import Optional

from django.db.models import QuerySet

from apps.tests.models import Instrument, TestApplication, TestInterpretationTemplate


def get_instruments() -> QuerySet[Instrument]:
    # Injeta essenciais se sumirem do banco (Pós-Reset)
    essentials = [
        {
            "code": "scared",
            "name": "SCARED - Ansiedade Infantil",
            "category": "Ansiedade",
        },
        {"code": "ravlt", "name": "RAVLT - Memória Auditiva", "category": "Memoria"},
        {
            "code": "srs2",
            "name": "SRS-2 - Social / Autismo",
            "category": "Social / Autismo",
        },
        {
            "code": "ssrs",
            "name": "SSRS - Habilidades Sociais",
            "category": "Social / Comportamento",
        },
        {
            "code": "cars2_hf",
            "name": "CARS2-HF - Childhood Autism Rating Scale – Second Edition, High Functioning Version",
            "category": "Social / Autismo",
        },
        {
            "code": "mchat",
            "name": "M-CHAT - Modified Checklist for Autism in Toddlers",
            "category": "Social / Autismo",
        },
    ]
    for item in essentials:
        Instrument.objects.get_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "category": item["category"],
                "is_active": True,
            },
        )

    return Instrument.objects.filter(is_active=True).order_by("name")


def get_instrument_by_id(instrument_id: int) -> Optional[Instrument]:
    return Instrument.objects.filter(id=instrument_id).first()


def get_instrument_by_code(code: str) -> Optional[Instrument]:
    return Instrument.objects.filter(code=code).first()


def get_test_applications() -> QuerySet[TestApplication]:
    return TestApplication.objects.with_details().all().order_by("-created_at")


def get_test_application_by_id(application_id: int) -> Optional[TestApplication]:
    return TestApplication.objects.with_details().filter(id=application_id).first()


def get_test_applications_by_evaluation(
    evaluation_id: int,
) -> QuerySet[TestApplication]:
    return (
        TestApplication.objects.with_details()
        .filter(evaluation_id=evaluation_id)
        .order_by("-created_at")
    )


def get_validated_test_applications_by_evaluation(
    evaluation_id: int,
) -> QuerySet[TestApplication]:
    return (
        TestApplication.objects.with_details()
        .filter(evaluation_id=evaluation_id, is_validated=True)
        .order_by("applied_on", "created_at")
    )


def get_active_template_for_instrument(
    instrument_id: int,
) -> Optional[TestInterpretationTemplate]:
    return (
        TestInterpretationTemplate.objects.filter(
            instrument_id=instrument_id,
            is_active=True,
        )
        .order_by("-updated_at")
        .first()
    )
