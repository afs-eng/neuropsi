from datetime import date
import csv
import math
from pathlib import Path
import re
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.tests.bai import BAIModule
from apps.tests.bpa2 import BPA2Module
from apps.tests.bpa2.interpreters import build_gold_standard_interpretation
from apps.tests.bpa2.pdf_service import BPA2PdfService
from apps.tests.bfp import BFPModule
from apps.tests.base.types import TestContext
from apps.tests.cars2_hf import CARS2HFModule
from apps.tests.cars2_hf.classifiers import classify_cars2_hf
from apps.tests.cars2_hf.loaders import load_cars2_hf_norms
from apps.tests.etdah_ad import ETDAHADModule
from apps.tests.etdah_ad.calculators import calculate_raw_scores
from apps.tests.etdah_ad.interpreters import interpret_results as interpret_etdah_ad_results
from apps.tests.etdah_pais import ETDAHPAISModule
from apps.tests.ebadep_a.pdf_service import EBADEPAPdfService
from apps.tests.epq_j import EPQJModule
from apps.tests.epq_j.calculators import calcular_escore
from apps.tests.fdt import FDTModule
from apps.tests.fdt.pdf_service import FDTPdfService
from apps.tests.ravlt.pdf_service import RAVLTPdfService
from apps.tests.mchat import MCHATModule
from apps.tests.mchat.constants import FAILURE_RULES, ITEMS
from apps.tests.ravlt import RAVLTModule
from apps.tests.ravlt.ai_interpretation import RAVLTAIInterpretationHandler
from apps.tests.services.ai_interpretation_orchestrator import TestAIInterpretationOrchestrator
from apps.tests.services.ai_interpretation_types import TestAIInterpretationDraft
from apps.tests.norms.bai import get_norms_metadata, lookup_t_score
from apps.tests.scared import SCAREDModule
from apps.tests.services.pdf_export_service import TestPdfExportService
from apps.tests.srs2 import SRS2Module
from apps.tests.srs2.interpreters import validate_srs2_interpretation
from apps.tests.srs2.pdf_service import SRS2PdfService
from apps.tests.wisc4 import WISC4Module
from apps.tests.wisc4.calculators import _carregar_tabela_ncp, buscar_ponderado
from apps.tests.wisc4.pdf_service import WISC4PdfService
from apps.tests.srs2.norms import get_norm_data
from apps.tests.wasi import WASIModule
from apps.tests.wais3.interpreters import build_wais3_interpretation
from apps.tests.wais3.classifiers import classify_wais3_payload
from apps.tests.wais3.pdf_service import WAIS3PdfService


class BAINormsTests(SimpleTestCase):
    def test_lookup_t_score_uses_official_ranges(self):
        self.assertEqual(lookup_t_score(0), 39)
        self.assertEqual(lookup_t_score(3), 42)
        self.assertEqual(lookup_t_score(4), 42)
        self.assertEqual(lookup_t_score(47), 79)
        self.assertEqual(lookup_t_score(63), 80)

    def test_norms_metadata_exposes_expected_fields(self):
        metadata = get_norms_metadata()

        self.assertEqual(metadata["instrument"], "BAI")
        self.assertEqual(metadata["scale"], "Amostra Geral (T)")
        self.assertEqual(metadata["dimension"], "Escore Total")
        self.assertEqual(metadata["age_range"], "18-90")
        self.assertEqual(metadata["fidedignidade"], 0.90)
        self.assertEqual(metadata["reliability"], 0.90)


class BAIModuleTests(SimpleTestCase):
    def test_classify_returns_compatible_classification_shape(self):
        module = BAIModule()
        context = TestContext(
            patient_name="Paciente Teste",
            evaluation_id=1,
            instrument_code="bai",
            raw_scores={f"item_{index:02d}": 1 for index in range(1, 22)},
        )

        computed = module.compute(context)
        classified = module.classify(computed)

        self.assertEqual(classified["escore_total"], 21)
        self.assertEqual(classified["faixa_normativa"], "Moderado")
        self.assertEqual(classified["classificacao"]["label"], "Moderado")
        self.assertEqual(classified["classificacao"]["raw"]["label"], "Moderado")
        self.assertEqual(classified["classificacao_raw"]["label"], "Moderado")


class CARS2HFModuleTests(SimpleTestCase):
    def test_loads_norms_and_classifies_example_payload(self):
        norms = load_cars2_hf_norms()
        self.assertGreater(len(norms), 0)

        module = CARS2HFModule()
        context = TestContext(
            patient_name="Paciente Exemplo",
            evaluation_id=1,
            instrument_code="CARS2_HF",
            raw_scores={
                "patient_name": "Paciente Exemplo",
                "evaluation_date": "2026-04-15",
                "examiner_name": "Andre",
                "birth_date": "2016-02-10",
                "age_years": 10,
                "age_months": 2,
                "informant": "Mae",
                "items": {
                    "compreensao_socio_emocional": {
                        "score": 2.5,
                        "observations": "Dificuldade para compreender nuances emocionais.",
                    },
                    "expressao_emocional_regulacao": {
                        "score": 2.0,
                        "observations": "Oscilacoes emocionais e rigidez em situacoes frustrantes.",
                    },
                    "relacionamento_com_pessoas": {
                        "score": 3.0,
                        "observations": "Baixa reciprocidade social.",
                    },
                    "uso_do_corpo": {
                        "score": 1.5,
                        "observations": "Sem estereotipias evidentes; leve rigidez motora.",
                    },
                    "uso_objetos_brincadeiras": {
                        "score": 2.5,
                        "observations": "Brincadeira simbolica restrita.",
                    },
                    "adaptacao_mudancas_interesses_restritos": {
                        "score": 3.0,
                        "observations": "Resistencia importante a mudancas.",
                    },
                    "resposta_visual": {
                        "score": 2.5,
                        "observations": "Contato visual inconsistente.",
                    },
                    "resposta_auditiva": {
                        "score": 1.5,
                        "observations": "Responde ao nome, mas de forma irregular.",
                    },
                    "resposta_sensorial": {
                        "score": 2.0,
                        "observations": "Sensibilidade seletiva a texturas.",
                    },
                    "medo_ou_ansiedade": {
                        "score": 2.0,
                        "observations": "Ansiedade em situacoes novas.",
                    },
                    "comunicacao_verbal": {
                        "score": 2.5,
                        "observations": "Discurso pouco reciproco.",
                    },
                    "comunicacao_nao_verbal": {
                        "score": 3.0,
                        "observations": "Gestos pouco integrados a comunicacao.",
                    },
                    "integracao_pensamento_cognicao": {
                        "score": 2.0,
                        "observations": "Dificuldade em integrar informacoes globais.",
                    },
                    "resposta_intelectual": {
                        "score": 1.5,
                        "observations": "Funcionamento cognitivo global preservado, com discrepancias.",
                    },
                    "impressoes_gerais": {
                        "score": 3.0,
                        "observations": "Conjunto clinico compativel com alteracoes do espectro autista.",
                    },
                },
            },
        )

        self.assertEqual(module.validate(context), [])

        computed = module.compute(context)
        self.assertEqual(computed["raw_total"], 34.0)
        self.assertEqual(computed["t_score"], 51)
        self.assertEqual(computed["percentile"], "54")

        classified = module.classify(computed)
        self.assertEqual(classified["severity_code"], "severe")
        self.assertEqual(classify_cars2_hf(34.0)["severity_code"], "severe")

        interpretation = module.interpret(context, {**computed, **classified})
        self.assertIn("CARS2-HF evidenciou escore bruto total de 34.0", interpretation)
        self.assertIn("Relacionamento com pessoas", interpretation)


class MCHATModuleTests(SimpleTestCase):
    def test_computes_failures_and_positive_triage(self):
        module = MCHATModule()
        items = {
            slug: {
                "answer": FAILURE_RULES[number]
                if number in {1, 2, 7}
                else ("Não" if FAILURE_RULES[number] == "Sim" else "Sim")
            }
            for number, slug in ITEMS
        }

        context = TestContext(
            patient_name="Paciente M-CHAT",
            evaluation_id=1,
            instrument_code="MCHAT",
            raw_scores={
                "patient_name": "Paciente M-CHAT",
                "evaluation_date": "2026-04-15",
                "birth_date": "2024-02-10",
                "age_months": 22,
                "respondent_name": "Mae",
                "respondent_relationship": "Mãe",
                "items": items,
            },
        )

        self.assertEqual(module.validate(context), [])

        computed = module.compute(context)
        self.assertEqual(computed["critical_failures"], 2)
        self.assertEqual(computed["total_failures"], 3)

        classified = module.classify(computed)
        self.assertEqual(classified["screen_code"], "positive")

        interpretation = module.interpret(context, {**computed, **classified})
        self.assertIn("Triagem positiva", interpretation)
        self.assertIn("itens críticos", interpretation)


class FDTModuleTests(SimpleTestCase):
    def test_compute_exposes_dynamic_chart_payload(self):
        module = FDTModule()
        context = TestContext(
            patient_name="Larissa Souza",
            evaluation_id=1,
            instrument_code="fdt",
            raw_scores={
                "leitura": {"tempo": 18, "erros": 0},
                "contagem": {"tempo": 22, "erros": 1},
                "escolha": {"tempo": 26, "erros": 2},
                "alternancia": {"tempo": 35, "erros": 3},
            },
            reviewed_scores={"age": 9},
        )

        computed = module.compute(context)

        automaticos = computed["charts"]["automaticos"]
        controlados = computed["charts"]["controlados"]

        self.assertEqual(automaticos["categories"][0], "Sem Indicativo de Déficit")
        self.assertEqual(automaticos["series"][0]["label"], "CONTAGEM")
        self.assertEqual(automaticos["series"][0]["values"][4], 1)
        self.assertEqual(automaticos["series"][1]["values"][5], 18.0)
        self.assertEqual(controlados["series"][0]["label"], "FLEXIBILIDADE")
        self.assertEqual(controlados["series"][0]["values"][4], 0)
        self.assertEqual(controlados["series"][2]["values"][4], 3)

    def test_interpretation_for_preserved_profile_mentions_absence_of_errors(self):
        module = FDTModule()
        context = TestContext(
            patient_name="Larissa Souza",
            evaluation_id=1,
            instrument_code="fdt",
        )
        merged_data = {
            "metric_results": [
                {"codigo": "leitura", "classificacao": "Media", "categoria": "Processos Automaticos"},
                {"codigo": "contagem", "classificacao": "Superior", "categoria": "Processos Automaticos"},
                {"codigo": "escolha", "classificacao": "Media", "categoria": "Processos Controlados"},
                {"codigo": "alternancia", "classificacao": "Media Superior", "categoria": "Processos Controlados"},
                {"codigo": "inibicao", "classificacao": "Media", "categoria": "Processos Controlados"},
                {"codigo": "flexibilidade", "classificacao": "Superior", "categoria": "Processos Controlados"},
            ],
            "erros": {
                "leitura": {"qtde_erros": 0},
                "contagem": {"qtde_erros": 0},
                "escolha": {"qtde_erros": 0},
                "alternancia": {"qtde_erros": 0},
            },
        }

        interpretation = module.interpret(context, merged_data)

        self.assertIn("Larissa", interpretation)
        self.assertIn("A ausência de erros em todas as etapas", interpretation)
        self.assertIn("Em análise clínica", interpretation)

    def test_interpretation_for_altered_profile_mentions_controlled_errors(self):
        module = FDTModule()
        context = TestContext(
            patient_name="Bruno Lima",
            evaluation_id=1,
            instrument_code="fdt",
        )
        merged_data = {
            "metric_results": [
                {"codigo": "leitura", "classificacao": "Media", "categoria": "Processos Automaticos"},
                {"codigo": "contagem", "classificacao": "Media Inferior", "categoria": "Processos Automaticos"},
                {"codigo": "escolha", "classificacao": "Inferior", "categoria": "Processos Controlados"},
                {"codigo": "alternancia", "classificacao": "Muito Inferior", "categoria": "Processos Controlados"},
                {"codigo": "inibicao", "classificacao": "Inferior", "categoria": "Processos Controlados"},
                {"codigo": "flexibilidade", "classificacao": "Media", "categoria": "Processos Controlados"},
            ],
            "erros": {
                "leitura": {"qtde_erros": 0},
                "contagem": {"qtde_erros": 1},
                "escolha": {"qtde_erros": 3},
                "alternancia": {"qtde_erros": 4},
            },
        }

        interpretation = module.interpret(context, merged_data)

        self.assertIn("A frequência elevada de erros", interpretation)
        self.assertIn("controle inibitório", interpretation)
        self.assertIn("Em análise clínica", interpretation)


