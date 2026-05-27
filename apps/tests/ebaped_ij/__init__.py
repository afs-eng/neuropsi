from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module
from .config import EBADEPIJ_CODE, EBADEPIJ_NAME, ITENS_POSITIVOS, ITENS_NEGATIVOS
from .schemas import EBADEPIJRawInput, EBADEPIJResult, EBADEPIJNorms, ItemDetail
from .validators import validate_ebadep_ij_input
from .calculators import calcular_pontuacoes, classificar_tabela_18, obter_normas
from .interpreters import interpret_result, get_synthesis, get_report_interpretation


class EBADEPIJModule(BaseTestModule):
    code = EBADEPIJ_CODE
    name = EBADEPIJ_NAME

    def validate(self, context: TestContext) -> list[str]:
        try:
            data = EBADEPIJRawInput(**context.raw_scores)
            return validate_ebadep_ij_input(data)
        except Exception as e:
            return [f"Erro na validação: {e}"]

    def compute(self, context: TestContext) -> dict:
        respostas = []
        for i in range(1, 28):
            key = f"item_{i:02d}"
            respostas.append(context.raw_scores[key])
        return calcular_pontuacoes(respostas)

    def classify(self, computed_data: dict, faixa: str = "") -> dict:
        pontuacao_total = computed_data["pontuacao_total"]
        classificacao = classificar_tabela_18(pontuacao_total)
        normas = obter_normas(pontuacao_total)

        detalhe_itens = []
        for d in computed_data.get("detalhe_itens", []):
            detalhe_itens.append(ItemDetail(**d))

        result = EBADEPIJResult(
            soma_itens_negativos=computed_data["soma_itens_negativos"],
            soma_itens_positivos=computed_data["soma_itens_positivos"],
            pontuacao_total=pontuacao_total,
            classificacao=classificacao,
            normas=EBADEPIJNorms(**normas) if normas else None,
            detalhe_itens=detalhe_itens,
        )

        items_criticos = [d for d in detalhe_itens if d.corrigido == 2]

        return {
            "result": result.model_dump(),
            "classificacao": classificacao,
            "pontuacao_total": pontuacao_total,
            "normas": normas,
            "items_criticos": [d.model_dump() for d in items_criticos],
            "sintese": get_synthesis(classificacao),
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        classificacao = merged_data.get("classificacao", "")
        pontos = merged_data.get("pontuacao_total", 0)
        normas = merged_data.get("normas", {})
        percentil = normas.get("percentil", "—")
        escore_t = normas.get("T", "—")
        estanino = normas.get("estanino", "—")
        
        interp = interpret_result(classificacao)
        descricao = interp.get("descricao", "")

        report = [
            "## Resultado",
            "",
            f"Avaliado foi submetido(a) à EBADEP-IJ e obteve uma pontuação bruta total de **{pontos} pontos**, correspondente ao **percentil {percentil}**, **escore T {escore_t}** e **estanino {estanino}**.",
            "",
            f"Esse resultado sugere que o avaliado se encontra na categoria **{classificacao}**.",
            "",
            f"{descricao}",
            "",
            "Ainda assim, recomenda-se investigação clínica mais aprofundada, especialmente quanto à presença de sintomas ligados a humor deprimido ou irritável, anedonia, desesperança e ideação autolesiva."
        ]

        return "\n".join(report)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        normas = merged_data.get("normas") or {}
        interpretation = self.interpret(context, merged_data)
        return {
            "results": [
                {
                    "scale": "EBADEP-IJ",
                    "raw_score": merged_data.get("pontuacao_total"),
                    "percentile": normas.get("percentil"),
                    "classification": merged_data.get("classificacao"),
                }
            ],
            "summary_for_report": merged_data.get("sintese") or interpretation.split(". ")[0].strip(),
            "technical_notes": [
                f"Escore T: {normas.get('T', '—')}",
                f"Estanino: {normas.get('estanino', '—')}",
            ],
            "clinical_flags": [f"item_{item.get('item')}" for item in merged_data.get("items_criticos") or []],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(EBADEPIJ_CODE, EBADEPIJModule())
