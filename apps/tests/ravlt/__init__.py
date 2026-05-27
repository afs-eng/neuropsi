from apps.tests.base.types import BaseTestModule, TestContext
from apps.tests.registry import register_test_module
from .config import (
    RAVLT_CODE,
    RAVLT_NAME,
    RAVLT_TRIAL_FIELDS,
    RAVLT_MAX_SCORES,
)
from .norms import (
    NORMS,
    get_age_band,
    safe_div,
    compute_recognition_score,
    z_score,
    calc_weighted_score,
    percentile_from_z,
    classify_by_percentile,
)
from .pdf_service import RAVLTPdfService
from datetime import date


RAVLT_CHART_LABELS = [
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "B1",
    "A6",
    "A7",
    "R",
    "ALT",
    "RET",
    "I.P.",
    "I.R.",
]

RAVLT_CHART_NORM_KEYS = {
    "A1": "A1",
    "A2": "A2",
    "A3": "A3",
    "A4": "A4",
    "A5": "A5",
    "B1": "B1",
    "A6": "A6",
    "A7": "A7",
    "R": "Reconhecimento Lista A",
    "ALT": "Aprend. longo das Tentativas",
    "RET": "Velocidade de Esquecimento",
    "I.P.": "Interferência Proativa",
    "I.R.": "Interferência Retroativa",
}


def _first_name(name: str) -> str:
    return (name or "Paciente").split(" ", 1)[0]


def _format_score(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}".replace(".", ",")
    return str(value)


def _result_map(merged_data: dict) -> dict:
    return {item.get("variavel"): item for item in merged_data.get("resultados", [])}


def _ravlt_obtained_chart_values(computed_data: dict) -> list[float]:
    return [
        float(computed_data.get("a1", {}).get("escore") or 0),
        float(computed_data.get("a2", {}).get("escore") or 0),
        float(computed_data.get("a3", {}).get("escore") or 0),
        float(computed_data.get("a4", {}).get("escore") or 0),
        float(computed_data.get("a5", {}).get("escore") or 0),
        float(computed_data.get("b", {}).get("escore") or 0),
        float(computed_data.get("a6", {}).get("escore") or 0),
        float(computed_data.get("a7", {}).get("escore") or 0),
        float(computed_data.get("reconhecimento", {}).get("escore") or 0),
        float(computed_data.get("aprend_longo", {}).get("escore") or 0),
        float(computed_data.get("velocidade_esquecimento", {}).get("escore") or 0),
        float(computed_data.get("interferencia_proativa", {}).get("escore") or 0),
        float(computed_data.get("interferencia_retroativa", {}).get("escore") or 0),
    ]


def _build_ravlt_chart_payload(computed_data: dict, band: str) -> dict:
    norms = NORMS.get(band, NORMS["21-30"])
    esperado = []
    minimo = []

    for label in RAVLT_CHART_LABELS:
        norm = norms.get(RAVLT_CHART_NORM_KEYS[label])
        esperado.append(float(norm.p50) if norm else 0.0)
        minimo.append(float(norm.p25) if norm else 0.0)

    return {
        "title": "RAVLT - Quantidade de palavras evocadas",
        "labels": RAVLT_CHART_LABELS,
        "series": [
            {"key": "esperado", "label": "Esperado", "color": "#ED7D31", "values": esperado},
            {"key": "minimo", "label": "Mínimo", "color": "#FFC000", "values": minimo},
            {"key": "obtido", "label": "Obtido", "color": "#70AD47", "values": _ravlt_obtained_chart_values(computed_data)},
        ],
        "y_axis": {"min": 0, "max": 21, "ticks": [0, 5, 10, 15, 20]},
    }


def _expected_phrase(classification: str) -> str:
    if classification in {"Muito Superior", "Superior"}:
        return "acima do esperado"
    if classification == "Média Superior":
        return "dentro do esperado em nível alto"
    if classification == "Média":
        return "dentro do esperado"
    if classification == "Média Inferior":
        return "no limite inferior da faixa normativa"
    return "abaixo do esperado"