class FDTPdfServiceTests(SimpleTestCase):
    def test_generate_pdf_bytes_returns_pdf_document(self):
        application = SimpleNamespace(
            id=42,
            evaluation_id=7,
            applied_on=date(2026, 5, 14),
            classified_payload={
                "idade": 14,
                "faixa": "Normas Brasileiras",
                "stage_totals": {
                    "leitura": {"tempo": 26, "erros": 0},
                    "contagem": {"tempo": 43, "erros": 1},
                    "escolha": {"tempo": 67, "erros": 2},
                    "alternancia": {"tempo": 80, "erros": 2},
                },
                "metric_results": [
                    {"codigo": "leitura", "media": 20.4, "valor": 26.45, "percentil_num": 5, "classificacao": "Inferior"},
                    {"codigo": "contagem", "media": 23.8, "valor": 42.97, "percentil_num": 5, "classificacao": "Inferior"},
                    {"codigo": "escolha", "media": 34.0, "valor": 67.14, "percentil_num": 5, "classificacao": "Inferior"},
                    {"codigo": "alternancia", "media": 44.8, "valor": 79.65, "percentil_num": 5, "classificacao": "Inferior"},
                    {"codigo": "inibicao", "media": 13.6, "valor": 40.69, "percentil_num": 5, "classificacao": "Inferior"},
                    {"codigo": "flexibilidade", "media": 24.4, "valor": 53.2, "percentil_num": 5, "classificacao": "Inferior"},
                ],
            },
            evaluation=SimpleNamespace(
                patient=SimpleNamespace(
                    full_name="Paciente Exemplo",
                    sex="Masculino",
                    state="Goiás",
                    email="paciente@email.com",
                    grade_year="Ensino Fundamental",
                    schooling=None,
                ),
                examiner=SimpleNamespace(full_name="André F. Silva", display_name=None, crp="00/0000"),
            ),
        )

        payload = FDTPdfService.generate_pdf_bytes(application)

        self.assertTrue(payload.startswith(b"%PDF"))
        self.assertIn(b"/Page", payload)


class RAVLTModuleTests(SimpleTestCase):
    def test_classify_exposes_dynamic_chart_payload(self):
        module = RAVLTModule()
        context = TestContext(
            patient_name="Ana Souza",
            evaluation_id=1,
            instrument_code="ravlt",
            raw_scores={
                "a1": 7,
                "a2": 8,
                "a3": 12,
                "a4": 13,
                "a5": 13,
                "b": 5,
                "a6": 12,
                "a7": 11,
                "reconhecimento": 14,
            },
        )

        computed = module.compute(context)
        classified = module.classify(computed, idade=21)

        chart = classified["chart"]
        self.assertEqual(chart["labels"][0], "A1")
        self.assertEqual(chart["labels"][-1], "I.R.")
        self.assertEqual(chart["series"][0]["label"], "Esperado")
        self.assertEqual(chart["series"][1]["label"], "Mínimo")
        self.assertEqual(chart["series"][2]["label"], "Obtido")
        self.assertEqual(chart["series"][2]["values"][:4], [7.0, 8.0, 12.0, 13.0])
        self.assertEqual(chart["series"][2]["values"][8], -21.0)

    def test_interpret_uses_process_based_clinical_model(self):
        module = RAVLTModule()
        context = TestContext(
            patient_name="Ana Souza",
            evaluation_id=1,
            instrument_code="ravlt",
            raw_scores={
                "a1": 7,
                "a2": 8,
                "a3": 12,
                "a4": 13,
                "a5": 13,
                "b": 5,
                "a6": 12,
                "a7": 11,
                "reconhecimento": 14,
            },
        )

        computed = module.compute(context)
        interpretation = module.interpret(context, {**computed, **module.classify(computed, idade=21)})

        self.assertIn("A aquisição inicial situou-se", interpretation)
        self.assertIn("A curva de aprendizagem apresentou padrão", interpretation)
        self.assertIn("O reconhecimento verbal situou-se", interpretation)
        self.assertIn("Os achados devem ser integrados", interpretation)


class RAVLTPdfServiceTests(SimpleTestCase):
    def _ravlt_application_fixture(self):
        return SimpleNamespace(
            id=52,
            evaluation_id=9,
            applied_on=date(2026, 5, 21),
            instrument=SimpleNamespace(code="ravlt"),
            raw_payload={
                "a1": 5,
                "a2": 8,
                "a3": 10,
                "a4": 12,
                "a5": 11,
                "b": 3,
                "a6": 11,
                "a7": 11,
                "reconhecimento": 14,
            },
            classified_payload={
                "faixa_etaria": "21-30",
                "idade": 24,
                "resultados": [
                    {"variavel": "A1", "bruto": 5, "classificacao": "Média", "media": 5.1, "dp": 1.2, "ponderado": 10.0, "percentil": 50.0},
                    {"variavel": "A2", "bruto": 8, "classificacao": "Superior", "media": 7.2, "dp": 1.4, "ponderado": 13.0, "percentil": 90.0},
                    {"variavel": "A3", "bruto": 10, "classificacao": "Superior", "media": 8.3, "dp": 1.5, "ponderado": 13.0, "percentil": 90.0},
                    {"variavel": "A4", "bruto": 12, "classificacao": "Superior", "media": 9.5, "dp": 1.4, "ponderado": 14.0, "percentil": 95.0},
                    {"variavel": "A5", "bruto": 11, "classificacao": "Superior", "media": 10.1, "dp": 1.3, "ponderado": 13.0, "percentil": 90.0},
                    {"variavel": "B1", "bruto": 3, "classificacao": "Inferior", "media": 4.9, "dp": 1.1, "ponderado": 7.0, "percentil": 10.0},
                    {"variavel": "A6", "bruto": 11, "classificacao": "Superior", "media": 9.7, "dp": 1.2, "ponderado": 13.0, "percentil": 90.0},
                    {"variavel": "A7", "bruto": 11, "classificacao": "Superior", "media": 9.4, "dp": 1.3, "ponderado": 13.0, "percentil": 90.0},
                    {"variavel": "Reconhecimento Lista A", "bruto": 15, "classificacao": "Superior", "media": 13.4, "dp": 1.4, "ponderado": 14.0, "percentil": 95.0},
                    {"variavel": "Escore Total", "bruto": 46, "classificacao": "Superior", "media": 39.0, "dp": 4.2, "ponderado": 14.0, "percentil": 95.0},
                    {"variavel": "Aprend. longo das Tentativas", "bruto": 21, "classificacao": "Superior", "media": 39.0, "dp": 4.2, "ponderado": 14.0, "percentil": 95.0},
                    {"variavel": "Velocidade de Esquecimento", "bruto": 1.00, "classificacao": "Média", "media": 0.92, "dp": 0.12, "ponderado": 10.0, "percentil": 50.0},
                    {"variavel": "Interferência Proativa", "bruto": 0.60, "classificacao": "Inferior", "media": 0.85, "dp": 0.14, "ponderado": 7.0, "percentil": 10.0},
                    {"variavel": "Interferência Retroativa", "bruto": 1.00, "classificacao": "Média", "media": 0.93, "dp": 0.10, "ponderado": 10.0, "percentil": 50.0},
                ],
            },
            interpretation_text="",
            report_payload={},
            evaluation=SimpleNamespace(
                patient=SimpleNamespace(full_name="Paciente Exemplo", sex="M", grade_year=None, schooling="Ensino superior completo"),
            ),
        )

    def test_generate_pdf_bytes_returns_pdf_document(self):
        application = self._ravlt_application_fixture()
        application.classified_payload["chart"] = {
            "title": "RAVLT - Quantidade de palavras evocadas",
            "labels": ["A1", "A2", "A3", "A4", "A5", "B1", "A6", "A7", "R", "ALT", "RET", "I.P.", "I.R."],
            "series": [
                {"key": "esperado", "label": "Esperado", "color": "#ED7D31", "values": [5, 7, 8, 9, 10, 4, 9, 9, 13, 40, 1, 1, 1]},
                {"key": "minimo", "label": "Mínimo", "color": "#FFC000", "values": [4, 6, 7, 8, 9, 3, 8, 8, 12, 35, 1, 1, 1]},
                {"key": "obtido", "label": "Obtido", "color": "#70AD47", "values": [5, 8, 10, 12, 11, 3, 11, 11, 15, 46, 1, 0.6, 1]},
            ],
            "y_axis": {"min": 0, "max": 21, "ticks": [0, 5, 10, 15, 20]},
        }

        payload = RAVLTPdfService.generate_pdf_bytes(application)

        self.assertTrue(payload.startswith(b"%PDF"))
        self.assertIn(b"/Page", payload)

    def test_summary_and_box_reflect_structural_fragilities(self):
        result_map = {
            "A1": {"classificacao": "Superior"},
            "Escore Total": {"classificacao": "Média Superior"},
            "A7": {"classificacao": "Média"},
            "Reconhecimento Lista A": {"classificacao": "Média Inferior"},
            "Aprend. longo das Tentativas": {"classificacao": "Muito Inferior"},
            "Interferência Proativa": {"classificacao": "Média"},
            "Interferência Retroativa": {"classificacao": "Média"},
        }
        raw_payload = {"a1": 12, "a2": 8, "a3": 11, "a4": 12, "a5": 10, "a6": 10, "a7": 10, "b": 11}

        clinical_box = RAVLTPdfService._clinical_box_text("jacqueline Oliveira Caires", raw_payload, result_map)
        summary = RAVLTPdfService._summary_for_report("jacqueline Oliveira Caires", raw_payload, result_map)

        self.assertIn("o RAVLT indicou aquisição inicial preservada, porém com menor eficiência na aquisição progressiva e no benefício da repetição sucessiva.", clinical_box)
        self.assertIn("aquisição inicial na faixa Superior", clinical_box)
        self.assertIn("Escore Total na faixa Média Superior", clinical_box)
        self.assertIn("aprendizagem ao longo das tentativas em nível Deficitário", clinical_box)
        self.assertIn("reconhecimento verbal na faixa Média Inferior", clinical_box)
        self.assertIn("O RAVLT indicou aquisição inicial preservada, porém com menor eficiência na aquisição progressiva e no benefício da repetição sucessiva.", summary)
        self.assertIn("aquisição inicial na faixa Superior, Escore Total na faixa Média Superior e evocação tardia dentro da média", summary)
        self.assertIn("aprendizagem ao longo das tentativas em nível Deficitário e reconhecimento verbal na faixa Média Inferior", summary)
        self.assertIn("preservação relativa de aquisição inicial, volume global de evocação verbal e retenção tardia, com vulnerabilidades em aquisição progressiva, benefício da repetição sucessiva e reconhecimento verbal", summary)

    def test_normative_and_schooling_labels_are_humanized(self):
        patient = SimpleNamespace(schooling="fundamental_completo", grade_year=None)

        self.assertEqual(RAVLTPdfService._schooling_label(patient), "Ensino fundamental completo")
        self.assertEqual(RAVLTPdfService._normative_label("6 a 18 anos", 10), "Infantil / 6 a 18 anos")

    def test_text_classification_and_number_formatting_are_humanized(self):
        self.assertEqual(RAVLTPdfService._faixa_text("Muito Superior"), "na faixa Superior")
        self.assertEqual(RAVLTPdfService._faixa_text("Muito Inferior", nivel=True), "Deficitário")
        self.assertEqual(RAVLTPdfService._format_text_number(53.0), "53")
        self.assertEqual(RAVLTPdfService._format_text_number(-2.0), "-2")

    def test_box_and_summary_handle_interference_only_without_empty_placeholders(self):
        result_map = {
            "A1": {"classificacao": "Média"},
            "B1": {"classificacao": "Média Inferior"},
            "A6": {"classificacao": "Média Inferior"},
            "A7": {"classificacao": "Média Superior"},
            "Reconhecimento Lista A": {"classificacao": "Média Superior"},
            "Escore Total": {"classificacao": "Média"},
            "Aprend. longo das Tentativas": {"classificacao": "Média"},
            "Interferência Proativa": {"classificacao": "Média Inferior"},
            "Interferência Retroativa": {"classificacao": "Inferior"},
        }
        raw_payload = {"a1": 7, "a2": 8, "a3": 11, "a4": 12, "a5": 13, "a6": 8, "a7": 13, "b": 4}

        clinical_box = RAVLTPdfService._clinical_box_text("Asriel David´s Santana Alves", raw_payload, result_map)
        summary = RAVLTPdfService._summary_for_report("Asriel David´s Santana Alves", raw_payload, result_map)

        self.assertNotIn("Contudo, observou-se .", clinical_box)
        self.assertNotIn("vulnerabilidade na ,", clinical_box)
        self.assertIn("Escore Total dentro da média", clinical_box)
        self.assertIn("vulnerabilidade à interferência proativa", clinical_box)
        self.assertIn("B1 na faixa Média Inferior, I.P. na faixa Média Inferior, A6 na faixa Média Inferior e I.R. em nível Inferior", clinical_box)
        self.assertIn("aquisição inicial dentro da média, Escore Total dentro da média, evocação tardia na faixa Média Superior e reconhecimento verbal na faixa Média Superior", summary)
        self.assertIn("interferência proativa e interferência retroativa", summary)

    @override_settings(TEST_INTERPRETATION_AI_ENABLED=False)
    def test_ai_orchestrator_returns_fallback_when_feature_is_disabled(self):
        application = self._ravlt_application_fixture()
        fallback = TestAIInterpretationDraft(
            clinical_paragraphs=["p1", "p2", "p3", "p4", "p5"],
            clinical_box_text="o RAVLT indicou funcionamento mnésico verbal preservado.",
            summary_for_report="O RAVLT indicou funcionamento mnésico verbal preservado.",
        )

        draft = TestAIInterpretationOrchestrator.generate_for_application(application, fallback)

        self.assertEqual(draft.metadata.get("generation_path"), "fallback")
        self.assertEqual(draft.metadata.get("fallback_reason"), "feature_disabled")
        self.assertEqual(draft.summary_for_report, fallback.summary_for_report)

    @override_settings(TEST_INTERPRETATION_AI_ENABLED=True, AI_PROVIDER="openai", OPENAI_API_KEY="test-key")
    @patch("apps.tests.services.ai_interpretation_orchestrator.TextGenerationService.generate_from_prompt")
    def test_ai_orchestrator_accepts_valid_ravlt_response(self, mock_generate):
        application = self._ravlt_application_fixture()
        fallback = TestAIInterpretationDraft(
            clinical_paragraphs=["p1", "p2", "p3", "p4", "p5"],
            clinical_box_text="o RAVLT indicou funcionamento mnésico verbal preservado.",
            summary_for_report="O RAVLT indicou funcionamento mnésico verbal preservado.",
        )
        mock_generate.return_value = {
            "content": '{"clinical_paragraphs": ["Parágrafo 1.", "Parágrafo 2.", "Parágrafo 3 com interferência proativa em B1.", "Parágrafo 4.", "Parágrafo 5 com interferência proativa."], "clinical_box_text": "o RAVLT indicou funcionamento mnésico verbal predominantemente preservado, com ponto de atenção em interferência proativa evidenciada por B1.", "summary_for_report": "O RAVLT indicou funcionamento mnésico verbal predominantemente preservado, com ponto de atenção em interferência proativa evidenciada por B1."}',
            "provider": "openai",
            "model": "gpt-test",
            "warnings": [],
        }

        draft = TestAIInterpretationOrchestrator.generate_for_application(application, fallback)

        self.assertEqual(draft.metadata.get("generation_path"), "ai")
        self.assertEqual(draft.metadata.get("provider"), "openai")
        self.assertEqual(len(draft.clinical_paragraphs), 5)
        self.assertEqual(draft.summary_for_report, "O RAVLT indicou funcionamento mnésico verbal predominantemente preservado, com ponto de atenção em interferência proativa evidenciada por B1.")

    @override_settings(TEST_INTERPRETATION_AI_ENABLED=True, AI_PROVIDER="openai", OPENAI_API_KEY="test-key")
    @patch("apps.tests.services.ai_interpretation_orchestrator.TextGenerationService.generate_from_prompt")
    def test_ai_orchestrator_rejects_invalid_response_and_uses_fallback(self, mock_generate):
        application = self._ravlt_application_fixture()
        fallback = TestAIInterpretationDraft(
            clinical_paragraphs=["p1", "p2", "p3", "p4", "p5"],
            clinical_box_text="o RAVLT indicou funcionamento mnésico verbal preservado.",
            summary_for_report="O RAVLT indicou funcionamento mnésico verbal preservado.",
        )
        mock_generate.return_value = {
            "content": '{"clinical_paragraphs": ["Parágrafo único."], "clinical_box_text": "Box inválido", "summary_for_report": "Resumo inválido"}',
            "provider": "openai",
            "model": "gpt-test",
            "warnings": [],
        }

        draft = TestAIInterpretationOrchestrator.generate_for_application(application, fallback)

        self.assertEqual(draft.metadata.get("generation_path"), "fallback")
        self.assertEqual(draft.metadata.get("fallback_reason"), "validation_failed")
        self.assertIn("exatamente 5 paragrafos clinicos", " ".join(draft.warnings))

    def test_ravlt_ai_validator_rejects_unsuported_muito_superior_and_recognition_vulnerability(self):
        handler = RAVLTAIInterpretationHandler()
        payload = {
            "profile": "perfil_misto",
            "results": {
                "B1": {"classification": "Superior"},
                "R": {"classification": "Média"},
                "Aprend. longo das tentativas": {"classification": "Inferior"},
                "A6": {"classification": "Inferior"},
                "I.R.": {"classification": "Inferior"},
                "I.P.": {"classification": "Média Superior"},
            },
        }
        response = {
            "clinical_paragraphs": ["P1.", "P2.", "P3 B1 classificada como Muito Superior.", "P4.", "P5."],
            "clinical_box_text": "o RAVLT indicou funcionamento mnésico verbal heterogêneo. Andre apresentou recursos preservados. Contudo, observou-se aprendizagem ao longo das tentativas em nível Inferior. Esse perfil sugere vulnerabilidade no reconhecimento verbal.",
            "summary_for_report": "O RAVLT indicou funcionamento mnésico verbal heterogêneo. Andre apresentou Escore Total dentro da média. Em análise clínica, esse perfil sugere vulnerabilidade no reconhecimento verbal.",
        }

        errors = handler.validate_response(response, payload)

        self.assertIn("Muito Superior", " ".join(errors))
        self.assertIn("reconhecimento verbal foi descrito como vulnerabilidade", " ".join(errors))

    def test_ravlt_ai_handler_maps_payload_classifications_to_table_labels(self):
        handler = RAVLTAIInterpretationHandler()
        application = self._ravlt_application_fixture()

        payload = handler.build_payload(application)

        self.assertEqual(payload["results"]["A2"]["classification"], "Superior")
        self.assertEqual(payload["results"]["Aprend. longo das tentativas"]["classification"], "Superior")

    def test_ravlt_ai_validator_rejects_deficitario_and_superior_conversion(self):
        handler = RAVLTAIInterpretationHandler()
        payload = {
            "profile": "perfil_misto",
            "results": {
                "A1": {"classification": "Superior"},
                "B1": {"classification": "Superior"},
                "Aprend. longo das tentativas": {"classification": "Deficitário"},
                "R": {"classification": "Média Inferior"},
            },
        }
        response = {
            "clinical_paragraphs": [
                "A aquisição inicial situou-se em Muito Superior.",
                "A aprendizagem ao longo das tentativas situou-se em Muito Inferior.",
                "B1 foi Muito Superior.",
                "P4.",
                "P5.",
            ],
            "clinical_box_text": "o RAVLT indicou funcionamento mnésico verbal heterogêneo.",
            "summary_for_report": "O RAVLT indicou funcionamento mnésico verbal heterogêneo.",
        }

        errors = handler.validate_response(response, payload)

        self.assertIn("converteu 'Superior' em 'Muito Superior'", " ".join(errors))
        self.assertIn("converteu 'Deficitário' em 'Muito Inferior'", " ".join(errors))

    def test_ravlt_ai_validator_requires_retroactive_fragility_in_closing(self):
        handler = RAVLTAIInterpretationHandler()
        payload = {
            "profile": "perfil_misto",
            "results": {
                "A6": {"classification": "Inferior"},
                "I.R.": {"classification": "Inferior"},
                "Aprend. longo das tentativas": {"classification": "Média"},
                "R": {"classification": "Média"},
            },
        }
        response = {
            "clinical_paragraphs": ["P1.", "P2.", "P3.", "P4.", "P5."],
            "clinical_box_text": "o RAVLT indicou funcionamento mnésico verbal heterogêneo. Andre apresentou retenção tardia preservada.",
            "summary_for_report": "O RAVLT indicou funcionamento mnésico verbal heterogêneo. Andre apresentou evocação tardia dentro da média. Em análise clínica, esse perfil sugere preservação mnésica global.",
        }

        errors = handler.validate_response(response, payload)

        self.assertIn("sensibilidade retroativa", " ".join(errors))

    def test_ravlt_ai_validator_blocks_acquisition_and_consolidation_contradictions(self):
        handler = RAVLTAIInterpretationHandler()
        payload = {
            "profile": "perfil_misto",
            "results": {
                "A1": {"classification": "Média"},
                "A7": {"classification": "Média Superior"},
                "Velocidade de esquecimento": {"classification": "Média"},
                "R": {"classification": "Média Inferior"},
                "Aprend. longo das tentativas": {"classification": "Média"},
            },
        }
        response = {
            "clinical_paragraphs": [
                "Há fragilidade na aquisição inicial apesar de A1 dentro da média.",
                "P2.",
                "P3.",
                "P4 com fragilidade na consolidação.",
                "P5.",
            ],
            "clinical_box_text": "o RAVLT indicou perfil misto com reconhecimento preservado.",
            "summary_for_report": "O RAVLT indicou perfil misto com reconhecimento preservado.",
        }

        errors = handler.validate_response(response, payload)

        self.assertIn("aquisicao inicial foi descrita como fragil", " ".join(errors))
        self.assertIn("fragilidade de consolidacao", " ".join(errors))
        self.assertIn("reconhecimento verbal foi descrito como preservado", " ".join(errors))


