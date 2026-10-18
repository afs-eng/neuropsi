from unittest.mock import patch

import requests
from django.test import SimpleTestCase

from apps.reports.services.clinical_consistency_audit_service import ClinicalConsistencyAuditService


class ClinicalAuditDiagnosticsTests(SimpleTestCase):
    def setUp(self):
        self.fingerprint = patch(
            "apps.reports.services.report_approval_service.ReportApprovalService.fingerprint",
            return_value="source-fingerprint",
        )
        self.fingerprint.start()
        self.addCleanup(self.fingerprint.stop)
        payload = patch.object(ClinicalConsistencyAuditService, "_build_audit_payload", return_value={})
        payload.start()
        self.addCleanup(payload.stop)

    def audit(self, response):
        with patch.object(ClinicalConsistencyAuditService, "_call_ai", return_value=response):
            return ClinicalConsistencyAuditService.audit_report(object(), {})

    def test_different_response_failures_have_distinct_safe_codes(self):
        for content, code in [
            ("", "empty_response"), ("not JSON", "invalid_json"),
            ("{}", "invalid_schema"), ('{"alerts":null}', "invalid_schema"),
            ('{"alerts":[{"severity":"alta","issue":"Verificar"}]}', "invalid_schema"),
        ]:
            with self.subTest(content=content):
                result = self.audit({"content": content})
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["error_code"], code)
                self.assertEqual(result["source_sha256"], "source-fingerprint")
                self.assertEqual(result["alerts"][0]["severity"], "high")

    def test_truncation_cannot_be_accepted_even_if_partial_json_is_valid(self):
        for reason in ["length", "max_tokens"]:
            with self.subTest(reason=reason):
                result = self.audit({"content": '{"alerts":[]}', "finish_reason": reason})
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["error_code"], "truncated_response")

    def test_refusal_is_not_interpreted_as_a_clean_audit(self):
        result = self.audit({"content": '{"alerts":[]}', "finish_reason": "content_filter"})
        self.assertEqual(result["error_code"], "provider_refusal")
        self.assertEqual(result["status"], "error")

    def test_successful_empty_alert_list_is_still_valid(self):
        result = self.audit({"content": '{"alerts":[]}', "finish_reason": "stop"})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["alerts"], [])
        self.assertNotIn("error_code", result)

    def test_timeout_wrapped_by_legacy_service_is_identified(self):
        error = ValueError("Provider failed with sensitive details")
        error.__cause__ = requests.Timeout("Sensitive URL")
        with patch.object(ClinicalConsistencyAuditService, "_call_ai", side_effect=error):
            result = ClinicalConsistencyAuditService.audit_report(object(), {})
        self.assertEqual(result["error_code"], "provider_timeout")
        self.assertEqual(result["status"], "error")

    def test_rate_limit_and_auth_failures_are_distinct(self):
        for status, code in [(429, "provider_rate_limit"), (401, "provider_auth"), (402, "provider_auth")]:
            response = requests.Response()
            response.status_code = status
            error = requests.HTTPError("Sensitive data", response=response)
            with self.subTest(status=status), patch.object(ClinicalConsistencyAuditService, "_call_ai", side_effect=error):
                result = ClinicalConsistencyAuditService.audit_report(object(), {})
                self.assertEqual(result["error_code"], code)

    def test_logs_and_result_do_not_include_raw_provider_error_or_clinical_content(self):
        private = "Paciente privado TOKEN-SECRET"
        with patch.object(ClinicalConsistencyAuditService, "_call_ai", side_effect=ValueError(private)):
            with self.assertLogs("apps.reports.services.clinical_consistency_audit_service", level="WARNING") as logs:
                result = ClinicalConsistencyAuditService.audit_report(object(), {})
        self.assertNotIn(private, str(result))
        self.assertNotIn(private, " ".join(logs.output))
        self.assertIn("code=provider_error", " ".join(logs.output))

    def test_model_supplied_error_fields_are_not_logged_verbatim(self):
        private = "Paciente privado TOKEN-SECRET"
        with self.assertLogs("apps.reports.services.clinical_consistency_audit_service", level="WARNING") as logs:
            result = self.audit({"content": '{"status":"error","error_code":"' + private + '","alerts":[]}'})
        self.assertEqual(result["error_code"], "invalid_schema")
        self.assertNotIn(private, " ".join(logs.output))

    def test_non_dict_provider_response_is_rejected(self):
        self.assertEqual(self.audit(None)["status"], "error")
