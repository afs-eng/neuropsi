import json

from django.contrib.auth import get_user_model
from django.test import TestCase


class AccountAuthTests(TestCase):
    def test_login_returns_female_title_and_sex(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="jacqueline",
            email="jacqueline@example.com",
            password="secret123",
            full_name="Jacqueline Oliveira Caires",
            sex="F",
            specialty="Neuropsicóloga",
        )

        response = self.client.post(
            "/api/accounts/login",
            data=json.dumps({"email": "jacqueline@example.com", "password": "secret123"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["display_name"], "Dra. Jacqueline")
        self.assertEqual(data["user"]["sex"], "F")
