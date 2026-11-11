from copy import deepcopy

from django.test import SimpleTestCase

from apps.tests.test_vineland3 import raw
from apps.tests.test_vineland_extensive_analysis import REFERENCE_SCORES
from apps.tests.vineland3.calculators import compute_scores
from apps.tests.vineland3.extensive_interpretation import build_extensive_interpretation


class ExtensiveInterpretationTests(SimpleTestCase):
    def reference(self):
        return compute_scores({**raw("entrevista", birth="2020-01-15"), "raw_scores": dict(REFERENCE_SCORES)})["analysis"]

    def test_reference_interprets_every_subdomain_and_respects_direction(self):
        analysis = self.reference()
        before = deepcopy(analysis)
        output = build_extensive_interpretation(analysis)
        self.assertTrue(output["preliminary"])
        self.assertEqual(analysis, before)
        self.assertEqual([d["code"] for d in output["domains"]], ["COM", "AVD", "SOC", "HMOT"])
        rows = [r for d in output["domains"] for r in d["subdomains"]]
        self.assertEqual(len(rows), 11)
        self.assertIn("escore padrão 78, percentil 7, IC95% 74–82; faixa moderadamente baixo", output["overview"][0])
        self.assertIn("Atividades da Vida Diária apresenta 25 pontos de escore padrão a mais que Comunicação", " ".join(output["domain_comparisons"]))
        by_code = {r["scale"]: r for r in rows}
        self.assertIn("Escala-v 7, abaixo da referência normativa de 15", by_code["rec"]["interpretation"])
        self.assertIn("Escala-v 19, acima da referência normativa de 15", by_code["esc"]["interpretation"])
        self.assertIn("força relativa", by_code["esc"]["interpretation"])
        self.assertIn("Escala-v 12, abaixo da referência normativa de 15", by_code["enf"]["interpretation"])
        self.assertIn("força relativa", by_code["enf"]["interpretation"])
        self.assertEqual(by_code["com"]["display_code"], "CMD")
        self.assertIn("diferenças significativas", output["synthesis"][0])

    def test_missing_motor_produces_no_detailed_motor_section_or_inferred_items(self):
        data = {**raw("entrevista", birth="2020-01-15"), "raw_scores": dict(REFERENCE_SCORES)}
        for code in ("cmg", "cmf"):
            data["raw_scores"].pop(code)
        output = build_extensive_interpretation(compute_scores(data)["analysis"])
        self.assertEqual([r["code"] for r in output["domains"]], ["COM", "AVD", "SOC"])
        self.assertIn("Habilidades Motoras: resultado indisponível", " ".join(output["overview"]))
        self.assertIn("não equivale a escore zero", " ".join(output["overview"]))
        self.assertIn("não permitem afirmar quais itens específicos", " ".join(output["synthesis"]))

    def test_teacher_descriptions_use_school_subdomains_not_home_subdomains(self):
        analysis = compute_scores(raw("professores", birth="2020-01-15"))["analysis"]
        output = build_extensive_interpretation(analysis)
        avd = next(d for d in output["domains"] if d["code"] == "AVD")
        self.assertEqual([r["scale"] for r in avd["subdomains"]], ["pes", "num", "cme"])
        self.assertIn("conceitos numéricos", avd["subdomains"][1]["interpretation"])
        self.assertIn("ambiente escolar", avd["subdomains"][2]["interpretation"])

    def test_tied_scores_and_non_significant_differences_do_not_become_weaknesses(self):
        analysis = self.reference()
        for row in analysis["subdomains"]:
            row["v_scale"] = 15
        analysis["subdomain_mean_v_scale"] = 15
        for row in analysis["subdomain_strengths"]:
            row.update(score=15, standard_score=15, difference=0, significant=False, finding="Não significativa")
        for row in analysis["subdomain_pairs"] + analysis["pairs"]:
            row.update(difference=0, significant=False)
        output = build_extensive_interpretation(analysis)
        for row in (r for d in output["domains"] for r in d["subdomains"]):
            self.assertIn("igual à referência normativa de 15", row["interpretation"])
            self.assertIn("Não apresentou diferença significativa", row["interpretation"])
            self.assertNotIn("É uma força relativa", row["interpretation"])
        self.assertIn("não prova equivalência", output["synthesis"][0])
        self.assertEqual(output["domain_comparisons"], [])

    def test_unavailable_norms_are_not_interpreted_as_negative_findings(self):
        analysis = self.reference()
        analysis["cca"]["confidence_interval"] = None
        for row in analysis["subdomain_strengths"]:
            row.update(significant=None, finding="Não disponível", critical_value=None, base_rate=None)
        for row in analysis["subdomain_pairs"] + analysis["pairs"]:
            row.update(significant=None, critical_value=None, base_rate=None)
        output = build_extensive_interpretation(analysis)
        self.assertIn("IC95% indisponível", output["overview"][0])
        self.assertIn("não é possível concluir ausência", output["synthesis"][0])
        self.assertIn("não é possível concluir ausência", output["domains"][0]["subdomains"][0]["interpretation"])
        self.assertTrue(all("Não há comparações normativas disponíveis" in d["pair_interpretations"][0] for d in output["domains"]))

    def test_no_global_development_age_diagnosis_or_invalid_form_inference(self):
        output = build_extensive_interpretation(self.reference())
        self.assertIn("não são idade global de desenvolvimento", output["limitations"])
        self.assertIn("Não foram inferidos diagnóstico", output["limitations"])
        for payload in ({}, {"form_level": "niveis_dominio", "normative_scoring": True}):
            with self.assertRaises(ValueError):
                build_extensive_interpretation(payload)
