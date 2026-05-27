from datetime import date

from apps.tests.bpa2.calculators import get_age_group as _get_bpa2_age_group
from apps.tests.bpa2.calculators import load_table as _load_bpa2_table
from apps.tests.base.types import TestContext
from apps.tests.registry import get_test_module
from apps.tests.selectors import get_test_applications_by_evaluation
from apps.tests.services.report_payload_service import TestReportPayloadService
from apps.tests.selectors import get_validated_test_applications_by_evaluation
from apps.tests.wais3.constants import WAIS3_ALL_SUBTESTS, classify_scaled_score
from apps.tests.wais3.loaders import WAIS3NormLoader
from apps.tests.wais3.norm_utils import resolve_age_range as _resolve_wais3_age_range
from apps.tests.wisc4.calculators import _calcular_idade, _carregar_tabela_ncp


SECTION_MAP = {
    "wisc4": "eficiencia_intelectual",
    "wais3": "eficiencia_intelectual",
    "bpa2": "atencao",
    "fdt": "funcoes_executivas",
    "ravlt": "memoria_aprendizagem",
    "epq_j": "escalas_complementares",
    "scared": "escalas_complementares",
    "srs2": "escalas_complementares",
    "bai": "escalas_complementares",
    "ebadep_a": "escalas_complementares",
    "ebaped_ij": "escalas_complementares",
    "etdah_ad": "atencao",
    "etdah_pais": "atencao",
}

BPA2_SERIES_META = {
    "ac": ("ATENÇÃO CONCENTRADA", "#E67E22"),
    "ad": ("ATENÇÃO DIVIDIDA", "#F1B500"),
    "aa": ("ATENÇÃO ALTERNADA", "#7BAE45"),
    "ag": ("ATENÇÃO GERAL", "#A94F0B"),
}



def _clean_text(value) -> str:
    if value is None:
        return ""
    return str(value).replace("_", " ").strip()


def _format_number(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _parse_score_range(value: str | None) -> tuple[int, int] | None:
    if not value or value == "-":
        return None
    text = str(value).strip()
    if "-" in text:
        start_text, end_text = text.split("-", 1)
    else:
        start_text = end_text = text
    try:
        return int(start_text.strip()), int(end_text.strip())
    except ValueError:
        return None


def _format_result_line(label: str, *parts) -> str:
    details = [str(part).strip() for part in parts if part not in (None, "", [], {})]
    suffix = " | ".join(details)
    return f"- {label}: {suffix}" if suffix else f"- {label}"


def _extract_generic_rows(data, depth: int = 0) -> list[str]:
    if depth > 2:
        return []

    rows: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            label = _clean_text(key).title()
            if isinstance(value, dict):
                simple_parts = []
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (dict, list)):
                        continue
                    simple_parts.append(
                        f"{_clean_text(sub_key)} {_format_number(sub_value)}"
                    )
                if simple_parts:
                    rows.append(_format_result_line(label, *simple_parts[:4]))
                else:
                    rows.extend(_extract_generic_rows(value, depth + 1))
            elif isinstance(value, list):
                if value and all(isinstance(item, dict) for item in value):
                    for item in value[:6]:
                        item_label = _clean_text(
                            item.get("nome")
                            or item.get("subteste")
                            or item.get("name")
                            or item.get("indice")
                            or key
                        ).title()
                        details = []
                        for field in (
                            "escore_composto",
                            "escore_padrao",
                            "raw_score",
                            "valor",
                            "total",
                            "percentil",
                            "percentil_num",
                            "classificacao",
                            "classification",
                        ):
                            if field in item and item[field] not in (None, ""):
                                details.append(
                                    f"{_clean_text(field)} {_format_number(item[field])}"
                                )
                        rows.append(_format_result_line(item_label, *details[:4]))
                elif value and all(
                    not isinstance(item, (dict, list)) for item in value
                ):
                    rows.append(
                        _format_result_line(
                            label, ", ".join(_format_number(item) for item in value[:8])
                        )
                    )
            else:
                rows.append(_format_result_line(label, _format_number(value)))
    return rows[:12]


