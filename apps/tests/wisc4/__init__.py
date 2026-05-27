from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module
from .calculators import (
    WISC4_CODE,
    WISC4_NAME,
    WISC4_SUBTESTS,
    WISC4_SUPPLEMENTAL_SUBTESTS,
    WISC4_INDICES,
    SUBTEST_SEM,
    _carregar_tabela_ncp,
    _calcular_idade,
    _idade_em_meses,
    buscar_ponderado,
    get_classification_padrao,
    get_classification_composto,
    get_percentil_subteste,
    calculate_index_score,
    calculate_qi_total,
    calculate_confidence_interval,
    build_process_scores,
    lookup_composite_score,
    lookup_gai_score,
    lookup_cpi_score,
)
from .classifiers import find_strengths_weaknesses, find_significant_differences
from .interpreters import interpret_index, interpret_qi, interpret_wisc4_profile


class WISC4Module(BaseTestModule):
    code = WISC4_CODE
    name = WISC4_NAME

    def _build_subtest_result(self, tabela: list[dict], code: str, config: dict, eb):
        coluna = config["code"]
        if eb is None:
            pp = None
            classificacao = None
            ic = None
            percentil = None
        else:
            try:
                pp = buscar_ponderado(tabela, coluna, eb)
            except ValueError:
                pp = 10
            classificacao = get_classification_padrao(pp)
            sem = SUBTEST_SEM.get(coluna, 1.22)
            ic = calculate_confidence_interval(pp, sem=sem)
            percentil = get_percentil_subteste(pp)

        return {
            "subteste": config["name"],
            "codigo": config["code"],
            "escore_bruto": eb,
            "escore_padrao": pp,
            "percentil": percentil,
            "classificacao": classificacao,
            "intervalo_confianca_95": ic,
        }

    def _resolve_index_subtests(self, computed_data: dict, idx_config: dict) -> tuple[list[dict], list[dict]]:
        selected_subtests = []
        missing_codes = []

        for code in idx_config["subtests"]:
            subtest = computed_data.get(code)
            if not subtest or subtest.get("escore_padrao") is None:
                missing_codes.append(code)
                continue
            selected_subtests.append(subtest)

        substitution_sources = []
        if len(missing_codes) == 1:
            for supplemental_code in idx_config.get("supplemental", []):
                supplemental = computed_data.get(supplemental_code)
                if supplemental and supplemental.get("escore_padrao") is not None:
                    selected_subtests.append(
                        {
                            **supplemental,
                            "substituicao_de": missing_codes[0],
                            "subteste_original": supplemental.get("subteste"),
                            "subteste": f"{supplemental.get('subteste')} (substituindo {missing_codes[0].upper()})",
                        }
                    )
                    substitution_sources.append(supplemental)
                    missing_codes = []
                    break

        return selected_subtests, substitution_sources

    def validate(self, context: TestContext) -> list[str]:
        errors = []

        birth_date = context.reviewed_scores.get("birth_date")
        evaluation_date = context.reviewed_scores.get("evaluation_date")
        if birth_date and evaluation_date:
            from datetime import date as dt

            bd = (
                dt.fromisoformat(birth_date)
                if isinstance(birth_date, str)
                else birth_date
            )
            ed = (
                dt.fromisoformat(evaluation_date)
                if isinstance(evaluation_date, str)
                else evaluation_date
            )
            anos, meses = _calcular_idade(bd, ed)
            idade_meses = _idade_em_meses(anos, meses)
            min_meses = _idade_em_meses(6, 0)
            max_meses = _idade_em_meses(16, 11)
            if idade_meses < min_meses or idade_meses > max_meses:
                errors.append(
                    f"WISC-IV é indicado para faixa etária de 6 anos a 16 anos e 11 meses. "
                    f"Paciente com {anos} anos e {meses} meses está fora da faixa."
                )

        for code, config in WISC4_SUBTESTS.items():
            valor = context.raw_scores.get(code)
            if valor is None:
                errors.append(f"Subteste '{config['name']}' não informado")
            elif valor < 0:
                errors.append(f"{config['name']}: escore bruto não pode ser negativo")
            elif valor > config["max"]:
                errors.append(
                    f"{config['name']}: escore bruto ({valor}) maior que o máximo ({config['max']})"
                )
        return errors

    def compute(self, context: TestContext) -> dict:
        patient_name = context.patient_name
        birth_date = context.reviewed_scores.get("birth_date")
        evaluation_date = context.reviewed_scores.get("evaluation_date")

        if birth_date and evaluation_date:
            from datetime import date

            if isinstance(birth_date, str):
                birth_date = date.fromisoformat(birth_date)
            if isinstance(evaluation_date, str):
                evaluation_date = date.fromisoformat(evaluation_date)
            anos, meses = _calcular_idade(birth_date, evaluation_date)
        else:
            anos, meses = 6, 0

        tabela = _carregar_tabela_ncp(anos, meses)

        subtest_results = {}
        for code, config in {**WISC4_SUBTESTS, **WISC4_SUPPLEMENTAL_SUBTESTS}.items():
            eb = context.raw_scores.get(code)
            subtest_results[code] = self._build_subtest_result(tabela, code, config, eb)

        subtest_results["process_scores"] = build_process_scores(
            context.raw_scores,
            anos,
            meses,
            subtest_results,
        )

        return subtest_results

    def classify(self, computed_data: dict, faixa: str = "") -> dict:
        confidence_level = faixa if faixa in ("90", "95") else "95"

        index_results = []
        for idx_code, idx_config in WISC4_INDICES.items():
            subtests_for_index, substitution_sources = self._resolve_index_subtests(
                computed_data, idx_config
            )
            sp_list = [item.get("escore_padrao") for item in subtests_for_index]
            has_missing_scores = any(score is None for score in sp_list)
            soma_ponderados = None if has_missing_scores else calculate_index_score(sp_list)

            composite_data = None
            if idx_code in ("icv", "iop", "imt", "ivp") and soma_ponderados is not None:
                try:
                    composite_data = lookup_composite_score(idx_code, soma_ponderados)
                except ValueError:
                    composite_data = {
                        "escore": None,
                        "percentil": None,
                        "ic_90": None,
                        "ic_95": None,
                    }

            index_entry = {
                "indice": idx_code,
                "nome": idx_config["name"],
                "soma_ponderados": soma_ponderados,
                "subtestes": subtests_for_index,
                "subtestes_suplementares": substitution_sources,
            }
            if composite_data:
                composite_classification = None
                if composite_data["escore"] is not None:
                    _, composite_classification = get_classification_composto(
                        composite_data["escore"]
                    )
                index_entry.update(
                    {
                        "escore_composto": composite_data["escore"],
                        "percentil": composite_data["percentil"],
                        "intervalo_confianca": composite_data[f"ic_{confidence_level}"],
                        "classificacao": composite_classification,
                    }
                )
            index_results.append(index_entry)

        core_index_entries = [
            r for r in index_results if r["indice"] in ("icv", "iop", "imt", "ivp")
        ]
        soma_pp_por_indice = [r["soma_ponderados"] for r in core_index_entries]
        soma_total = None if any(value is None for value in soma_pp_por_indice) else sum(soma_pp_por_indice)

        qit_data = None
        if soma_total is not None:
            try:
                qit_data = lookup_composite_score("qit", soma_total)
            except ValueError:
                qit_data = {
                    "escore": calculate_qi_total(soma_total),
                    "percentil": None,
                    "ic_90": None,
                    "ic_95": None,
                }

        qi_total = qit_data["escore"] if qit_data else None
        qit_classificacao = None
        if qi_total is not None:
            _, qit_classificacao = get_classification_composto(qi_total)

        # GAI = ICV + IOP
        gai_components = [
            r["soma_ponderados"] for r in index_results if r["indice"] in ("icv", "iop")
        ]
        gai_soma = None if any(value is None for value in gai_components) else sum(gai_components)
        gai_data = None
        if gai_soma is not None:
            try:
                gai_data = lookup_gai_score(gai_soma)
            except ValueError:
                gai_data = {
                    "escore": None,
                    "percentil": None,
                    "ic_95": None,
                    "classificacao": None,
                }

        # CPI = IMO + IVP
        cpi_components = [
            r["soma_ponderados"] for r in index_results if r["indice"] in ("imt", "ivp")
        ]
        cpi_soma = None if any(value is None for value in cpi_components) else sum(cpi_components)
        cpi_data = None
        if cpi_soma is not None:
            try:
                cpi_data = lookup_cpi_score(cpi_soma)
            except ValueError:
                cpi_data = {
                    "escore": None,
                    "percentil": None,
                    "ic_95": None,
                    "classificacao": None,
                }

        all_subtests = [computed_data[code] for code in WISC4_SUBTESTS if code in computed_data]
        pontos_fortes, pontos_fragilizados = find_strengths_weaknesses(all_subtests)
        diferencas = find_significant_differences(index_results, qi_total)

        return {
            "subtestes": all_subtests,
            "indices": index_results,
            "qi_total": qi_total,
            "qit_data": {
                "soma_ponderados": soma_total,
                "escore_composto": qit_data["escore"] if qit_data else None,
                "percentil": qit_data["percentil"] if qit_data else None,
                "intervalo_confianca": qit_data[f"ic_{confidence_level}"] if qit_data else None,
                "classificacao": qit_classificacao,
            },
            "gai_data": {
                "soma_ponderados": gai_soma,
                "escore_composto": gai_data["escore"] if gai_data else None,
                "percentil": gai_data["percentil"] if gai_data else None,
                "intervalo_confianca": gai_data["ic_95"] if gai_data else None,
                "classificacao": gai_data["classificacao"] if gai_data else None,
            },
            "cpi_data": {
                "soma_ponderados": cpi_soma,
                "escore_composto": cpi_data["escore"] if cpi_data else None,
                "percentil": cpi_data["percentil"] if cpi_data else None,
                "intervalo_confianca": cpi_data["ic_95"] if cpi_data else None,
                "classificacao": cpi_data["classificacao"] if cpi_data else None,
            },
            "pontos_fortes": pontos_fortes,
            "pontos_fragilizados": pontos_fragilizados,
            "diferencas_significativas": diferencas,
            "confidence_level": confidence_level,
            "process_scores": computed_data.get("process_scores") or {},
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        first_name = (context.patient_name or "Paciente").split(" ", 1)[0]
        return interpret_wisc4_profile(merged_data, first_name)

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        interpretation = self.interpret(context, merged_data)
        qit = merged_data.get("qit_data") or {}
        indices = merged_data.get("indices") or []
        subtestes = merged_data.get("subtestes") or []
        results = [
            {
                "scale": item.get("nome") or item.get("indice"),
                "raw_score": item.get("escore_composto"),
                "percentile": item.get("percentil"),
                "classification": item.get("classificacao"),
            }
            for item in indices
        ]
        results.extend(
            {
                "scale": item.get("subteste") or item.get("codigo"),
                "raw_score": item.get("escore_padrao"),
                "percentile": item.get("percentil"),
                "classification": item.get("classificacao"),
            }
            for item in subtestes
        )
        summary = (
            f"Funcionamento cognitivo global com QI total {qit.get('escore_composto', '-')}, "
            f"classificado como {str(qit.get('classificacao') or 'não classificado').lower()}."
        )
        return {
            "results": results,
            "summary_for_report": summary,
            "technical_notes": [],
            "clinical_flags": merged_data.get("pontos_fragilizados") or [],
            "chart_payload": {},
            "interpretation": interpretation,
        }


register_test_module(WISC4_CODE, WISC4Module())
