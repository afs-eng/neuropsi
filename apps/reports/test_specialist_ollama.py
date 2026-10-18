import json
from unittest.mock import patch

import httpx2
from django.test import TestCase, override_settings

from apps.reports import test_specialist_runs
from apps.reports.services.specialist_agent_service import SpecialistAgentService
from apps.reports.services.specialist_run_service import SpecialistRunService


@override_settings(
    SPECIALIST_AI_ENABLED=True, SPECIALIST_AI_INSTRUMENTS=["wisc4"],
    SPECIALIST_AI_PROVIDER="ollama", SPECIALIST_AI_MODEL="qwen3:8b",
    SPECIALIST_OLLAMA_BASE_URL="http://127.0.0.1:11434/v1",
    AI_PROVIDER="openai", OPENAI_API_KEY="must-not-leave-process",
    OPENAI_BASE_URL="https://external.example/v1",
)
class SpecialistOllamaTests(TestCase):
    def setUp(self):
        test_specialist_runs.SpecialistRunTests.setUp(self)

    def enqueue(self):
        return SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)[0][0]

    @override_settings(OPENAI_API_KEY="")
    def test_local_configuration_does_not_require_remote_key(self):
        run = self.enqueue()
        self.assertEqual(run.provider_name, "ollama")
        self.assertEqual(run.provider_base_url, "http://127.0.0.1:11434/v1")
        self.assertEqual(run.model_name, "qwen3:8b")

    def test_remote_or_ambiguous_local_endpoints_are_rejected(self):
        for url in ["https://ollama.com/v1", "http://external.example/v1", "http://127.0.0.1:11434/api", "http://user:pass@localhost:11434/v1"]:
            with self.subTest(url=url), override_settings(SPECIALIST_OLLAMA_BASE_URL=url):
                with self.assertRaises(ValueError):
                    self.enqueue()

    def test_cloud_models_are_rejected(self):
        for model in ["qwen3:cloud", "org/qwen3:8b"]:
            with self.subTest(model=model), override_settings(SPECIALIST_AI_MODEL=model):
                with self.assertRaises(ValueError):
                    self.enqueue()

    def test_provider_change_is_not_deduplicated_and_blocks_old_run(self):
        with override_settings(SPECIALIST_AI_PROVIDER="openai", OPENAI_BASE_URL="http://127.0.0.1:11434/v1"):
            external = self.enqueue()
        local = self.enqueue()
        self.assertNotEqual(local.pk, external.pk)
        with patch.object(SpecialistAgentService, "generate") as generate:
            result = SpecialistRunService.process_next(report_id=self.report.pk)
            self.assertEqual(result.pk, external.pk)
            self.assertEqual(result.error_code, "configuration_changed")
            generate.assert_not_called()

    def mock_client(self, handler):
        def create(**kwargs):
            self.assertFalse(kwargs["trust_env"])
            self.assertFalse(kwargs["follow_redirects"])
            return httpx2.AsyncClient(transport=httpx2.MockTransport(handler), **kwargs)
        return patch("apps.reports.services.specialist_agent_service.DefaultAsyncHttpxClient", side_effect=create)

    def test_real_agent_sends_local_schema_no_thinking_no_external_key(self):
        run = self.enqueue()
        requests = []

        def respond(request):
            requests.append(request)
            body = json.loads(request.content)
            self.assertEqual(str(request.url), "http://127.0.0.1:11434/v1/chat/completions")
            self.assertEqual(request.headers["authorization"], "Bearer ollama-local")
            self.assertNotIn("must-not-leave-process", str(request.headers))
            self.assertEqual(body["reasoning_effort"], "none")
            self.assertEqual(body.get("max_tokens", body.get("max_completion_tokens")), 4000)
            self.assertEqual(body["response_format"]["type"], "json_schema")
            self.assertNotIn(self.patient.full_name, request.content.decode())
            self.assertEqual(body["model"], "qwen3:8b")
            return httpx2.Response(200, json={
                "id": "synthetic", "object": "chat.completion", "created": 1,
                "model": "qwen3:8b", "choices": [{"index": 0, "finish_reason": "stop", "message": {
                    "role": "assistant", "content": json.dumps(test_specialist_runs.VALID_OUTPUT),
                }}], "usage": {"prompt_tokens": 50, "completion_tokens": 60, "total_tokens": 110},
            })

        with self.mock_client(respond):
            output, usage = SpecialistAgentService.generate(run)
        self.assertEqual(output, test_specialist_runs.VALID_OUTPUT)
        self.assertEqual(usage["requests"], 1)
        self.assertEqual(len(requests), 1)

    def test_unavailable_local_server_fails_without_fallback(self):
        self.enqueue()
        calls = []

        def unavailable(request):
            calls.append(str(request.url))
            raise httpx2.ConnectError("offline", request=request)

        with self.mock_client(unavailable):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "provider_connection")
        self.assertEqual(calls, ["http://127.0.0.1:11434/v1/chat/completions"])
        self.assertEqual(result.output_payload, {})

    def test_direct_generation_also_blocks_changed_provider(self):
        run = self.enqueue()
        with override_settings(SPECIALIST_AI_PROVIDER="openai"):
            with patch("apps.reports.services.specialist_agent_service.AsyncOpenAI") as client:
                with self.assertRaises(ValueError):
                    SpecialistAgentService.generate(run)
                client.assert_not_called()

    def test_local_server_redirect_cannot_forward_clinical_payload(self):
        self.enqueue()
        calls = []

        def redirect(request):
            calls.append(str(request.url))
            return httpx2.Response(307, headers={"location": "https://external.example/v1/chat/completions"})

        with self.mock_client(redirect):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "failed")
        self.assertEqual(calls, ["http://127.0.0.1:11434/v1/chat/completions"])