class BPA2PdfServiceTests(SimpleTestCase):
    def _application_fixture(self):
        return SimpleNamespace(
            id=63,
            evaluation_id=12,
            applied_on=date(2026, 5, 22),
            instrument=SimpleNamespace(code="bpa2", name="BPA-2"),
            raw_payload={
                "ac": {"brutos": 83, "erros": 3, "omissoes": 0},
                "ad": {"brutos": 101, "erros": 1, "omissoes": 0},
                "aa": {"brutos": 120, "erros": 2, "omissoes": 0},
            },
            computed_payload={},
            classified_payload={
                "faixa": "31-40 anos",
                "norm_type": "idade",
                "subtestes": [
                    {"subteste": "Atenção Concentrada", "codigo": "ac", "brutos": 83, "erros": 3, "omissoes": 0, "total": 80, "classificacao": "Média", "percentil": 40},
                    {"subteste": "Atenção Dividida", "codigo": "ad", "brutos": 101, "erros": 1, "omissoes": 0, "total": 100, "classificacao": "Superior", "percentil": 90},
                    {"subteste": "Atenção Alternada", "codigo": "aa", "brutos": 120, "erros": 2, "omissoes": 0, "total": 118, "classificacao": "Superior", "percentil": 90},
                    {"subteste": "Atenção Geral", "codigo": "ag", "brutos": 304, "erros": 6, "omissoes": 0, "total": 298, "classificacao": "Média Superior", "percentil": 80},
                ],
            },
            interpretation_text="",
            evaluation=SimpleNamespace(
                examiner=None,
                patient=SimpleNamespace(
                    full_name="Andre Alekhine",
                    sex="M",
                    age=31,
                    birth_date=None,
                    schooling="middle",
                    grade_year=None,
                ),
            ),
        )

    def test_build_context_uses_bpa2_pdf_layout_data(self):
        context = BPA2PdfService._build_context(self._application_fixture())

        self.assertEqual(context["codigo_avaliado"], "AVL-063")
        self.assertEqual(context["codigo_relatorio"], "RPT-BPA2-063")
        self.assertEqual(context["tabela_normativa"], "Adulto / 31-40 anos")
        self.assertEqual([row["short_label"] for row in context["rows"]], ["AC", "AD", "AA", "AG"])
        self.assertEqual(context["rows"][0]["points"], "80")
        self.assertEqual(context["rows"][3]["classification"], "Média Superior")
        self.assertEqual([bar["label"] for bar in context["chart_bars"]], ["AC", "AD", "AA", "Erros", "AG"])
        self.assertEqual(context["chart_bars"][3]["value"], "6")
        self.assertIn("A BPA-2 indicou desempenho atencional geral", context["clinical_paragraphs"][0])
        self.assertIn("esse índice deve ser interpretado com cautela", context["clinical_paragraphs"][0])
        self.assertIn("Os erros observados nesse domínio", context["clinical_paragraphs"][1])
        self.assertNotIn("omissões", " ".join(context["clinical_paragraphs"]).lower())
        self.assertIn("Em análise clínica", context["clinical_box_text"])
        self.assertIn("A BPA-2 indicou desempenho atencional geral na faixa Média Superior", context["synthesis_text"])

    def test_gold_standard_interpretation_integrates_errors_omissions_and_domains(self):
        subtests = self._application_fixture().classified_payload["subtestes"]

        interpretation = build_gold_standard_interpretation(subtests, "Andre Alekhine")

        self.assertEqual(len(interpretation["clinical_paragraphs"]), 5)
        self.assertIn("Na Atenção Concentrada", interpretation["clinical_paragraphs"][1])
        self.assertIn("Na Atenção Dividida", interpretation["clinical_paragraphs"][2])
        self.assertIn("Na Atenção Alternada", interpretation["clinical_paragraphs"][3])
        self.assertIn("presença de erros em quantidade moderada", interpretation["clinical_paragraphs"][4])
        self.assertNotIn("omissões", " ".join(interpretation["clinical_paragraphs"]).lower())
        self.assertIn("não devendo ser interpretados de forma isolada", interpretation["synthesis_text"])

    def test_gold_standard_interpretation_is_less_cautious_for_homogeneous_superior_profile(self):
        subtests = [
            {"subteste": "Atenção Concentrada", "codigo": "ac", "erros": 0, "omissoes": 0, "total": 120, "classificacao": "Muito Superior", "percentil": 99},
            {"subteste": "Atenção Dividida", "codigo": "ad", "erros": 0, "omissoes": 3, "total": 114, "classificacao": "Muito Superior", "percentil": 99},
            {"subteste": "Atenção Alternada", "codigo": "aa", "erros": 0, "omissoes": 0, "total": 120, "classificacao": "Muito Superior", "percentil": 99},
            {"subteste": "Atenção Geral", "codigo": "ag", "erros": 0, "omissoes": 3, "total": 354, "classificacao": "Muito Superior", "percentil": 99},
        ]

        interpretation = build_gold_standard_interpretation(subtests, "Ariel")
        text = " ".join([*interpretation["clinical_paragraphs"], interpretation["clinical_box_text"], interpretation["synthesis_text"]])

        self.assertIn("desempenho convergente entre atenção concentrada, atenção dividida e atenção alternada", text)
        self.assertIn("A ausência de erros", text)
        self.assertNotIn("mascare discrepâncias", text)
        self.assertNotIn("omissões", text.lower())

    def test_bpa2_module_uses_gold_standard_interpretation(self):
        module = BPA2Module()
        context = TestContext(
            patient_name="Andre Alekhine",
            evaluation_id=14,
            instrument_code="bpa2",
            raw_scores={
                "ac": {"brutos": 83, "erros": 3, "omissoes": 0},
                "ad": {"brutos": 101, "erros": 1, "omissoes": 0},
                "aa": {"brutos": 120, "erros": 2, "omissoes": 0},
            },
        )
        merged_data = self._application_fixture().classified_payload

        text = module.interpret(context, merged_data)

        self.assertIn("A BPA-2 indicou desempenho atencional geral situado", text)
        self.assertIn("Em análise clínica", text)
        self.assertIn("não devendo ser interpretados de forma isolada", text)

    def test_pdf_export_service_registers_bpa2_exporter(self):
        self.assertIn("bpa2", TestPdfExportService.EXPORTERS)


