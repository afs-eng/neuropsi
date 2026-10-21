from copy import deepcopy
from datetime import date
from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.reports.services.specialist_input_service import SpecialistInputService
from apps.tests.wais3.calculators import compute_wais3_payload
from apps.tests.wais3.classifiers import classify_wais3_payload
from apps.tests.wais3.constants import WAIS3_SUBTEST_ORDER


def application(computed, classified, code="wais3"):
    patient = SimpleNamespace(
        pk=1, full_name="Pessoa Sintética", mother_name="", father_name="",
        responsible_name="", birth_date=date(1996, 1, 1), sex="F", schooling="superior",
    )
    return SimpleNamespace(
        pk=1, evaluation_id=1, evaluation=SimpleNamespace(patient=patient, start_date=date(2026, 1, 1)),
        instrument=SimpleNamespace(code=code), applied_on=date(2026, 1, 1), is_validated=True,
        raw_payload={}, computed_payload=computed, classified_payload=classified, reviewed_payload={},
    )


class WAIS3SpecialistInputTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.computed = compute_wais3_payload({
            "idade": {"anos": 30, "meses": 0},
            "subtestes": {key: {"pontos_brutos": 10} for key in WAIS3_SUBTEST_ORDER},
            "process_scores": {
                "digitos_ordem_direta": 8, "digitos_ordem_inversa": 5,
                "maior_sequencia_digitos_direta": 6, "maior_sequencia_digitos_inversa": 4,
            },
        })
        cls.classified = classify_wais3_payload(cls.computed)

    def test_full_engine_results_fit_without_normative_tables_or_rendering_copies(self):
        app = application(deepcopy(self.computed), deepcopy(self.classified))
        before = deepcopy((app.computed_payload, app.classified_payload))
        facts = SpecialistInputService.build(app)["facts"]
        self.assertLessEqual(len(facts), 600)
        for key in ("supplementary_tables", "psychometrics_tables", "charts", "render_ready_tables",
                    "subtestes_ordenados", "composites", "facilidades_dificuldades_tabela",
                    "discrepancias_tabela", "manifest"):
            self.assertFalse(any(f"/{key}/" in path for path in facts), key)
        for key in ("subtestes", "indices", "strengths_weaknesses", "discrepancy_analysis", "digitos"):
            self.assertTrue(any(path.startswith(f"/computed_payload/{key}/") for path in facts), key)
            self.assertFalse(any(path.startswith(f"/classified_payload/{key}/") for path in facts), key)
        for key in ("gai_data", "clusters"):
            self.assertTrue(any(path.startswith(f"/classified_payload/{key}/") for path in facts), key)
        self.assertEqual(facts["/computed_payload/indices/qi_total/pontuacao_composta"],
                         self.computed["indices"]["qi_total"]["pontuacao_composta"])
        self.assertIn("/computed_payload/indices/qi_total/ic_95", facts)
        self.assertEqual((app.computed_payload, app.classified_payload), before)

    def test_retains_new_classifications_and_alerts_and_zero_false_values(self):
        app = application(
            {"indices": {"qi_total": {"pontuacao_composta": 100}}, "warnings": ["Conferir norma."]},
            {"indices": {"qi_total": {"pontuacao_composta": 100, "classificacao": "Média"}},
             "gai_data": {"interpretavel": False, "diferenca_icv_iop": 0, "alerta": "Não interpretar."}},
        )
        facts = SpecialistInputService.build(app)["facts"]
        self.assertEqual(facts["/classified_payload/indices/qi_total/classificacao"], "Média")
        self.assertIs(facts["/classified_payload/gai_data/interpretavel"], False)
        self.assertEqual(facts["/classified_payload/gai_data/diferenca_icv_iop"], 0)
        self.assertEqual(facts["/classified_payload/gai_data/alerta"], "Não interpretar.")
        self.assertEqual(facts["/computed_payload/warnings/0"], "Conferir norma.")

    def test_conflicting_sources_and_aliases_are_rejected(self):
        for key in ("indices", "subtestes", "strengths_weaknesses", "discrepancy_analysis", "digitos"):
            with self.subTest(key=key):
                app = application({key: {"score": 100}}, {key: {"score": 101}})
                with self.assertRaisesRegex(ValueError, "divergentes"):
                    SpecialistInputService.build(app)
        with self.assertRaisesRegex(ValueError, "divergentes"):
            SpecialistInputService.build(application({"indices": {"qi": 100}, "composites": {"qi": 101}}, {}))

    def test_composites_only_sources_use_canonical_indices(self):
        facts = SpecialistInputService.build(application({"composites": {"qi_total": {"pontuacao_composta": 100}}}, {}))["facts"]
        self.assertEqual(facts["/computed_payload/indices/qi_total/pontuacao_composta"], 100)

    def test_classifier_can_append_warnings_without_losing_existing_alerts(self):
        facts = SpecialistInputService.build(application(
            {"indices": {"qi": 100}, "warnings": ["Normas incompletas."]},
            {"indices": {"qi": 100}, "warnings": ["Normas incompletas.", "GAI indisponível."]},
        ))["facts"]
        self.assertEqual(facts["/computed_payload/warnings/0"], "Normas incompletas.")
        self.assertEqual(facts["/classified_payload/warnings/0"], "GAI indisponível.")
        self.assertNotIn("/classified_payload/warnings/1", facts)

    def test_old_prose_and_identifying_fields_remain_excluded(self):
        facts = SpecialistInputService.build(application({
            "indices": {"qi": 100, "interpretation": "QI antigo 120", "patient_name": "Nome antigo"},
            "clinical_interpretation": "Texto antigo", "raw_payload": {"answers": [1, 2]},
        }, {}))["facts"]
        self.assertFalse(any("interpretation" in path or "patient_name" in path or "answers" in path for path in facts))

    def test_large_canonical_results_still_fail_without_truncation(self):
        with self.assertRaisesRegex(ValueError, "limite de fatos"):
            SpecialistInputService.build(application({"subtestes": {str(i): i for i in range(601)}}, {}))

    def test_other_instruments_keep_original_input_behavior(self):
        facts = SpecialistInputService.build(application({"qi": 100}, {"qi": 100}, code="wisc4"))["facts"]
        self.assertEqual(facts["/computed_payload/qi"], 100)
        self.assertEqual(facts["/classified_payload/qi"], 100)

    def test_policy_version_changes_only_wais3_fingerprint(self):
        from unittest.mock import patch
        app = application({"indices": {"qi": 100}}, {})
        original = SpecialistInputService.fingerprint(app)
        with patch("apps.reports.services.specialist_input_service.WAIS3_INPUT_VERSION", "future-policy"):
            self.assertNotEqual(SpecialistInputService.fingerprint(app), original)
        app.instrument.code = "wisc4"
        original = SpecialistInputService.fingerprint(app)
        with patch("apps.reports.services.specialist_input_service.WAIS3_INPUT_VERSION", "future-policy"):
            self.assertEqual(SpecialistInputService.fingerprint(app), original)
