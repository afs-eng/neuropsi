import json
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import UserRole
from apps.accounts.services import issue_api_token
from apps.evaluations.models import Evaluation
from apps.patients.models import Patient
from apps.tests.models import Instrument


class WISC4SubmitApiTests(TestCase):
    def test_submit_saves_wisc4_application(self):
        user = get_user_model().objects.create_user(
            username="clinico",
            email="clinico@example.com",
            password="secret123",
            role=UserRole.NEUROPSYCHOLOGIST,
        )
        token = issue_api_token(user)
        patient = Patient.objects.create(
            full_name="Paciente WISC",
            birth_date=date(2014, 5, 10),
            sex="F",
        )
        evaluation = Evaluation.objects.create(
            patient=patient,
            examiner=user,
            start_date=date(2024, 6, 1),
        )
        Instrument.objects.get_or_create(
            code="wisc4",
            defaults={
                "name": "WISC-IV - Escala de Inteligência Wechsler para Crianças",
                "category": "Inteligência",
                "version": "4",
            },
        )

        payload = {
            "evaluation_id": evaluation.id,
            "cb": "20",
            "sm": "18",
            "dg": "12",
            "cn": "14",
            "cd": "45",
            "vc": "24",
            "snl": "10",
            "rm": "18",
            "co": "20",
            "ps": "25",
            "cf": "",
            "ca": "",
            "in_": "",
            "ar": "",
            "rp": "",
            "cusb": "",
            "diod": "",
            "dioi": "",
            "caa": "",
            "cae": "",
            "udiod": "",
            "udioi": "",
        }

        response = self.client.post(
            "/api/tests/wisc4/submit",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data["application_id"], int)
        self.assertEqual(data["scores"]["cubos"], 20)
