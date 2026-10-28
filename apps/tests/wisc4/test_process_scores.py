from unittest import TestCase
from unittest.mock import patch

from apps.tests.base.types import TestContext
from apps.tests.wisc4 import WISC4Module
from apps.tests.wisc4.calculators import (
    PROCESS_SCORE_CONFIG,
    WISC4_SUBTESTS,
    _carregar_tabela_a8,
    build_process_scores,
)


class WISC4ProcessScoresTests(TestCase):
    def test_thirteen_year_old_can_compute_without_optional_process_scores(self):
        module = WISC4Module()
        for month in range(12):
            with self.subTest(month=month):
                context = TestContext(
                    patient_name="Paciente Teste",
                    evaluation_id=1,
                    instrument_code="wisc4",
                    raw_scores={key: config["max"] // 2 for key, config in WISC4_SUBTESTS.items()},
                    reviewed_scores={
                        "birth_date": "2010-01-01",
                        "evaluation_date": f"2023-{month + 1:02d}-01",
                    },
                )

                computed = module.compute(context)
                classified = module.classify(computed)

                self.assertIsNotNone(classified["qit_data"]["escore_composto"])
                for row in computed["process_scores"]["scaled_rows"]:
                    self.assertIsNone(row["raw_score"])
                    self.assertIsNone(row["scaled_score"])

    @patch("apps.tests.wisc4.calculators._carregar_tabela_a8")
    def test_blank_process_scores_do_not_load_a8(self, load_a8):
        raw_scores = {key: None for key in PROCESS_SCORE_CONFIG}

        result = build_process_scores(raw_scores, 13, 11, {})

        load_a8.assert_not_called()
        self.assertEqual(len(result["scaled_rows"]), len(PROCESS_SCORE_CONFIG))

    @patch("apps.tests.wisc4.calculators._carregar_tabela_a8")
    def test_sequence_scores_do_not_require_a8(self, load_a8):
        result = build_process_scores({"udiod": 6, "udioi": 4}, 13, 11, {})

        load_a8.assert_not_called()
        self.assertEqual(result["raw_discrepancy_rows"][0]["difference"], 2)
        for row in result["sequence_frequency_rows"]:
            self.assertIsNotNone(row["frequency"])

    def test_provided_process_scores_still_require_age_specific_norms(self):
        for key in PROCESS_SCORE_CONFIG:
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "Tabela A8 não encontrada.*13a 11m"):
                    build_process_scores({key: 0}, 13, 11, {})

    def test_available_a8_norms_are_used_for_provided_scores(self):
        with patch(
            "apps.tests.wisc4.calculators._carregar_tabela_a8", wraps=_carregar_tabela_a8
        ) as load_a8:
            result = build_process_scores({"cusb": 0}, 12, 11, {})

        load_a8.assert_called_once_with(12, 11)
        cubos = next(row for row in result["scaled_rows"] if row["code"] == "CUSB")
        self.assertEqual(cubos["raw_score"], 0)
        self.assertEqual(cubos["scaled_score"], 1)
