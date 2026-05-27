from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module
from .calculators import compute_scared_scores
from .classifiers import classify_scared_scores
from .config import SCARED_CODE, SCARED_NAME
from .interpreters import interpret_scared_results
from .validators import validate_scared_input


class SCAREDModule(BaseTestModule):
    code = SCARED_CODE
    name = SCARED_NAME

    def validate(self, context: TestContext) -> list[str]:
        return validate_scared_input(context.raw_scores)

    def compute(self, context: TestContext) -> dict:
        return compute_scared_scores(context.raw_scores, patient_age=context.patient_age)

    def classify(self, computed_data: dict, idade: int = 0) -> dict:
        return classify_scared_scores(computed_data, idade=idade)

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        return interpret_scared_results(merged_data, context.patient_name)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        factors = merged_data.get("factor_results") or merged_data.get("results") or {}
        interpretation = self.interpret(context, merged_data)
        results = []
        if isinstance(factors, dict):
            for key, item in factors.items():
                if not isinstance(item, dict):
                    continue
                results.append(
                    {
                        "scale": item.get("label") or key,
                        "raw_score": item.get("raw_score") or item.get("score"),
                        "percentile": item.get("percentile"),
                        "classification": item.get("classification") or item.get("classificacao"),
                    }
                )
        return {
            "results": results,
            "summary_for_report": interpretation.split(". ")[0].strip() if interpretation else "",
            "technical_notes": [],
            "clinical_flags": [item.get("scale") for item in results if item.get("classification") in {"Elevado", "Muito Elevado", "Clinicamente significativo"}],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(SCARED_CODE, SCAREDModule())
