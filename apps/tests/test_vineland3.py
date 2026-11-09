import json
from copy import deepcopy
from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from docx import Document

from apps.accounts.models import UserRole
from apps.accounts.services import issue_api_token
from apps.evaluations.models import Evaluation
from apps.patients.models import Patient
from apps.reports.builders.tests_builder import build_validated_tests_snapshot
from apps.reports.services.report_export_service import ReportExportService
from apps.tests.base.types import TestContext
from apps.tests.models import Instrument, TestApplication
from apps.tests.registry import get_test_module
from apps.tests.services.scoring_service import TestScoringService
from apps.tests.vineland3 import Vineland3Module
from apps.tests.vineland3 import domain_protocol
from apps.tests.vineland3.calculators import compute_scores
from apps.tests.vineland3.item_protocol import DOMAIN_ITEMS, PROTOCOL_ID, item_protocol, normalize_item_responses
from apps.tests.vineland3.import_norms import age_range
from apps.tests.vineland3.norms import age_months, age_table, load_norms, lookup
from apps.tests.vineland3.validators import validate_input


# D.1, PDF page 8: these raw ranges correspond to v-scale 15.
PROFESSOR_SCORES = {"rec": 40, "exp": 47, "esc": 4, "pes": 30, "num": 5,
                    "cme": 19, "rin": 38, "bri": 24, "enf": 32, "cmg": 38, "cmf": 20}


def raw(form="professores", birth="2023-01-15", applied="2026-01-15"):
    table = age_table(form, "subdomains", age_months({"birth_date": birth, "reference_date": applied}))
    scores = {key: entries[0][0] for key, entries in table["scores"].items() if entries}
    return {"form": form, "respondent": "Respondente de referência", "entry_mode": "totals",
            "birth_date": birth, "reference_date": applied, "raw_scores": scores}


