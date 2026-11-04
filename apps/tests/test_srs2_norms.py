import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from apps.tests.srs2.classifiers import classify_srs2_scores
from apps.tests.srs2.import_norms import export_norms, normalize_value
from apps.tests.srs2.norms import NORMS, get_norm_data
from apps.tests.srs2.paths import TABLES_DIR


class SRS2NormsTests(TestCase):
    def test_adult_heteroreport_regression(self):
        expected = {
            "percepção_social": (6, 51, 52, "Dentro dos limites normais"),
            "cognição_social": (23, 64, 92, "Leve"),
            "comunicação_social": (34, 63, 90, "Leve"),
            "motivação_social": (23, 69, 97, "Moderado"),
            "padrões_restritos": (17, 61, 87, "Leve"),
            "cis": (86, 65, 93, "Leve"),
            "total": (103, 65, 93, "Leve"),
        }
        computed = {"form": "adulto_heterorrelato"}
        computed.update({key: {"escore": values[0]} for key, values in expected.items()})
        for gender in ("M", "F"):
            classified = classify_srs2_scores(computed, gender=gender, age=30)
            for row in classified["resultados"]:
                with self.subTest(gender=gender, factor=row["variável"]):
                    raw, tscore, percentile, label = expected[row["variável"]]
                    self.assertEqual(
                        (row["bruto"], row["tscore"], row["percentil"], row["classificação"]),
                        (raw, tscore, percentile, label),
                    )

    def test_every_form_has_contiguous_norms_for_all_seven_scales(self):
        for form, genders in NORMS.items():
            for gender, factors in genders.items():
                self.assertEqual(len(factors), 7)
                for factor, table in factors.items():
                    with self.subTest(form=form, gender=gender, factor=factor):
                        self.assertTrue(table)
                        self.assertEqual(set(table), set(range(max(table) + 1)))

    def test_missing_norms_are_not_replaced_by_other_raw_scores(self):
        partial = {"adulto_heterorrelato": {"default": {"percepção_social": {23: (71, 98), 25: (75, 99)}}}}
        with patch("apps.tests.srs2.norms.NORMS", partial):
            for raw in (6, 24, 26):
                self.assertEqual(get_norm_data(raw, "adulto_heterorrelato", "F", "percepção_social"), (None, None))
            self.assertEqual(get_norm_data(23, "adulto_heterorrelato", "F", "percepção_social"), (71, 98))

    def test_bounded_tscore_at_zero_is_loaded(self):
        self.assertEqual(get_norm_data(0, "adulto_heterorrelato", "M", "total"), (23, 1))

    def test_export_preserves_bounds(self):
        self.assertEqual(normalize_value("< 23"), "< 23")
        self.assertEqual(normalize_value("0.9", percentile=True), "<1")
        self.assertEqual(normalize_value("99.1", percentile=True), ">99")

    def test_csvs_match_workbook_export(self):
        workbook = Path(__file__).resolve().parents[2] / "aux" / "CORRECAO.xlsm"
        if not workbook.exists():
            self.skipTest("Planilha de referência não disponível neste ambiente")
        with TemporaryDirectory() as output:
            counts = export_norms(workbook, output)
            self.assertEqual(len(counts), 10)
            for filename in counts:
                with self.subTest(filename=filename):
                    with (Path(output) / filename).open(encoding="utf-8") as generated:
                        expected = list(csv.reader(generated))
                    with (Path(TABLES_DIR) / filename).open(encoding="utf-8") as saved:
                        self.assertEqual(list(csv.reader(saved)), expected)
