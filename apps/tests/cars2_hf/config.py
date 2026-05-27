from apps.tests.base.types import BaseTestModule, TestContext

from .calculators import build_computed_payload
from .classifiers import classify_cars2_hf
from .interpreters import build_cars2_hf_interpretation
from .schemas import CARS2HFInput
from .validators import validate_cars2_hf_payload


class CARS2HFModule(BaseTestModule):
    code = "CARS2_HF"
    name = "CARS2 – HF"

    def validate(self, context: TestContext) -> list[str]:
        try:
            data = CARS2HFInput(**context.raw_scores)
            validate_cars2_hf_payload(data.model_dump())
            return []
        except Exception as exc:
            return [f"Erro na validacao: {exc}"]

    def compute(self, context: TestContext) -> dict:
        data = CARS2HFInput(**context.raw_scores)
        return build_computed_payload(data.model_dump())

    def classify(self, computed_data: dict) -> dict:
        classification = classify_cars2_hf(computed_data["raw_total"])
        return {
            **classification,
            "highest_domains": computed_data.get("highest_domains", []),
            "domain_scores": computed_data.get("domain_scores", {}),
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        computed_payload = {
            "raw_total": merged_data.get("raw_total"),
            "t_score": merged_data.get("t_score"),
            "percentile": merged_data.get("percentile"),
            "highest_domains": merged_data.get("highest_domains", []),
        }
        classification = {
            "severity_group": merged_data.get("severity_group", "Resultado invalido"),
            "severity_code": merged_data.get("severity_code", "invalid"),
        }
        return build_cars2_hf_interpretation(computed_payload, classification)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        interpretation = self.interpret(context, merged_data)
        highest_domains = merged_data.get("highest_domains") or []
        return {
            "results": [
                {
                    "scale": key,
                    "raw_score": value,
                    "percentile": None,
                    "classification": merged_data.get("severity_group"),
                }
                for key, value in (merged_data.get("domain_scores") or {}).items()
            ],
            "summary_for_report": (
                f"Perfil CARS2-HF com escore bruto {merged_data.get('raw_total', '-')}, T-escore {merged_data.get('t_score', '-')}, "
                f"percentil {merged_data.get('percentile', '-')} e gravidade {str(merged_data.get('severity_group') or 'não classificada').lower()}."
            ),
            "technical_notes": [f"Domínios mais elevados: {', '.join(highest_domains)}"] if highest_domains else [],
            "clinical_flags": highest_domains,
            "chart_payload": {},
            "interpretation": interpretation,
        }
