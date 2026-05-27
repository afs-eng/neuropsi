from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module
from .config import EPQJ_CODE, EPQJ_NAME, ITEM_LABELS
from .schemas import EPQJRawInput, EPQJResult, EPQJFactorResult
from .validators import validate_epq_j_input
from .calculators import calcular_escore, obter_percentil_e_classificacao
from .interpreters import interpret_result, get_synthesis, get_report_interpretation


class EPQJModule(BaseTestModule):
    code = EPQJ_CODE
    name = EPQJ_NAME

    def validate(self, context: TestContext) -> list[str]:
        try:
            data = EPQJRawInput(**context.raw_scores)
            return validate_epq_j_input(data)
        except Exception as e:
            return [f"Erro na validação: {e}"]

    def compute(self, context: TestContext) -> dict:
        respostas = {}
        for i in range(1, 61):
            key = f"item_{i:02d}"
            respostas[i] = context.raw_scores.get(key, 0)

        bruto = calcular_escore(respostas)

        sexo = context.raw_scores.get("sexo", "M")

        resultados = obter_percentil_e_classificacao(
            bruto["P"], bruto["E"], bruto["N"], bruto["S"], sexo
        )

        return {
            "escore_bruto": bruto,
            "resultados": resultados,
            "sexo": sexo,
        }

    def classify(self, computed_data: dict, faixa: str = "") -> dict:
        resultados = computed_data.get("resultados", {})

        fatores = {}
        for f in ["P", "E", "N", "S"]:
            if f in resultados:
                r = resultados[f]
                fatores[f] = EPQJFactorResult(
                    escore=r["escore"],
                    percentil=r["percentil"],
                    classificacao=r["classificacao"],
                ).model_dump()

        return {
            "fatores": fatores,
            "sexo": computed_data.get("sexo", "M"),
            "sintese": get_synthesis(resultados),
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        fatores = merged_data.get("fatores", {})
        return get_report_interpretation(fatores, context.patient_name)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        fatores = merged_data.get("fatores") or {}
        interpretation = self.interpret(context, merged_data)
        return {
            "results": [
                {
                    "scale": key,
                    "raw_score": value.get("escore"),
                    "percentile": value.get("percentil"),
                    "classification": value.get("classificacao"),
                }
                for key, value in fatores.items()
            ],
            "summary_for_report": merged_data.get("sintese") or interpretation.split(". ")[0].strip(),
            "technical_notes": [f"Sexo normativo: {merged_data.get('sexo', 'M')}"],
            "clinical_flags": [key for key, value in fatores.items() if value.get("classificacao") in {"ALTO", "MUITO ALTO"}],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(EPQJ_CODE, EPQJModule())