def _global_memory_phrase(classification: str) -> str:
    if classification in {"Muito Superior", "Superior"}:
        return "superior"
    if classification == "Média Superior":
        return "acima da média"
    if classification == "Média":
        return "adequado"
    if classification == "Média Inferior":
        return "no limite inferior da média"
    return "rebaixado"


def _learning_curve_phrase(a1: int, a2: int, a3: int, a4: int, a5: int) -> str:
    gains = sum(1 for earlier, later in ((a1, a2), (a2, a3), (a3, a4), (a4, a5)) if later >= earlier)
    total_gain = a5 - a1
    if gains >= 3 and total_gain >= 4:
        return "com curva de aprendizagem ascendente, ganho progressivo ao longo das tentativas"
    if gains >= 2 and total_gain >= 2:
        return "com curva de aprendizagem progressiva, com ganho ao longo das tentativas"
    return "com curva de aprendizagem pouco consistente, sem ganho expressivo ao longo das tentativas"


def _acquisition_phrase(classification: str) -> str:
    if classification in {"Muito Superior", "Superior", "Média Superior"}:
        return "indicando boa capacidade de codificação e aproveitamento da repetição"
    if classification == "Média":
        return "indicando capacidade adequada de codificação e aproveitamento da repetição"
    return "sugerindo menor eficiência de codificação e menor aproveitamento da repetição"


def _efficiency_phrase(classification: str) -> str:
    if classification in {"Muito Superior", "Superior", "Média Superior"}:
        return "e boa eficiência nos processos de aquisição, retenção e evocação do material verbal"
    if classification == "Média":
        return "e eficiência adequada nos processos de aquisição, retenção e evocação do material verbal"
    return "com oscilações nos processos de aquisição, retenção e evocação do material verbal"


def _consolidation_phrase(classification: str) -> str:
    if classification in {"Muito Superior", "Superior", "Média Superior", "Média"}:
        return "evidenciando boa consolidação e recuperação espontânea do conteúdo aprendido"
    return "sugerindo fragilidade na consolidação e/ou na recuperação espontânea do conteúdo aprendido"


def _storage_phrase(classification: str) -> str:
    if classification in {"Muito Superior", "Superior", "Média Superior", "Média"}:
        return "reforçando armazenamento eficiente do material verbal"
    return "sugerindo menor eficiência no armazenamento do material verbal"


def _clinical_summary(name: str, alt_class: str, a7_class: str, r_class: str, ip_class: str) -> str:
    preserved = {"Média", "Média Superior", "Superior", "Muito Superior"}
    high = {"Média Superior", "Superior", "Muito Superior"}

    if alt_class in high and a7_class in preserved and r_class in preserved:
        summary = (
            f"Em análise clínica, os resultados indicam que {name} apresenta memória auditivo-verbal preservada e qualitativamente fortalecida, "
            "com bom desempenho em aprendizagem progressiva, evocação imediata, evocação tardia e reconhecimento."
        )
    elif alt_class in preserved and a7_class in preserved and r_class in preserved:
        summary = (
            f"Em análise clínica, os resultados indicam que {name} apresenta memória auditivo-verbal preservada, "
            "com desempenho compatível com o esperado em aprendizagem progressiva, evocação tardia e reconhecimento."
        )
    else:
        summary = (
            f"Em análise clínica, os resultados indicam que {name} apresenta oscilação no desempenho da memória auditivo-verbal, "
            "com fragilidades em parte dos processos de aprendizagem, retenção e/ou recuperação do material verbal."
        )

    if ip_class == "Média Inferior":
        return summary + " O único ponto de atenção refere-se a uma leve suscetibilidade à interferência proativa, sem repercussão significativa sobre o desempenho global do teste."
    if ip_class in {"Inferior", "Muito Inferior"}:
        return summary + " Destaca-se, contudo, suscetibilidade aumentada à interferência proativa, o que pode dificultar a aquisição de novas informações diante de conteúdos previamente aprendidos."
    return summary


