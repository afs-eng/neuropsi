from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module

from .calculators import compute_wasi_payload
from .config import WASI_CODE, WASI_NAME
from .interpreters import build_wasi_interpretation
from .schemas import WASIRawInput
from .validators import validate_wasi_input


class WASIModule(BaseTestModule):
    code = WASI_CODE
    name = WASI_NAME

    def validate(self, context: TestContext) -> list[str]:
        try:
            data = WASIRawInput(**(context.raw_scores or {}))
        except Exception as exc:
            return [f"Erro na validação: {exc}"]
        return validate_wasi_input(data)

    def compute(self, context: TestContext) -> dict:
        return compute_wasi_payload(context.raw_scores or {})

    def classify(self, computed_data: dict, **kwargs) -> dict:
        composites = computed_data.get("composites", {})
        return {
            "summary": {
                key: {
                    "qi": value.get("qi"),
                    "classification": value.get("classification"),
                    "interpretability": value.get("interpretability", {}),
                }
                for key, value in composites.items()
            }
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        return build_wasi_interpretation(merged_data, patient_name=context.patient_name)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        composites = merged_data.get("composites") or {}
        subtests = merged_data.get("subtests") or {}
        interpretation = self.interpret(context, merged_data)
        results = [
            {
                "scale": item.get("name") or key,
                "raw_score": item.get("qi"),
                "percentile": item.get("percentile_display") or item.get("percentile"),
                "classification": item.get("classification"),
            }
            for key, item in composites.items()
        ]
        results.extend(
            {
                "scale": item.get("name") or key,
                "raw_score": item.get("weighted_score") or item.get("raw_score"),
                "percentile": item.get("percentile"),
                "classification": item.get("classification"),
            }
            for key, item in subtests.items()
        )
        qit4 = composites.get("qit_4", {})
        summary = (
            f"Funcionamento intelectual global {str(qit4.get('classification') or 'não classificado').lower()}, "
            f"com QIT-4 {qit4.get('qi', '-')} e integração entre recursos verbais e de execução."
        )
        return {
            "results": results,
            "summary_for_report": summary,
            "technical_notes": [
                item.get("interpretability", {}).get("warning", "")
                for item in composites.values()
                if item.get("interpretability", {}).get("warning")
            ],
            "clinical_flags": [],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(WASI_CODE, WASIModule())
