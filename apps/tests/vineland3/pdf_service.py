from pathlib import Path

from django.template import engines

from apps.tests.services.playwright_pdf_service import generate_pdf_from_html

from .domain_protocol import DOMAIN_ITEMS, PROTOCOL_ID, build_item_summary
from .norms import age_months
from .domain_scoring import results_for_application
from .review import review_state
from .domain_totals import totals_summary


class Vineland3PdfService:
    TEMPLATE_PATH = Path(__file__).parent / "templates" / "tests" / "pdf" / "vineland3_report.html"
    ABBREVIATIONS = {"comunicacao": "COM", "vida_diaria": "AVD", "socializacao": "SOC", "atividade_fisica": "HMOT"}
    ADAPTIVE_LABELS = {"comunicacao": "Comunicação", "vida_diaria": "Atividades de Vida Diária",
                       "socializacao": "Socialização", "atividade_fisica": "Habilidades Motoras"}

    @classmethod
    def generate_pdf_bytes(cls, application):
        return generate_pdf_from_html(cls.render_html(application))

    @classmethod
    def render_html(cls, application):
        context = cls._build_context(application)
        context["header_template"] = engines["django"].from_string(
            cls.TEMPLATE_PATH.with_name("header.html").read_text(encoding="utf-8")
        ).template
        template = engines["django"].from_string(cls.TEMPLATE_PATH.read_text(encoding="utf-8"))
        return template.render(context)

    @classmethod
    def _build_context(cls, application):
        raw = application.raw_payload or {}
        totals = raw.get("entry_mode") == "totals" and raw.get("form_level") == "niveis_dominio"
        if (application.instrument.code != "vineland3" or not totals and (raw.get("entry_mode") != "items"
                or raw.get("item_protocol_id") != PROTOCOL_ID)):
            raise ValueError("Este PDF é exclusivo dos Níveis de Domínio: questionário Pais/Cuidadores ou totais do protocolo.")
        if raw.get("completion_status") != "finalized":
            raise ValueError("Finalize o questionário Vineland antes de gerar o PDF.")
        # Rebuild from the recorded answers; never export a stale cached summary.
        normative = results_for_application(application)
        summary = totals_summary(normative) if totals else build_item_summary(raw.get("item_responses"))
        evaluation = application.evaluation
        patient = evaluation.patient
        applied = application.applied_on
        birth = patient.birth_date
        months = age_months({"birth_date": birth.isoformat() if birth else None,
                             "reference_date": applied.isoformat() if applied else None})
        examiner = evaluation.examiner
        professional = (examiner.full_name or examiner.get_full_name() or examiner.username) if examiner else "Não informado"
        if examiner and examiner.crp:
            professional = f"{professional} · CRP {examiner.crp}"
        adaptive = []
        behavior = []
        for section in summary["sections"]:
            row = {**section, "score_label": section["raw_score"] if section["raw_score"] is not None else "—"}
            result = next((r for r in normative["adaptive"] + normative["behavior"] if r["code"] == section["code"]), {})
            row.update(result)
            row["ci_label"] = " – ".join(map(str, result["confidence_interval"])) if result.get("confidence_interval") else "—"
            if section["kind"] == "adaptive":
                row.update(abbreviation=cls.ABBREVIATIONS[section["code"]],
                           display_label=cls.ADAPTIVE_LABELS[section["code"]],
                           bar_width=(result.get("standard_score") or 0) / 160 * 100)
                adaptive.append(row)
            elif section["kind"] == "behavior":
                row["short_label"] = "Internalizante (A)" if section["code"] == "comportamento_a" else "Externalizante (B)"
                behavior.append(row)
        critical = next((section for section in summary["sections"] if section["kind"] == "critical"), {"applied": False})
        critical_responses = (raw.get("item_responses") or {}).get("comportamento_c", {})
        critical_rows = [{"id": str(index), "text": text,
                          "response": critical_responses.get(str(index), {}).get("response", "") or "—",
                          "flagged": critical_responses.get(str(index), {}).get("response") in {"1", "2"}}
                         for index, text in enumerate(DOMAIN_ITEMS["comportamento_c"][1], 1)]
        cca = {**normative["cca"], "abbreviation": "CCA", "display_label": "Composto Adaptativo (CCA)",
               "score_label": "—", "bar_width": (normative["cca"]["standard_score"] or 0) / 160 * 100,
               "ci_label": " – ".join(map(str, normative["cca"]["confidence_interval"])) if normative["cca"]["confidence_interval"] else "—"}
        normative_rows = adaptive[:3] + [cca] + adaptive[3:]
        for index, row in enumerate(normative_rows):
            row["plot_x"] = 80 + index * 75
            if row["standard_score"] is not None:
                row["plot_y"] = 300 - (row["standard_score"] - 20) * 2
                interval = row["confidence_interval"] or [row["standard_score"]] * 2
                row["plot_low"] = 300 - (interval[0] - 20) * 2
                row["plot_high"] = 300 - (interval[1] - 20) * 2
        return {
            "name": patient.full_name,
            "entry_mode": "totals" if totals else "items",
            "form_label": normative.get("form_label", "Pais/Cuidadores — Níveis de Domínio"),
            "table_codes": normative.get("table_codes", "C.3, C.4, C.5 e E.2"),
            "appendix": {"entrevista": "B", "professores": "D"}.get(raw.get("form"), "C"),
            "behavior_table": {"entrevista": "E.1", "professores": "E.3"}.get(raw.get("form"), "E.2"),
            "sex": {"M": "Masculino", "F": "Feminino", "O": "Outro"}.get(patient.sex, patient.sex or "Não informado"),
            "schooling": patient.get_schooling_display() or "Não informado",
            "age": f"{months // 12} anos e {months % 12} meses",
            "birth_date": birth.strftime("%d/%m/%Y"),
            "applied_on": applied.strftime("%d/%m/%Y"),
            "professional": professional, "respondent": raw.get("respondent") or "Não informado",
            "application_code": f"AVL-{application.pk:03d}",
            "report_code": f"RPT-VINELAND3-{application.pk:03d}",
            "adaptive": adaptive, "behavior": behavior, "summary": summary,
            "normative": normative, "normative_rows": normative_rows,
            "clinical_review": review_state(application, normative),
            "plot_ticks": [{"value": s, "y": 300 - (s - 20) * 2} for s in range(20, 161, 20)],
            "critical_applied": critical["applied"], "critical_rows": critical_rows,
            "observations": raw.get("general_observations") or "Nenhuma observação geral registrada.",
            "pairs": [("COM", "AVD"), ("COM", "SOC"), ("AVD", "SOC"), ("COM", "HMOT"), ("AVD", "HMOT"), ("SOC", "HMOT")],
        }
