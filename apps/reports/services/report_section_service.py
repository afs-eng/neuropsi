from apps.reports.models import Report, ReportSection


class ReportSectionService:
    AI_FALLBACK_WARNING = "A IA nao esta disponivel no momento; a secao foi regenerada pelo fallback deterministico."

    @staticmethod
    def _is_wasi_report(report: Report) -> bool:
        context = getattr(report, "context_payload", None) or {}
        for item in context.get("validated_tests") or []:
            if item.get("instrument_code") == "wasi":
                return True
        return False

    @classmethod
    def _compose_report_markdown(cls, report: Report) -> str:
        blocks: list[str] = []
        inserted_wasi_subscales = False
        for item in report.sections.all():
            if cls._is_wasi_report(report) and item.key in {"linguagem", "gnosias_praxias"}:
                if not inserted_wasi_subscales:
                    blocks.append("### Subescalas WASI")
                    inserted_wasi_subscales = True
                if item.key == "linguagem":
                    blocks.append("#### Escala Verbal")
                elif item.key == "gnosias_praxias":
                    blocks.append("#### Escala de Execução")
            blocks.append(f"## {item.title}\n{item.content_edited or item.content_generated}")
        return "\n\n".join(blocks)

    @staticmethod
    def _rebuild_report_text(report: Report):
        report.edited_text = ReportSectionService._compose_report_markdown(report)
        report.save(update_fields=["edited_text", "updated_at"])

    @staticmethod
    def regenerate_section(report: Report, section_key: str, user=None):
        """
        Regenera o texto de uma única seção baseando-se no snapshot de contexto original do laudo.
        Cria uma nova entrada de histórico no ReportVersion se houver mudanças significativas.
        """
        from apps.reports.services.section_regeneration_service import (
            SectionRegenerationService,
        )

        return SectionRegenerationService.regenerate_section(
            report, section_key, user=user
        )

    @staticmethod
    def update_manual_content(section: ReportSection, new_content: str):
        """Atualiza o conteúdo editado pelo profissional"""
        section.content_edited = new_content
        section.save()
        report = section.report
        ReportSectionService._rebuild_report_text(report)
        return section
