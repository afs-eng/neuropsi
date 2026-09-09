from django.core.management.base import BaseCommand
from apps.tests.models import Instrument


class Command(BaseCommand):
    help = "Cria instrumentos padrão do sistema"

    def handle(self, *args, **options):
        instrumentos = [
            {
                "code": "fdt",
                "name": "FDT - Five Digits Test",
                "category": "Funções executivas",
                "version": "1.0",
                "is_active": True,
            },
            {
                "code": "wisc4",
                "name": "WISC-IV - Escala de Inteligência de Wechsler para Crianças",
                "category": "Inteligência",
                "version": "4ª Edição",
                "is_active": True,
            },
            {
                "code": "wais3",
                "name": "WAIS-III - Escala de Inteligência de Wechsler para Adultos",
                "category": "Inteligência",
                "version": "3ª Edição",
                "is_active": True,
            },
            {
                "code": "bpa2",
                "name": "BPA-2 - Brief Psychological Assessment",
                "category": "Atenção",
                "version": "2ª Edição",
                "is_active": True,
            },
            {
                "code": "ebadep_a",
                "name": "EBADEP-A - Escala Brasileira de Avaliação de Déficits de Atenção e Hiperatividade - Adulto",
                "category": "TDAH",
                "version": "1.0",
                "is_active": True,
            },
            {
                "code": "ebadep_ij",
                "name": "EBADEP-IJ - Escala Brasileira de Avaliação de Déficits de Atenção e Hiperatividade - Infantojuvenil",
                "category": "TDAH",
                "version": "1.0",
                "is_active": True,
            },
            {
                "code": "epq_j",
                "name": "EPQ-J - Questionário de Personalidade para Crianças e Adolescentes",
                "category": "Personalidade",
                "version": "1.0",
                "is_active": True,
            },
            {
                "code": "etdah_ad",
                "name": "ETDAH-AD - Escala de Transtorno de Déficit de Atenção e Hiperatividade - Adulto",
                "category": "TDAH",
                "version": "1.0",
                "is_active": True,
            },
            {
                "code": "etdah_pais",
                "name": "ETDAH-PAIS - Escala de Transtorno de Déficit de Atenção e Hiperatividade - Versão para Pais",
                "category": "TDAH",
                "version": "1.0",
                "is_active": True,
            },
            {
                "code": "cars2_hf",
                "name": "CARS2-HF - Childhood Autism Rating Scale – Second Edition, High Functioning Version",
                "category": "Social / Autismo",
                "version": "1.0",
                "is_active": True,
            },
            {
                "code": "mchat",
                "name": "M-CHAT - Modified Checklist for Autism in Toddlers",
                "category": "Social / Autismo",
                "version": "1.0",
                "is_active": True,
            },
            {
                "code": "ssrs",
                "name": "SSRS - Inventario de Habilidades Sociais, Problemas de Comportamento e Competencia Academica",
                "category": "Social / Comportamento",
                "version": "1.0",
                "is_active": True,
            },
        ]

        for inst in instrumentos:
            obj, created = Instrument.objects.get_or_create(
                code=inst["code"], defaults=inst
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Criado: {obj.name}"))
            else:
                self.stdout.write(f"Já existe: {obj.name}")

        self.stdout.write(self.style.SUCCESS("Instrumentos criados com sucesso!"))
