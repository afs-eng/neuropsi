from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module
from .config import EBADEPA_CODE, EBADEPA_NAME, ITEM_LABELS
from .schemas import EBADEPARawInput, EBADEPAResult, EBADEPANorms, ItemDetail
from .validators import validate_ebadep_a_input
from .calculators import calcular_escore, obter_percentil, classificar
from .interpreters import interpret_result, get_synthesis, get_report_interpretation


class EBADEPAModule(BaseTestModule):
    code = EBADEPA_CODE
    name = EBADEPA_NAME

    def validate(self, context: TestContext) -> list[str]:
        try:
            data = EBADEPARawInput(**context.raw_scores)
            return validate_ebadep_a_input(data)
        except Exception as e:
            return [f"Erro na validação: {e}"]

    def compute(self, context: TestContext) -> dict:
        respostas = []
        for i in range(1, 46):
            key = f"item_{i:02d}"
            respostas.append(context.raw_scores[key])

        escore_total = calcular_escore(respostas)

        detalhes = []
        for i in range(1, 46):
            detalhes.append(ItemDetail(item=i, resposta=respostas[i - 1]).model_dump())

        return {
            "escore_total": escore_total,
            "detalhe_itens": detalhes,
        }

    def classify(self, computed_data: dict, faixa: str = "") -> dict:
        escore_total = computed_data["escore_total"]
        classificacao = classificar(escore_total)
        percentil = obter_percentil(escore_total)

        result = EBADEPAResult(
            escore_total=escore_total,
            classificacao=classificacao,
            percentil=percentil,
            detalhe_itens=[
                ItemDetail(**d) for d in computed_data.get("detalhe_itens", [])
            ],
        )

        items_criticos = [d for d in result.detalhe_itens if d.resposta == 3]

        return {
            "result": result.model_dump(),
            "classificacao": classificacao,
            "escore_total": escore_total,
            "percentil": percentil,
            "items_criticos": [d.model_dump() for d in items_criticos],
            "sintese": get_synthesis(classificacao),
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        classificacao = merged_data.get("classificacao", "")
        interp = interpret_result(classificacao)

        parts = []
        parts.append(f"Classificação Clínica: {classificacao}")
        parts.append(f"Interpretação e Observações Clínicas: {interp.get('geral', '')}")

        if merged_data.get("items_criticos"):
            items = [str(d["item"]) for d in merged_data["items_criticos"]]
            parts.append(f"Itens com escore máximo (pontuação 3): {', '.join(items)}")

        parts.append(f"Síntese Clínica: {get_synthesis(classificacao)}")

        return "\n".join(parts)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        interpretation = self.interpret(context, merged_data)
        return {
            "results": [
                {
                    "scale": "EBADEP-A",
                    "raw_score": merged_data.get("escore_total"),
                    "percentile": merged_data.get("percentil"),
                    "classification": merged_data.get("classificacao"),
                }
            ],
            "summary_for_report": merged_data.get("sintese") or interpretation.split(". ")[0].strip(),
            "technical_notes": [],
            "clinical_flags": [f"item_{item.get('item')}" for item in merged_data.get("items_criticos") or []],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(EBADEPA_CODE, EBADEPAModule())