def _build_wisc4_rows(payload: dict) -> list[str]:
    rows = []
    qit = payload.get("qit_data") or {}
    if qit:
        rows.append(
            _format_result_line(
                "QI Total",
                f"escore composto {_format_number(qit.get('escore_composto'))}",
                f"percentil {_format_number(qit.get('percentil'))}",
            )
        )
    for item in (payload.get("indices") or [])[:6]:
        rows.append(
            _format_result_line(
                item.get("nome") or item.get("indice") or "Indice",
                f"escore composto {_format_number(item.get('escore_composto'))}",
                f"percentil {_format_number(item.get('percentil'))}",
            )
        )
    strengths = payload.get("pontos_fortes") or []
    if strengths:
        rows.append(_format_result_line("Pontos fortes", ", ".join(strengths)))
    weaknesses = payload.get("pontos_fragilizados") or []
    if weaknesses:
        rows.append(_format_result_line("Pontos fragilizados", ", ".join(weaknesses)))
    return rows


def _build_bpa2_rows(payload: dict) -> list[str]:
    rows = []
    for item in payload.get("subtestes") or []:
        rows.append(
            _format_result_line(
                item.get("subteste") or item.get("codigo") or "Subteste",
                f"total {_format_number(item.get('total'))}",
                f"percentil {_format_number(item.get('percentil'))}",
                item.get("classificacao"),
            )
        )
    return rows


def _build_wais3_rows(payload: dict) -> list[str]:
    rows = []
    indices = payload.get("indices") or {}
    for key in (
        "qi_total",
        "qi_verbal",
        "qi_execucao",
        "compreensao_verbal",
        "organizacao_perceptual",
        "memoria_operacional",
        "velocidade_processamento",
    ):
        item = indices.get(key) or {}
        if not item:
            continue
        parts = []
        if item.get("pontuacao_composta") not in (None, ""):
            parts.append(f"pontuação composta {_format_number(item.get('pontuacao_composta'))}")
        if item.get("percentil") not in (None, ""):
            parts.append(f"percentil {_format_number(item.get('percentil'))}")
        if item.get("classificacao"):
            parts.append(item.get("classificacao"))
        if item.get("subtestes_ausentes"):
            parts.append("subtestes ausentes " + ", ".join(item.get("subtestes_ausentes")[:5]))
        rows.append(_format_result_line(item.get("nome") or key, *parts))
    warnings = payload.get("warnings") or []
    if warnings:
        rows.append(_format_result_line("Alertas", "; ".join(warnings[:3])))
    return rows


def _bpa2_age_group_for_application(evaluation, applied_on) -> str | None:
    birth_date = getattr(getattr(evaluation, "patient", None), "birth_date", None)
    if not birth_date:
        return None
    reference_date = applied_on or evaluation.start_date
    if not reference_date:
        return None
    if isinstance(reference_date, str):
        reference_date = date.fromisoformat(reference_date[:10])
    age = reference_date.year - birth_date.year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return _get_bpa2_age_group(age)


def _bpa2_reference_scores(code: str, age_group: str | None) -> tuple[float, float, float]:
    if not age_group:
        return (0.0, 0.0, 0.0)

    try:
        table = _load_bpa2_table(code, "idade")
    except Exception:
        return (0.0, 0.0, 0.0)

    values_by_percentile: dict[int, float] = {}
    for row in table:
        try:
            percentile = int(row.get("Percentil") or 0)
            value = float(str(row.get(age_group) or "0").replace(",", "."))
        except ValueError:
            continue
        values_by_percentile[percentile] = value

    return (
        values_by_percentile.get(99, 0.0),
        values_by_percentile.get(40, 0.0),
        values_by_percentile.get(10, 0.0),
    )


def _build_bpa2_chart_data(payload: dict, evaluation, applied_on) -> dict:
    age_group = _bpa2_age_group_for_application(evaluation, applied_on)
    subtests = {
        str(item.get("codigo") or "").lower(): item for item in payload.get("subtestes") or []
    }
    domains = []

    for code in ("ac", "ad", "aa", "ag"):
        item = subtests.get(code)
        if not item:
            continue
        maximo, medio, minimo = _bpa2_reference_scores(code, age_group)
        label, color = BPA2_SERIES_META[code]
        domains.append(
            {
                "label": label,
                "color": color,
                "values": {
                    "maximo": maximo,
                    "medio": medio,
                    "minimo": minimo,
                    "bruto": float(item.get("total") or item.get("brutos") or 0),
                    "percentil": float(item.get("percentil") or 0),
                },
            }
        )

    return {
        "title": "BPA - BATERIA PSICOLÓGICA PARA AVALIAÇÃO DA ATENÇÃO",
        "domains": domains,
    }


