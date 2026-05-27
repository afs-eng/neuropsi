from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module
from .config import ETDAHPAIS_CODE, ETDAHPAIS_NAME
from .schemas import ETDAHPAISInput, ETDAHPAISResponse
from .validators import validate_etdah_pais_input, validate_responses
from .calculators import calculate_raw_scores
from .interpreters import interpret_results, generate_report


class ETDAHPAISModule(BaseTestModule):
    code = ETDAHPAIS_CODE
    name = ETDAHPAIS_NAME

    def validate(self, context: TestContext) -> list[str]:
        errors = []

        errors.extend(validate_etdah_pais_input(context.raw_scores))

        responses = context.raw_scores.get("responses", {})
        errors.extend(validate_responses(responses))

        return errors

    def compute(self, context: TestContext) -> dict:
        responses = context.raw_scores.get("responses", {})
        raw_scores = calculate_raw_scores(responses)
        age = context.raw_scores.get("age", 10)
        sex = context.raw_scores.get("sex", "M")

        return {
            "raw_scores": raw_scores,
            "age": age,
            "sex": sex,
            "responses": responses,
        }

    def classify(self, computed_data: dict, faixa: str = "") -> dict:
        raw_scores = computed_data.get("raw_scores", {})
        age = computed_data.get("age", 10)
        sex = computed_data.get("sex", "M")

        results = interpret_results(raw_scores, age, sex)

        return {
            "raw_scores": raw_scores,
            "results": results,
            "age": age,
            "sex": sex,
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        raw_scores = merged_data.get("raw_scores", {})
        age = merged_data.get("age", context.raw_scores.get("age", 10))
        sex = merged_data.get("sex", context.raw_scores.get("sex", "M"))

        return generate_report(raw_scores, age, sex, patient_name=context.patient_name)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        results = merged_data.get("results") or {}
        interpretation = self.interpret(context, merged_data)
        return {
            "results": [
                {
                    "scale": value.get("label") or key,
                    "raw_score": value.get("raw_score") or value.get("score"),
                    "percentile": value.get("percentile") or value.get("percentile_guilmette"),
                    "classification": value.get("classification"),
                }
                for key, value in results.items()
                if isinstance(value, dict)
            ],
            "summary_for_report": interpretation.split(". ")[0].strip() if interpretation else "",
            "technical_notes": [f"Norma: {merged_data.get('age', 10)} anos / sexo {merged_data.get('sex', 'M')}"],
            "clinical_flags": [value.get("label") or key for key, value in results.items() if isinstance(value, dict) and value.get("classification") in {"Superior", "Média Superior"}],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(ETDAHPAIS_CODE, ETDAHPAISModule())
