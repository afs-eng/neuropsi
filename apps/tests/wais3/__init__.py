from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module

from .calculators import compute_wais3_payload
from .classifiers import classify_wais3_payload
from .config import WAIS3_CODE, WAIS3_NAME
from .interpreters import build_wais3_interpretation
from .schemas import WAIS3RawInput
from .validators import validate_wais3_input


class WAIS3Module(BaseTestModule):
    code = WAIS3_CODE
    name = WAIS3_NAME

    def validate(self, context: TestContext) -> list[str]:
        try:
            data = WAIS3RawInput(**(context.raw_scores or {}))
        except Exception as exc:
            return [f"Erro na validação: {exc}"]
        return validate_wais3_input(data)

    def compute(self, context: TestContext) -> dict:
        return compute_wais3_payload(context.raw_scores or {})

    def classify(self, computed_data: dict) -> dict:
        return classify_wais3_payload(computed_data)

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        return build_wais3_interpretation(merged_data or {}, context.patient_name)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        interpretation = self.interpret(context, merged_data)
        indices = merged_data.get("indices") or {}
        subtestes = merged_data.get("subtestes") or {}
        results = [
            {
                "scale": item.get("nome") or key,
                "raw_score": item.get("pontuacao_composta"),
                "percentile": item.get("percentil"),
                "classification": item.get("classificacao"),
            }
            for key, item in indices.items()
        ]
        results.extend(
            {
                "scale": item.get("nome") or key,
                "raw_score": item.get("escore_ponderado") or item.get("pontos_brutos"),
                "percentile": None,
                "classification": item.get("classificacao"),
            }
            for key, item in subtestes.items()
        )
        qit = (indices.get("qi_total") or {}).get("pontuacao_composta")
        qit_class = (indices.get("qi_total") or {}).get("classificacao")
        summary = (
            f"Funcionamento intelectual global com QI total {qit or '-'}, "
            f"classificado como {str(qit_class or 'não classificado').lower()}."
        )
        return {
            "results": results,
            "summary_for_report": summary,
            "technical_notes": list(merged_data.get("warnings") or []),
            "clinical_flags": [],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(WAIS3_CODE, WAIS3Module())