class WISC4PdfServiceTests(SimpleTestCase):
    def _application_fixture(self):
        subtests = [
            {"subteste": "Cubos", "codigo": "CB", "escore_bruto": 31, "escore_padrao": 9, "percentil": 37, "classificacao": "Média", "intervalo_confianca_95": (7, 12)},
            {"subteste": "Semelhanças", "codigo": "SM", "escore_bruto": 22, "escore_padrao": 8, "percentil": 25, "classificacao": "Média", "intervalo_confianca_95": (6, 10)},
            {"subteste": "Dígitos", "codigo": "DG", "escore_bruto": 13, "escore_padrao": 6, "percentil": 9, "classificacao": "Dificuldade Leve", "intervalo_confianca_95": (4, 8)},
        ]
        indices = [
            {"indice": "icv", "nome": "Índice de Compreensão Verbal", "soma_ponderados": 25, "escore_composto": 88, "percentil": 21, "intervalo_confianca": (82, 95), "classificacao": "Média Inferior"},
            {"indice": "iop", "nome": "Índice de Organização Perceptual", "soma_ponderados": 30, "escore_composto": 100, "percentil": 50, "intervalo_confianca": (93, 107), "classificacao": "Média"},
            {"indice": "imt", "nome": "Índice de Memória Operacional", "soma_ponderados": 12, "escore_composto": 76, "percentil": 5, "intervalo_confianca": (70, 84), "classificacao": "Limítrofe"},
            {"indice": "ivp", "nome": "Índice de Velocidade de Processamento", "soma_ponderados": 18, "escore_composto": 90, "percentil": 25, "intervalo_confianca": (84, 98), "classificacao": "Média Inferior"},
        ]
        return SimpleNamespace(
            id=52,
            evaluation_id=8,
            applied_on=date(2026, 5, 22),
            instrument=SimpleNamespace(code="wisc4", name="WISC-IV"),
            raw_payload={},
            computed_payload={
                "cf": {"subteste": "Completar Figuras", "codigo": "CF", "escore_bruto": 18, "escore_padrao": 8, "classificacao": "Média"},
            },
            classified_payload={
                "subtestes": subtests,
                "indices": indices,
                "qit_data": {"soma_ponderados": 85, "escore_composto": 86, "percentil": 18, "intervalo_confianca": (81, 92), "classificacao": "Média Inferior"},
                "gai_data": {"soma_ponderados": 55, "escore_composto": 94, "percentil": 34, "intervalo_confianca": (88, 101), "classificacao": "Média"},
                "cpi_data": {"soma_ponderados": 30, "escore_composto": 82, "percentil": 12, "intervalo_confianca": (76, 90), "classificacao": "Média Inferior"},
                "pontos_fortes": ["Cubos"],
                "pontos_fragilizados": ["Dígitos"],
                "diferencas_significativas": ["Índice de Memória Operacional difere significativamente do QI Total: 10 pontos"],
                "confidence_level": "95",
                "process_scores": {
                    "scaled_rows": [
                        {"name": "Cubos sem Tempo de Bônus", "code": "CUSB", "raw_score": 19, "scaled_score": 8},
                    ],
                    "sequence_frequency_rows": [
                        {"name": "Sequência Maior de Dígitos Ordem Direta", "code": "UDIOD", "raw_score": 5, "frequency": 64.0},
                    ],
                    "raw_discrepancy_rows": [
                        {"label": "UDIOD - UDIOI", "first": 5, "second": 3, "difference": 2, "frequency": 62.7},
                    ],
                    "process_discrepancy_rows": [
                        {"label": "Cubos - Cubos sem Tempo de Bônus", "first": 9, "second": 8, "difference": 1, "critical": 3.1, "significant": False, "frequency": 13.3},
                    ],
                },
            },
            interpretation_text="Interpretação e Observações Clínicas\n\nO WISC-IV indicou funcionamento cognitivo global abaixo da média normativa.\n\nEm análise clínica, o perfil deve ser integrado aos demais dados.",
            evaluation=SimpleNamespace(
                examiner=None,
                patient=SimpleNamespace(
                    full_name="Paciente Exemplo",
                    sex="F",
                    age=None,
                    birth_date=date(2016, 1, 10),
                    schooling="elementary",
                    grade_year=None,
                ),
            ),
        )

    def test_build_context_uses_wisc4_pdf_layout_data(self):
        context = WISC4PdfService._build_context(self._application_fixture())

        self.assertEqual(context["codigo_avaliado"], "AVL-052")
        self.assertEqual(context["codigo_relatorio"], "RPT-WISC4-052")
        self.assertEqual(context["nome"], "Paciente Exemplo")
        self.assertEqual(context["idade"], "10 anos e 4 meses")
        self.assertEqual([row["code"] for row in context["subtest_rows"]], ["CB", "SM", "DG"])
        self.assertEqual(context["composite_rows"][4]["abbreviation"], "QIT")
        self.assertEqual(context["composite_rows"][4]["score"], "86")
        self.assertEqual(context["supplemental_rows"][0]["code"], "CF")
        self.assertEqual(context["process_scaled_rows"][0]["scaled_score"], "8")
        self.assertEqual(context["process_discrepancy_rows"][0]["significant"], "Não")
        self.assertEqual(len(context["clinical_paragraphs"]), 2)
        self.assertIn("inferências diagnósticas isoladas", context["clinical_box_text"])

    def test_pdf_export_service_registers_wisc4_exporter(self):
        self.assertIn("wisc4", TestPdfExportService.EXPORTERS)
        self.assertIn("WISC-IV", TestPdfExportService.EXPORTERS)


