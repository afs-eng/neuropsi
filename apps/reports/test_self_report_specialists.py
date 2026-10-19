import copy
import json
from unittest.mock import patch

import httpx2
from django.test import SimpleTestCase, TestCase, override_settings
from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from apps.reports import test_specialist_runs
from apps.reports.models import SpecialistReview, SpecialistRun
from apps.reports.services.self_report_specialists import (
    BFP_FACTORS, BFP_FACETS, BFP_INSTRUCTIONS, ETDAH_AD_INSTRUCTIONS, ETDAH_FACTORS,
    SELF_REPORT_VERSIONS, self_report_reading_guide,
)
from apps.reports.services.specialist_agent_service import SpecialistAgentService
from apps.reports.services.specialist_contracts import (
    self_report_generation_model, specialist_output_model, validate_evidence,
)
from apps.reports.services.specialist_errors import SpecialistGenerationError, SpecialistValidationError, safe_diagnostics
from apps.reports.services.specialist_input_service import SpecialistInputService
from apps.reports.services.specialist_instructions import INSTRUMENT_INSTRUCTIONS
from apps.reports.services.specialist_review_service import SpecialistReviewService
from apps.reports.services.specialist_run_service import SpecialistRunService
from apps.tests.models import Instrument, TestApplication
from apps.tests.base.types import TestContext
from apps.tests.bfp import BFPModule
from apps.tests.etdah_ad import ETDAHADModule


def synthetic_sources(code):
    if code == "bfp":
        groups = {
            group: {scale: {"raw_score": float(index), "classification": "Média", "percentile": 50.0}
                    for index, scale in enumerate(known, 1)}
            for group, known in (("factors", BFP_FACTORS), ("facets", BFP_FACETS))
        }
        computed = {**groups, "sample": "geral"}
        classified = {
            "sample": "geral", "factor_classifications": dict.fromkeys(BFP_FACTORS, "Média"),
            "facet_classifications": dict.fromkeys(BFP_FACETS, "Média"),
        }
    else:
        scores = {scale: index for index, scale in enumerate(ETDAH_FACTORS)}
        computed = {"raw_scores": scores, "schooling": "higher"}
        classified = {
            "raw_scores": copy.deepcopy(scores), "schooling": "higher",
            "results": {scale: {"raw_score": score, "classification": "Média", "percentile_text": "40"}
                        for scale, score in scores.items()},
        }
    return computed, classified


def synthetic_output(code, facts):
    dimensions = self_report_reading_guide(code, facts)["dimensions"]
    if code == "bfp":
        groups = [[factor, *(scale for scale in BFP_FACETS if scale[0] == factor[0])]
                  for factor in BFP_FACTORS]
    else:
        groups = [["D", "I"], ["AE"], ["AAMA"], ["H", "escore_geral"]]
    findings = []
    for group in groups:
        scales = [scale for scale in group if scale in dimensions]
        if not scales:
            continue
        refs = [dimensions[scale] for scale in scales]
        descriptions, evidence = [], []
        for item in refs:
            classes = item["classification_ids"]
            descriptions.append(f"{item['name']}: classificação {facts[classes[0]]}" if classes else f"{item['name']}: somente escore disponível")
            evidence.append((classes or item["score_ids"])[0])
        findings.append({
            "statement": "; ".join(descriptions) + ". Os resultados descrevem apenas as dimensões deste autorrelato, sem diagnóstico.",
            "scale_codes": scales, "evidence_ids": evidence,
        })
    return {
        "findings": findings,
        "limitations": ["Escopo restrito ao autorrelato. Faltam manual/versão, validade e integração clínica; requer revisão profissional."],
        "review_questions": ["Conferir as lacunas indicadas no guia, a referência normativa e a validade antes de interpretar clinicamente."],
    }


def flat_facts(code):
    computed, classified = synthetic_sources(code)
    facts = {}

    def visit(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, f"{path}/{key}")
        else:
            facts[path] = value

    visit(computed, "/computed_payload")
    visit(classified, "/classified_payload")
    return facts


