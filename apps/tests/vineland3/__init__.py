from apps.tests.base.types import BaseTestModule
from apps.tests.registry import register_test_module

from .calculators import compute_scores
from .config import CODE, NAME
from .interpreters import interpret_results
from .validators import validate_input


class Vineland3Module(BaseTestModule):
    code = CODE
    name = NAME

    def validate(self, context):
        return validate_input(context.raw_scores)

    def compute(self, context):
        return compute_scores(context.raw_scores)

    def classify(self, computed_data):
        # The supplied appendices contain score tables, not qualitative cutoffs.
        return {"classification_status": "pending_manual_verification"}

    def interpret(self, context, merged_data):
        return interpret_results(merged_data)

    def build_report_payload(self, context, merged_data):
        return {
            "results": merged_data.get("results", []),
            "summary_for_report": interpret_results(merged_data),
            "technical_notes": merged_data.get("technical_notes", []),
            "clinical_flags": [],
            "chart_payload": {
                "metric": "standard_score", "min": 20, "max": 140,
                "series": [{"code": row["scale"], "label": row["label"], "value": row["standard_score"]}
                           for row in merged_data.get("domains", [])],
            },
        }


register_test_module(CODE, Vineland3Module())
