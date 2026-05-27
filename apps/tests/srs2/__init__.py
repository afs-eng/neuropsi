from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module
from .calculators import compute_srs2_scores
from .classifiers import classify_srs2_scores
from .config import SRS2_CODE, SRS2_NAME
from .interpreters import interpret_srs2_results
from .validators import validate_srs2_input


class SRS2Module(BaseTestModule):
    code = SRS2_CODE
    name = SRS2_NAME

    def validate(self, context: TestContext) -> list[str]:
        responses = context.raw_scores.get("responses", {})
        errors = validate_srs2_input(responses, expected_count=65)
        if not responses:
            return ["Nenhuma resposta recebida"]
        return errors

    def compute(self, context: TestContext) -> dict:
        raw_responses = context.raw_scores.get("responses", {})
        form = context.raw_scores.get("form", "idade_escolar")
        computed = compute_srs2_scores(raw_responses, form)
        computed["gender"] = context.raw_scores.get("gender", "M")
        computed["age"] = context.raw_scores.get("age") or context.patient_age or 10
        return computed

    def classify(self, computed_data: dict, **kwargs) -> dict:
        gender = kwargs.get("gender") or computed_data.get("gender") or "M"
        age = kwargs.get("age") or computed_data.get("age") or 10
        return classify_srs2_scores(computed_data, gender=gender, age=age)

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        return interpret_srs2_results(merged_data)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        resultados = merged_data.get("resultados") or []
        interpretation = self.interpret(context, merged_data)
        total = next((item for item in resultados if item.get("variável") == "total"), {})
        return {
            "results": [
                {
                    "code": item.get("variável"),
                    "scale": item.get("variável"),
                    "name": item.get("nome"),
                    "raw_score": item.get("bruto"),
                    "t_score": item.get("tscore"),
                    "percentile": item.get("percentil"),
                    "classification": item.get("classificação"),
                }
                for item in resultados
            ],
            "summary_for_report": (
                f"Responsividade social com classificação global {str(total.get('classificação') or 'não classificada').lower()}, "
                f"a partir do escore T total {total.get('tscore') or '-'}."
            ),
            "technical_notes": [],
            "clinical_flags": [item.get("variável") for item in resultados if item.get("classificação") in {"Moderado", "Severo"}],
            "chart_payload": {
                "metric": "tscore",
                "norm_reference": 50,
                "cutoffs": {"normal_max": 59, "leve_max": 65, "moderado_max": 75},
                "series": [
                    {
                        "code": item.get("variável"),
                        "label": item.get("nome"),
                        "value": item.get("tscore"),
                    }
                    for item in resultados
                ],
            },
            "interpretation": interpretation,
        }


register_test_module(SRS2_CODE, SRS2Module())
