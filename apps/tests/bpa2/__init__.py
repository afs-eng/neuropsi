from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module
from .config import BPA2_CODE, BPA2_NAME, BPA2_SUBTESTS
from .schemas import BPA2RawInput, SubtestResult
from .validators import validate_bpa2_input
from .calculators import calculate_total, load_table, get_age_group, classify_score
from .classifiers import find_strengths_weaknesses
from .interpreters import (
    NOMES_SUBTESTES,
    build_gold_standard_interpretation,
)

SUBTEST_CODES = ["ac", "ad", "aa"]


class BPA2Module(BaseTestModule):
    code = BPA2_CODE
    name = BPA2_NAME

    def validate(self, context: TestContext) -> list[str]:
        try:
            data = BPA2RawInput(**context.raw_scores)
            return validate_bpa2_input(data)
        except Exception as e:
            return [f"Erro na validação: {e}"]

    def compute(self, context: TestContext) -> dict:
        data = BPA2RawInput(**context.raw_scores)
        raw_dict = data.model_dump()

        results = {}
        for code in SUBTEST_CODES:
            inp = raw_dict[code]
            total = calculate_total(inp["brutos"], inp["erros"], inp["omissoes"])
            results[code] = {
                "subteste": NOMES_SUBTESTES[code],
                "codigo": code,
                "brutos": inp["brutos"],
                "erros": inp["erros"],
                "omissoes": inp["omissoes"],
                "total": total,
            }

        ag_total = sum(r["total"] for r in results.values())
        ag_brutos = sum(r["brutos"] for r in results.values())
        ag_erros = sum(r["erros"] for r in results.values())
        ag_omissoes = sum(r["omissoes"] for r in results.values())

        results["ag"] = {
            "subteste": NOMES_SUBTESTES["ag"],
            "codigo": "ag",
            "brutos": ag_brutos,
            "erros": ag_erros,
            "omissoes": ag_omissoes,
            "total": ag_total,
        }

        return results

    def classify(self, computed_data: dict, faixa: str = "15-17 anos") -> dict:
        subtest_results = []
        for code in ["ac", "ad", "aa", "ag"]:
            entry = computed_data.get(code, {})
            tabela = load_table(code, "idade")

            try:
                classificacao, percentil = classify_score(entry["total"], tabela, faixa)
            except Exception:
                classificacao = "Não classificado"
                percentil = 0

            subtest_results.append(
                SubtestResult(
                    subteste=entry.get("subteste", ""),
                    codigo=code,
                    brutos=entry.get("brutos", 0),
                    erros=entry.get("erros", 0),
                    omissoes=entry.get("omissoes", 0),
                    total=entry.get("total", 0),
                    classificacao=classificacao,
                    percentil=percentil,
                )
            )

        pontos_fortes, pontos_fragilizados = find_strengths_weaknesses(
            [r.model_dump() for r in subtest_results]
        )

        return {
            "subtestes": [r.model_dump() for r in subtest_results],
            "pontos_fortes": pontos_fortes,
            "pontos_fragilizados": pontos_fragilizados,
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        patient_name = (context.patient_name or "Paciente").split(" ", 1)[0]
        interpretation = build_gold_standard_interpretation(merged_data.get("subtestes", []), patient_name)
        return "\n\n".join([
            *interpretation["clinical_paragraphs"],
            interpretation["clinical_box_text"],
            interpretation["synthesis_text"],
        ])

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        subtestes = merged_data.get("subtestes") or []
        results = [
            {
                "scale": item.get("subteste") or item.get("codigo"),
                "raw_score": item.get("total") or item.get("brutos"),
                "percentile": item.get("percentil"),
                "classification": item.get("classificacao"),
            }
            for item in subtestes
        ]
        interpretation = self.interpret(context, merged_data)
        gold_standard = build_gold_standard_interpretation(subtestes, (context.patient_name or "Paciente").split(" ", 1)[0])
        return {
            "results": results,
            "summary_for_report": gold_standard["synthesis_text"],
            "technical_notes": [],
            "clinical_flags": merged_data.get("pontos_fragilizados") or [],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(BPA2_CODE, BPA2Module())
