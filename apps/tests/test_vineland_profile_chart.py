from django.test import SimpleTestCase

from apps.tests.test_vineland3 import raw
from apps.tests.vineland3.calculators import compute_scores
from apps.tests.vineland3.profile_chart import subdomain_profile
from apps.tests.vineland3.presentation import build_subdomain_chart


class SubdomainProfileTests(SimpleTestCase):
    def test_forms_keep_domain_slots_reference_lines_and_integer_coordinates(self):
        for form in ("entrevista", "pais_cuidadores", "professores"):
            with self.subTest(form=form):
                result = compute_scores(raw(form, birth="2020-01-15"))["analysis"]
                chart = subdomain_profile(result)
                self.assertEqual(len(chart["columns"]), 11)
                self.assertEqual([g["code"] for g in chart["groups"]], ["COM", "AVD", "SOC", "HMOT"])
                self.assertEqual([t["value"] for t in chart["ticks"] if t["reference"]], [6, 9, 12, 15])
                self.assertEqual([t["value"] for t in chart["ticks"]], list(range(1, 25)))
                self.assertTrue(all(isinstance(c["y"], int) for c in chart["columns"]))
                avd = [c["code"] for c in chart["columns"]][3:6]
                self.assertEqual(avd, ["pes", "num", "cme"] if form == "professores" else ["pes", "dom", "com"])
                self.assertTrue(build_subdomain_chart({"normative_results": result}).startswith(b"\x89PNG"))

    def test_missing_internal_subdomain_breaks_line_without_shifting_columns(self):
        result = compute_scores(raw("entrevista", birth="2020-01-15"))["analysis"]
        original = subdomain_profile(result)
        result["subdomains"] = [r for r in result["subdomains"] if r["scale"] not in ("exp", "cmg", "cmf")]
        chart = subdomain_profile(result)
        self.assertEqual(len(chart["segments"]), 2)
        self.assertEqual(chart["columns"][1]["score"], None)
        self.assertEqual(chart["columns"][2]["x"], original["columns"][2]["x"])
        self.assertTrue(all(r["y"] is None for r in chart["columns"][-2:]))