def _is_effectively_applied_test(item) -> bool:
    instrument_code = getattr(getattr(item, "instrument", None), "code", "") or ""
    raw_payload = getattr(item, "raw_payload", None) or {}
    computed_payload = getattr(item, "computed_payload", None) or {}
    classified_payload = getattr(item, "classified_payload", None) or {}
    reviewed_payload = getattr(item, "reviewed_payload", None) or {}

    if instrument_code == "bfp":
        return bool(
            getattr(item, "applied_on", None)
            and (
                (computed_payload.get("factors") or computed_payload.get("facets"))
            or ((classified_payload or {}).get("factors") or (classified_payload or {}).get("facets"))
            or ((raw_payload or {}).get("responses"))
            )
        )

    if instrument_code == "scared":
        return bool(
            (classified_payload.get("analise_geral") or [])
            or (raw_payload.get("responses") or {})
            or computed_payload
            or reviewed_payload
        )

    return bool(
        getattr(item, "applied_on", None)
        or raw_payload
        or computed_payload
        or classified_payload
        or reviewed_payload
        or str(getattr(item, "interpretation_text", "") or "").strip()
    )


def _application_signature(item) -> tuple[str, str]:
    instrument_code = getattr(getattr(item, "instrument", None), "code", "") or ""
    classified_payload = getattr(item, "classified_payload", None) or {}
    raw_payload = getattr(item, "raw_payload", None) or {}
    form_type = (
        classified_payload.get("form_type")
        or raw_payload.get("form")
        or "default"
    )
    return instrument_code, str(form_type)


def _select_report_applications(evaluation) -> list:
    validated = list(get_validated_test_applications_by_evaluation(evaluation.id))
    all_applied = list(get_test_applications_by_evaluation(evaluation.id))

    selected: dict[tuple[str, str], object] = {}
    for item in validated:
        selected[_application_signature(item)] = item
    for item in all_applied:
        selected.setdefault(_application_signature(item), item)

    def sort_key(item):
        applied_on = getattr(item, "applied_on", None)
        created_at = getattr(item, "created_at", None)
        return (
            applied_on.isoformat() if applied_on else "",
            created_at.isoformat() if created_at else "",
            getattr(item, "id", 0),
        )

    return sorted(selected.values(), key=sort_key)




def _build_fdt_rows(payload: dict) -> list[str]:
    rows = []
    for item in payload.get("metric_results") or []:
        rows.append(
            _format_result_line(
                item.get("nome") or item.get("codigo") or "Metrica",
                f"valor {_format_number(item.get('valor'))}",
                f"percentil {_format_number(item.get('percentil_num'))}",
                item.get("classificacao"),
            )
        )
    derived = payload.get("derived_scores") or {}
    if derived:
        rows.append(
            _format_result_line(
                "Indices derivados",
                f"inibicao {_format_number(derived.get('inibicao'))}",
                f"flexibilidade {_format_number(derived.get('flexibilidade'))}",
                f"erros totais {_format_number(derived.get('total_erros'))}",
            )
        )
    return rows


def _build_ravlt_rows(payload: dict) -> list[str]:
    rows = []
    for key in ("a1", "a2", "a3", "a4", "a5", "b", "a6", "a7"):
        if key in payload:
            rows.append(
                _format_result_line(key.upper(), _format_number(payload.get(key)))
            )
    for key in ("alt", "ret", "ip", "ir", "r"):
        if key in payload:
            rows.append(
                _format_result_line(key.upper(), _format_number(payload.get(key)))
            )
    if not rows:
        rows.extend(_extract_generic_rows(payload))
    return rows


