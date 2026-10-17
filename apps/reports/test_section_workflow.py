from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from apps.common import test_clinical_access
from apps.reports.services.report_pipeline_service import ReportPipelineService
from apps.reports.services.section_workflow_service import SectionWorkflowService


class SectionDependencyTests(SimpleTestCase):
    def test_dependencies_are_generated_before_domains(self):
        context = {"validated_tests": [{"instrument_code": code} for code in ["wisc4", "fdt", "ravlt"]]}
        order = SectionWorkflowService.get_generation_order(context)
        self.assertLess(order.index("fdt"), order.index("funcoes_executivas"))
        self.assertLess(order.index("ravlt"), order.index("memoria_aprendizagem"))

    def test_absent_tests_do_not_block_wisc_domains(self):
        order = SectionWorkflowService.get_generation_order({"validated_tests": [{"instrument_code": "wisc4"}]})
        self.assertNotIn("fdt", order)
        self.assertNotIn("ravlt", order)
        self.assertIn("funcoes_executivas", order)
        self.assertIn("memoria_aprendizagem", order)
        self.assertTrue(SectionWorkflowService.can_generate("funcoes_executivas", set(), set(order)))

    def test_failed_present_dependency_still_blocks_its_domain(self):
        self.assertFalse(SectionWorkflowService.can_generate("funcoes_executivas", set(), {"fdt", "funcoes_executivas"}))

    def test_cycles_fail_explicitly(self):
        with patch.object(SectionWorkflowService, "get_dependencies", side_effect=lambda key: ["b" if key == "a" else "a"]):
            with self.assertRaisesMessage(ValueError, "ciclo"):
                SectionWorkflowService.order_sections(["a", "b"])


class SectionPresentationTests(TestCase):
    setUp = test_clinical_access.ClinicalAccessTests.setUp

    def test_dependency_execution_does_not_reorder_the_report_chapters(self):
        context = {"validated_tests": [{"instrument_code": code} for code in ["wisc4", "fdt", "ravlt"]]}
        order = SectionWorkflowService.get_generation_order(context)
        with patch.object(ReportPipelineService, "_generate_single_section", return_value={"content": "Texto", "warnings": [], "metadata": {}}):
            result = ReportPipelineService.generate_sections(self.report, context, order)
        self.assertEqual(result["failed_sections"], [])
        self.assertLess(result["generated_sections"].index("fdt"), result["generated_sections"].index("funcoes_executivas"))
        sections = list(self.report.sections.values_list("key", flat=True))
        self.assertLess(sections.index("funcoes_executivas"), sections.index("fdt"))
        self.assertLess(sections.index("memoria_aprendizagem"), sections.index("ravlt"))