class RAVLTModule(BaseTestModule):
    code = RAVLT_CODE
    name = RAVLT_NAME

    def validate(self, context: TestContext) -> list[str]:
        errors = []

        for field, label in RAVLT_TRIAL_FIELDS.items():
            valor = context.raw_scores.get(field)
            if valor is None:
                errors.append(f"'{label}' não informado")
            elif valor < 0:
                errors.append(f"{label}: escore não pode ser negativo")
            elif valor > RAVLT_MAX_SCORES.get(field, 15):
                errors.append(
                    f"{label}: escore ({valor}) maior que o máximo ({RAVLT_MAX_SCORES.get(field, 15)})"
                )

        reconhecimento = context.raw_scores.get("reconhecimento", 0)
        if reconhecimento is not None and (reconhecimento < 0 or reconhecimento > 50):
            errors.append("Reconhecimento deve estar entre 0 e 50")

        return errors

    def compute(self, context: TestContext) -> dict:
        a1 = context.raw_scores.get("a1", 0)
        a2 = context.raw_scores.get("a2", 0)
        a3 = context.raw_scores.get("a3", 0)
        a4 = context.raw_scores.get("a4", 0)
        a5 = context.raw_scores.get("a5", 0)
        b = context.raw_scores.get("b", 0)
        a6 = context.raw_scores.get("a6", 0)
        a7 = context.raw_scores.get("a7", 0)
        reconhecimento = context.raw_scores.get("reconhecimento", 0)

        rec_lista_a = compute_recognition_score(reconhecimento)
        escore_total = a1 + a2 + a3 + a4 + a5
        alt = escore_total - (5 * a1)
        ve = safe_div(a7, a6) if a6 else None
        ip = safe_div(b, a1) if a1 else None
        ir = safe_div(a6, a5) if a5 else None

        results = {}
        for field, label in RAVLT_TRIAL_FIELDS.items():
            valor = context.raw_scores.get(field, 0)
            results[field] = {
                "campo": label,
                "escore": valor,
                "max": RAVLT_MAX_SCORES.get(field, 15),
            }

        results["reconhecimento"] = {
            "campo": "Reconhecimento Lista A",
            "escore": rec_lista_a,
            "max": 15,
        }
        results["escore_total"] = {
            "campo": "Escore Total",
            "escore": escore_total,
            "max": 75,
        }
        results["aprend_longo"] = {
            "campo": "Aprend. longo das Tentativas",
            "escore": alt,
            "max": 60,
        }
        results["velocidade_esquecimento"] = {
            "campo": "Velocidade de Esquecimento",
            "escore": ve,
        }
        results["interferencia_proativa"] = {
            "campo": "Interferência Proativa",
            "escore": ip,
        }
        results["interferencia_retroativa"] = {
            "campo": "Interferência Retroativa",
            "escore": ir,
        }

        return results

    def classify(self, computed_data: dict, idade: int = 25) -> dict:
        try:
            band = get_age_band(idade)
        except ValueError:
            band = "21-30"

        norms = NORMS.get(band, NORMS["21-30"])

        results = []
        for var_name in [
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "B1",
            "A6",
            "A7",
            "Reconhecimento Lista A",
            "Escore Total",
            "Aprend. longo das Tentativas",
            "Velocidade de Esquecimento",
            "Interferência Proativa",
            "Interferência Retroativa",
        ]:
            raw = None
            key_map = {
                "A1": "a1",
                "A2": "a2",
                "A3": "a3",
                "A4": "a4",
                "A5": "a5",
                "B1": "b",
                "A6": "a6",
                "A7": "a7",
            }
            if var_name in key_map:
                raw = computed_data.get(key_map[var_name], {}).get("escore", 0)
            elif var_name == "Reconhecimento Lista A":
                raw = computed_data.get("reconhecimento", {}).get("escore", 0)
            elif var_name == "Escore Total":
                raw = computed_data.get("escore_total", {}).get("escore", 0)
            elif var_name == "Aprend. longo das Tentativas":
                raw = computed_data.get("aprend_longo", {}).get("escore", 0)
            elif var_name == "Velocidade de Esquecimento":
                raw = computed_data.get("velocidade_esquecimento", {}).get("escore")
            elif var_name == "Interferência Proativa":
                raw = computed_data.get("interferencia_proativa", {}).get("escore")
            elif var_name == "Interferência Retroativa":
                raw = computed_data.get("interferencia_retroativa", {}).get("escore")

            norm = norms.get(var_name)
            z = z_score(raw, norm.mean, norm.sd) if norm and raw is not None else None
            weighted = calc_weighted_score(z)
            percentile = percentile_from_z(z)
            classification = classify_by_percentile(percentile)

            results.append(
                {
                    "variavel": var_name,
                    "bruto": raw,
                    "media": norm.mean if norm else None,
                    "dp": norm.sd if norm else None,
                    "z": z,
                    "ponderado": weighted,
                    "percentil": percentile,
                    "classificacao": classification,
                }
            )

        return {
            "faixa_etaria": band,
            "idade": idade,
            "resultados": results,
            "chart": _build_ravlt_chart_payload(computed_data, band),
        }

    def interpret(self, context: TestContext, merged_data: dict) -> str:
        result_map = _result_map(merged_data)
        if not result_map:
            return "Sem resultados para interpretação."

        raw_payload = {
            "a1": merged_data.get("a1", {}).get("escore"),
            "a2": merged_data.get("a2", {}).get("escore"),
            "a3": merged_data.get("a3", {}).get("escore"),
            "a4": merged_data.get("a4", {}).get("escore"),
            "a5": merged_data.get("a5", {}).get("escore"),
            "b": merged_data.get("b", {}).get("escore"),
            "a6": merged_data.get("a6", {}).get("escore"),
            "a7": merged_data.get("a7", {}).get("escore"),
            "reconhecimento": merged_data.get("reconhecimento", {}).get("escore"),
        }
        paragraphs = RAVLTPdfService._clinical_paragraphs(context.patient_name, raw_payload, result_map)
        summary = RAVLTPdfService._summary_for_report(context.patient_name, raw_payload, result_map)
        return "\n\n".join([*paragraphs, summary])

    def build_report_payload(self, context: TestContext, merged_data: dict) -> dict:
        resultados = merged_data.get("resultados") or []
        faixa = merged_data.get("faixa_etaria") or "21-30"
        interpretation = self.interpret(context, merged_data)
        raw_payload = {
            "a1": merged_data.get("a1", {}).get("escore"),
            "a2": merged_data.get("a2", {}).get("escore"),
            "a3": merged_data.get("a3", {}).get("escore"),
            "a4": merged_data.get("a4", {}).get("escore"),
            "a5": merged_data.get("a5", {}).get("escore"),
            "b": merged_data.get("b", {}).get("escore"),
            "a6": merged_data.get("a6", {}).get("escore"),
            "a7": merged_data.get("a7", {}).get("escore"),
            "reconhecimento": merged_data.get("reconhecimento", {}).get("escore"),
        }
        result_map = _result_map(merged_data)
        return {
            "results": [
                {
                    "scale": item.get("variavel"),
                    "raw_score": item.get("bruto"),
                    "percentile": item.get("percentil"),
                    "classification": item.get("classificacao"),
                }
                for item in resultados
            ],
            "summary_for_report": RAVLTPdfService._summary_for_report(context.patient_name, raw_payload, result_map),
            "technical_notes": [f"Faixa etária normativa: {faixa}"],
            "clinical_flags": [
                item.get("variavel")
                for item in resultados
                if item.get("classificacao") in {"Inferior", "Muito Inferior", "Limítrofe"}
            ],
            "chart_payload": merged_data.get("chart") or {},
            "interpretation": interpretation,
        }


register_test_module(RAVLT_CODE, RAVLTModule())