class SelfReportContractTests(SimpleTestCase):
    def validate(self, code, data, facts):
        return validate_evidence(specialist_output_model(code).model_validate(data), facts, code)

    def test_both_profiles_cover_all_dimensions_without_percentiles_in_prose(self):
        for code in SELF_REPORT_VERSIONS:
            with self.subTest(code=code):
                facts = flat_facts(code)
                data = synthetic_output(code, facts)
                original = copy.deepcopy(data)
                self.validate(code, data, facts)
                self.assertEqual(data, original)
                self.assertGreaterEqual(len(data["findings"]), 2)
                self.assertLessEqual(len(data["findings"]), 5)
                guide = self_report_reading_guide(code, facts)
                self.assertEqual(len(guide["dimensions"]), 22 if code == "bfp" else 6)
                self.assertTrue(any(item["percentile_ids"] for item in guide["dimensions"].values()))

    def test_schemas_require_dimensions_and_reject_extra_diagnoses(self):
        for code in SELF_REPORT_VERSIONS:
            data = synthetic_output(code, flat_facts(code))
            for mutation in ("diagnosis", "missing_codes", "too_few", "too_many"):
                wrong = copy.deepcopy(data)
                if mutation == "diagnosis":
                    wrong["diagnosis"] = "Não permitido"
                elif mutation == "missing_codes":
                    wrong["findings"][0].pop("scale_codes")
                elif mutation == "too_few":
                    wrong["findings"] = wrong["findings"][:1]
                else:
                    wrong["findings"] = wrong["findings"] * 2
                with self.subTest(code=code, mutation=mutation), self.assertRaises(ValidationError):
                    specialist_output_model(code).model_validate(wrong)

    def test_native_schema_enumerates_only_the_current_applications_dimensions_and_facts(self):
        schemas = {}
        for code in SELF_REPORT_VERSIONS:
            facts = flat_facts(code)
            schema = self_report_generation_model(code, facts).model_json_schema()
            props = schema["$defs"]["SelfReportGroundedFinding"]["properties"]
            self.assertEqual(props["evidence_ids"]["items"]["enum"], sorted(facts))
            schemas[code] = props["scale_codes"]["items"]["enum"]
            self.assertEqual(schemas[code], sorted(self_report_reading_guide(code, facts)["dimensions"]))
        self.assertNotIn("NN", schemas["etdah_ad"])
        self.assertNotIn("AAMA", schemas["bfp"])

    def test_percentiles_are_rejected_in_every_textual_field_even_when_grounded(self):
        for code in SELF_REPORT_VERSIONS:
            facts = flat_facts(code)
            for text in ("percentil 50", "percentis informados", "posição percentílica", "centil 50", "P50", "50%", "por cento"):
                for field in ("statement", "limitations", "review_questions"):
                    data = synthetic_output(code, facts)
                    if field == "statement":
                        data["findings"][0][field] += f" Referência: {text}."
                        data["findings"][0]["evidence_ids"].extend(self_report_reading_guide(code, facts)["dimensions"][data["findings"][0]["scale_codes"][0]]["percentile_ids"])
                    else:
                        data[field] = [f"Conferir {text} na tabela antes da revisão."]
                    with self.subTest(code=code, text=text, field=field), self.assertRaises(SpecialistValidationError):
                        self.validate(code, data, facts)

    def test_missing_foreign_duplicate_and_omitted_dimensions_are_rejected(self):
        for mutation in ("foreign", "duplicate", "omit", "no_class_evidence", "wrong_class"):
            for code in SELF_REPORT_VERSIONS:
                facts = flat_facts(code)
                data = synthetic_output(code, facts)
                finding = data["findings"][0]
                if mutation == "foreign":
                    finding["scale_codes"].append("not_in_application")
                elif mutation == "duplicate":
                    finding["scale_codes"].append(finding["scale_codes"][0])
                elif mutation == "omit":
                    data["findings"].pop()
                elif mutation == "no_class_evidence":
                    finding["evidence_ids"] = ["/computed_payload/sample" if code == "bfp" else "/computed_payload/schooling"]
                else:
                    finding["statement"] = finding["statement"].replace("Média", "Superior")
                with self.subTest(code=code, mutation=mutation), self.assertRaises(SpecialistValidationError):
                    self.validate(code, data, facts)

    def test_conflicting_classifications_and_scores_block_source_preparation(self):
        facts = flat_facts("bfp")
        facts["/classified_payload/factor_classifications/NN"] = "Superior"
        with self.assertRaisesRegex(ValueError, "divergentes"):
            self_report_reading_guide("bfp", facts)
        for path in ("/computed_payload/raw_scores/D", "/classified_payload/raw_scores/D", "/classified_payload/results/D/raw_score"):
            facts = flat_facts("etdah_ad")
            facts[path] = 100
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "divergentes"):
                self_report_reading_guide("etdah_ad", facts)

    def test_zero_scores_are_preserved_and_not_replaced_by_missing_values(self):
        facts = flat_facts("etdah_ad")
        guide = self_report_reading_guide("etdah_ad", facts)
        self.assertEqual([facts[key] for key in guide["dimensions"]["D"]["score_ids"]], [0, 0, 0])

    def test_mixed_classifications_remain_exact_for_factors_and_facets(self):
        for code in SELF_REPORT_VERSIONS:
            facts = flat_facts(code)
            for index, item in enumerate(self_report_reading_guide(code, facts)["dimensions"].values()):
                label = ("Média Inferior", "Muito Superior", "Superior", "Baixo", "Média Superior")[index % 5]
                for key in item["classification_ids"]:
                    facts[key] = label
            self.validate(code, synthetic_output(code, facts), facts)

    def test_percentile_evidence_does_not_authorize_relabeling_it_as_a_score(self):
        for code in SELF_REPORT_VERSIONS:
            facts = flat_facts(code)
            data = synthetic_output(code, facts)
            refs = self_report_reading_guide(code, facts)["dimensions"][data["findings"][0]["scale_codes"][0]]
            key = refs["percentile_ids"][0]
            data["findings"][0]["evidence_ids"].append(key)
            data["findings"][0]["statement"] += f" O escore foi {facts[key]}."
            with self.subTest(code=code), self.assertRaises(SpecialistValidationError) as caught:
                self.validate(code, data, facts)
            self.assertEqual(caught.exception.code, "ungrounded_number")

    def test_native_schema_does_not_cache_another_applications_evidence(self):
        facts = flat_facts("etdah_ad")
        first = self_report_generation_model("etdah_ad", facts).model_json_schema()
        second = self_report_generation_model("etdah_ad", {**facts, "/application/age_months": 300}).model_json_schema()
        def ids(schema):
            return schema["$defs"]["SelfReportGroundedFinding"]["properties"]["evidence_ids"]["items"]["enum"]
        self.assertNotIn("/application/age_months", ids(first))
        self.assertIn("/application/age_months", ids(second))

    def test_invalid_nonfinite_or_boolean_scores_are_not_usable_facts(self):
        for value in (True, float("inf"), float("nan"), "0"):
            facts = flat_facts("bfp")
            facts["/computed_payload/factors/NN/raw_score"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self_report_reading_guide("bfp", facts)

    def test_missing_classification_is_not_normal_and_requires_pending_questions(self):
        facts = flat_facts("etdah_ad")
        del facts["/classified_payload/results/D/classification"]
        guide = self_report_reading_guide("etdah_ad", facts)
        self.assertIn("classification:D", guide["missing_data"])
        data = synthetic_output("etdah_ad", facts)
        self.validate("etdah_ad", data, facts)
        data["review_questions"] = []
        with self.assertRaises(SpecialistValidationError) as caught:
            self.validate("etdah_ad", data, facts)
        self.assertEqual(caught.exception.code, "self_report_missing_data")

    def test_missing_dimensions_cannot_be_invented_or_required_as_aggregate(self):
        facts = flat_facts("etdah_ad")
        facts = {key: value for key, value in facts.items() if "/escore_geral" not in key and "/H" not in key}
        guide = self_report_reading_guide("etdah_ad", facts)
        self.assertIn("dimension:H", guide["missing_data"])
        self.assertNotIn("dimension:escore_geral", guide["missing_data"])
        self.assertNotIn("H", guide["dimensions"])
        self.validate("etdah_ad", synthetic_output("etdah_ad", facts), facts)

    def test_metadata_only_and_invalid_classification_are_not_clinical_results(self):
        for code in SELF_REPORT_VERSIONS:
            with self.assertRaises(ValueError):
                self_report_reading_guide(code, {"/application/age_months": 300})
            facts = flat_facts(code)
            class_key = next(key for key in facts if key.endswith("/classification"))
            facts[class_key] = "Normal inventado"
            with self.assertRaises(ValueError):
                self_report_reading_guide(code, facts)

    def test_known_diagnosis_assertions_are_blocked_but_negative_limits_are_accepted(self):
        for code in SELF_REPORT_VERSIONS:
            for text in ("Confirma diagnóstico de TDAH.", "Apresenta transtorno de personalidade.", "Diagnóstico CID F90."):
                facts = flat_facts(code)
                data = synthetic_output(code, facts)
                data["findings"][0]["statement"] += " " + text
                with self.subTest(code=code, text=text), self.assertRaises(SpecialistValidationError):
                    self.validate(code, data, facts)
            data = synthetic_output(code, facts)
            data["findings"][0]["statement"] += " Não estabelece diagnóstico nem confirma TDAH."
            self.validate(code, data, facts)

    def test_etdah_clinical_direction_cannot_be_invented_from_superior(self):
        facts = {key: ("Superior" if key.endswith("/classification") else value) for key, value in flat_facts("etdah_ad").items()}
        self.assertIn("clinical_direction_by_factor", self_report_reading_guide("etdah_ad", facts)["missing_data"])
        for text in ("Isso indica maior frequência de sintomas.", "Há melhor desempenho.", "Foram observados sintomas elevados."):
            data = synthetic_output("etdah_ad", facts)
            data["findings"][0]["statement"] += " " + text
            with self.subTest(text=text), self.assertRaises(SpecialistValidationError):
                self.validate("etdah_ad", data, facts)

    def test_unknown_evidence_and_numbers_are_never_repaired_silently(self):
        for code in SELF_REPORT_VERSIONS:
            facts = flat_facts(code)
            for text, evidence in (("", "/made_up"), (" Escore 999.", None)):
                data = synthetic_output(code, facts)
                data["findings"][0]["statement"] += text
                if evidence:
                    data["findings"][0]["evidence_ids"].append(evidence)
                with self.subTest(code=code, text=text), self.assertRaises(SpecialistValidationError):
                    self.validate(code, data, facts)

    def test_diagnostics_only_persist_allowlisted_codes(self):
        result = safe_diagnostics(validation_code="self_report_classification", validation_section="Paciente privado")
        self.assertEqual(result, {"validation_code": "self_report_classification"})

    def test_existing_specialists_and_bpa2_versions_remain_unchanged(self):
        self.assertEqual(len(INSTRUMENT_INSTRUCTIONS), 11)
        self.assertEqual(SpecialistRunService.version_for("wisc4", "openai"), "pydantic-specialist-1")
        self.assertEqual(SpecialistRunService.version_for("bpa2", "openai"), "pydantic-bpa2-6")
        self.assertIn("Pró-Sociabilidade", BFP_INSTRUCTIONS)
        self.assertIn("direção clínica", ETDAH_AD_INSTRUCTIONS)
        for code, version in SELF_REPORT_VERSIONS.items():
            self.assertEqual(SpecialistRunService.version_for(code, "ollama"), version + "-ollama-4k")


@override_settings(
    SPECIALIST_AI_ENABLED=True, SPECIALIST_AI_INSTRUMENTS=["bfp", "etdah_ad"],
    SPECIALIST_AI_PROVIDER="ollama", SPECIALIST_AI_MODEL="synthetic-local-model",
    SPECIALIST_OLLAMA_BASE_URL="http://127.0.0.1:11434/v1",
    OPENAI_API_KEY="must-not-leave-process", OPENAI_BASE_URL="https://external.example/v1",
)
class SelfReportIntegrationTests(TestCase):
    def setUp(self):
        test_specialist_runs.SpecialistRunTests.setUp(self)
        self.application.delete()
        self.patient.birth_date = self.patient.birth_date.replace(year=1990)
        self.patient.save(update_fields=["birth_date"])
        self.owner.crp = "00/12345"
        self.owner.save(update_fields=["crp"])
        self.applications = {}
        for code in SELF_REPORT_VERSIONS:
            instrument, _ = Instrument.objects.get_or_create(code=code, defaults={"name": code.upper()})
            computed, classified = synthetic_sources(code)
            computed.update({"responses": {"1": 4}, "response_scale": {"1": "Item protegido"}})
            if code == "bfp":
                computed["facets"]["N1"].update({"reversed_items": [1, 2], "item_count": 9, "interpretation": "Texto antigo privado"})
            classified["interpretation"] = "Texto antigo privado"
            self.applications[code] = TestApplication.objects.create(
                evaluation=self.evaluation, instrument=instrument, is_validated=True,
                computed_payload=computed, classified_payload=classified,
                raw_payload={"responses": {"1": 4}, "respondent_name": "Mãe Exemplo"},
                interpretation_text="Interpretação humana preservada.",
            )

    def enqueue(self, code):
        runs, skipped = SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk, application_ids=[self.applications[code].pk])
        self.assertEqual(skipped, [])
        return runs[0]

    def generator(self, run):
        return synthetic_output(run.instrument_code, run.input_payload["facts"]), {"requests": 1, "input_tokens": 20, "output_tokens": 50}

    def test_input_excludes_items_keys_identifiers_and_old_narratives(self):
        for code, app in self.applications.items():
            payload = SpecialistInputService.build(app)
            text = json.dumps(payload, ensure_ascii=False)
            for excluded in ("responses", "response_scale", "reversed_items", "item_count", "Item protegido", "Texto antigo privado", "Mãe Exemplo", self.patient.full_name):
                self.assertNotIn(excluded, text)
            self.assertEqual(payload["instrument_code"], code)
            self.assertIn("/application/age_months", payload["facts"])
            self.assertEqual(payload, SpecialistInputService.build(app))

    def test_real_deterministic_modules_produce_compatible_private_inputs(self):
        for code, module, responses in (
            ("bfp", BFPModule(), {str(index): 4 for index in range(1, 127)}),
            ("etdah_ad", ETDAHADModule(), {index: 2 for index in range(1, 70)}),
        ):
            app = self.applications[code]
            context = TestContext(
                patient_name=self.patient.full_name, evaluation_id=self.evaluation.pk, instrument_code=code,
                raw_scores={"responses": responses, "sample": "geral", "schooling": "higher"},
            )
            app.computed_payload = module.compute(context)
            app.classified_payload = module.classify(app.computed_payload)
            payload = SpecialistInputService.build(app)
            self.assertNotIn("responses", json.dumps(payload))
            self.assertNotIn("reversed_items", json.dumps(payload))
            self.assertEqual(len(payload["reading_guide"]["dimensions"]), 22 if code == "bfp" else 5)
            validate_evidence(
                specialist_output_model(code).model_validate(synthetic_output(code, payload["facts"])),
                payload["facts"], code,
            )

    def test_conflicting_sources_abort_enqueue_without_creating_jobs(self):
        app = self.applications["bfp"]
        app.classified_payload["factor_classifications"]["NN"] = "Superior"
        app.save()
        with self.assertRaises(ValueError):
            self.enqueue("bfp")
        self.assertFalse(SpecialistRun.objects.exists())

    def test_unusable_or_malformed_sources_do_not_generate_interpretation(self):
        for computed in ({"responses": {"1": 1}}, {"factors": []}, {"factors": {"foreign": {"raw_score": 1}}}, {"factors": {"NN": {"raw_score": []}}}):
            app = self.applications["bfp"]
            app.computed_payload, app.classified_payload = computed, {}
            with self.subTest(computed=computed), self.assertRaises(ValueError):
                SpecialistInputService.build(app)

    def test_explicit_allowlist_status_and_api_privacy(self):
        path = f"/{self.report.pk}/specialist-status"
        with patch.object(SpecialistAgentService, "generate") as generate:
            self.assertEqual(self.client.get(path).status_code, 401)
            self.assertEqual(self.client.get(path, headers=self.other_headers).status_code, 404)
            response = self.client.get(path, headers=self.headers)
            self.assertEqual(response["Cache-Control"], "private, no-store")
            self.assertTrue(all(app["supported"] and app["enabled"] for app in response.json()["applications"]))
            with override_settings(SPECIALIST_AI_INSTRUMENTS=[]):
                status = self.client.get(path, headers=self.headers).json()
                self.assertFalse(status["can_request"])
                self.assertTrue(all(app["supported"] and not app["enabled"] for app in status["applications"]))
                runs, skipped = SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)
                self.assertEqual(runs, [])
                self.assertEqual(len(skipped), 2)
            generate.assert_not_called()

    def test_queue_is_idempotent_and_professional_review_preserves_original_report(self):
        for code in SELF_REPORT_VERSIONS:
            run = self.enqueue(code)
            self.assertEqual(self.enqueue(code).pk, run.pk)
            result = SpecialistRunService.process_next(generator=self.generator, report_id=self.report.pk)
            self.assertEqual(result.status, "needs_review")
            review = SpecialistReviewService.review(
                user=self.owner, report_id=self.report.pk, run_id=run.pk, decision="approved", notes="Revisão sintética.",
                source_sha256=run.source_sha256, output_sha256=SpecialistReviewService.output_fingerprint(result),
            )
            self.assertEqual(review.decision, "approved")
            self.applications[code].refresh_from_db()
            self.assertEqual(self.applications[code].interpretation_text, "Interpretação humana preservada.")
        self.report.refresh_from_db()
        self.section.refresh_from_db()
        self.assertEqual(self.report.status, "draft")
        self.assertEqual(self.report.edited_text, "Texto revisado que deve ser preservado.")
        self.assertEqual(self.section.content_edited, "Revisão humana.")
        self.assertEqual(SpecialistReview.objects.count(), 2)

    def test_each_application_has_its_own_job_and_corrections_invalidate_old_sources(self):
        app = self.applications["bfp"]
        first = self.enqueue("bfp")
        second_app = TestApplication.objects.create(
            evaluation=self.evaluation, instrument=app.instrument, is_validated=True,
            computed_payload=app.computed_payload, classified_payload=app.classified_payload,
            raw_payload={"respondent_name": "Outro informante"},
        )
        runs, _ = SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk, application_ids=[app.pk, second_app.pk])
        self.assertEqual(len(runs), 2)
        self.assertEqual(len({run.pk for run in runs}), 2)
        app.computed_payload["factors"]["NN"]["raw_score"] = 4
        app.save()
        self.assertFalse(SpecialistRunService.is_current(SpecialistRunService._load(first.pk)))
        self.assertNotEqual(self.enqueue("bfp").pk, first.pk)

    def test_invalid_draft_fails_without_text_persistence_or_automatic_replay(self):
        self.enqueue("etdah_ad")

        def wrong(run):
            data, usage = self.generator(run)
            data["findings"][0]["statement"] += " Conteúdo privado inválido: percentis informados."
            return data, usage

        result = SpecialistRunService.process_next(generator=wrong, report_id=self.report.pk)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.output_payload, {})
        self.assertEqual(result.usage_payload["validation_code"], "self_report_percentile_text")
        self.assertNotIn("privado", json.dumps(result.usage_payload))
        with patch.object(SpecialistAgentService, "generate") as generate:
            self.assertIsNone(SpecialistRunService.process_next(report_id=self.report.pk))
            generate.assert_not_called()

    def test_finalized_or_unvalidated_sources_never_call_the_model(self):
        self.enqueue("bfp")
        self.applications["bfp"].is_validated = False
        self.applications["bfp"].save()
        with patch.object(SpecialistAgentService, "generate") as generate:
            result = SpecialistRunService.process_next(report_id=self.report.pk)
            self.assertEqual(result.status, "stale")
            generate.assert_not_called()
        self.report.status = "finalized"
        self.report.save()
        with self.assertRaises(ValueError):
            self.enqueue("etdah_ad")

    def test_approval_revalidates_contract_and_rejects_changed_or_invalid_output(self):
        run = self.enqueue("etdah_ad")
        result = SpecialistRunService.process_next(generator=self.generator, report_id=self.report.pk)
        result.output_payload["findings"][0]["statement"] += " Confirma TDAH."
        result.save(update_fields=["output_payload"])
        with self.assertRaises(ValueError):
            SpecialistReviewService.review(
                user=self.owner, report_id=self.report.pk, run_id=run.pk, decision="approved", notes="",
                source_sha256=run.source_sha256, output_sha256=SpecialistReviewService.output_fingerprint(result),
            )
        self.assertFalse(SpecialistReview.objects.exists())

    def test_real_agent_offline_retries_editorial_failures_within_existing_budget(self):
        for code in SELF_REPORT_VERSIONS:
            run = self.enqueue(code)
            valid = synthetic_output(code, run.input_payload["facts"])
            invalid = copy.deepcopy(valid)
            invalid["findings"][0]["statement"] += " Percentis informados."
            calls = []

            def respond(messages, info):
                calls.append(messages)
                self.assertNotIn(self.patient.full_name, str(messages))
                return ModelResponse(parts=[TextPart(json.dumps(invalid if len(calls) == 1 else valid))])

            with patch("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False):
                output, usage = SpecialistAgentService.generate(run, model_override=FunctionModel(respond))
            self.assertEqual(output, valid)
            self.assertEqual(usage["requests"], 2)
            self.assertEqual(len(calls), 2)

    def test_agent_terminal_failure_has_safe_diagnostics_and_no_fallback(self):
        run = self.enqueue("bfp")
        data = synthetic_output("bfp", run.input_payload["facts"])
        data["findings"][0]["statement"] += " Percentis informados."
        calls = []

        def respond(messages, info):
            calls.append(1)
            return ModelResponse(parts=[TextPart(json.dumps(data))])

        with patch("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False), self.assertRaises(SpecialistGenerationError) as caught:
            SpecialistAgentService.generate(run, model_override=FunctionModel(respond))
        self.assertEqual(len(calls), 2)
        self.assertEqual(caught.exception.code, "output_validation_failed")
        self.assertEqual(caught.exception.diagnostics["validation_code"], "self_report_percentile_text")

    def test_ollama_transport_is_mocked_local_only_and_keeps_four_thousand_token_limit(self):
        for code in SELF_REPORT_VERSIONS:
            run = self.enqueue(code)
            valid = synthetic_output(code, run.input_payload["facts"])
            requests = []

            def respond(request):
                requests.append(request)
                body = json.loads(request.content)
                self.assertEqual(str(request.url), "http://127.0.0.1:11434/v1/chat/completions")
                self.assertEqual(request.headers["authorization"], "Bearer ollama-local")
                self.assertNotIn("must-not-leave-process", str(request.headers))
                self.assertEqual(body.get("max_tokens", body.get("max_completion_tokens")), 4000)
                self.assertEqual(body["reasoning_effort"], "none")
                self.assertEqual(body["response_format"]["type"], "json_schema")
                self.assertNotIn(self.patient.full_name, request.content.decode())
                return httpx2.Response(200, json={
                    "id": "synthetic", "object": "chat.completion", "created": 1, "model": "synthetic-local-model",
                    "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(valid)}}],
                    "usage": {"prompt_tokens": 50, "completion_tokens": 60, "total_tokens": 110},
                })

            def client(**kwargs):
                self.assertFalse(kwargs["trust_env"])
                self.assertFalse(kwargs["follow_redirects"])
                return httpx2.AsyncClient(transport=httpx2.MockTransport(respond), **kwargs)

            with patch("apps.reports.services.specialist_agent_service.DefaultAsyncHttpxClient", side_effect=client):
                output, usage = SpecialistAgentService.generate(run)
            self.assertEqual(output, valid)
            self.assertEqual(usage["requests"], 1)
            self.assertEqual(len(requests), 1)