def _build_scale_rows(payload: dict) -> list[str]:
    if payload.get("results") and isinstance(payload["results"], dict):
        rows = []
        for _, item in payload["results"].items():
            rows.append(
                _format_result_line(
                    item.get("name") or "Fator",
                    f"escore {_format_number(item.get('raw_score'))}",
                    f"percentil {_format_number(item.get('percentile_text') or item.get('percentil'))}",
                    item.get("classification") or item.get("classificacao"),
                )
            )
        return rows

    if payload.get("result") and isinstance(payload["result"], dict):
        base = payload.get("result") or {}
        return [
            _format_result_line(
                "Resultado principal",
                f"escore {_format_number(base.get('escore_total') or base.get('pontuacao_total'))}",
                f"percentil {_format_number(base.get('percentil') or (base.get('normas') or {}).get('percentil'))}",
                base.get("classificacao"),
            )
        ]

    return _extract_generic_rows(payload)


def _normalize_wisc_cell(cell: str) -> tuple[int | None, int | None]:
    raw = (cell or "").strip().replace(":", "-")
    if not raw or raw == "-":
        return (None, None)
    if "-" in raw:
        start, end = raw.split("-", 1)
        try:
            return (int(start), int(end))
        except ValueError:
            return (None, None)
    if raw.isdigit():
        if len(raw) == 2 and int(raw[1]) == int(raw[0]) + 1:
            return (int(raw[0]), int(raw[1]))
        if len(raw) == 4:
            left, right = raw[:2], raw[2:]
            if left.isdigit() and right.isdigit():
                return (int(left), int(right))
        number = int(raw)
        return (number, number)
    return (None, None)


def _wisc_reference_scores(table: list[dict] | None, code: str) -> tuple[str, str, str]:
    if not table:
        return ("-", "-", "-")

    rows_by_pp = {}
    for row in table:
        try:
            rows_by_pp[int(row.get("PP") or 0)] = row
        except ValueError:
            continue

    max_start, max_end = _normalize_wisc_cell((rows_by_pp.get(19) or {}).get(code, ""))
    max_text = "-" if max_start is None else str(max_start) if max_start == max_end else f"{max_start}-{max_end}"

    mid_start, _ = _normalize_wisc_cell((rows_by_pp.get(8) or {}).get(code, ""))
    _, mid_end = _normalize_wisc_cell((rows_by_pp.get(12) or {}).get(code, ""))
    mid_text = "-" if mid_start is None or mid_end is None else str(mid_start) if mid_start == mid_end else f"{mid_start}-{mid_end}"

    min_start, _ = _normalize_wisc_cell((rows_by_pp.get(5) or {}).get(code, ""))
    min_text = str(min_start) if min_start is not None else "-"
    return (max_text, mid_text, min_text)


def _wisc_ncp_table_for_application(evaluation, applied_on) -> list[dict] | None:
    if not evaluation.patient.birth_date:
        return None
    reference_date = applied_on or evaluation.start_date
    if not reference_date:
        return None
    if isinstance(reference_date, str):
        reference_date = date.fromisoformat(reference_date[:10])
    years, months = _calcular_idade(evaluation.patient.birth_date, reference_date)
    return _carregar_tabela_ncp(years, months)


def _build_wisc_tables(payload: dict, evaluation, applied_on) -> dict:
    ncp_table = _wisc_ncp_table_for_application(evaluation, applied_on)
    subtests = {item.get("codigo"): item for item in payload.get("subtestes") or []}
    domains = {
        "funcoes_executivas": ["SM", "CN", "CO", "RM"],
        "linguagem": ["SM", "VC", "CO"],
        "gnosias_praxias": ["RM", "CB"],
        "memoria_aprendizagem": ["SNL", "DG"],
    }
    tables = {}
    for domain, codes in domains.items():
        rows = []
        for code in codes:
            item = subtests.get(code)
            if not item:
                continue
            score_max, score_mid, score_min = _wisc_reference_scores(ncp_table, code)
            rows.append(
                {
                    "label": "Seq. Núm. e Letras" if code == "SNL" else item.get("subteste") or code,
                    "maxScore": score_max,
                    "avgScore": score_mid,
                    "minScore": score_min,
                    "obtainedScore": _format_number(item.get("escore_bruto")),
                    "classification": item.get("classificacao") or "-",
                }
            )
        if domain == "linguagem":
            rows.append(
                {
                    "label": "Fala Espontânea",
                    "note": "Dentro do esperado para a sua idade",
                }
            )
        tables[domain] = rows
    return tables


