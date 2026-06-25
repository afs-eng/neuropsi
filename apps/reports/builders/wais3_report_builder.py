from dataclasses import dataclass, field
from typing import Callable


@dataclass
class _TestSection:
    title: str
    table_caption: str | None
    table_key: str
    chart_caption: str | None
    interpretation_section: str | None
    builder_fn: Callable | None = None


@dataclass
class _SubtestBlock:
    title: str
    table_caption: str | None
    table_key: str
    interpretation_section: str
    rows_fn: Callable


@dataclass
class WAIS3ReportBuilder:
    sections: list[_TestSection] = field(default_factory=list)
    subtest_blocks: list[_SubtestBlock] = field(default_factory=list)

    @classmethod
    def for_adolescent(cls, available: set[str]) -> "WAIS3ReportBuilder":
        builder = cls()
        builder.subtest_blocks = [
            _SubtestBlock(
                title="Função Executiva",
                table_caption="Resultado da Função executiva",
                table_key="wais_funcoes_executivas",
                interpretation_section="funcoes_executivas",
                rows_fn=None,
            ),
            _SubtestBlock(
                title="Linguagem",
                table_caption="Resultados da Linguagem",
                table_key="wais_linguagem",
                interpretation_section="linguagem",
                rows_fn=None,
            ),
            _SubtestBlock(
                title="Gnosias e Praxias",
                table_caption="Resultados da Gnosias e praxias",
                table_key="wais_gnosias",
                interpretation_section="gnosias_praxias",
                rows_fn=None,
            ),
            _SubtestBlock(
                title="Memória e Aprendizagem",
                table_caption="Resultados de Memória e Aprendizagem",
                table_key="wais_memoria",
                interpretation_section="memoria_aprendizagem",
                rows_fn=None,
            ),
        ]

        if "bpa2" in available:
            builder.sections.append(
                _TestSection(
                    title="BPA-2 – BATERIA PSICOLÓGICA PARA AVALIAÇÃO DA ATENÇÃO",
                    table_caption="Atenção BPA-2 Resultados",
                    table_key="bpa",
                    chart_caption="BPA-2 Resultados da Avaliação da Atenção",
                    interpretation_section="bpa2",
                )
            )
        if "ravlt" in available:
            builder.sections.append(
                _TestSection(
                    title="RAVLT – REY AUDITORY VERBAL LEARNING TEST",
                    table_caption=None,
                    table_key="ravlt",
                    chart_caption="RAVLT Resultados",
                    interpretation_section="memoria_aprendizagem",
                )
            )
        if "fdt" in available:
            builder.sections.append(
                _TestSection(
                    title="FDT – TESTE DOS CINCO DÍGITOS",
                    table_caption="FDT Processos Automáticos e Controlados",
                    table_key="fdt",
                    chart_caption="FDT Processos Automáticos",
                    interpretation_section="funcoes_executivas",
                )
            )
        if "etdah_ad" in available:
            builder.sections.append(
                _TestSection(
                    title="E--TDAH-AD",
                    table_caption="ETDAH-AD RESULTADO",
                    table_key="etdah_ad",
                    chart_caption="E-TDAH-AD RESULTADO",
                    interpretation_section="etdah_ad",
                )
            )
        if "scared" in available:
            builder.sections.append(
                _TestSection(
                    title="SCARED",
                    table_caption=None,
                    table_key=None,
                    chart_caption=None,
                    interpretation_section=None,
                )
            )
        if "bfp" in available:
            builder.sections.append(
                _TestSection(
                    title="BFP – BATERIA FATORIAL DE PERSONALIDADE",
                    table_caption="BFP Resultados dos fatores",
                    table_key="bfp",
                    chart_caption=None,
                    interpretation_section="aspectos_emocionais_comportamentais",
                )
            )
        if "srs2" in available:
            builder.sections.append(
                _TestSection(
                    title="SRS-2 – ESCALA DE RESPONSIVIDADE SOCIAL",
                    table_caption="SRS-2 Resultados",
                    table_key="srs2",
                    chart_caption="SRS-2 Resultados",
                    interpretation_section=None,
                )
            )
        return builder

    @classmethod
    def for_adult(cls, available: set[str]) -> "WAIS3ReportBuilder":
        builder = cls()
        builder.subtest_blocks = [
            _SubtestBlock(
                title="Linguagem",
                table_caption="Resultado da escala Linguagem",
                table_key="wais_linguagem",
                interpretation_section="linguagem",
                rows_fn=None,
            ),
            _SubtestBlock(
                title="Gnosias e Praxias",
                table_caption="Resultados da escala Gnosias e praxias",
                table_key="wais_gnosias",
                interpretation_section="gnosias_praxias",
                rows_fn=None,
            ),
            _SubtestBlock(
                title="Função Executiva",
                table_caption="Resultados da escala Função Executiva",
                table_key="wais_funcoes_executivas",
                interpretation_section="funcoes_executivas",
                rows_fn=None,
            ),
            _SubtestBlock(
                title="Memória e Aprendizagem",
                table_caption="Resultados da escala Memória e Aprendizagem",
                table_key="wais_memoria",
                interpretation_section="memoria_aprendizagem",
                rows_fn=None,
            ),
        ]

        if "bpa2" in available:
            builder.sections.append(
                _TestSection(
                    title="BPA-2 Bateria Psicológica para Avaliação da Atenção",
                    table_caption="Atenção BPA-2 Resultados",
                    table_key="bpa",
                    chart_caption="BPA-2 apresenta os resultados da avaliação da atenção",
                    interpretation_section="bpa2",
                )
            )
        if "ravlt" in available:
            builder.sections.append(
                _TestSection(
                    title="RAVLT Rey Auditory Verbal Learning Test",
                    table_caption=None,
                    table_key="ravlt",
                    chart_caption="RAVLT Resultados",
                    interpretation_section="memoria_aprendizagem",
                )
            )
        if "fdt" in available:
            builder.sections.append(
                _TestSection(
                    title="FDT- TESTE DOS CINCO DÍGITOS",
                    table_caption="FDT Processos Automáticos e Controlados",
                    table_key="fdt",
                    chart_caption="FDT Processos Automáticos",
                    interpretation_section="funcoes_executivas",
                )
            )
        if "etdah_ad" in available:
            builder.sections.append(
                _TestSection(
                    title="ETDAH-AD",
                    table_caption="ETDAH-AD RESULTADO",
                    table_key="etdah_ad",
                    chart_caption="E-TDAH-AD RESULTADO",
                    interpretation_section="etdah_ad",
                )
            )
        if "iphexa" in available:
            builder.sections.append(
                _TestSection(
                    title="iphexa Inventário de Personalidade Hexadimensional",
                    table_caption=None,
                    table_key=None,
                    chart_caption=None,
                    interpretation_section="aspectos_emocionais_comportamentais",
                )
            )
        if "ebadep_a" in available or "ebadep_ij" in available or "ebaped_ij" in available:
            builder.sections.append(
                _TestSection(
                    title="EBADEP-A",
                    table_caption="EBADEP-A - Resultado da sintomatologia",
                    table_key="scale_summary",
                    chart_caption=None,
                    interpretation_section="aspectos_emocionais_comportamentais",
                )
            )
        if "bfp" in available:
            builder.sections.append(
                _TestSection(
                    title="BFP – Bateria Fatorial de Personalidade",
                    table_caption="BFP Resultados dos fatores",
                    table_key="bfp",
                    chart_caption=None,
                    interpretation_section="aspectos_emocionais_comportamentais",
                )
            )
        if "scared" in available:
            builder.sections.append(
                _TestSection(
                    title="SCARED",
                    table_caption=None,
                    table_key=None,
                    chart_caption=None,
                    interpretation_section=None,
                )
            )
        if "srs2" in available:
            builder.sections.append(
                _TestSection(
                    title="SRS-2 Escala de Responsividade Social",
                    table_caption="SRS-2 Resultados dos fatores",
                    table_key="srs2",
                    chart_caption="SRS-2 Resultados da discrepância entre respondentes",
                    interpretation_section=None,
                )
            )
        return builder