class WAIS3PdfServiceTests(SimpleTestCase):
    def _application_fixture(self):
        indices = {
            "qi_verbal": {"nome": "QI Verbal", "soma_ponderada": 62, "pontuacao_composta": 102, "percentil": 55, "ic_95": "97–107", "classificacao": "Média"},
            "qi_execucao": {"nome": "QI de Execução", "soma_ponderada": 52, "pontuacao_composta": 102, "percentil": 55, "ic_95": "96–108", "classificacao": "Média"},
            "qi_total": {"nome": "QI Total", "soma_ponderada": 114, "pontuacao_composta": 102, "percentil": 55, "ic_95": "98–106", "classificacao": "Média"},
            "compreensao_verbal": {"nome": "Índice de Compreensão Verbal", "soma_ponderada": 32, "pontuacao_composta": 104, "percentil": 61, "ic_95": "98–109", "classificacao": "Média"},
            "organizacao_perceptual": {"nome": "Índice de Organização Perceptual", "soma_ponderada": 29, "pontuacao_composta": 98, "percentil": 45, "ic_95": "91–105", "classificacao": "Média"},
            "memoria_operacional": {"nome": "Índice de Memória Operacional", "soma_ponderada": 29, "pontuacao_composta": 98, "percentil": 45, "ic_95": "90–106", "classificacao": "Média"},
            "velocidade_processamento": {"nome": "Índice de Velocidade de Processamento", "soma_ponderada": 20, "pontuacao_composta": 100, "percentil": 50, "ic_95": "90–110", "classificacao": "Média"},
        }
        subtestes = {
            "vocabulario": {"nome": "Vocabulário", "pontos_brutos": 36, "escore_ponderado": 11, "classificacao": "Média"},
            "semelhancas": {"nome": "Semelhanças", "pontos_brutos": 22, "escore_ponderado": 10, "classificacao": "Média"},
            "aritmetica": {"nome": "Aritmética", "pontos_brutos": 8, "escore_ponderado": 8, "classificacao": "Média"},
            "digitos": {"nome": "Dígitos", "pontos_brutos": 13, "escore_ponderado": 9, "classificacao": "Média"},
            "informacao": {"nome": "Informação", "pontos_brutos": 13, "escore_ponderado": 11, "classificacao": "Média"},
            "compreensao": {"nome": "Compreensão", "pontos_brutos": 27, "escore_ponderado": 13, "classificacao": "Média Superior"},
            "sequencia_numeros_letras": {"nome": "Sequência de Números e Letras", "pontos_brutos": 10, "escore_ponderado": 12, "classificacao": "Média Superior"},
            "completar_figuras": {"nome": "Completar Figuras", "pontos_brutos": 18, "escore_ponderado": 10, "classificacao": "Média"},
            "codigos": {"nome": "Códigos", "pontos_brutos": 59, "escore_ponderado": 10, "classificacao": "Média"},
            "cubos": {"nome": "Cubos", "pontos_brutos": 22, "escore_ponderado": 8, "classificacao": "Média"},
            "raciocinio_matricial": {"nome": "Raciocínio Matricial", "pontos_brutos": 16, "escore_ponderado": 11, "classificacao": "Média"},
            "arranjo_figuras": {"nome": "Arranjo de Figuras", "pontos_brutos": 17, "escore_ponderado": 13, "classificacao": "Média Superior"},
            "procurar_simbolos": {"nome": "Procurar Símbolos", "pontos_brutos": 26, "escore_ponderado": 10, "classificacao": "Média"},
            "armar_objetos": {"nome": "Armar Objetos", "pontos_brutos": 0, "escore_ponderado": 1, "classificacao": "Extremamente Baixo"},
        }
        return SimpleNamespace(
            id=77,
            evaluation_id=9,
            applied_on=date(2026, 5, 23),
            instrument=SimpleNamespace(code="wais3", name="WAIS-III"),
            raw_payload={"idade": {"anos": 30, "meses": 0}},
            computed_payload={"idade_normativa": "idade_30-39", "indices": indices, "subtestes": subtestes},
            classified_payload={
                "indices": indices,
                "subtestes": subtestes,
                "digitos": {
                    "maior_sequencia_direta": {"raw_score": 6, "cumulative_frequency": 61.8},
                    "maior_sequencia_inversa": {"raw_score": 4, "cumulative_frequency": 70.7},
                    "diferenca_maior_sequencia": {"difference": 2, "cumulative_frequency": 58.7},
                },
                "clusters": {
                    "Gf": {"nome": "Raciocínio Fluido (Gf)", "soma": 32, "escore": 104, "percentil": 61, "ic_95": "96 - 112", "classificacao": "Média"},
                    "Gv": {"nome": "Processamento Visual (Gv)", "soma": 18, "escore": 98, "percentil": 45, "ic_95": "89 - 107", "classificacao": "Média"},
                    "Gf_nonverbal": {"nome": "Raciocínio Fluido Não Verbal", "soma": 24, "escore": 117, "percentil": 87, "ic_95": "107 - 127", "classificacao": "Média Superior"},
                    "Gf_verbal": {"nome": "Raciocínio Fluido Verbal", "soma": 23, "escore": 100, "percentil": 50, "ic_95": "91 - 109", "classificacao": "Média"},
                    "Gc_LK": {"nome": "Conhecimento Lexical (Gc-LK)", "soma": 21, "escore": 103, "percentil": 58, "ic_95": "96 - 110", "classificacao": "Média"},
                    "Gc_K0": {"nome": "Informação Geral (Gc-K0)", "soma": 24, "escore": 114, "percentil": 82, "ic_95": "106 - 122", "classificacao": "Média Superior"},
                    "Gc_LTM": {"nome": "Memória de Longo Prazo (Gc-LTM)", "soma": 22, "escore": 116, "percentil": 86, "ic_95": "110 - 122", "classificacao": "Média Superior"},
                    "Gsm_WM": {"nome": "Memória de Curto Prazo (Gsm-WM)", "soma": 21, "escore": 103, "percentil": 58, "ic_95": "94 - 112", "classificacao": "Média"},
                },
            },
            interpretation_text="Interpretação e Observações Clínicas\n\nO WAIS-III indicou funcionamento intelectual global na faixa média. O CPI foi estimado em 135 (muito superior). Foram identificadas discrepâncias clinicamente relevantes entre índices, o que recomenda interpretação cautelosa do perfil global.",
            evaluation=SimpleNamespace(
                examiner=None,
                patient=SimpleNamespace(full_name="Camila Caires", sex="F", age=None, birth_date=date(1996, 5, 20), schooling="higher_incomplete"),
            ),
        )

    def test_build_context_uses_wais3_pdf_layout_data(self):
        context = WAIS3PdfService._build_context(self._application_fixture())

        self.assertEqual(context["application_code"], "AVL-077")
        self.assertEqual(context["patient_name"], "Camila Caires")
        self.assertEqual(context["patient_sex"], "Feminino")
        self.assertEqual(context["patient_schooling"], "Ensino superior incompleto")
        self.assertEqual(context["index_rows"][0]["abbreviation"], "QIV")
        self.assertEqual(context["index_rows"][2]["score"], "102")
        self.assertEqual(context["verbal_profile"][0]["abbreviation"], "V")
        self.assertAlmostEqual(context["execution_profile"][-1]["top"], 97.368421, places=4)
        self.assertEqual(context["discrepancy_rows"][1]["frequency"], "52,5")
        self.assertEqual(context["digit_rows"][2]["difference"], "2")

    def test_wais3_discrepancy_frequency_uses_b2_table_for_large_differences(self):
        application = self._application_fixture()
        application.classified_payload["indices"]["qi_verbal"]["pontuacao_composta"] = 148
        application.classified_payload["indices"]["qi_execucao"]["pontuacao_composta"] = 100

        context = WAIS3PdfService._build_context(application)

        self.assertEqual(context["discrepancy_rows"][0]["difference"], "48")
        self.assertEqual(context["discrepancy_rows"][0]["frequency"], "0,0")

    def test_render_template_replaces_wais3_model_data(self):
        template = WAIS3PdfService.TEMPLATE_PATH.read_text(encoding="utf-8")
        rendered = WAIS3PdfService._render_html(template, self._application_fixture())

        self.assertIn("Camila Caires", rendered)
        self.assertIn("Ensino superior incompleto", rendered)
        self.assertIn("WAIS-III / Brasil / 30 a 39 anos", rendered)
        self.assertIn("<tr><td>Soma dos escores ponderados</td><td>62</td><td>52</td><td>114</td>", rendered)
        self.assertIn('style="--score:48.18%"', rendered)
        self.assertIn("Análise de Clusters", rendered)
        self.assertIn("Comparações Clínicas", rendered)
        self.assertIn("Comparações entre as Discrepâncias", rendered)
        self.assertIn('<section class="page results-page">', rendered)
        self.assertIn(".results-page .wais-ruler { height: 102mm; }", rendered)
        self.assertIn(".cover .footer", rendered)
        self.assertIn("background: transparent;", rendered)
        self.assertIn("<tr><td>Compreensão Verbal - Organização Perceptual</td><td>ICV</td><td>IOP</td><td>6</td><td>Não</td><td>52,5</td></tr>", rendered)
        self.assertIn("Nível Subteste", rendered)
        self.assertIn('<section class="page clinical-page">', rendered)
        self.assertIn('<div class="footer-logo">Neuro<span>avalia</span></div>', rendered)
        self.assertIn('<div class="footer-right">Página 1 de ', rendered)
        self.assertIn("break-inside: avoid;", rendered)
        self.assertLess(rendered.index("Comparações entre as Discrepâncias"), rendered.index("Nível Subteste"))
        self.assertLess(rendered.index("Nível Subteste"), rendered.index("Análise de Clusters"))
        self.assertLess(rendered.index("Análise de Clusters"), rendered.index("Comparações Clínicas"))
        self.assertIn('<td>Raciocínio Fluido (RM + AF + AR)</td><td class="abbr">Gf</td><td>5</td><td class="not-interpretable">NÃO</td><td>—</td><td>—</td>', rendered)
        self.assertIn("Gc-VL x Gc-K0", rendered)
        self.assertIn('class="negative">-11</td><td>17</td><td>Não raro</td><td class="abbr">Gc-VL</td><td class="relation">&lt;</td><td class="abbr">Gc-K0</td>', rendered)
        self.assertIn("O WAIS-III indicou funcionamento intelectual global na faixa média.", rendered)
        self.assertNotIn("Interpretação e Observações Clínicas", rendered)
        self.assertNotIn("CPI", rendered)
        self.assertNotIn("O CPI foi estimado", rendered)
        self.assertNotIn("Nota interpretativa", rendered)
        self.assertNotIn("Nome do Avaliado", rendered)
        self.assertNotIn("Andre Alekhine", rendered)
        self.assertNotIn("QIV 110", rendered)

    def test_wais3_long_clinical_text_creates_pages_with_headers(self):
        application = self._application_fixture()
        application.interpretation_text = "\n\n".join(
            f"Parágrafo clínico {index}. " + "Este conteúdo simula uma interpretação clínica extensa com dados funcionais, observações e integração dos achados do WAIS-III. " * 5
            for index in range(1, 9)
        )
        template = WAIS3PdfService.TEMPLATE_PATH.read_text(encoding="utf-8")
        rendered = WAIS3PdfService._render_html(template, application)

        clinical_pages = re.findall(r'<section class="page clinical-page">.*?</section>', rendered, flags=re.S)

        self.assertGreater(len(clinical_pages), 1)
        self.assertTrue(all('<div class="report-header">' in page for page in clinical_pages))
        self.assertIn(f"Página {3 + len(clinical_pages)} de {3 + len(clinical_pages)}", clinical_pages[-1])

    def test_pdf_export_service_registers_wais3_exporter(self):
        self.assertIn("wais3", TestPdfExportService.EXPORTERS)

    def test_wais3_interpretation_follows_skill_structure(self):
        application = self._application_fixture()
        application.classified_payload["indices"]["compreensao_verbal"]["pontuacao_composta"] = 125
        application.classified_payload["indices"]["organizacao_perceptual"]["pontuacao_composta"] = 123
        application.classified_payload["indices"]["velocidade_processamento"]["pontuacao_composta"] = 105
        application.classified_payload["subtestes"]["codigos"]["escore_ponderado"] = 7
        application.classified_payload["subtestes"]["procurar_simbolos"]["escore_ponderado"] = 12
        application.classified_payload["discrepancias"] = [
            {
                "nivel": "0,05",
                "pares": [
                    {
                        "par": "Índice de Compreensão Verbal × Índice de Velocidade de Processamento",
                        "diferenca": 20,
                        "critico": 12.4,
                        "nivel": "0,05",
                    }
                ],
            }
        ]
        text = build_wais3_interpretation(application.classified_payload, "Camila Caires")

        self.assertIn("WAIS-III – Escala de Inteligência Wechsler para Adultos", text)
        self.assertIn("funcionamento intelectual global", text)
        self.assertIn("QI Verbal", text)
        self.assertIn("QI de Execução", text)
        self.assertIn("Índice de Compreensão Verbal", text)
        self.assertIn("Análise dos Resultados Psicométricos", text)
        self.assertIn("Subtestes com maior rendimento relativo", text)
        self.assertIn("A direção favorece Índice de Compreensão Verbal", text)
        self.assertNotIn("instrumento de aplicação individual destinado", text)
        self.assertIn("O contraste entre ICV e IVP indica", text)
        self.assertIn("organização perceptual, associado a velocidade de processamento inferior", text)
        self.assertIn("Códigos ficou abaixo de Procurar Símbolos", text)
        self.assertIn("Análise dos Clusters e Comparações Complementares", text)
        self.assertIn("recurso complementar à interpretação principal", text)
        self.assertIn("No perfil de Camila", text)
        self.assertIn("Raciocínio Fluido (Gf), com diferença interna de 5 pontos ponderados", text)
        self.assertIn("a leitura deve retornar aos subtestes", text)
        self.assertIn("Esses achados devem ser integrados ao padrão intraindividual", text)
        self.assertIn("O WAIS-III não deve ser utilizado isoladamente para fechamento diagnóstico", text)
        self.assertLess(len(text), 8000)
        self.assertNotIn("WISC-IV", text)
        self.assertNotIn("confirma diagnóstico", text)

    def test_wais3_interpretation_blocks_inconsistent_clusters(self):
        application = self._application_fixture()
        application.classified_payload["clusters"]["Gf_nonverbal"] = {
            "nome": "Raciocínio Fluido Não Verbal",
            "soma": 19,
            "escore": 20,
            "percentil": 42.0,
            "ic_95": "87-107",
            "classificacao": "Extremamente Baixo",
        }

        text = build_wais3_interpretation(application.classified_payload, "Camila Caires")

        self.assertIn("Clusters bloqueados por inconsistência psicométrica", text)
        self.assertIn("Raciocínio Fluido Não Verbal (Gf-nv)", text)
        self.assertIn("escore composto fora do intervalo de confiança", text)
        self.assertIn("percentil incompatível com o escore composto", text)
        self.assertNotIn("Gf-nv < Gv", text)

    def test_wais3_classifier_uses_only_gai_as_general_index(self):
        subtestes = {
            "vocabulario": {"escore_ponderado": 15},
            "semelhancas": {"escore_ponderado": 14},
            "informacao": {"escore_ponderado": 14},
            "completar_figuras": {"escore_ponderado": 14},
            "cubos": {"escore_ponderado": 14},
            "raciocinio_matricial": {"escore_ponderado": 15},
            "digitos": {"escore_ponderado": 12},
            "sequencia_numeros_letras": {"escore_ponderado": 14},
            "codigos": {"escore_ponderado": 11},
            "procurar_simbolos": {"escore_ponderado": 12},
        }
        indices = {
            "compreensao_verbal": {"pontuacao_composta": 125},
            "organizacao_perceptual": {"pontuacao_composta": 123},
        }

        classified = classify_wais3_payload({"indices": indices, "subtestes": subtestes})

        self.assertEqual(classified["gai_data"]["soma_ponderados"], 86)
        self.assertEqual(classified["gai_data"]["escore_composto"], 131)
        self.assertEqual(classified["gai_data"]["percentil"], 98.0)
        self.assertEqual(classified["gai_data"]["intervalo_confianca"], [125, 135])
        self.assertTrue(classified["gai_data"]["normativo"])
        self.assertIn("Apêndice C", classified["gai_data"]["fonte_normativa"])
        self.assertNotIn("cpi_data", classified)
        self.assertFalse(any("CPI" in warning for warning in classified.get("warnings", [])))


class WISC4SupplementalTablesTests(SimpleTestCase):
    TABLES_DIR = Path(__file__).resolve().parent / "wisc4" / "tabelas" / "tabelas-ncp"
    SUPPLEMENTAL_DIR = Path(__file__).resolve().parent / "wisc4" / "tabelas" / "tabelas-suplementares"

    def test_all_ncp_tables_include_supplemental_columns(self):
        expected_header = ["PP", "CB", "SM", "DG", "CN", "CD", "VC", "SNL", "RM", "CO", "PS", "CF", "CA", "IN", "AR", "RP"]
        paths = sorted(self.TABLES_DIR.glob("idade_*.csv"))

        self.assertEqual(len(paths), 33)
        for path in paths:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[0], expected_header, path.name)
            self.assertEqual([row[0] for row in rows[1:]], [str(index) for index in range(1, 20)], path.name)

    def test_supplemental_source_csvs_cover_all_ncp_age_ranges(self):
        ncp_names = {path.name for path in self.TABLES_DIR.glob("idade_*.csv")}
        supplemental_names = {path.name for path in self.SUPPLEMENTAL_DIR.glob("idade_*.csv")}

        self.assertEqual(supplemental_names, ncp_names)

    def test_merged_ncp_table_converts_supplemental_subtests(self):
        table = _carregar_tabela_ncp(10, 4)

        self.assertEqual(buscar_ponderado(table, "CF", 6), 2)
        self.assertEqual(buscar_ponderado(table, "CA", 69), 10)
        self.assertEqual(buscar_ponderado(table, "IN", 15), 10)
        self.assertEqual(buscar_ponderado(table, "AR", 10), 2)
        self.assertEqual(buscar_ponderado(table, "RP", 20), 19)

    def test_wisc4_module_computes_ar_as_supplemental_subtest(self):
        module = WISC4Module()
        context = TestContext(
            patient_name="Paciente WISC",
            evaluation_id=1,
            instrument_code="wisc4",
            raw_scores={"ar": 10},
            reviewed_scores={"birth_date": "2016-01-10", "evaluation_date": "2026-05-22"},
        )

        computed = module.compute(context)

        self.assertEqual(computed["ar"]["codigo"], "AR")
        self.assertEqual(computed["ar"]["escore_padrao"], 2)
        self.assertEqual(computed["ar"]["classificacao"], "Dificuldade Grave")

    def test_wisc4_module_computes_process_scores(self):
        module = WISC4Module()
        context = TestContext(
            patient_name="Paciente WISC",
            evaluation_id=1,
            instrument_code="wisc4",
            raw_scores={
                "cubos": 31,
                "cusb": 19,
                "diod": 8,
                "dioi": 6,
                "caa": 29,
                "cae": 33,
                "udiod": 5,
                "udioi": 3,
            },
            reviewed_scores={"birth_date": "2016-01-10", "evaluation_date": "2026-05-22"},
        )

        computed = module.compute(context)
        classified = module.classify(computed)
        process_scores = classified["process_scores"]

        scaled_by_code = {row["code"]: row for row in process_scores["scaled_rows"]}
        self.assertEqual(scaled_by_code["CUSB"]["scaled_score"], 8)
        self.assertEqual(scaled_by_code["DIOD"]["scaled_score"], 10)
        self.assertEqual(scaled_by_code["DIOI"]["scaled_score"], 9)
        self.assertEqual(scaled_by_code["CAA"]["scaled_score"], 9)
        self.assertEqual(scaled_by_code["CAE"]["scaled_score"], 9)
        self.assertEqual(process_scores["raw_discrepancy_rows"][0]["difference"], 2)
        self.assertEqual(len(process_scores["process_discrepancy_rows"]), 3)