def _wais3_age_group_for_application(evaluation, applied_on) -> str | None:
    birth_date = getattr(getattr(evaluation, "patient", None), "birth_date", None)
    if not birth_date:
        return None
    reference_date = applied_on or evaluation.start_date
    if not reference_date:
        return None
    if isinstance(reference_date, str):
        reference_date = date.fromisoformat(reference_date[:10])

    years, months = _calcular_idade(birth_date, reference_date)
    try:
        return _resolve_wais3_age_range(years, months)
    except ValueError:
        return None


def _wais3_reference_scores(loader: WAIS3NormLoader, age_group: str | None, subtest_key: str) -> tuple[str, str, str]:
    if not age_group:
        return ("-", "-", "-")

    domain = "verbal" if subtest_key in {"vocabulario", "semelhancas", "aritmetica", "digitos", "informacao", "compreensao", "sequencia_numeros_letras"} else "execucao"
    rows = loader._read_csv_rows(loader.base_path / "raw_to_scaled" / domain / f"{age_group}.csv")
    if not rows:
        return ("-", "-", "-")

    values_by_scaled: dict[int, list[int]] = {}
    max_raw: int | None = None
    for row in rows:
        raw_value = row.get("raw_score")
        scaled_value = row.get(subtest_key)
        try:
            raw = int(float(str(raw_value).replace(",", ".")))
            scaled = int(float(str(scaled_value).replace(",", ".")))
        except (TypeError, ValueError):
            continue
        max_raw = raw if max_raw is None else max(max_raw, raw)
        values_by_scaled.setdefault(scaled, []).append(raw)

    def _format_range(scores: list[int]) -> str:
        if not scores:
            return "-"
        start = min(scores)
        end = max(scores)
        return str(start) if start == end else f"{start}-{end}"

    avg_values: list[int] = []
    for scaled in range(8, 13):
        avg_values.extend(values_by_scaled.get(scaled, []))

    return (
        str(max_raw) if max_raw is not None else "-",
        _format_range(avg_values),
        _format_range(values_by_scaled.get(5, [])),
    )


def _build_wais3_tables(payload: dict, evaluation, applied_on) -> dict:
    age_group = _wais3_age_group_for_application(evaluation, applied_on)
    loader = WAIS3NormLoader()
    subtests = payload.get("subtestes") or {}
    domains = {
        "linguagem": ["semelhancas", "vocabulario", "compreensao"],
        "gnosias_praxias": ["raciocinio_matricial", "cubos"],
        "funcoes_executivas": ["semelhancas", "compreensao", "raciocinio_matricial"],
        "memoria_aprendizagem": ["sequencia_numeros_letras", "digitos"],
    }
    tables = {}
    for domain, codes in domains.items():
        rows = []
        for code in codes:
            item = subtests.get(code)
            if not item:
                continue
            score_max, score_mid, score_min = _wais3_reference_scores(loader, age_group, code)
            classification = item.get("classificacao") or "-"
            raw_score = item.get("pontos_brutos")
            try:
                scaled_score = loader.get_scaled_score(code, int(raw_score), age_group) if age_group and raw_score not in (None, "") else None
            except (TypeError, ValueError):
                scaled_score = None
            if scaled_score is not None:
                classification = classify_scaled_score(scaled_score) or classification
            try:
                raw_score_int = int(raw_score) if raw_score not in (None, "") else None
            except (TypeError, ValueError):
                raw_score_int = None
            avg_range = _parse_score_range(score_mid)
            if raw_score_int is not None and avg_range and avg_range[0] <= raw_score_int <= avg_range[1]:
                classification = "Média"
            rows.append(
                {
                    "label": item.get("nome") or WAIS3_ALL_SUBTESTS.get(code) or code,
                    "maxScore": score_max,
                    "avgScore": score_mid,
                    "minScore": score_min,
                    "obtainedScore": _format_number(item.get("pontos_brutos")),
                    "classification": classification,
                }
            )
        if domain == "linguagem":
            rows.append(
                {
                    "label": "Fala Espontânea",
                    "note": "Fala espontânea dentro do esperado para a sua idade",
                }
            )
        elif domain == "memoria_aprendizagem":
            rows.append(
                {
                    "label": "RAVLT",
                    "maxScore": "-",
                    "avgScore": "-",
                    "minScore": "-",
                    "obtainedScore": "-",
                    "classification": "Leitura do Gráfico",
                }
            )
        tables[domain] = rows
    return tables


