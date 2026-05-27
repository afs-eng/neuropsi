from __future__ import annotations

from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module

from apps.tests.norms.bai import get_norms_metadata
from .calculators import BAICalculator
from .classifiers import BAIClassifier
from .constants import ITEMS, RAW_SCORE_BANDS
from .interpreters import build_bai_interpretation, get_report_interpretation
from .schemas import BAIItemResponse, BAIRawPayload
from .validators import BAIValidator

BAI_CODE = "bai"
BAI_NAME = "BAI - Inventário de Ansiedade de Beck"


class BAIModule(BaseTestModule):
    code = BAI_CODE
    name = BAI_NAME

    def __init__(self, chart_output_dir: str = "/tmp/bai_charts"):
        self.calculator = BAICalculator(chart_output_dir=chart_output_dir)

    def validate(self, context: TestContext) -> list[str]:
        """Valida raw_scores do contexto."""
        try:
            from .schemas import BAIRawInput

            data = BAIRawInput(**context.raw_scores)
            from .validators import validate_bai_input

            return validate_bai_input(data)
        except Exception as e:
            return [f"Erro na validação: {e}"]

    def compute(self, context: TestContext) -> dict:
        """Calcula escores do BAI a partir do TestContext."""
        responses = []
        for i in range(1, 22):
            key = f"item_{i:02d}"
            score = context.raw_scores.get(key, 0)
            responses.append(BAIItemResponse(item_number=i, score=score))

        payload = BAIRawPayload(
            respondent_name=context.patient_name,
            application_mode="system",
            responses=responses,
        )

        return self.calculator.score(payload)

    def classify(self, computed_data: dict, **kwargs) -> dict:
        """Classifica resultados do BAI."""
        total_raw_score = computed_data.get("total_raw_score", 0)
        t_score = computed_data.get("t_score")

        classificacao_raw = BAIClassifier.classify_raw_score(total_raw_score)
        classificacao_t = BAIClassifier.classify_t_score(t_score) if t_score else None
        classificacao = {
            "raw": classificacao_raw,
            "t_score": classificacao_t,
            "label": classificacao_raw["label"],
            "key": classificacao_raw["key"],
            "interpretation": classificacao_raw["interpretation"],
        }

        return {
            "escore_total": total_raw_score,
            "t_score": t_score,
            "percentile": computed_data.get("percentile"),
            "confidence_interval": computed_data.get("confidence_interval"),
            "classificacao": classificacao,
            "classificacao_raw": classificacao_raw,
            "classificacao_t": classificacao_t,
            "faixa_normativa": classificacao_raw["label"],
            "interpretacao_faixa": classificacao_raw["interpretation"],
            "norms_metadata": get_norms_metadata(),
            "tables": computed_data.get("tables", {}),
            "charts": computed_data.get("charts", {}),
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        """Gera interpretação do BAI."""
        return get_report_interpretation(merged_data)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        classification = merged_data.get("classificacao") or {}
        tables = merged_data.get("tables") or {}
        details = tables.get("detail_table") or []
        interpretation = self.interpret(context, merged_data)
        return {
            "results": [
                {
                    "scale": item.get("label") or item.get("item") or "BAI",
                    "raw_score": item.get("raw_score") or item.get("value"),
                    "percentile": item.get("percentile"),
                    "classification": item.get("classification") or item.get("band"),
                }
                for item in details
            ],
            "summary_for_report": (
                f"Sintomatologia ansiosa classificada como {str(classification.get('label') or 'não classificada').lower()}, "
                f"com escore total {merged_data.get('escore_total', 0)} e escore T {merged_data.get('t_score', '-')}."
            ),
            "technical_notes": [classification.get("interpretation", "")],
            "clinical_flags": [classification.get("label")] if classification.get("key") in {"grave"} else [],
            "chart_payload": (merged_data.get("charts") or {}).get("profile") or {},
            "interpretation": interpretation,
        }


# Registra no sistema
register_test_module(BAI_CODE, BAIModule())
