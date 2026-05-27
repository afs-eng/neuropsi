from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module
from .config import ETDAHAD_CODE, ETDAHAD_NAME
from .schemas import ETDAHADInput, ETDAHADResponse
from .validators import validate_etdah_ad_input, validate_responses
from .calculators import calculate_raw_scores
from .interpreters import interpret_results, generate_report


class ETDAHADModule(BaseTestModule):
    code = ETDAHAD_CODE
    name = ETDAHAD_NAME

    def validate(self, context: TestContext) -> list[str]:
        errors = []

        errors.extend(validate_etdah_ad_input(context.raw_scores))

        responses = context.raw_scores.get("responses", {})
        errors.extend(validate_responses(responses))

        return errors

    def compute(self, context: TestContext) -> dict:
        responses = context.raw_scores.get("responses", {})
        raw_scores = calculate_raw_scores(responses)
        schooling = context.raw_scores.get("schooling", "elementary")

        return {
            "raw_scores": raw_scores,
            "schooling": schooling,
            "responses": responses,
        }

    def classify(self, computed_data: dict, faixa: str = "") -> dict:
        raw_scores = computed_data.get("raw_scores", {})
        schooling = computed_data.get("schooling", "elementary")

        results = interpret_results(raw_scores, schooling)

        return {
            "raw_scores": raw_scores,
            "results": results,
            "schooling": schooling,
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        raw_scores = merged_data.get("raw_scores", {})
        schooling = merged_data.get("schooling", "elementary")

        return generate_report(raw_scores, schooling, patient_name=context.patient_name)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        results = merged_data.get("results") or {}
        interpretation = self.interpret(context, merged_data)
        return {
            "results": [
                {
                    "scale": value.get("label") or key,
                    "raw_score": value.get("raw_score") or value.get("score"),
                    "percentile": value.get("percentile") or value.get("percentile_text"),
                    "classification": value.get("classification"),
                }
                for key, value in results.items()
                if isinstance(value, dict)
            ],
            "summary_for_report": interpretation.split(". ")[0].strip() if interpretation else "",
            "technical_notes": [f"Escolaridade normativa: {merged_data.get('schooling', 'elementary')}"],
            "clinical_flags": [value.get("label") or key for key, value in results.items() if isinstance(value, dict) and value.get("classification") in {"Superior", "Média Superior"}],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(ETDAHAD_CODE, ETDAHADModule())