class ETDAHPAISModuleTests(SimpleTestCase):
    def test_non_clinical_classifications_are_not_treated_as_deficit(self):
        module = ETDAHPAISModule()
        context = TestContext(
            patient_name="Debora Silva",
            evaluation_id=1,
            instrument_code="etdah_pais",
            raw_scores={
                "age": 10,
                "sex": "F",
                "responses": {},
            },
        )
        merged_data = {
            "raw_scores": {
                "fator_1": 40,
                "fator_2": 35,
                "fator_3": 45,
                "fator_4": 24,
                "escore_geral": 150,
            },
            "age": 10,
            "sex": "F",
        }

        interpretation = module.interpret(context, merged_data)

        self.assertIn("Fator 1 — Regulação Emocional", interpretation)
        self.assertIn("funcionamento dentro dos limites esperados", interpretation)
        self.assertEqual(interpretation.count("Em análise clínica"), 1)

    def test_focal_elevation_is_described_without_automatic_diagnostic_hypothesis(self):
        module = ETDAHPAISModule()
        context = TestContext(
            patient_name="Debora Silva",
            evaluation_id=1,
            instrument_code="etdah_pais",
            raw_scores={
                "age": 10,
                "sex": "F",
                "responses": {},
            },
        )
        merged_data = {
            "raw_scores": {
                "fator_1": 40,
                "fator_2": 70,
                "fator_3": 45,
                "fator_4": 45,
                "escore_geral": 150,
            },
            "age": 10,
            "sex": "F",
        }

        interpretation = module.interpret(context, merged_data)

        self.assertIn("Fator 2 — Hiperatividade/Impulsividade", interpretation)
        self.assertIn("Fator 4 — Atenção", interpretation)
        self.assertIn("sem configuração de comprometimento global amplo", interpretation)
        self.assertIn("Há hipótese diagnóstica de Transtorno do Déficit de Atenção e Hiperatividade, apresentação combinada", interpretation)


class ETDAHADModuleTests(SimpleTestCase):
    def test_factor_mapping_matches_official_order(self):
        raw_scores = calculate_raw_scores(
            {
                1: 4,
                2: 1,
                4: 1,
                5: 5,
                8: 5,
                9: 1,
                10: 5,
                14: 5,
                16: 5,
                27: 5,
                29: 5,
                42: 5,
                58: 5,
                59: 5,
                65: 5,
            }
        )

        self.assertEqual(raw_scores["I"], 1)
        self.assertEqual(raw_scores["AE"], 1)
        self.assertEqual(raw_scores["AAMA"], 1)
        self.assertEqual(raw_scores["H"], 1)

    def test_interpret_results_uses_remapped_means(self):
        results = interpret_etdah_ad_results(
            {"D": 64, "I": 20, "AE": 57, "AAMA": 6, "H": 25},
            "fundamental",
        )

        self.assertEqual(results["I"]["mean"], 14.35)
        self.assertEqual(results["AE"]["mean"], 44.3)
        self.assertEqual(results["AAMA"]["mean"], 5.77)
        self.assertEqual(results["H"]["mean"], 21.1)

    def test_non_clinical_classifications_are_not_treated_as_deficit(self):
        module = ETDAHADModule()
        context = TestContext(
            patient_name="Marina Costa",
            evaluation_id=1,
            instrument_code="etdah_ad",
            raw_scores={
                "schooling": "higher",
                "responses": {},
            },
        )
        merged_data = {
            "raw_scores": {
                "D": 30,
                "I": 30,
                "AE": 4,
                "AAMA": 18,
                "H": 10,
            },
            "schooling": "higher",
        }

        interpretation = module.interpret(context, merged_data)

        self.assertIn("Fator 1 — Desatenção", interpretation)
        self.assertIn("funcionamento dentro dos limites esperados", interpretation)
        self.assertEqual(interpretation.count("Em análise integrada"), 1)

    def test_elevated_domains_are_summarized_without_automatic_diagnostic_hypothesis(self):
        module = ETDAHADModule()
        context = TestContext(
            patient_name="Marina Costa",
            evaluation_id=1,
            instrument_code="etdah_ad",
            raw_scores={
                "schooling": "higher",
                "responses": {},
            },
        )
        merged_data = {
            "raw_scores": {
                "D": 60,
                "I": 55,
                "AE": 10,
                "AAMA": 6,
                "H": 25,
            },
            "schooling": "higher",
        }

        interpretation = module.interpret(context, merged_data)

        self.assertIn("Fator 1 — Desatenção", interpretation)
        self.assertIn("Fator 4 — Autorregulação da Atenção, Motivação e Ação", interpretation)
        self.assertIn("Em análise integrada", interpretation)
        self.assertIn("há hipótese diagnóstica de Transtorno do Déficit de Atenção e Hiperatividade (TDAH), apresentação combinada", interpretation)


class EBADEPAPdfServiceTests(SimpleTestCase):
    def _application_fixture(self):
        detail_items = [{"item": index, "resposta": index % 4} for index in range(1, 46)]
        return SimpleNamespace(
            id=63,
            evaluation_id=12,
            applied_on=date(2026, 5, 24),
            instrument=SimpleNamespace(code="ebadep_a", name="EBADEP-A"),
            raw_payload={f"item_{index:02d}": index % 4 for index in range(1, 46)},
            computed_payload={"escore_total": 82, "detalhe_itens": detail_items},
            classified_payload={
                "result": {"detalhe_itens": detail_items},
                "escore_total": 82,
                "percentil": 91,
                "classificacao": "Sintomatologia Depressiva Moderada",
                "sintese": "com indicadores moderados de sintomatologia depressiva",
                "items_criticos": [{"item": 3, "resposta": 3}, {"item": 7, "resposta": 3}],
            },
            interpretation_text="Interpretação clínica do EBADEP-A.",
            evaluation=SimpleNamespace(
                examiner=SimpleNamespace(full_name="Iris", crp="CRP: 1234"),
                patient=SimpleNamespace(
                    full_name="Avaliado Teste",
                    cpf="",
                    sex="F",
                    age=35,
                    birth_date=None,
                    schooling="higher_complete",
                    state="Paraná",
                    email="avaliado@email.com.br",
                ),
            ),
        )

    def test_build_context_uses_ebadep_a_pdf_layout_data(self):
        context = EBADEPAPdfService._build_context(self._application_fixture())

        self.assertEqual(context["application_code"], "AVL-063")
        self.assertEqual(context["report_code"], "RPT-EBADEPA-063")
        self.assertEqual(context["patient_name"], "Avaliado Teste")
        self.assertEqual(context["patient_sex"], "Feminino")
        self.assertEqual(context["patient_schooling"], "Ensino superior completo")
        self.assertEqual(context["classification_level"], "moderate")
        self.assertEqual(context["response_rows"][0]["cells"][0]["item"], "001")
        self.assertTrue(context["clinical_alert"])

    def test_render_template_uses_neuroavalia_wais3_layout(self):
        rendered = EBADEPAPdfService._render_html(self._application_fixture())

        self.assertIn('<section class="page cover">', rendered)
        self.assertIn("Neuro<span>avalia</span>", rendered)
        self.assertIn("EBADEP-A", rendered)
        self.assertIn("Relatório Técnico Completo", rendered)
        self.assertIn("Avaliado Teste", rendered)
        self.assertIn("Página 4 de 4", rendered)
        self.assertIn("Sintomatologia Depressiva Moderada", rendered)
        self.assertIn("Registro de respostas", rendered)
        self.assertNotIn("Nome do Avaliado", rendered)

    def test_pdf_export_service_registers_ebadep_a_exporter(self):
        self.assertIn("ebadep_a", TestPdfExportService.EXPORTERS)


