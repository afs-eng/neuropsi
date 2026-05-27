from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module

from .calculators import compute_bfp_scores
from .config import BFP_CODE, BFP_NAME, FACTOR_DEFINITIONS, FACET_DEFINITIONS
from .interpreters import get_report_interpretation
from .schemas import BFPRawInput
from .validators import validate_bfp_input


class BFPModule(BaseTestModule):
    code = BFP_CODE
    name = BFP_NAME

    def validate(self, context: TestContext) -> list[str]:
        try:
            BFPRawInput(**context.raw_scores)
        except Exception as e:
            return [f"Erro na validação: {e}"]
        return validate_bfp_input(context.raw_scores)

    def compute(self, context: TestContext) -> dict:
        return compute_bfp_scores(context.raw_scores)

    def classify(self, computed_data: dict, **kwargs) -> dict:
        factor_classifications = {
            code: result["classification"]
            for code, result in computed_data.get("factors", {}).items()
        }
        facet_classifications = {
            code: result["classification"]
            for code, result in computed_data.get("facets", {}).items()
        }
        highlights = [
            {
                "code": code,
                "name": result["name"],
                "classification": result["classification"],
                "percentile": result["percentile"],
            }
            for code, result in computed_data.get("facets", {}).items()
            if result["classification"] != "Médio"
        ]
        return {
            "sample": computed_data.get("sample", "geral"),
            "factor_classifications": factor_classifications,
            "facet_classifications": facet_classifications,
            "highlights": highlights,
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        return get_report_interpretation(merged_data, patient_name=context.patient_name)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        factors = merged_data.get("factors") or {}
        facets = merged_data.get("facets") or {}
        interpretation = self.interpret(context, merged_data)
        ordered_codes: list[str] = []
        for factor_code, factor_definition in FACTOR_DEFINITIONS.items():
            ordered_codes.extend(factor_definition["facets"])
            ordered_codes.append(factor_code)

        results = []
        for code in ordered_codes:
            item = facets.get(code) or factors.get(code)
            if not item:
                continue
            scale_name = FACET_DEFINITIONS[code]["name"] if code in FACET_DEFINITIONS else FACTOR_DEFINITIONS[code]["name"]
            results.append(
                {
                    "code": code,
                    "scale": scale_name,
                    "raw_score": item.get("raw_score") or item.get("weighted_score"),
                    "z_score": item.get("z_score"),
                    "percentile": item.get("percentile"),
                    "classification": item.get("classification"),
                }
            )
        return {
            "results": results,
            "summary_for_report": interpretation.split(". ")[0].strip() if interpretation else "",
            "technical_notes": [f"Amostra normativa: {merged_data.get('sample_label') or merged_data.get('sample') or 'geral'}"],
            "clinical_flags": [item.get("name") or key for key, item in facets.items() if item.get("classification") and item.get("classification") != "Médio"],
            "chart_payload": {
                "factors": [
                    {
                        "code": code,
                        "name": data.get("name"),
                        "percentile": data.get("percentile"),
                    }
                    for code, data in factors.items()
                ],
                "facets": [
                    {
                        "code": code,
                        "name": data.get("name"),
                        "percentile": data.get("percentile"),
                    }
                    for code, data in facets.items()
                ],
                "norm_reference": 50,
            },
            "interpretation": interpretation,
        }


register_test_module(BFP_CODE, BFPModule())
