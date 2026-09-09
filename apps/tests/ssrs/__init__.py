from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module

from .calculators import compute_ssrs_importance, compute_ssrs_scores
from .classifiers import classify_ssrs_scores
from .config import SSRS_CODE, SSRS_NAME
from .interpreters import interpret_ssrs_results
from .validators import validate_ssrs_input


class SSRSModule(BaseTestModule):
    code = SSRS_CODE
    name = SSRS_NAME

    def validate(self, context: TestContext) -> list[str]:
        raw_scores = context.raw_scores or {}
        return validate_ssrs_input(
            raw_scores.get("responses", {}),
            raw_scores.get("informant", "crianca"),
            raw_scores.get("importance"),
        )

    def compute(self, context: TestContext) -> dict:
        raw_scores = context.raw_scores or {}
        computed = compute_ssrs_scores(raw_scores.get("responses", {}), raw_scores.get("informant", "crianca"))
        if raw_scores.get("importance"):
            computed["importance"] = compute_ssrs_importance(raw_scores.get("importance", {}), computed["informant"])
        computed["gender"] = raw_scores.get("gender", "F")
        return computed

    def classify(self, computed_data: dict, **kwargs) -> dict:
        return classify_ssrs_scores(computed_data, gender=kwargs.get("gender") or computed_data.get("gender") or "F")

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        return interpret_ssrs_results(merged_data)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        rows = merged_data.get("resultados") or []
        return {
            "results": rows,
            "summary_for_report": self.interpret(context, merged_data),
            "technical_notes": ["Normas conferidas nas tabelas 4 a 9 do arquivo SSRS_tabelas_1_a_12_organizadas.xlsx."],
            "clinical_flags": [
                row.get("name")
                for row in rows
                if row.get("domain") == "behavior_problems" and (row.get("percentile") or 0) >= 66
            ],
            "chart_payload": {
                "metric": "percentile",
                "series": [
                    {"code": row.get("scale"), "label": row.get("name"), "value": row.get("percentile")}
                    for row in rows
                    if row.get("scale") == "eg"
                ],
            },
            "interpretation": self.interpret(context, merged_data),
        }


register_test_module(SSRS_CODE, SSRSModule())