class SRS2ModuleTests(SimpleTestCase):
    def test_female_school_age_norms_are_available(self):
        self.assertEqual(get_norm_data(17, "idade_escolar", "F", "percepção_social"), (78.0, 99.0))
        self.assertEqual(get_norm_data(54, "idade_escolar", "F", "cis"), (61.0, 87.0))
        self.assertEqual(get_norm_data(80, "idade_escolar", "F", "total"), (65.0, 93.0))

    def test_classify_uses_female_school_age_norms(self):
        module = SRS2Module()
        computed = {
            "form": "idade_escolar",
            "percepção_social": {"nome": "Percepção Social", "escore": 17, "max": 21},
            "cognição_social": {"nome": "Cognição Social", "escore": 26, "max": 24},
            "comunicação_social": {"nome": "Comunicação Social", "escore": 49, "max": 33},
            "motivação_social": {"nome": "Motivação Social", "escore": 28, "max": 33},
            "padrões_restritos": {"nome": "Padrões Restritos e Repetitivos", "escore": 31, "max": 24},
            "cis": {"nome": "Comunicação e Interação Social", "escore": 54, "max": 111},
            "total": {"nome": "Pontuação SRS-2 Total", "escore": 80, "max": 195},
        }

        classified = module.classify(computed, gender="F", age=10)

        self.assertEqual(classified["faixa_etária"], "6 a 18 anos")
        self.assertEqual(classified["resultados"][0]["tscore"], 78.0)
        self.assertEqual(classified["resultados"][0]["percentil"], 99.0)
        self.assertEqual(classified["resultados"][0]["classificação"], "Severo")

    def test_compute_keeps_demographics_for_classification(self):
        module = SRS2Module()
        context = TestContext(
            patient_name="Paciente SRS-2",
            evaluation_id=1,
            instrument_code="srs2",
            raw_scores={
                "form": "idade_escolar",
                "gender": "F",
                "age": 10,
                "responses": {str(item): 4 for item in range(1, 66)},
            },
        )

        computed = module.compute(context)
        classified = module.classify(computed)

        self.assertEqual(computed["gender"], "F")
        self.assertEqual(computed["age"], 10)
        self.assertEqual(classified["faixa_etária"], "6 a 18 anos")

    def test_report_payload_exposes_tscore_chart_data(self):
        module = SRS2Module()
        context = TestContext(
            patient_name="Paciente SRS-2",
            evaluation_id=1,
            instrument_code="srs2",
        )
        merged_data = {
            "resultados": [
                {"variável": "total", "nome": "Pontuação SRS-2 Total", "bruto": 80, "tscore": 65, "percentil": 93, "classificação": "Leve"},
            ]
        }

        payload = module.build_report_payload(context, merged_data)

        self.assertEqual(payload["results"][0]["t_score"], 65)
        self.assertEqual(payload["chart_payload"]["metric"], "tscore")
        self.assertIn("escore T total 65", payload["summary_for_report"])

    def test_interpretation_classifies_by_tscore_not_text_label(self):
        module = SRS2Module()
        rows = [
            {"variável": "percepcao_social", "nome": "Percepção Social", "bruto": 6, "tscore": 54, "classificação": "Moderado"},
            {"variável": "cognicao_social", "nome": "Cognição Social", "bruto": 12, "tscore": 62, "classificação": "Dentro dos limites normais"},
            {"variável": "comunicacao_social", "nome": "Comunicação Social", "bruto": 16, "tscore": 58, "classificação": "Dentro dos limites normais"},
            {"variável": "motivacao_social", "nome": "Motivação Social", "bruto": 10, "tscore": 55, "classificação": "Dentro dos limites normais"},
            {"variável": "padroes_restritos", "nome": "Padrões Restritos e Repetitivos", "bruto": 9, "tscore": 57, "classificação": "Dentro dos limites normais"},
            {"variável": "cis", "nome": "Comunicação e Interação Social", "bruto": 38, "tscore": 59, "classificação": "Dentro dos limites normais"},
            {"variável": "total", "nome": "Pontuação SRS-2 Total", "bruto": 47, "tscore": 58, "classificação": "Dentro dos limites normais"},
        ]

        interpretation = module.interpret(
            TestContext(patient_name="Paciente SRS-2", evaluation_id=1, instrument_code="srs2"),
            {"resultados": rows},
        )

        self.assertIn("O domínio de Percepção Social situou-se dentro dos limites normativos", interpretation)
        self.assertNotIn("O domínio de Percepção Social apresentou elevação", interpretation)
        self.assertIn("O domínio de Cognição Social apresentou elevação em nível leve", interpretation)
        self.assertIn("Domínios elevados: Cognição Social", interpretation)

    def test_interpretation_describes_combined_cis_and_repetitive_axes(self):
        module = SRS2Module()
        rows = [
            {"variável": "percepcao_social", "nome": "Percepção Social", "bruto": 10, "tscore": 58, "classificação": "Dentro dos limites normais"},
            {"variável": "cognicao_social", "nome": "Cognição Social", "bruto": 18, "tscore": 66, "classificação": "Moderado"},
            {"variável": "comunicacao_social", "nome": "Comunicação Social", "bruto": 33, "tscore": 70, "classificação": "Moderado"},
            {"variável": "motivacao_social", "nome": "Motivação Social", "bruto": 18, "tscore": 66, "classificação": "Moderado"},
            {"variável": "padroes_restritos", "nome": "Padrões Restritos e Repetitivos", "bruto": 18, "tscore": 68, "classificação": "Moderado"},
            {"variável": "cis", "nome": "Comunicação e Interação Social", "bruto": 69, "tscore": 68, "classificação": "Moderado"},
            {"variável": "total", "nome": "Pontuação SRS-2 Total", "bruto": 87, "tscore": 69, "classificação": "Moderado"},
        ]

        interpretation = module.interpret(
            TestContext(patient_name="Paciente SRS-2", evaluation_id=1, instrument_code="srs2"),
            {"resultados": rows},
        )

        self.assertIn("dois grandes eixos sintomatológicos", interpretation)
        self.assertIn("dois eixos centrais associados ao Transtorno do Espectro Autista", interpretation)
        self.assertIn("não confirma diagnóstico isoladamente", interpretation)
        self.assertNotIn("confirmou diagnóstico", interpretation)

    def test_interpretation_validator_blocks_normal_domain_as_altered(self):
        rows = [
            {"variável": "percepcao_social", "nome": "Percepção Social", "tscore": 54},
            {"variável": "total", "nome": "Pontuação SRS-2 Total", "tscore": 58},
        ]
        text = (
            "Em análise clínica, o SRS-2 foi usado como instrumento de rastreio. "
            "O domínio de Percepção Social apresentou elevação em nível leve."
        )

        errors = validate_srs2_interpretation(rows, text)

        self.assertTrue(any("Percepção Social" in error for error in errors))

    def test_pdf_export_service_registers_srs2_exporter(self):
        self.assertIn("srs2", TestPdfExportService.EXPORTERS)

    def test_srs2_pdf_replaces_model_readings_with_application_data(self):
        rows = [
            {"variável": "percepcao_social", "nome": "Percepção Social", "bruto": 12, "tscore": 62, "percentil": 88, "classificação": "Leve"},
            {"variável": "cognicao_social", "nome": "Cognição Social", "bruto": 15, "tscore": 64, "percentil": 92, "classificação": "Leve"},
            {"variável": "comunicacao_social", "nome": "Comunicação Social", "bruto": 33, "tscore": 70, "percentil": 97, "classificação": "Moderado"},
            {"variável": "motivacao_social", "nome": "Motivação Social", "bruto": 16, "tscore": 60, "percentil": 84, "classificação": "Leve"},
            {"variável": "padroes_restritos", "nome": "Padrões Restritos e Repetitivos", "bruto": 18, "tscore": 66, "percentil": 95, "classificação": "Moderado"},
            {"variável": "cis", "nome": "Comunicação e Interação Social", "bruto": 76, "tscore": 69, "percentil": 97, "classificação": "Moderado"},
            {"variável": "total", "nome": "Pontuação SRS-2 Total", "bruto": 94, "tscore": 68, "percentil": 96, "classificação": "Moderado"},
        ]
        application = SimpleNamespace(
            raw_payload={"form": "idade_escolar", "gender": "F", "responses": {str(item): 2 for item in range(1, 66)}},
            computed_payload={"form": "idade_escolar"},
            interpretation_text="Interpretação clínica real do protocolo.",
            applied_on=date(2026, 5, 24),
            evaluation=SimpleNamespace(
                patient=SimpleNamespace(full_name="Sophia Correa", age=11, sex="F", schooling="elementary")
            ),
        )

        template = SRS2PdfService.TEMPLATE_PATH.read_text(encoding="utf-8")
        rendered = SRS2PdfService._replace_dynamic_content(template, application, rows)

        self.assertIn('<section class="page">', template)
        self.assertIn('.page{width:var(--page-w);height:var(--page-h);', template)
        self.assertIn('<section class="page analysis-page">', rendered)
        self.assertIn('.analysis-page .clinical-box p{font-size:8.9pt;', rendered)
        self.assertIn('text-align:justify;text-justify:inter-word', rendered)
        self.assertIn("O Escore Total foi T=68, classificado em nível moderado", rendered)
        self.assertNotIn("Em Sophia Correa, o Escore Total foi", rendered)
        self.assertIn("<strong>Idade Escolar · Feminino</strong>", rendered)
        self.assertNotIn("Idade escolar (6-18 anos) · Escore T (50+10z)", rendered)
        self.assertIn("O resultado geral do SRS-2 apresenta elevação clinicamente relevante", rendered)
        self.assertIn("Comunicação Social", rendered)
        self.assertIn("depende da integração com outros dados clínicos", rendered)
        self.assertIn('aria-label="Radar clínico dos domínios"', rendered)
        self.assertIn('<section class="summary-cards">', rendered)
        self.assertIn('<div class="profile-head">', rendered)
        self.assertIn('<div class="axis-top"><span class="min">min</span>', rendered)
        self.assertIn('<div class="profile-label">Comunic. e Interação Social</div>', rendered)
        self.assertIn('<div class="summary-row"><span>Percepção Social</span><strong>T 62</strong></div>', rendered)
        self.assertIn('<div class="summary-row"><span>Comunicação Social</span><strong>T 70</strong></div>', rendered)
        self.assertNotIn('<div class="summary-row"><span>Percepção Social</span><strong>T 50</strong></div>', rendered)
        self.assertNotIn("Estatísticas das respostas", rendered)
        self.assertNotIn("Leitura das estatísticas das respostas", rendered)
        self.assertIn("Análise clínica", rendered)
        self.assertNotIn("Análise clínica integrada", rendered)
        self.assertNotIn("Modelo de texto automático para o NeuroAvalia", rendered)
        self.assertNotIn("permanecendo dentro dos limites normais", rendered)
        self.assertNotIn("não indica elevação global clinicamente significativa", rendered)
        self.assertNotIn("Herick", rendered)
        self.assertNotIn("T=54", rendered)
        self.assertNotIn("com T=61, classificado em nível leve", rendered)

    def test_srs2_pdf_uses_dynamic_normative_table_label(self):
        rows = [
            {"variável": "total", "nome": "Pontuação SRS-2 Total", "bruto": 80, "tscore": 65, "percentil": 93, "classificação": "Leve"},
        ]
        application = SimpleNamespace(
            raw_payload={"form": "idade_escolar", "gender": "M", "responses": {str(item): 2 for item in range(1, 66)}},
            computed_payload={"form": "idade_escolar"},
            interpretation_text="Interpretação clínica real do protocolo.",
            applied_on=date(2026, 5, 24),
            evaluation=SimpleNamespace(
                patient=SimpleNamespace(full_name="Paciente SRS-2", age=10, sex="M", schooling="elementary")
            ),
        )

        template = SRS2PdfService.TEMPLATE_PATH.read_text(encoding="utf-8")
        rendered = SRS2PdfService._replace_dynamic_content(template, application, rows)

        self.assertIn("<strong>Idade Escolar · Masculino</strong>", rendered)
        self.assertNotIn("<strong>Idade Escolar</strong>", rendered)

    def test_srs2_complete_pdf_template_uses_application_data(self):
        rows = [
            {"variável": "percepcao_social", "nome": "Percepção Social", "bruto": 12, "tscore": 62, "percentil": 88, "classificação": "Leve"},
            {"variável": "cognicao_social", "nome": "Cognição Social", "bruto": 15, "tscore": 64, "percentil": 92, "classificação": "Leve"},
            {"variável": "comunicacao_social", "nome": "Comunicação Social", "bruto": 33, "tscore": 70, "percentil": 97, "classificação": "Moderado"},
            {"variável": "motivacao_social", "nome": "Motivação Social", "bruto": 16, "tscore": 60, "percentil": 84, "classificação": "Leve"},
            {"variável": "padroes_restritos", "nome": "Padrões Restritos e Repetitivos", "bruto": 18, "tscore": 66, "percentil": 95, "classificação": "Moderado"},
            {"variável": "cis", "nome": "Comunicação e Interação Social", "bruto": 76, "tscore": 69, "percentil": 97, "classificação": "Moderado"},
            {"variável": "total", "nome": "Pontuação SRS-2 Total", "bruto": 94, "tscore": 68, "percentil": 96, "classificação": "Moderado"},
        ]
        application = SimpleNamespace(
            raw_payload={"form": "idade_escolar", "gender": "F", "respondent_name": "Mãe", "responses": {str(item): 2 for item in range(1, 66)}},
            computed_payload={"form": "idade_escolar"},
            interpretation_text="Interpretação clínica real do protocolo.",
            applied_on=date(2026, 5, 24),
            evaluation=SimpleNamespace(
                patient=SimpleNamespace(full_name="Sophia Correa", age=11, sex="F", schooling="elementary")
            ),
        )

        template = SRS2PdfService.COMPLETE_TEMPLATE_PATH.read_text(encoding="utf-8")
        rendered = SRS2PdfService._replace_complete_dynamic_content(template, application, rows)

        self.assertIn("Relatório Técnico Completo", rendered)
        self.assertIn("Sophia Correa", rendered)
        self.assertIn('<svg class="brand-logo" viewBox="0 0 760 210"', rendered)
        self.assertIn("<strong>Idade Escolar · Feminino</strong>", rendered)
        self.assertIn("<td>Comunicação Social</td>\n<td class=\"num\">33</td>\n<td class=\"num\">70</td>", rendered)
        self.assertIn("Interpretação clínica real do protocolo.", rendered)
        self.assertNotIn("Teste_01", rendered)
        self.assertIn("Estatísticas das respostas", rendered)
        self.assertIn("Distribuição das respostas", rendered)
        self.assertIn('<td class="bar-cell"><span style="--w:100%"></span></td>', rendered)
        self.assertIn("Não estão disponíveis informações extras para esta administração.", rendered)
        self.assertNotIn('<div class="stat">', rendered)

    @patch("apps.tests.services.pdf_export_service.SRS2PdfService.generate_pdf_bytes")
    def test_srs2_pdf_export_service_accepts_complete_report_type(self, mock_generate):
        mock_generate.return_value = b"%PDF-complete"
        application = SimpleNamespace(instrument=SimpleNamespace(code="srs2"))

        payload = TestPdfExportService.build_pdf_bytes(application, report_type="complete")

        self.assertEqual(payload, b"%PDF-complete")
        mock_generate.assert_called_once_with(application, report_type="complete")

    def test_srs2_pdf_handles_light_total_with_moderate_domain(self):
        rows = [
            {"variável": "percepcao_social", "nome": "Percepção Social", "bruto": 17, "tscore": 72, "percentil": 99, "classificação": "Moderado"},
            {"variável": "cognicao_social", "nome": "Cognição Social", "bruto": 16, "tscore": 62, "percentil": 88, "classificação": "Leve"},
            {"variável": "comunicacao_social", "nome": "Comunicação Social", "bruto": 32, "tscore": 63, "percentil": 90, "classificação": "Leve"},
            {"variável": "motivacao_social", "nome": "Motivação Social", "bruto": 18, "tscore": 65, "percentil": 93, "classificação": "Leve"},
            {"variável": "padroes_restritos", "nome": "Padrões Restritos e Repetitivos", "bruto": 17, "tscore": 63, "percentil": 90, "classificação": "Leve"},
            {"variável": "cis", "nome": "Comunicação e Interação Social", "bruto": 65, "tscore": 65, "percentil": 93, "classificação": "Leve"},
            {"variável": "total", "nome": "Pontuação SRS-2 Total", "bruto": 80, "tscore": 65, "percentil": 93, "classificação": "Leve"},
        ]
        module = SRS2Module()
        interpretation = module.interpret(TestContext(patient_name="Jacqueline", evaluation_id=1, instrument_code="srs2"), {"resultados": rows})
        application = SimpleNamespace(
            raw_payload={"form": "idade_escolar", "gender": "F", "responses": {str(item): 2 for item in range(1, 66)}},
            computed_payload={"form": "idade_escolar"},
            interpretation_text=interpretation,
            applied_on=date(2026, 5, 24),
            evaluation=SimpleNamespace(
                patient=SimpleNamespace(full_name="jacqueline Oliveira Caires", age=10, sex="F", schooling="elementary_complete")
            ),
        )

        template = SRS2PdfService.TEMPLATE_PATH.read_text(encoding="utf-8")
        rendered = SRS2PdfService._replace_dynamic_content(template, application, rows)

        self.assertIn("Jacqueline Oliveira Caires", rendered)
        self.assertNotIn("jacqueline Oliveira Caires", rendered)
        self.assertIn("elevação global em nível leve na responsividade social, com destaque para Percepção Social", interpretation)
        self.assertIn("Percepção Social, que apresentou elevação em nível moderado", interpretation)
        self.assertNotIn("Em contraste", interpretation)
        self.assertRegex(rendered, r"<span>Conclusão do teste</span>\s*<strong>Perfil global em nível leve</strong>")
        self.assertNotRegex(rendered, r"<span>Classificação global</span>\s*<strong>Dentro dos limites normais</strong>\s*<b>T=65</b>")
        self.assertIn('<div class="summary-row"><span>Percepção Social</span><strong>T 72</strong></div>', rendered)

    def test_srs2_radar_axis_labels_use_uniform_radius(self):
        rows = [
            {"variável": "percepcao_social", "nome": "Percepção Social", "tscore": 62},
            {"variável": "cognicao_social", "nome": "Cognição Social", "tscore": 64},
            {"variável": "comunicacao_social", "nome": "Comunicação Social", "tscore": 70},
            {"variável": "motivacao_social", "nome": "Motivação Social", "tscore": 60},
            {"variável": "padroes_restritos", "nome": "Padrões Restritos e Repetitivos", "tscore": 66},
        ]

        svg = SRS2PdfService._radar_svg(rows)

        def label_position(label: str) -> tuple[float, float]:
            match = re.search(
                rf'<text class="axis-label" text-anchor="[^"]+" x="([-0-9.]+)" y="([-0-9.]+)" dominant-baseline="middle">{re.escape(label)}</text>',
                svg,
            )
            self.assertIsNotNone(match)
            return float(match.group(1)), float(match.group(2))

        positions = [
            label_position("Percepção Social"),
            label_position("Cognição Social"),
            label_position("Comunicação Social"),
            label_position("Motivação Social"),
        ]
        restricted_lines = re.findall(
            r'<text class="axis-label" text-anchor="end" x="([-0-9.]+)" y="([-0-9.]+)" dominant-baseline="middle">(?:Padrões Restritos|e Repetitivos)</text>',
            svg,
        )
        self.assertEqual(len(restricted_lines), 2)
        restricted_x = float(restricted_lines[0][0])
        restricted_y = sum(float(line[1]) for line in restricted_lines) / 2
        positions.append((restricted_x, restricted_y))

        distances = [round(math.hypot(x - 205.0, y - 150.0), 1) for x, y in positions]
        self.assertEqual(distances, [140.0] * 5)


