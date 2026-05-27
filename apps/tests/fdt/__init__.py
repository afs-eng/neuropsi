from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module

from .calculators import calculate_fdt_results, calculate_stage_totals
from .config import FDT_CODE, FDT_NAME
from .interpreters import interpret_fdt_result
from .schemas import FDTRawInput
from .validators import validate_fdt_input


class FDTModule(BaseTestModule):
    code = FDT_CODE
    name = FDT_NAME

    def validate(self, context: TestContext) -> list[str]:
        try:
            data = FDTRawInput(**context.raw_scores)
            age = context.reviewed_scores.get("age")
            return validate_fdt_input(data, age=age)
        except Exception as e:
            return [f"Erro na validacao: {e}"]

    def compute(self, context: TestContext) -> dict:
        data = FDTRawInput(**context.raw_scores)
        age = context.reviewed_scores.get("age")
        stage_totals = calculate_stage_totals(data.model_dump())
        return calculate_fdt_results(stage_totals, age)

    def classify(self, computed_data: dict) -> dict:
        return computed_data

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        return interpret_fdt_result(merged_data, patient_name=context.patient_name)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        metric_results = merged_data.get("metric_results") or []
        derived = merged_data.get("derived_scores") or {}
        interpretation = self.interpret(context, merged_data)
        return {
            "results": [
                {
                    "scale": item.get("nome") or item.get("codigo"),
                    "raw_score": item.get("valor"),
                    "percentile": item.get("percentil_num"),
                    "classification": item.get("classificacao"),
                }
                for item in metric_results
            ],
            "summary_for_report": interpretation.split(". ")[0].strip() if interpretation else "",
            "technical_notes": [
                f"Inibição: {derived.get('inibicao')}" if derived.get("inibicao") is not None else "",
                f"Flexibilidade: {derived.get('flexibilidade')}" if derived.get("flexibilidade") is not None else "",
            ],
            "clinical_flags": [
                item.get("nome") or item.get("codigo")
                for item in metric_results
                if item.get("classificacao") in {"Inferior", "Muito Inferior", "Deficitario"}
            ],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(FDT_CODE, FDTModule())
