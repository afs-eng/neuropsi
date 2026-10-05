from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module

from .calculators import compute_thcp_scores
from .classifiers import classify_thcp_scores
from .config import TECHNICAL_NOTES, THCP_CODE, THCP_NAME
from .interpreters import interpret_thcp_results
from .validators import validate_thcp_input


class THCPModule(BaseTestModule):
    code = THCP_CODE
    name = THCP_NAME

    def validate(self, context: TestContext) -> list[str]:
        return validate_thcp_input(context)

    def compute(self, context: TestContext) -> dict:
        return compute_thcp_scores(context.raw_scores, context.patient_age)

    def classify(self, computed_data: dict) -> dict:
        return classify_thcp_scores(computed_data)

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        return interpret_thcp_results(merged_data, context.patient_name)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        results = merged_data.get("results", [])
        interpretation = self.interpret(context, merged_data)
        return {
            "results": [{**row, "scale": row["label"]} for row in results],
            "summary_for_report": interpretation.split("\n\n")[0],
            "interpretation": interpretation,
            "technical_notes": [*TECHNICAL_NOTES, *merged_data.get("warnings", [])],
            "clinical_flags": [row["label"] for row in results if row.get("classification") in {"Limítrofe", "Deficitário"}],
            "chart_payload": {
                "labels": [row["label"] for row in results],
                "percentiles": [row.get("percentile") for row in results],
                "metric": "Percentil estimado pela distribuição normal",
            },
        }


register_test_module(THCP_CODE, THCPModule())
