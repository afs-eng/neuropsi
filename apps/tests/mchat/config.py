from apps.tests.base.types import BaseTestModule, TestContext

from .calculators import build_computed_payload
from .classifiers import classify_mchat
from .interpreters import build_mchat_interpretation
from .validators import validate_mchat_payload


class MCHATModule(BaseTestModule):
    code = "MCHAT"
    name = "M-CHAT"

    def validate(self, context: TestContext) -> list[str]:
        try:
            validate_mchat_payload(context.raw_scores)
            return []
        except Exception as exc:
            return [f"Erro na validacao: {exc}"]

    def compute(self, context: TestContext) -> dict:
        return build_computed_payload(context.raw_scores)

    def classify(self, computed_data: dict) -> dict:
        return classify_mchat(computed_data)

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        return build_mchat_interpretation(merged_data, merged_data)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        item_results = merged_data.get("item_results") or {}
        interpretation = self.interpret(context, merged_data)
        total_failures = merged_data.get("total_failures")
        critical_failures = merged_data.get("critical_failures")
        screen_result = merged_data.get("screen_result") or merged_data.get("classification") or "não classificado"
        return {
            "results": [
                {
                    "scale": value.get("item_label") or f"Item {value.get('item_number')}",
                    "raw_score": None,
                    "percentile": None,
                    "classification": value.get("result"),
                }
                for value in item_results.values()
                if isinstance(value, dict)
            ],
            "summary_for_report": f"Triagem M-CHAT com {total_failures or 0} falhas totais, {critical_failures or 0} falhas críticas e resultado {str(screen_result).lower()}.",
            "technical_notes": [],
            "clinical_flags": [f"item_{item}" for item in merged_data.get("failed_critical_items") or []],
            "chart_payload": {},
            "interpretation": interpretation,
        }