def build_result_rows(instrument_code: str, payload: dict) -> list[str]:
    if not payload:
        return []
    if instrument_code == "wisc4":
        return _build_wisc4_rows(payload)
    if instrument_code == "wais3":
        return _build_wais3_rows(payload)
    if instrument_code == "bpa2":
        return _build_bpa2_rows(payload)
    if instrument_code == "fdt":
        return _build_fdt_rows(payload)
    if instrument_code == "ravlt":
        return _build_ravlt_rows(payload)
    if instrument_code in {
        "etdah_ad",
        "etdah_pais",
        "ebadep_a",
        "ebaped_ij",
        "epq_j",
        "scared",
        "srs2",
    }:
        return _build_scale_rows(payload)
    return _extract_generic_rows(payload)


def build_validated_tests_snapshot(evaluation) -> list[dict]:
    tests = _select_report_applications(evaluation)
    snapshots: list[dict] = []

    for item in tests:
        if not _is_effectively_applied_test(item):
            continue
        warnings = []
        structured_results = item.classified_payload or item.computed_payload or {}
        clinical_interpretation = (item.interpretation_text or "").strip()

        module = get_test_module(item.instrument.code)
        report_payload = TestReportPayloadService.build_for_application(item)
        if module:
            try:
                context = TestContext(
                    patient_name=item.evaluation.patient.full_name,
                    evaluation_id=item.evaluation_id,
                    instrument_code=item.instrument.code,
                    raw_scores=item.raw_payload or {},
                )
                merged_data = {
                    **(item.computed_payload or {}),
                    **(item.classified_payload or {}),
                }
                recalculated = (module.interpret(context, merged_data) or "").strip()
                if recalculated:
                    clinical_interpretation = recalculated
            except Exception:
                warnings.append(
                    "Nao foi possivel recalcular a interpretacao tecnica atual; usando texto persistido."
                )

        summary = (
            (report_payload.get("summary_for_report") or "").strip()
            or (clinical_interpretation.split(". ")[0].strip() if clinical_interpretation else "")
        )
        if not clinical_interpretation:
            warnings.append(
                "Interpretacao clinica ausente; usando apenas payload estruturado."
            )

        result_rows = build_result_rows(item.instrument.code, structured_results)
        wisc_tables = (
            _build_wisc_tables(structured_results, item.evaluation, item.applied_on)
            if item.instrument.code == "wisc4"
            else {}
        )
        wais3_tables = (
            _build_wais3_tables(structured_results, item.evaluation, item.applied_on)
            if item.instrument.code == "wais3"
            else {}
        )
        bpa_chart_data = (
            _build_bpa2_chart_data(structured_results, item.evaluation, item.applied_on)
            if item.instrument.code == "bpa2"
            else {}
        )
        snapshots.append(
            {
                "id": item.id,
                "instrument": item.instrument.name,
                "instrument_code": item.instrument.code,
                "instrument_name": item.instrument.name,
                "domain": item.instrument.category or "geral",
                "report_section": SECTION_MAP.get(
                    item.instrument.code, "escalas_complementares"
                ),
                "applied_on": item.applied_on.isoformat() if item.applied_on else None,
                "is_validated": item.is_validated,
                "summary": summary,
                "structured_results": structured_results,
                "classified_payload": item.classified_payload or {},
                "computed_payload": item.computed_payload or {},
                "clinical_interpretation": clinical_interpretation,
                "interpretation_text": clinical_interpretation,
                "report_payload": report_payload,
                "result_rows": result_rows,
                "wisc_tables": wisc_tables,
                "wais3_tables": wais3_tables,
                "bpa_chart_data": bpa_chart_data,
                "warnings": warnings,
            }
        )

    return snapshots