class SCAREDModuleTests(SimpleTestCase):
    def test_autorrelato_classification_uses_norms(self):
        module = SCAREDModule()
        context = TestContext(
            patient_name="Paciente SCARED",
            evaluation_id=1,
            instrument_code="scared",
            patient_age=10,
            raw_scores={
                "form": "child",
                "gender": "F",
                "age": 10,
                "responses": {str(i): 2 for i in range(1, 42)},
            },
        )

        self.assertEqual(module.validate(context), [])

        computed = module.compute(context)
        classified = module.classify(computed, idade=10)
        interpretation = module.interpret(context, classified)

        self.assertEqual(classified["form_type"], "child")
        self.assertEqual(classified["sexo"], "feminino")
        self.assertTrue(any(item.get("percentil") is not None for item in classified["analise_geral"]))
        self.assertIn("SCARED - Autorrelato", interpretation)

    def test_parent_classification_uses_cutoffs(self):
        module = SCAREDModule()
        context = TestContext(
            patient_name="Paciente SCARED",
            evaluation_id=1,
            instrument_code="scared",
            patient_age=10,
            raw_scores={
                "form": "parent",
                "gender": "M",
                "age": 10,
                "responses": {str(i): 2 for i in range(1, 42)},
            },
        )

        self.assertEqual(module.validate(context), [])

        computed = module.compute(context)
        classified = module.classify(computed, idade=10)
        interpretation = module.interpret(context, classified)

        self.assertEqual(classified["form_type"], "parent")
        self.assertTrue(all(item.get("nota_corte") is not None for item in classified["analise_geral"]))
        self.assertTrue(any(item.get("classificacao") == "Clínico" for item in classified["analise_geral"]))
        self.assertIn("SCARED - Pais/Cuidadores", interpretation)

    def test_validate_rejects_invalid_form(self):
        module = SCAREDModule()
        context = TestContext(
            patient_name="Paciente SCARED",
            evaluation_id=1,
            instrument_code="scared",
            patient_age=10,
            raw_scores={
                "form": "invalid",
                "responses": {str(i): 0 for i in range(1, 42)},
            },
        )

        errors = module.validate(context)
        self.assertIn("Formulário SCARED inválido.", errors)


class EPQJModuleTests(SimpleTestCase):
    def test_calculate_scores_accepts_saved_payload_keys(self):
        scores = calcular_escore(
            {
                "item_03": 1,
                "item_08": 1,
                "item_02": 1,
                "item_01": 1,
            }
        )

        self.assertEqual(scores["P"], 1)
        self.assertEqual(scores["E"], 1)
        self.assertEqual(scores["N"], 1)
        self.assertEqual(scores["S"], 1)

    def test_interpretation_mentions_desirability_when_sincerity_is_high(self):
        module = EPQJModule()
        context = TestContext(
            patient_name="Marina Costa",
            evaluation_id=1,
            instrument_code="epq_j",
        )

        interpretation = module.interpret(
            context,
            {
                "fatores": {
                    "P": {"escore": 2, "percentil": 40, "classificacao": "MEDIO"},
                    "E": {"escore": 10, "percentil": 50, "classificacao": "MEDIO"},
                    "N": {"escore": 8, "percentil": 50, "classificacao": "MEDIO"},
                    "S": {"escore": 16, "percentil": 99, "classificacao": "MUITO ALTO"},
                }
            },
        )

        self.assertIn("Sinceridade apresentou classificação muito alto (percentil 99)", interpretation)
        self.assertIn("desejabilidade social", interpretation)
        self.assertIn("não há elementos suficientes para sustentar hipótese diagnóstica específica", interpretation)

    def test_interpretation_builds_internalizing_profile(self):
        module = EPQJModule()
        context = TestContext(
            patient_name="Lucas Almeida",
            evaluation_id=1,
            instrument_code="epq_j",
        )

        interpretation = module.interpret(
            context,
            {
                "fatores": {
                    "P": {"escore": 1, "percentil": 20, "classificacao": "BAIXO"},
                    "E": {"escore": 6, "percentil": 10, "classificacao": "BAIXO"},
                    "N": {"escore": 16, "percentil": 90, "classificacao": "ALTO"},
                    "S": {"escore": 10, "percentil": 50, "classificacao": "MEDIO"},
                }
            },
        )

        self.assertIn("O escore alto em Neuroticismo (percentil 90)", interpretation)
        self.assertIn("funcionamento mais introspectivo", interpretation)
        self.assertIn("Em análise clínica, o perfil de Lucas no EPQ-J", interpretation)
        self.assertIn("há hipótese diagnóstica de vulnerabilidade emocional e sintomatologia ansiosa ou internalizante", interpretation)

    def test_interpretation_covers_all_required_sections(self):
        module = EPQJModule()
        context = TestContext(
            patient_name="Ana Silva",
            evaluation_id=1,
            instrument_code="epq_j",
        )

        interpretation = module.interpret(
            context,
            {
                "fatores": {
                    "P": {"escore": 0, "percentil": 5, "classificacao": "MUITO BAIXO"},
                    "E": {"escore": 12, "percentil": 90, "classificacao": "ALTO"},
                    "N": {"escore": 3, "percentil": 10, "classificacao": "BAIXO"},
                    "S": {"escore": 8, "percentil": 30, "classificacao": "MEDIO"},
                }
            },
        )

        self.assertIn("O resultado de Ana nesse fator", interpretation)
        self.assertIn("O fator Extroversão apresentou classificação alto (percentil 90)", interpretation)
        self.assertIn("O fator Sinceridade apresentou classificação médio (percentil 30)", interpretation)
        self.assertIn("Em análise clínica", interpretation)
        self.assertIn("Análise Clínica:", interpretation)


class BFPModuleTests(SimpleTestCase):
    @staticmethod
    def _responses(default: int = 4) -> dict[str, int]:
        return {str(item): default for item in range(1, 127)}

    def test_compute_scores_with_general_sample(self):
        module = BFPModule()
        context = TestContext(
            patient_name="Paciente BFP",
            evaluation_id=1,
            instrument_code="bfp",
            raw_scores={
                "sample": "geral",
                "responses": self._responses(4),
            },
        )

        computed = module.compute(context)

        self.assertEqual(computed["sample"], "geral")
        self.assertEqual(computed["factors"]["NN"]["name"], "Neuroticismo")
        self.assertEqual(computed["facets"]["A2"]["raw_score"], 4.0)
        self.assertEqual(computed["facets"]["N4"]["raw_score"], 4.0)

    def test_reversed_items_change_facet_average(self):
        module = BFPModule()
        responses = self._responses(4)
        responses["1"] = 1
        context = TestContext(
            patient_name="Paciente BFP",
            evaluation_id=1,
            instrument_code="bfp",
            raw_scores={
                "sample": "geral",
                "responses": responses,
            },
        )

        computed = module.compute(context)

        self.assertAlmostEqual(computed["facets"]["A2"]["raw_score"], 31 / 7, places=4)

    def test_normative_sample_changes_percentile(self):
        module = BFPModule()
        responses = self._responses(4)

        male = module.compute(
            TestContext(
                patient_name="Paciente BFP",
                evaluation_id=1,
                instrument_code="bfp",
                raw_scores={"sample": "masculino", "responses": responses},
            )
        )
        female = module.compute(
            TestContext(
                patient_name="Paciente BFP",
                evaluation_id=1,
                instrument_code="bfp",
                raw_scores={"sample": "feminino", "responses": responses},
            )
        )

        self.assertNotEqual(male["factors"]["SS"]["percentile"], female["factors"]["SS"]["percentile"])

    def test_interpretation_mentions_factor_and_facet(self):
        module = BFPModule()
        responses = self._responses(4)
        for item in [55, 60, 73, 75, 79, 82, 89, 110, 118]:
            responses[str(item)] = 7

        context = TestContext(
            patient_name="Marina Costa",
            evaluation_id=1,
            instrument_code="bfp",
            raw_scores={"sample": "geral", "responses": responses},
        )

        computed = module.compute(context)
        classified = module.classify(computed)
        interpretation = module.interpret(context, {**computed, **classified})

        self.assertIn("Bateria Fatorial de Personalidade (BFP)", interpretation)
        self.assertIn("O fator Neuroticismo", interpretation)
        self.assertIn("A faceta Vulnerabilidade", interpretation)
        self.assertIn("Em análise clínica", interpretation)
        self.assertIn("indicadores de tendências de personalidade", interpretation)
        self.assertIn("interpretation", classified)

    def test_bfp_uses_seven_band_classification_model(self):
        module = BFPModule()
        computed = module.compute(
            TestContext(
                patient_name="Paciente BFP",
                evaluation_id=1,
                instrument_code="bfp",
                raw_scores={"sample": "geral", "responses": self._responses(4)},
            )
        )

        self.assertIn(computed["factors"]["NN"]["classification"], {
            "Muito Baixo",
            "Baixo",
            "Média Inferior",
            "Média",
            "Média Superior",
            "Superior",
            "Muito Superior",
        })
        self.assertTrue(computed["factors"]["NN"]["classification_meaning"])

    def test_report_payload_orders_facets_and_factors(self):
        module = BFPModule()
        context = TestContext(
            patient_name="Paciente BFP",
            evaluation_id=1,
            instrument_code="bfp",
            raw_scores={"sample": "geral", "responses": self._responses(4)},
        )

        computed = module.compute(context)
        payload = module.build_report_payload(context, {**computed, **module.classify(computed)})

        codes = [item["code"] for item in payload["results"][:6]]
        self.assertEqual(codes, ["N1", "N2", "N3", "N4", "NN", "E1"])
        self.assertEqual(payload["chart_payload"]["norm_reference"], 50)

    def test_pdf_export_service_generates_bfp_pdf(self):
        module = BFPModule()
        context = TestContext(
            patient_name="Paciente BFP",
            evaluation_id=1,
            instrument_code="bfp",
            raw_scores={"sample": "feminino", "responses": self._responses(4)},
        )
        computed = module.compute(context)
        application = SimpleNamespace(
            instrument=SimpleNamespace(code="bfp", name="BFP"),
            evaluation=SimpleNamespace(
                patient=SimpleNamespace(full_name="Paciente BFP", sex="F", schooling="middle_complete")
            ),
            evaluation_id=1,
            raw_payload={"sample": "feminino", "responses": self._responses(4)},
            computed_payload=computed,
            interpretation_text=module.interpret(context, {**computed, **module.classify(computed)}),
            applied_on=date(2026, 5, 17),
            updated_at=date(2026, 5, 18),
        )

        payload = TestPdfExportService.build_pdf_bytes(application)

        self.assertTrue(payload.startswith(b"%PDF"))


class WASIModuleTests(SimpleTestCase):
    def test_compute_matches_excel_sample_for_adult_band(self):
        module = WASIModule()
        context = TestContext(
            patient_name="Paciente WASI",
            evaluation_id=1,
            instrument_code="wasi",
            raw_scores={
                "vc": 50,
                "cb": 50,
                "sm": 22,
                "rm": 36,
                "birth_date": "1940-01-01",
                "applied_on": "2026-04-30",
                "confidence_level": "95",
            },
        )

        computed = module.compute(context)

        self.assertEqual(computed["subtests"]["vc"]["t_score"], 54)
        self.assertEqual(computed["subtests"]["vc"]["weighted_score"], 11)
        self.assertEqual(computed["subtests"]["cb"]["t_score"], 79)
        self.assertEqual(computed["subtests"]["cb"]["weighted_score"], 19)
        self.assertEqual(computed["subtests"]["sm"]["t_score"], 44)
        self.assertEqual(computed["subtests"]["rm"]["t_score"], 70)
        self.assertEqual(computed["composites"]["qi_verbal"]["qi"], 98)
        self.assertEqual(computed["composites"]["qi_execucao"]["qi"], 144)
        self.assertEqual(computed["composites"]["qit_4"]["qi"], 122)
        self.assertEqual(computed["composites"]["qit_2"]["qi"], 122)

    def test_interpretability_flags_follow_excel_rules(self):
        module = WASIModule()
        computed = module.compute(
            TestContext(
                patient_name="Paciente WASI",
                evaluation_id=1,
                instrument_code="wasi",
                raw_scores={
                    "vc": 50,
                    "cb": 50,
                    "sm": 22,
                    "rm": 36,
                    "birth_date": "1940-01-01",
                    "applied_on": "2026-04-30",
                    "confidence_level": "95",
                },
            )
        )

        self.assertTrue(computed["composites"]["qi_verbal"]["interpretability"]["ok"])
        self.assertTrue(computed["composites"]["qi_execucao"]["interpretability"]["ok"])
        self.assertFalse(computed["composites"]["qit_4"]["interpretability"]["ok"])
        self.assertFalse(computed["composites"]["qit_2"]["interpretability"]["ok"])

    def test_interpretation_mentions_core_indices(self):
        module = WASIModule()
        context = TestContext(
            patient_name="Marina Souza",
            evaluation_id=1,
            instrument_code="wasi",
            raw_scores={
                "vc": 50,
                "cb": 50,
                "sm": 22,
                "rm": 36,
                "birth_date": "1940-01-01",
                "applied_on": "2026-04-30",
                "confidence_level": "95",
            },
        )
        computed = module.compute(context)
        interpretation = module.interpret(context, {**computed, **module.classify(computed)})

        self.assertIn("WASI", interpretation)
        self.assertIn("QI Verbal", interpretation)
        self.assertIn("QI Execucao", interpretation)
