from apps.tests.models import Instrument


REQUIRED_INSTRUMENTS = [
    {
        "code": "bfp",
        "name": "BFP - Bateria Fatorial de Personalidade",
        "category": "Personalidade",
    },
    {
        "code": "wasi",
        "name": "WASI - Escala Wechsler Abreviada de Inteligência",
        "category": "Inteligência",
    },
    {
        "code": "scared",
        "name": "SCARED - Screen for Child Anxiety",
        "category": "Ansiedade",
    },
    {"code": "ravlt", "name": "RAVLT - Memória Auditiva", "category": "Memoria"},
    {
        "code": "srs2",
        "name": "SRS-2 - Escala de Responsividade Social",
        "category": "Social / Autismo",
    },
    {
        "code": "ssrs",
        "name": "SSRS - Habilidades Sociais",
        "category": "Social / Comportamento",
    },
    {
        "code": "bai",
        "name": "BAI - Inventário de Ansiedade de Beck",
        "category": "Ansiedade",
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


def ensure_required_instruments() -> None:
    for item in REQUIRED_INSTRUMENTS:
        Instrument.objects.get_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "category": item["category"],
                "is_active": True,
            },
        )