class Vineland3NormTests(SimpleTestCase):
    def test_domain_level_bank_has_all_180_items_in_seven_sections(self):
        protocol = domain_protocol.item_protocol()
        self.assertEqual([len(domain["items"]) for domain in protocol["domains"]], [40, 40, 40, 25, 13, 11, 11])
        self.assertTrue(protocol["complete"])
        self.assertTrue(protocol["supports_estimates"])
        self.assertFalse(protocol["scoring_enabled"])
        self.assertEqual(set(protocol["legend"]), {"2", "1", "0"})
        for domain in protocol["domains"]:
            self.assertEqual([item["id"] for item in domain["items"]], [str(i) for i in range(1, len(domain["items"]) + 1)])
            for item in domain["items"]:
                self.assertNotIn("TRANSCRIÇÃO NÃO RECUPERADA", item["text"])
                self.assertNotIn("[", item["text"])
        # OCR merged these questions into their predecessors; the PDF separates them.
        self.assertTrue(domain_protocol.DOMAIN_ITEMS["comunicacao"][1][28].startswith("Compreende a ordem alfabética."))
        self.assertTrue(domain_protocol.DOMAIN_ITEMS["vida_diaria"][1][30].startswith("Lava a louça."))
        self.assertTrue(domain_protocol.DOMAIN_ITEMS["atividade_fisica"][1][0].startswith("Desembrulha pequenos objetos."))
        self.assertIn("arranca o cabelo", domain_protocol.DOMAIN_ITEMS["comportamento_c"][1][2])

    def test_domain_level_drafts_preserve_zero_blank_estimates_and_notes(self):
        data = {"comunicacao": {"1": {"response": "0", "estimated": True, "observation": "Conferir"},
                                "2": {"response": ""}}, "comportamento_c": {"11": {"response": "2"}}}
        result = domain_protocol.normalize_item_responses(data)
        self.assertEqual(result["comunicacao"]["1"], data["comunicacao"]["1"])
        self.assertEqual(result["comunicacao"]["2"], {"response": "", "estimated": False, "observation": ""})
        self.assertEqual(domain_protocol.normalize_item_responses({}), {})

    def test_domain_level_binary_items_and_strict_estimates(self):
        for domain, numbers in domain_protocol.BINARY_ITEMS.items():
            for number in numbers:
                for value in ("0", "2", ""):
                    domain_protocol.normalize_item_responses({domain: {str(number): {"response": value}}})
                with self.assertRaises(ValueError):
                    domain_protocol.normalize_item_responses({domain: {str(number): {"response": "1"}}})
        for entry in ({"response": "N"}, {"response": "D"}, {"response": 0}, {"response": True},
                      {"response": "3"}, {"response": "20"}, {"response": " ", "estimated": False},
                      {"response": "", "estimated": True}, {"response": "2", "estimated": "true"},
                      {"response": "2", "estimated": 1}, {"response": "2", "observation": None},
                      {"response": "2", "observation": "x" * 2001}, {"response": "2", "score": 2}):
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                domain_protocol.normalize_item_responses({"comunicacao": {"1": entry}})
        for data in (None, [], {"autonomia": {}}, {"vida_diaria": {"41": {}}}, {"comportamento_c": {"12": {}}}):
            with self.assertRaises(ValueError):
                domain_protocol.normalize_item_responses(data)

    def test_importer_understands_portuguese_and_english_age_ranges(self):
        for text, expected in [("Idades 0:2:0–0:2:30", (2, 2)), ("Ages 3:0–3:3", (36, 39)),
                               ("Ages 90+", (1080, None))]:
            self.assertEqual(age_range(text), expected)

    def test_partial_bank_is_not_presented_as_verified_vineland3(self):
        protocol = item_protocol()
        self.assertFalse(protocol["edition_verified"])
        self.assertFalse(protocol["scoring_enabled"])
        self.assertFalse(protocol["complete"])
        self.assertEqual([len(items) for _, items in DOMAIN_ITEMS.values()], [33, 10, 5, 5, 5])
        self.assertEqual(set(protocol["legend"]), {"2", "1", "0", "N", "D"})

    def test_item_codes_blank_and_observations_are_preserved(self):
        for code in ("2", "1", "0", "N", "D", "n", "d", ""):
            with self.subTest(code=code):
                data = normalize_item_responses({"comunicacao": {"1": {"response": code, "observation": "Observação clínica"}}})
                self.assertEqual(data["comunicacao"]["1"], {"response": code.upper(), "observation": "Observação clínica"})
        self.assertEqual(normalize_item_responses({}), {})

    def test_invalid_item_codes_and_identifiers_are_rejected_not_coerced(self):
        for code in (0, 2, True, None, "3", "20", "ND", " "):
            with self.subTest(code=code), self.assertRaises(ValueError):
                normalize_item_responses({"comunicacao": {"1": {"response": code}}})
        for data in (None, [], {"unknown": {}}, {"comunicacao": []}, {"comunicacao": {"34": {}}},
                     {"autonomia": {"1": {"observation": None}}}, {"autonomia": {"1": {"observation": "x" * 2001}}},
                     {"autonomia": {"1": {"score": 0}}}):
            with self.subTest(data=str(data)[:80]), self.assertRaises(ValueError):
                normalize_item_responses(data)

    def test_registry_and_reference_case_from_d1_d3(self):
        self.assertIsInstance(get_test_module("vineland3"), Vineland3Module)
        data = compute_scores({**raw(), "raw_scores": PROFESSOR_SCORES})
        self.assertEqual({row["v_scale"] for row in data["subdomains"]}, {15})
        # D.3 PDF page 58, extensive (left) columns, not domain-level columns.
        domains = {row["scale"]: row for row in data["domains"]}
        self.assertEqual({key: row["standard_score"] for key, row in domains.items()},
                         {"COM": 99, "AVD": 98, "SOC": 100, "HMOT": 99, "ABC": 99})
        self.assertEqual(domains["ABC"]["sum_standard_scores"], 297)
        self.assertEqual(domains["ABC"]["percentile"], "47")
        self.assertEqual(data["norm_source"]["domain_pages"], [57, 58, 59])

    def test_source_coverage_and_continuity(self):
        expected = {"entrevista": (90, 30), "pais_cuidadores": (90, 30), "professores": (46, 23)}
        for form, source in load_norms()["forms"].items():
            self.assertEqual((len(source["subdomains"]), len(source["domains"])), expected[form])
            self.assertEqual(len(source["sha256"]), 64)
            for kind in ["subdomains", "domains"]:
                for previous, current in zip(source[kind], source[kind][1:]):
                    self.assertEqual(previous["max_months"] + 1, current["min_months"])
                for table in source[kind]:
                    for entries in table["scores"].values():
                        for previous, current in zip(entries, entries[1:]):
                            self.assertEqual(previous[1] + 1, current[0])

    def test_every_age_band_can_compute_minimum_and_maximum_raw_scores(self):
        for form, source in load_norms()["forms"].items():
            for table in source["subdomains"]:
                months = table["min_months"]
                applied = f"{1900 + months // 12:04d}-{1 + months % 12:02d}-01"
                for index in (0, -1):
                    scores = {key: entries[index][0 if index == 0 else 1]
                              for key, entries in table["scores"].items() if entries}
                    with self.subTest(form=form, months=months, boundary=index):
                        data = compute_scores({**raw(form, "1900-01-01", applied), "raw_scores": scores})
                        self.assertTrue(data["domains"])

    def test_infant_forms_are_distinct_and_zero_is_preserved(self):
        interview = compute_scores(raw("entrevista", "2026-01-15"))
        parents = compute_scores(raw("pais_cuidadores", "2026-01-15"))
        self.assertEqual(interview["subdomains"][0]["raw_score"], 0)
        self.assertEqual(interview["subdomains"][0]["v_scale"], 9)
        self.assertEqual(parents["subdomains"][0]["v_scale"], 7)
        self.assertNotIn("esc", {row["scale"] for row in interview["subdomains"]})

    def test_parent_coping_norms_start_at_two_not_three(self):
        table = age_table("pais_cuidadores", "subdomains", 24)
        self.assertTrue(table["scores"]["enf"])
        self.assertEqual(lookup(table["scores"]["enf"], 0)[0], 6)

    def test_age_limits_and_birthdays(self):
        self.assertEqual(age_months({"birth_date": "2020-01-31", "reference_date": "2020-02-29"}), 1)
        self.assertEqual(age_months({"birth_date": "2023-01-15", "reference_date": "2026-01-14"}), 35)
        for months in (0, 35, 228, 300):
            with self.assertRaises(ValueError):
                age_table("professores", "subdomains", months)
        self.assertTrue(age_table("professores", "subdomains", 227))
        self.assertTrue(age_table("entrevista", "subdomains", 1200))

    def test_dates_form_respondent_and_input_modes_are_validated(self):
        for changes in ({"birth_date": None}, {"reference_date": "invalid"}, {"birth_date": "2027-01-01"},
                        {"form": "invalid"}, {"respondent": " "}, {"entry_mode": "items"},
                        {"item_responses": {}}, {"raw_scores": None}):
            with self.subTest(changes=changes):
                self.assertTrue(validate_input({**raw(), **changes}))
                with self.assertRaises(ValueError):
                    compute_scores({**raw(), **changes})

    def test_strict_raw_score_validation(self):
        for value in (-1, 61, 0.5, True, "40", None):
            data = raw()
            data["raw_scores"]["rec"] = value
            self.assertTrue(validate_input(data))
        for key in ("rec", "num", "cme"):
            data = raw()
            del data["raw_scores"][key]
            self.assertTrue(validate_input(data))
        data = raw()
        data["raw_scores"]["dom"] = 1
        self.assertTrue(validate_input(data))

    def test_motor_is_optional_paired_and_age_limited(self):
        data = raw()
        del data["raw_scores"]["cmg"]
        self.assertTrue(validate_input(data))
        del data["raw_scores"]["cmf"]
        self.assertEqual(validate_input(data), [])
        self.assertNotIn("HMOT", {row["scale"] for row in compute_scores(data)["domains"]})
        data = raw(birth="2016-01-15")
        data["raw_scores"]["cmg"] = 0
        self.assertTrue(validate_input(data))

    def test_classification_is_explicitly_pending_and_text_uses_computed_scores(self):
        module = Vineland3Module()
        context = TestContext(patient_name="Paciente", evaluation_id=1, instrument_code="vineland3", raw_scores=raw())
        data = module.compute(context)
        self.assertEqual(module.classify(data), {"classification_status": "pending_manual_verification"})
        self.assertIn("normas americanas", module.interpret(context, data))
        self.assertIn("não foi emitida", module.interpret(context, data))
        self.assertEqual(module.build_report_payload(context, data)["chart_payload"]["metric"], "standard_score")
        self.assertTrue(data["requires_clinical_review"])

    def test_extreme_percentiles_are_not_converted_to_exact_percentiles(self):
        table = age_table("professores", "domains", 36)
        self.assertEqual(lookup(table["scores"]["ABC"], 60), (20, "<1"))
        self.assertEqual(lookup(table["scores"]["ABC"], 420), (140, ">99"))
        with self.assertRaises(ValueError):
            lookup(table["scores"]["ABC"], 421)


