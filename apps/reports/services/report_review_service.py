from __future__ import annotations


class ReportReviewService:
    @staticmethod
    def review(report) -> dict:
        sections = list(report.sections.all())
        findings: list[str] = []
        warnings: list[str] = []

        if not sections:
            warnings.append("Laudo sem seções geradas.")
            return {
                "status": "needs_attention",
                "findings": findings,
                "warnings": warnings,
                "missing_sections": [],
                "section_count": 0,
            }

        missing_sections = []
        for section in sections:
            if (section.generation_metadata or {}).get("stale"):
                warnings.append(f"Seção desatualizada: {section.title}.")
            text = (section.content_edited or section.content_generated or "").strip()
            if not text:
                missing_sections.append(section.key)
                warnings.append(f"Seção vazia: {section.title}.")
            for item in section.warnings_payload or []:
                warnings.append(f"{section.title}: {item}")

        conclusion = next((s for s in sections if s.key == "conclusao"), None)
        hypothesis = next(
            (s for s in sections if s.key == "hipotese_diagnostica"), None
        )

        if conclusion and hypothesis:
            conclusion_text = (
                conclusion.content_edited or conclusion.content_generated or ""
            ).lower()
            hypothesis_text = (
                hypothesis.content_edited or hypothesis.content_generated or ""
            ).lower()
            if "hipótese" in conclusion_text and "hipótese" not in hypothesis_text:
                findings.append(
                    "Conclusão menciona hipótese clínica sem seção correspondente clara."
                )
            if (
                "não deve ser interpretada isoladamente" in conclusion_text
                and "isoladamente" not in hypothesis_text
            ):
                warnings.append(
                    "Conclusão destaca interpretação integrada, mas a hipótese diagnóstica não reforça esse limite."
                )

        if report.ai_metadata.get("mode") == "deterministic" and len(sections) > 10:
            warnings.append(
                "Laudo gerado sem IA em um caso com bastante conteúdo clínico consolidado."
            )

        status = "ok"
        if missing_sections or findings:
            status = "needs_attention"
        elif warnings:
            status = "reviewed_with_warnings"

        return {
            "status": status,
            "findings": findings,
            "warnings": warnings,
            "missing_sections": missing_sections,
            "section_count": len(sections),
        }
