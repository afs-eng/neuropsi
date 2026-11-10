import csv
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.tests.vineland3.csv_tables import (
    _rows, catalog, domain_norms_from_csv, extensive_norms_from_csv, load_table, sources,
)
from apps.tests.vineland3.domain_scoring import load_domain_norms
from apps.tests.vineland3.import_csv_tables import EXPECTED_PAGES, bounds, csv_text, numeric
from apps.tests.vineland3.norms import load_norms
from apps.tests.vineland3.paths import BASE_DIR, TABELAS


class VinelandCsvTableTests(SimpleTestCase):
    def test_catalog_contains_every_table_and_all_509_pages(self):
        records = catalog()
        self.assertEqual(len(records), 573)
        self.assertEqual(sum(int(r["linhas"]) for r in records), 167713)
        self.assertEqual(set(sources()), set("BCDE"))
        covered = {}
        for entry in records:
            covered.setdefault(entry["tabela"].replace(".", ""), set()).update(entry["paginas"].split(";"))
        self.assertEqual({k: len(v) for k, v in covered.items()}, EXPECTED_PAGES)
        files = {p.relative_to(TABELAS).as_posix() for p in TABELAS.rglob("*.csv")}
        self.assertEqual(files - {"catalogo.csv", "fontes.csv"}, {r["arquivo"] for r in records})

    def test_all_csv_files_have_valid_hashes_rows_and_no_watermark_information(self):
        for entry in catalog():
            with self.subTest(file=entry["arquivo"]):
                path = TABELAS / entry["arquivo"]
                data = path.read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
                self.assertEqual(len(_rows(entry["arquivo"])), int(entry["linhas"]))
                text = data.decode("utf-8")
                self.assertNotIn("@", text)
                self.assertNotIn("CPF", text)
                self.assertNotIn("Copyright", text)
                self.assertNotIn("Viviane", text)

    def test_csv_reconstruction_is_identical_to_previously_validated_extensive_norms(self):
        expected = json.loads((BASE_DIR / "norms.json").read_text(encoding="utf-8"))
        self.assertEqual(extensive_norms_from_csv(), expected)

    def test_csv_reconstruction_is_identical_to_previously_validated_domain_norms(self):
        expected = json.loads((BASE_DIR / "domain_norms.json").read_text(encoding="utf-8"))
        self.assertEqual(domain_norms_from_csv(), expected)

    def test_runtime_loaders_do_not_read_json_or_require_pdf_sources(self):
        load_norms.cache_clear()
        load_domain_norms.cache_clear()
        with patch.object(Path, "read_text", side_effect=AssertionError("Runtime não deve ler JSON/PDF")):
            self.assertEqual(load_norms()["population"], "Normas americanas")
            self.assertEqual(load_domain_norms()["population"], "Normas americanas")

    def test_domain_level_age_and_confidence_filters_do_not_mix_extensive_forms(self):
        rows = load_table("C.3", level="niveis_dominio", months=72, kind="dominios")
        self.assertEqual(len(rows), 605)
        self.assertTrue(all(r["nivel"] == "niveis_dominio" for r in rows))
        com = next(r for r in rows if r["escala"] == "COM" and r["entrada_min"] == "72")
        self.assertEqual((com["escore"], com["percentil"]), ("130", "98"))
        ci = load_table("C.3", level="niveis_dominio", months=72, kind="ic")
        self.assertEqual(len(ci), 15)
        self.assertEqual(next(r["margem"] for r in ci if r["escala"] == "COM" and r["confianca"] == "95"), "8")

    def test_empty_conversion_is_preserved_and_not_replaced_with_zero(self):
        rows = load_table("C.3", level="niveis_dominio", months=72, kind="dominios")
        zero = next(r for r in rows if r["escala"] == "COM" and r["entrada_min"] == "0")
        self.assertEqual(zero["escore"], "38")
        self.assertTrue(any(r["entrada_min"] == "" for r in rows))
        self.assertTrue(any(r["percentil"] == "<1" for r in rows))
        self.assertTrue(any(r["percentil"] == ">99" for r in rows))

    def test_equivalent_age_and_growth_values_are_available_for_each_extensive_form(self):
        for appendix in "BCD":
            rows = load_table(f"{appendix}.2", level="extensivo")
            rec = next(r for r in rows if r["escala"] == "rec" and r["bruto"] == "0")
            self.assertEqual((rec["equivalente_idade"], rec["vec"]), ("<3:0" if appendix == "D" else "0:0", "10"))
            for scale in {r["escala"] for r in rows}:
                scores = [int(r["bruto"]) for r in rows if r["escala"] == scale]
                self.assertEqual(scores, list(range(max(scores) + 1)))
        self.assertTrue(any(r["equivalente_idade"].startswith("<") for r in load_table("C.2")))

    def test_all_statistics_are_indexed_and_filtered_by_age_and_level(self):
        rows = load_table("C.4", level="niveis_dominio", months=72)
        self.assertEqual(len(rows), 4)
        self.assertEqual(next(r["critico_p05"] for r in rows if r["escala"] == "COM"), "6.61")
        pairs = load_table("B.6", level="extensivo", months=84)
        self.assertEqual(len(pairs), 110)
        self.assertEqual({r["direcao"] for r in pairs}, {"<", ">"})
        teachers = load_table("D.4", months=72)
        self.assertEqual({r["escala"] for r in teachers if r["categoria"] == "subdominio"},
                         {"rec", "exp", "esc", "pes", "num", "cme", "rin", "bri", "enf", "cmg", "cmf"})

    def test_behavior_age_bands_include_whole_years_and_preserve_open_ended_label(self):
        for month in (36, 72, 83):
            rows = load_table("E.2", months=month)
            self.assertEqual(len(rows), 48)
            self.assertEqual({r["idade_texto"] for r in rows}, {"3–6"})
        self.assertEqual({r["idade_texto"] for r in load_table("E.2", months=84)}, {"7–11"})
        self.assertEqual({r["idade_texto"] for r in load_table("E.2", months=1200)}, {"70–90+"})
        self.assertEqual(load_table("E.3", months=228), [])

    def test_importer_age_bounds_numeric_validation_and_csv_roundtrip(self):
        for value, expected in [("3–6", (36, 83)), ("7–11", (84, 143)), ("70–90+", (840, None)),
                                ("3:0–3:3", (36, 39)), ("7:0+", (84, None))]:
            self.assertEqual(bounds(value), expected)
        for value in ("", "—", "–", "-"):
            self.assertEqual(numeric(value), "")
        with self.assertRaises(ValueError):
            numeric("texto não numérico")
        rows = [{"percentil": "<1", "valor": "0", "ausencia": "", "idade": "22:0+"}]
        self.assertEqual(list(csv.DictReader(io.StringIO(csv_text(rows)))), rows)

    def test_catalog_guard_rejects_unknown_tables_files_and_corruption(self):
        with self.assertRaises(ValueError):
            load_table("C.99")
        with self.assertRaises(ValueError):
            _rows("../../settings.py")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "test.csv").write_text("value\n999\n", encoding="utf-8")
            record = {"arquivo": "test.csv", "sha256": "0" * 64, "linhas": "1"}
            with patch("apps.tests.vineland3.csv_tables.TABELAS", root), patch("apps.tests.vineland3.csv_tables.catalog", return_value=(record,)):
                with self.assertRaisesMessage(ValueError, "corrompida"):
                    _rows.__wrapped__("test.csv")

    def test_returned_generic_rows_are_copies_not_mutable_cached_data(self):
        first = load_table("C.2")
        first[0]["vec"] = "999"
        self.assertEqual(load_table("C.2")[0]["vec"], "10")