class Vineland3ApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="vineland-clinico", email="vineland@example.com", role=UserRole.NEUROPSYCHOLOGIST)
        self.token = issue_api_token(self.user)
        self.patient = Patient.objects.create(full_name="Paciente Vineland", birth_date=date(2023, 1, 15), created_by=self.user)
        self.evaluation = Evaluation.objects.create(patient=self.patient, examiner=self.user, start_date=date(2026, 1, 15))
        self.payload = {"evaluation_id": self.evaluation.pk, "applied_on": "2026-01-15", "form": "professores",
                        "respondent": "Professor referência", "raw_scores": deepcopy(PROFESSOR_SCORES)}

    def submit(self, **overrides):
        return self.client.post("/api/tests/vineland3/submit", data=json.dumps({**self.payload, **overrides}),
                                content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_protocol_authentication_and_no_normative_tables_leaked(self):
        self.assertEqual(self.client.get("/api/tests/vineland3/protocol").status_code, 401)
        response = self.client.get("/api/tests/vineland3/protocol", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["entry_modes"], ["totals", "items"])
        self.assertEqual(response.json()["item_protocol"]["id"], domain_protocol.PROTOCOL_ID)
        self.assertEqual(response.json()["legacy_item_protocol"]["id"], PROTOCOL_ID)
        self.assertFalse(response.json()["item_protocol"]["scoring_enabled"])
        self.assertNotIn("scores", response.json())
        scales = response.json()["forms"]["pais_cuidadores"]["scales"]
        self.assertEqual(next(row for row in scales if row["code"] == "enf")["min_months"], 24)

    def test_separate_applications_do_not_overwrite_respondents_or_forms(self):
        first = self.submit()
        self.assertEqual(first.status_code, 200, first.content)
        second = self.submit(respondent="Outro professor")
        third = self.submit(form="entrevista", raw_scores=raw("entrevista")["raw_scores"])
        self.assertEqual(third.status_code, 200, third.content)
        self.assertNotEqual(first.json()["application_id"], second.json()["application_id"])
        self.assertEqual(TestApplication.objects.filter(instrument__code="vineland3").count(), 3)
        self.assertFalse(first.json()["is_validated"])
        self.assertEqual(build_validated_tests_snapshot(self.evaluation), [])
        TestApplication.objects.filter(instrument__code="vineland3").update(is_validated=True)
        snapshot = build_validated_tests_snapshot(self.evaluation)
        self.assertEqual(len(snapshot), 3)
        self.assertIn("Outro professor", {item["respondent_name"] for item in snapshot})

    def test_edit_same_id_clears_review_and_locked_blocks_edits(self):
        app_id = self.submit().json()["application_id"]
        app = TestApplication.objects.get(pk=app_id)
        app.is_validated = True
        app.reviewed_payload = {"old": "review"}
        app.save()
        response = self.submit(application_id=app_id, respondent="Nome corrigido")
        self.assertEqual(response.status_code, 200, response.content)
        app.refresh_from_db()
        self.assertFalse(app.is_validated)
        self.assertEqual(app.reviewed_payload, {})
        self.assertIn("Nome corrigido", app.interpretation_text)
        app.status = TestApplication.Status.LOCKED
        app.save()
        self.assertEqual(self.submit(application_id=app_id).status_code, 403)

    def test_unauthorized_evaluation_and_wrong_instrument_cannot_be_updated(self):
        other = get_user_model().objects.create_user(username="vineland-other", email="other-vineland@example.com", role=UserRole.NEUROPSYCHOLOGIST)
        patient = Patient.objects.create(full_name="Outro paciente", created_by=other)
        evaluation = Evaluation.objects.create(patient=patient, examiner=other)
        self.assertEqual(self.submit(evaluation_id=evaluation.pk).status_code, 404)
        application = TestApplication.objects.create(evaluation=self.evaluation, instrument=Instrument.objects.get(code="thcp"))
        self.assertEqual(self.submit(application_id=application.pk).status_code, 404)

    def test_readonly_cannot_submit(self):
        user = get_user_model().objects.create_user(username="vineland-readonly", email="readonly-vineland@example.com", role=UserRole.READONLY)
        self.token = issue_api_token(user)
        self.assertEqual(self.submit().status_code, 403)

    def test_validation_rejects_items_bad_scores_and_future_dates(self):
        for overrides in ({"entry_mode": "items"}, {"raw_scores": {"rec": True}}, {"applied_on": "2099-01-01"}):
            self.assertEqual(self.submit(**overrides).status_code, 400)
        self.assertEqual(self.submit(birth_date="2020-01-01").status_code, 422)
        self.assertEqual(TestApplication.objects.filter(instrument__code="vineland3").count(), 0)

    def submit_items(self, **overrides):
        return self.submit(form=None, entry_mode="items", raw_scores={}, item_protocol_id=PROTOCOL_ID,
                           item_responses={"comunicacao": {"1": {"response": "0", "observation": "Preservar zero"},
                                                           "2": {"response": "n", "observation": "Sem oportunidade"}},
                                           "autonomia": {"1": {"response": "", "observation": "Observar depois"}}}, **overrides)

    def submit_domain_items(self, **overrides):
        return self.submit(**{"form": None, "entry_mode": "items", "raw_scores": {},
                              "item_protocol_id": domain_protocol.PROTOCOL_ID,
                              "item_responses": {"comunicacao": {"1": {"response": "0", "estimated": True, "observation": "Conferir"}}},
                              **overrides})

    def test_empty_application_created_from_evaluation_accepts_questions_on_same_id(self):
        instrument, _ = Instrument.objects.get_or_create(code="vineland3", defaults={"name": "Vineland-3"})
        response = self.client.post("/api/tests/applications", data=json.dumps({
            "evaluation_id": self.evaluation.pk, "instrument_id": instrument.pk,
        }), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 201, response.content)
        app_id = response.json()["id"]
        self.assertEqual(response.json()["raw_payload"], {})
        result = self.submit_domain_items(application_id=app_id)
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(result.json()["application_id"], app_id)
        self.assertEqual(result.json()["raw_payload"]["item_protocol_id"], domain_protocol.PROTOCOL_ID)
        self.assertEqual(TestApplication.objects.filter(evaluation=self.evaluation, instrument=instrument).count(), 1)

    def test_application_with_only_date_can_be_initialized_but_recorded_data_cannot(self):
        instrument, _ = Instrument.objects.get_or_create(code="vineland3", defaults={"name": "Vineland-3"})
        app = TestApplication.objects.create(evaluation=self.evaluation, instrument=instrument, applied_on=date(2026, 1, 15))
        self.assertEqual(self.submit_domain_items(application_id=app.pk).status_code, 200)
        for fields in ({"raw_payload": {"respondent": "Nome salvo"}}, {"computed_payload": {"old": 1}},
                       {"classified_payload": {"old": 1}}, {"reviewed_payload": {"notes": "Preservar"}},
                       {"interpretation_text": "Texto salvo"}, {"is_validated": True}):
            with self.subTest(fields=fields):
                saved = TestApplication.objects.create(evaluation=self.evaluation, instrument=instrument, **fields)
                self.assertEqual(self.submit_domain_items(application_id=saved.pk).status_code, 400)
                saved.refresh_from_db()
                for field, value in fields.items():
                    self.assertEqual(getattr(saved, field), value)

    def test_locked_empty_application_cannot_be_initialized(self):
        instrument, _ = Instrument.objects.get_or_create(code="vineland3", defaults={"name": "Vineland-3"})
        app = TestApplication.objects.create(evaluation=self.evaluation, instrument=instrument, status=TestApplication.Status.LOCKED)
        self.assertEqual(self.submit_domain_items(application_id=app.pk).status_code, 403)
        app.refresh_from_db()
        self.assertEqual(app.raw_payload, {})

    def test_domain_level_items_persist_reopen_edit_and_remain_unscored(self):
        response = self.submit_domain_items(general_observations="Nota geral")
        self.assertEqual(response.status_code, 200, response.content)
        app = TestApplication.objects.get(pk=response.json()["application_id"])
        self.assertEqual(app.raw_payload["item_protocol_id"], domain_protocol.PROTOCOL_ID)
        self.assertTrue(app.raw_payload["edition_verified"])
        self.assertFalse(app.raw_payload["scoring_enabled"])
        read = self.client.get(f"/api/tests/applications/{app.pk}", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(read.json()["raw_payload"]["item_responses"], app.raw_payload["item_responses"])
        self.assertEqual(self.submit_domain_items(application_id=app.pk, respondent="Informante atualizado").status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.raw_payload["general_observations"], "Nota geral")
        self.assertTrue(app.raw_payload["item_responses"]["comunicacao"]["1"]["estimated"])
        self.assertEqual(app.computed_payload, {})
        self.assertEqual(app.classified_payload, {})
        self.assertEqual(app.interpretation_text, "")
        self.assertFalse(app.is_validated)
        app.is_validated = True
        app.save()
        self.assertEqual(build_validated_tests_snapshot(self.evaluation), [])
        self.assertFalse(TestScoringService.process(app)["ok"])
        app.status = TestApplication.Status.LOCKED
        app.save()
        self.assertEqual(self.submit_domain_items(application_id=app.pk).status_code, 403)

    def test_complete_domain_bank_can_be_saved_without_normative_scores(self):
        items = {domain["code"]: {item["id"]: {"response": "0", "estimated": False} for item in domain["items"]}
                 for domain in domain_protocol.item_protocol()["domains"]}
        response = self.submit_domain_items(item_responses=items)
        self.assertEqual(response.status_code, 200, response.content)
        app = TestApplication.objects.get(pk=response.json()["application_id"])
        self.assertEqual(sum(len(items) for items in app.raw_payload["item_responses"].values()), 180)
        self.assertEqual(app.computed_payload, {})

    def test_protocols_cannot_be_swapped_in_place(self):
        old_id = self.submit_items().json()["application_id"]
        self.assertEqual(self.submit_domain_items(application_id=old_id).status_code, 400)
        self.assertEqual(TestApplication.objects.get(pk=old_id).raw_payload["item_protocol_id"], PROTOCOL_ID)
        new_id = self.submit_domain_items().json()["application_id"]
        self.assertEqual(self.submit_items(application_id=new_id).status_code, 400)
        self.assertEqual(TestApplication.objects.get(pk=new_id).raw_payload["item_protocol_id"], domain_protocol.PROTOCOL_ID)

    def test_domain_level_invalid_responses_are_rejected(self):
        for items in ({"comunicacao": {"26": {"response": "1"}}}, {"vida_diaria": {"1": {"response": "N"}}},
                      {"comunicacao": {"1": {"response": "", "estimated": True}}}):
            self.assertEqual(self.submit_domain_items(item_responses=items).status_code, 400)
        self.assertEqual(self.submit_domain_items(form="pais_cuidadores").status_code, 400)
        self.assertEqual(TestApplication.objects.filter(instrument__code="vineland3").count(), 0)

    def test_partial_items_persist_without_scores_or_automatic_interpretation(self):
        response = self.submit_items()
        self.assertEqual(response.status_code, 200, response.content)
        app = TestApplication.objects.get(pk=response.json()["application_id"])
        self.assertEqual(app.raw_payload["item_responses"]["comunicacao"]["1"]["response"], "0")
        self.assertEqual(app.raw_payload["item_responses"]["comunicacao"]["2"]["response"], "N")
        self.assertEqual(app.raw_payload["item_responses"]["autonomia"]["1"], {"response": "", "observation": "Observar depois"})
        self.assertEqual(app.raw_payload["item_protocol_id"], PROTOCOL_ID)
        self.assertFalse(app.raw_payload["edition_verified"])
        self.assertEqual(app.computed_payload, {})
        self.assertEqual(app.classified_payload, {})
        self.assertEqual(app.interpretation_text, "")
        self.assertFalse(app.is_validated)
        result = self.client.get(f"/api/tests/applications/{app.pk}", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["raw_payload"]["item_responses"], app.raw_payload["item_responses"])

    def test_partial_items_never_enter_snapshot_even_if_marked_validated(self):
        app = TestApplication.objects.get(pk=self.submit_items().json()["application_id"])
        app.is_validated = True
        app.save()
        self.assertEqual(build_validated_tests_snapshot(self.evaluation), [])
        self.assertFalse(TestScoringService.process(app)["ok"])
        app.refresh_from_db()
        self.assertEqual(app.computed_payload, {})

    def test_general_observations_persist_and_can_be_cleared(self):
        response = self.submit_items(general_observations="Observação geral\nEm todos os domínios.")
        self.assertEqual(response.status_code, 200, response.content)
        app_id = response.json()["application_id"]
        result = self.client.get(f"/api/tests/applications/{app_id}", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(result.json()["raw_payload"]["general_observations"], "Observação geral\nEm todos os domínios.")
        # Older clients omitting the new field must not erase an existing note.
        self.assertEqual(self.submit_items(application_id=app_id).status_code, 200)
        app = TestApplication.objects.get(pk=app_id)
        self.assertEqual(app.raw_payload["general_observations"], "Observação geral\nEm todos os domínios.")
        self.assertEqual(app.raw_payload["item_responses"]["comunicacao"]["1"]["observation"], "Preservar zero")
        self.assertEqual(self.submit_items(application_id=app_id, general_observations="").status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.raw_payload["general_observations"], "")

    def test_general_observations_limit_is_enforced(self):
        self.assertEqual(self.submit_items(general_observations="x" * 10001).status_code, 422)
        self.assertEqual(TestApplication.objects.filter(instrument__code="vineland3").count(), 0)

    def test_item_edit_preserves_observations_and_locked_application_is_protected(self):
        app_id = self.submit_items().json()["application_id"]
        response = self.submit_items(application_id=app_id, respondent="Outro responsável")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(TestApplication.objects.filter(instrument__code="vineland3").count(), 1)
        app = TestApplication.objects.get(pk=app_id)
        self.assertEqual(app.raw_payload["item_responses"]["comunicacao"]["1"]["observation"], "Preservar zero")
        app.status = TestApplication.Status.LOCKED
        app.save()
        self.assertEqual(self.submit_items(application_id=app_id).status_code, 403)

    def test_items_cannot_replace_a_scored_application(self):
        app_id = self.submit().json()["application_id"]
        self.assertEqual(self.submit_items(application_id=app_id).status_code, 400)
        app = TestApplication.objects.get(pk=app_id)
        self.assertTrue(app.computed_payload["domains"])
        item_id = self.submit_items().json()["application_id"]
        self.assertEqual(self.submit(application_id=item_id).status_code, 400)

    def test_invalid_partial_record_is_not_saved(self):
        base = {**self.payload, "form": None, "entry_mode": "items", "raw_scores": {},
                "item_protocol_id": PROTOCOL_ID, "item_responses": {}}
        for overrides in ({"form": "professores"}, {"raw_scores": {"rec": 0}}, {"item_protocol_id": "unknown"},
                          {"item_responses": {"comunicacao": {"1": {"response": "3"}}}}, {"respondent": " "}):
            response = self.client.post("/api/tests/vineland3/submit", data=json.dumps({**base, **overrides}),
                                        content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token}")
            self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(TestApplication.objects.filter(instrument__code="vineland3").count(), 0)

    def test_rescoring_uses_authoritative_dates(self):
        app = TestApplication.objects.get(pk=self.submit().json()["application_id"])
        original = deepcopy(app.computed_payload)
        app.raw_payload["birth_date"] = "1900-01-01"
        result = TestScoringService.process(app)
        self.assertTrue(result["ok"], result)
        self.assertEqual(app.computed_payload, original)

    def test_docx_uses_computed_data_and_survives_serialization(self):
        app = TestApplication.objects.get(pk=self.submit().json()["application_id"])
        app.is_validated = True
        app.interpretation_text = "Texto antigo incompatível 999"
        app.save()
        snapshot = build_validated_tests_snapshot(self.evaluation)
        self.assertEqual(len(snapshot[0]["result_rows"]), 16)
        context = {"validated_tests": snapshot}
        document = Document()
        document.add_paragraph("14. CONCLUSÃO")
        ReportExportService._insert_vineland3_results(document, context)
        ReportExportService._remove_empty_paragraphs(document)
        self.assertEqual(len(document.tables), 1)
        self.assertEqual(len(document.inline_shapes), 1)
        self.assertEqual(len(document.tables[0].rows), 17)
        text = "\n".join(p.text for p in document.paragraphs)
        self.assertIn("escore padrão 99", text)
        self.assertNotIn("999", text)
        self.assertLess(text.index("escore padrão 99"), text.index("14. CONCLUSÃO"))
        output = BytesIO()
        document.save(output)
        restored = Document(BytesIO(output.getvalue()))
        self.assertEqual(len(restored.inline_shapes), 1)
