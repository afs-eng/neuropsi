from __future__ import annotations

import html
import json
import math
import re
from datetime import date
from pathlib import Path

from apps.tests.services.playwright_pdf_service import generate_pdf_from_html
from apps.tests.srs2.config import SRS2_FORMS, SRS2_GENDERS


class SRS2PdfService:
    TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tests" / "pdf" / "neuroavalia_srs2_relatorio_resumido.html"
    COMPLETE_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "tests" / "pdf" / "neuroavalia_srs2_relatorio_completo.html"
    LOGO_TEMPLATE_PATH = Path(__file__).resolve().parents[3] / "templates" / "neuroavalia-logo.html"
    NORM_LABELS = {
        "pre_escola": "Pré-Escolar",
        "idade_escolar": "Idade Escolar",
        "adulto_autorrelato": "Adulto Autorrelato",
        "adulto_heterorrelato": "Adulto Heterorrelato",
    }
    SCORE_ORDER = [
        "percepção_social",
        "cognição_social",
        "comunicação_social",
        "motivação_social",
        "padrões_restritos",
        "cis",
        "total",
    ]

    @staticmethod
    def _format_sex(value: str | None) -> str:
        if value == "M":
            return "Masculino"
        if value == "F":
            return "Feminino"
        return value or "Não informado"

    @classmethod
    def _normative_table_label(cls, form: str, gender: str | None) -> str:
        form_label = cls.NORM_LABELS.get(form, SRS2_FORMS.get(form, str(form).replace("_", " ").title()))
        parts = [form_label]
        if form == "idade_escolar":
            parts.append(SRS2_GENDERS.get(str(gender or "").upper(), "Sexo não informado"))
        return " · ".join(part for part in parts if part)

    @staticmethod
    def _format_schooling(value: str | None) -> str:
        labels = {
            "preschool": "Ensino pré-escolar",
            "elementary": "Ensino fundamental",
            "elementary_incomplete": "Ensino fundamental incompleto",
            "elementary_complete": "Ensino fundamental completo",
            "middle": "Ensino médio",
            "middle_incomplete": "Ensino médio incompleto",
            "middle_complete": "Ensino médio completo",
            "higher_incomplete": "Ensino superior incompleto",
            "higher": "Ensino superior",
            "higher_complete": "Ensino superior completo",
            "postgraduate": "Pós-graduação",
        }
        if not value:
            return "Não informado"
        return labels.get(str(value), str(value).replace("_", " ").strip().title())

    @staticmethod
    def _format_person_name(value: str | None) -> str:
        if not value:
            return "Paciente"
        particles = {"da", "de", "do", "das", "dos", "e"}
        words = []
        for index, word in enumerate(str(value).strip().split()):
            lower = word.lower()
            words.append(lower if index > 0 and lower in particles else lower.capitalize())
        return " ".join(words) or "Paciente"

    @classmethod
    def _replace_logo(cls, source: str) -> str:
        logo_source = cls.LOGO_TEMPLATE_PATH.read_text(encoding="utf-8")
        match = re.search(r"<svg\b.*?</svg>", logo_source, flags=re.S)
        if not match:
            return source
        logo_svg = re.sub(r"<svg\b", '<svg class="brand-logo"', match.group(0), count=1)
        return re.sub(r'<img\s+class="brand-logo"[^>]*>', logo_svg, source)

    @staticmethod
    def _patient_age(application) -> int | None:
        patient = getattr(getattr(application, "evaluation", None), "patient", None)
        explicit_age = getattr(patient, "age", None)
        if explicit_age is not None:
            return explicit_age

        raw_age = (getattr(application, "raw_payload", None) or {}).get("age")
        if raw_age:
            try:
                return int(raw_age)
            except (TypeError, ValueError):
                pass

        birth_date = getattr(patient, "birth_date", None)
        if not birth_date:
            return None

        reference_date = getattr(application, "applied_on", None) or date.today()
        years = reference_date.year - birth_date.year
        if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
            years -= 1
        return max(years, 0)

    @classmethod
    def _ordered_results(cls, application) -> list[dict]:
        classified = getattr(application, "classified_payload", None) or {}
        rows = classified.get("resultados") or []
        by_key = {row.get("variável"): row for row in rows if isinstance(row, dict)}
        return [by_key[key] for key in cls.SCORE_ORDER if key in by_key]

    @staticmethod
    def _display_name(row: dict) -> str:
        if row.get("variável") == "total":
            return "Escore Total"
        return row.get("nome") or row.get("variável") or "Escala"

    @classmethod
    def _profile_display_name(cls, row: dict) -> str:
        labels = {
            "padroes_restritos": "Padrões Rest. e Repet.",
            "padrões_restritos": "Padrões Rest. e Repet.",
            "cis": "Comunic. e Interação Social",
        }
        return labels.get(row.get("variável"), cls._display_name(row))

    @staticmethod
    def _ci_for_tscore(tscore) -> list[int]:
        try:
            tscore_value = int(round(float(tscore)))
        except (TypeError, ValueError):
            return [0, 0]
        return [max(20, tscore_value - 4), min(80, tscore_value + 4)]

    @classmethod
    def _scales_script(cls, rows: list[dict]) -> str:
        if not rows:
            rows = [
                {
                    "variável": "total",
                    "nome": "Escore Total",
                    "bruto": 0,
                    "tscore": 50,
                    "classificação": "Dentro dos limites normais",
                }
            ]
        scales = [
            {
                "name": cls._display_name(row),
                "raw": row.get("bruto") or 0,
                "t": row.get("tscore") or 0,
                "ci": cls._ci_for_tscore(row.get("tscore")),
            }
            for row in rows
        ]
        return f"const scales = {json.dumps(scales, ensure_ascii=False)};"

    @staticmethod
    def _paragraphs_html(text: str) -> str:
        paragraphs = [part.strip() for part in (text or "").split("\n\n") if part.strip()]
        if not paragraphs:
            paragraphs = [
                "Os resultados do SRS-2 devem ser interpretados de forma integrada à anamnese, observação clínica e demais instrumentos aplicados."
            ]
        return "\n".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in paragraphs)

    @staticmethod
    def _highest_row(rows: list[dict]) -> dict:
        domain_rows = [row for row in rows if row.get("variável") != "total"]
        return max(domain_rows or rows, key=lambda row: row.get("tscore") or 0, default={})

    @staticmethod
    def _format_score(value) -> str:
        if value in (None, ""):
            return "-"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if number.is_integer():
            return str(int(number))
        return f"{number:.1f}".replace(".", ",")

    @classmethod
    def _status_color(cls, value) -> str:
        try:
            tscore = float(value)
        except (TypeError, ValueError):
            return "var(--normal)"
        if tscore <= 59:
            return "var(--normal)"
        if tscore <= 65:
            return "var(--leve)"
        if tscore <= 75:
            return "var(--moderado)"
        return "var(--severo)"

    @classmethod
    def _position_for_tscore(cls, value) -> float:
        try:
            tscore = float(value)
        except (TypeError, ValueError):
            tscore = 20.0
        return ((max(20.0, min(80.0, tscore)) - 20.0) / 60.0) * 100.0

    @staticmethod
    def _classification_for_tscore(value) -> str:
        try:
            tscore = float(value)
        except (TypeError, ValueError):
            return "não classificado"
        if tscore <= 59:
            return "dentro dos limites normais"
        if tscore <= 65:
            return "nível leve"
        if tscore <= 75:
            return "nível moderado"
        return "nível severo"

    @classmethod
    def _classification_label(cls, value) -> str:
        classification = cls._classification_for_tscore(value)
        if classification == "não classificado":
            return "Não classificado"
        if classification == "dentro dos limites normais":
            return "Dentro dos limites normais"
        return classification[0].upper() + classification[1:]

    @staticmethod
    def _is_normal_tscore(value) -> bool:
        try:
            return float(value) <= 59
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _radar_point(cx: float, cy: float, radius: float, angle: float) -> tuple[float, float]:
        return cx + math.cos(angle) * radius, cy + math.sin(angle) * radius

    @staticmethod
    def _radar_label_anchor(angle: float) -> str:
        x_direction = math.cos(angle)
        if x_direction > 0.35:
            return "start"
        if x_direction < -0.35:
            return "end"
        return "middle"

    @classmethod
    def _radar_rows(cls, rows: list[dict]) -> list[dict]:
        keys = cls.SCORE_ORDER[:5]
        by_key = {row.get("variável"): row for row in rows if isinstance(row, dict)}
        selected = [by_key[key] for key in keys if key in by_key]
        return selected or [row for row in rows if row.get("variável") not in {"cis", "total"}][:5]

    @classmethod
    def _radar_radius(cls, value, max_radius: float) -> float:
        try:
            tscore = float(value)
        except (TypeError, ValueError):
            tscore = 20.0
        clamped = max(20.0, min(80.0, tscore))
        return ((clamped - 20.0) / 60.0) * max_radius

    @classmethod
    def _radar_label_svg(cls, label: str, x: float, y: float) -> str:
        escaped = html.escape(label)
        if label == "Padrões Restritos e Repetitivos":
            return (
                f'<text fill="#374151" font-size="9" font-weight="700" text-anchor="middle" x="{x:.1f}" y="{y:.1f}">'
                f'<tspan x="{x:.1f}" dy="0">Padrões Restritos</tspan><tspan x="{x:.1f}" dy="11">e Repetitivos</tspan></text>'
            )
        return f'<text fill="#374151" font-size="9" font-weight="700" text-anchor="middle" x="{x:.1f}" y="{y:.1f}">{escaped}</text>'

    @classmethod
    def _radar_svg(cls, rows: list[dict]) -> str:
        radar_rows = cls._radar_rows(rows)
        if not radar_rows:
            return '<svg class="radar-svg" viewBox="-36 0 500 332" aria-label="Radar clínico dos domínios"></svg>'

        cx = 205.0
        cy = 150.0
        max_radius = 112.0
        total = len(radar_rows)

        def angle_for(index: int) -> float:
            return -math.pi / 2 + (2 * math.pi * index / total)

        def points_for(radius: float) -> str:
            return " ".join(
                f"{cls._radar_point(cx, cy, radius, angle_for(index))[0]:.1f},{cls._radar_point(cx, cy, radius, angle_for(index))[1]:.1f}"
                for index in range(total)
            )

        rings = "".join(
            f'<polygon points="{points_for(radius)}" fill="none" stroke="#d9d9d9" stroke-width="1"/>'
            for radius in [max_radius * index / 8 for index in range(1, 9)]
        )
        spokes = "".join(
            f'<line x1="{cx:.0f}" y1="{cy:.0f}" x2="{cls._radar_point(cx, cy, max_radius, angle_for(index))[0]:.1f}" y2="{cls._radar_point(cx, cy, max_radius, angle_for(index))[1]:.1f}" stroke="#d4d4d4" stroke-width="1"/>'
            for index in range(total)
        )

        label_radius = max_radius + 28.0
        labels = "".join(
            cls._radar_axis_label_svg(
                cls._display_name(row),
                cls._radar_point(cx, cy, label_radius, angle_for(index))[0],
                cls._radar_point(cx, cy, label_radius, angle_for(index))[1],
                cls._radar_label_anchor(angle_for(index)),
            )
            for index, row in enumerate(radar_rows)
        )

        data_points = " ".join(
            f"{cls._radar_point(cx, cy, cls._radar_radius(row.get('tscore'), max_radius), angle_for(index))[0]:.1f},{cls._radar_point(cx, cy, cls._radar_radius(row.get('tscore'), max_radius), angle_for(index))[1]:.1f}"
            for index, row in enumerate(radar_rows)
        )
        cutoff_points = points_for(cls._radar_radius(60, max_radius))
        dots = "".join(
            f'<circle cx="{cls._radar_point(cx, cy, cls._radar_radius(row.get("tscore"), max_radius), angle_for(index))[0]:.1f}" cy="{cls._radar_point(cx, cy, cls._radar_radius(row.get("tscore"), max_radius), angle_for(index))[1]:.1f}" r="6" fill="#4b8e98"/>'
            for index, row in enumerate(radar_rows)
        )

        return (
            '<svg class="radar-svg" viewBox="-36 0 500 332" aria-label="Radar clínico dos domínios">'
            f"{rings}{spokes}"
            f'<polygon points="{cutoff_points}" fill="none" stroke="#f57c00" stroke-width="4" stroke-linejoin="round"/>'
            f'<polygon points="{data_points}" fill="rgba(61, 146, 214, .62)" stroke="#4b8e98" stroke-width="4" stroke-linejoin="round"/>'
            f"{dots}{labels}"
            "</svg>"
        )

    @classmethod
    def _radar_axis_label_svg(cls, label: str, x: float, y: float, anchor: str) -> str:
        if label == "Padrões Restritos e Repetitivos":
            return (
                f'<text class="axis-label" text-anchor="{anchor}" x="{x:.1f}" y="{y - 6:.1f}" dominant-baseline="middle">Padrões Restritos</text>'
                f'<text class="axis-label" text-anchor="{anchor}" x="{x:.1f}" y="{y + 6:.1f}" dominant-baseline="middle">e Repetitivos</text>'
            )
        return f'<text class="axis-label" text-anchor="{anchor}" x="{x:.1f}" y="{y:.1f}" dominant-baseline="middle">{html.escape(label)}</text>'

    @classmethod
    def _radar_legend_html(cls, rows: list[dict]) -> str:
        items = "".join(
            f'<div class="summary-row"><span>{html.escape(cls._display_name(row))}</span><strong>T {html.escape(cls._format_score(row.get("tscore")))}</strong></div>'
            for row in cls._radar_rows(rows)
        )
        return f"<div>{items}</div>"

    @classmethod
    def _radar_panel_html(cls, rows: list[dict]) -> str:
        return (
            '<div class="radar-panel">'
            '<div class="radar-layout">'
            '<div style="display:flex;justify-content:center;align-items:center">'
            f"{cls._radar_svg(rows)}"
            "</div>"
            f"{cls._radar_legend_html(rows)}"
            "</div>"
            "</div>"
        )

    @classmethod
    def _pill_row_html(cls, total: dict, highest: dict) -> str:
        return (
            '<section class="summary-cards">'
            f'<div class="summary-card"><span>Escore total</span><strong>{html.escape(cls._classification_label(total.get("tscore")))}</strong><b>T {html.escape(cls._format_score(total.get("tscore")))}</b></div>'
            f'<div class="summary-card"><span>Maior escore</span><strong>{html.escape(cls._display_name(highest))}</strong><b>T {html.escape(cls._format_score(highest.get("tscore")))}</b></div>'
            '<div class="summary-card"><span>Média normativa</span><strong>Referência central</strong><b>T 50</b></div>'
            "</section>"
        )

    @classmethod
    def _profile_chart_html(cls, rows: list[dict]) -> str:
        ticks = list(range(20, 81, 5))
        tick_marks = "\n".join(
            f'<span class="tick-mark" style="left:{cls._position_for_tscore(tick):.6f}%"></span>' for tick in ticks
        )
        tick_labels = "\n".join(
            f'<span class="tick-label {"edge-left" if tick == 20 else "edge-right" if tick == 80 else ""}" style="left:{cls._position_for_tscore(tick):.6f}%">{tick}</span>'
            for tick in ticks
        )
        plot_rows = []
        for row in rows:
            position = cls._position_for_tscore(row.get("tscore"))
            width = abs(position - 50.0)
            bar_left = min(position, 50.0)
            accent = "#2f78bd" if cls._is_normal_tscore(row.get("tscore")) else "#e75f2a"
            plot_rows.append(
                "\n".join(
                    [
                        '<div class="profile-row">',
                        f'<div class="profile-label">{html.escape(cls._profile_display_name(row))}</div>',
                        '<div class="profile-track">',
                        f'<span class="profile-bar" style="--bar-left:{bar_left:.4f}%;--w:{width:.4f}%;--x:{position:.4f}%;--c:{accent};"></span>',
                        f'<span class="profile-dot" style="--x:{position:.4f}%;--c:{accent};"></span>',
                        f'<span class="profile-score" style="--x:{position:.4f}%;--c:{accent};">T {html.escape(cls._format_score(row.get("tscore")))}</span>',
                        "</div>",
                        "</div>",
                    ]
                )
            )
        return (
            '<div class="profile-chart">'
            '<div class="axis">'
            '<div class="axis-top"><span class="min">min</span><span style="left:33.333333%">-s</span><span style="left:50%">m</span><span style="left:66.666667%">+s</span><span class="max">max</span></div>'
            '<div class="axis-line"></div>'
            f"{tick_marks}{tick_labels}"
            "</div>"
            '<div class="profile-rows">'
            f"{''.join(plot_rows)}"
            "</div>"
            "</div>"
        )

    @classmethod
    def _technical_profile_chart_html(cls, rows: list[dict]) -> str:
        labels = "\n".join(f"<div>{html.escape(cls._display_name(row))}</div>" for row in rows)
        plot_rows = []
        for row in rows:
            position = cls._position_for_tscore(row.get("tscore"))
            width = abs(position - 50.0)
            bar_left = min(position, 50.0)
            accent = cls._status_color(row.get("tscore"))
            plot_rows.append(
                "\n".join(
                    [
                        '<div class="row">',
                        f'<div class="bar" style="left:{bar_left:.1f}%;--w:{width:.1f}%;background:{accent}"></div>',
                        f'<i class="point" style="--x:{position:.1f}%;background:{accent};box-shadow:0 0 0 2px {accent}"></i>',
                        f'<span class="tlabel" style="--x:{position:.1f}%;color:{accent}">T {html.escape(cls._format_score(row.get("tscore")))}</span>',
                        "</div>",
                    ]
                )
            )
        return (
            '<div class="profile-chart">'
            f'<div class="profile-labels">{labels}</div>'
            '<div class="plot">'
            '<div class="ticks"><span>20</span><span>25</span><span>30</span><span>35</span><span>40</span><span>45</span><span>50</span><span>55</span><span>60</span><span>65</span><span>70</span><span>75</span><span>80</span></div>'
            '<div class="grid"></div><div class="mean-line"></div>'
            f"{''.join(plot_rows)}"
            "</div>"
            "</div>"
        )

    @classmethod
    def _technical_score_table_rows_html(cls, rows: list[dict]) -> str:
        return "\n".join(
            "\n".join(
                [
                    f'<tr class="{"total" if row.get("variável") == "total" else ""}">',
                    f"<td>{html.escape(cls._display_name(row))}</td>",
                    f'<td class="num">{html.escape(cls._format_score(row.get("bruto")))}</td>',
                    f'<td class="num">{html.escape(cls._format_score(row.get("tscore")))}</td>',
                    f'<td class="num">{html.escape(cls._format_score(cls._ci_for_tscore(row.get("tscore"))[0]))}–{html.escape(cls._format_score(cls._ci_for_tscore(row.get("tscore"))[1]))}</td>',
                    f"<td>{html.escape(cls._classification_label(row.get('tscore')))}</td>",
                    "</tr>",
                ]
            )
            for row in rows
        )

    @classmethod
    def _technical_summary_pills_html(cls, rows: list[dict], raw_payload: dict, total: dict, highest: dict) -> str:
        responses = raw_payload.get("responses") or {}
        missing_count = max(0, 65 - len(responses)) if isinstance(responses, dict) else 0
        respondent = raw_payload.get("respondent_name") or "Responsável"
        return (
            '<div class="grid-4 mt">'
            f'<div class="pill"><span>Escore total</span><strong>{html.escape(cls._classification_label(total.get("tscore")))}</strong><b>T {html.escape(cls._format_score(total.get("tscore")))}</b></div>'
            f'<div class="pill"><span>Maior escore</span><strong>{html.escape(cls._display_name(highest))}</strong><b>T {html.escape(cls._format_score(highest.get("tscore")))}</b></div>'
            f'<div class="pill"><span>Respondente</span><strong>{html.escape(str(respondent))}</strong><b>{missing_count} miss.</b></div>'
            '<div class="pill"><span>Status</span><strong>Aplicação válida</strong><b>SRS-2</b></div>'
            "</div>"
        )

    @classmethod
    def _technical_profile_section_html(cls, rows: list[dict], total: dict, highest: dict) -> str:
        total_level = cls._classification_for_tscore(total.get("tscore"))
        highest_name = cls._display_name(highest)
        normal = [row for row in rows if row.get("variável") != "total" and cls._is_normal_tscore(row.get("tscore"))]
        normal_names = ", ".join(cls._display_name(row) for row in normal) or "não informado"
        return (
            '<div class="profile-card">'
            '<div class="card-head"><div><h2>Perfil dos Escores T</h2><p>Distribuição dos escores T por dimensão, com média normativa em T=50.</p></div></div>'
            f"{cls._technical_profile_chart_html(rows)}"
            "</div>"
            '<div class="grid-3 mt">'
            f'<div class="analysis-card"><span>Leitura</span><strong>Perfil global em {html.escape(total_level)}</strong><p>O Escore Total está em {html.escape(total_level)}, com T={html.escape(cls._format_score(total.get("tscore")))}.</p></div>'
            f'<div class="analysis-card"><span>Maior domínio</span><strong>{html.escape(highest_name)}</strong><p>Maior escore do protocolo, com T={html.escape(cls._format_score(highest.get("tscore")))}.</p></div>'
            f'<div class="analysis-card"><span>Normalidade</span><strong>Domínios preservados</strong><p>{html.escape(normal_names)} permanecem dentro dos limites normativos.</p></div>'
            "</div>"
        )

    @classmethod
    def _technical_bell_svg(cls, value) -> str:
        position = 20.0 + (cls._position_for_tscore(value) / 100.0) * 260.0
        return (
            '<svg viewBox="0 0 300 150" aria-label="Distribuição normativa">'
            '<path d="M20 130 C70 126,80 30,150 30 C220 30,230 126,280 130" fill="#e3f8f7"/>'
            '<line x1="20" y1="130" x2="280" y2="130" stroke="#333"/>'
            '<line x1="150" y1="130" x2="150" y2="30" stroke="#ffffff"/>'
            f'<line x1="{position:.1f}" y1="130" x2="{position:.1f}" y2="58" stroke="#e4002b" stroke-width="4"/>'
            f'<circle cx="{position:.1f}" cy="58" r="7" fill="#e4002b"/>'
            "</svg>"
        )

    @classmethod
    def _technical_detail_cards_html(cls, rows: list[dict]) -> str:
        notes = {
            "percepção_social": "Mede a capacidade de reconhecer pistas sociais e aspectos perceptivos do comportamento social recíproco.",
            "cognição_social": "Refere-se à interpretação das pistas sociais após reconhecê-las, envolvendo aspectos cognitivo-interpretativos.",
            "comunicação_social": "Mede aspectos expressivos da comunicação social e do comportamento social recíproco.",
            "motivação_social": "Refere-se ao grau de motivação para engajamento social e comportamento interpessoal.",
            "padrões_restritos": "Mede rigidez, repetitividade, interesses restritos e dificuldades de flexibilidade comportamental.",
            "total": "Representa a medida global de responsividade social do protocolo.",
        }
        cards = []
        for row in rows:
            if row.get("variável") == "cis":
                continue
            ci = cls._ci_for_tscore(row.get("tscore"))
            cards.append(
                "\n".join(
                    [
                        '<div class="detail-card">',
                        "<div>",
                        f"<h3>{html.escape(cls._display_name(row))}</h3>",
                        '<table class="mini-table"><tbody>',
                        f'<tr><td>Pontuação bruta</td><td class="num">{html.escape(cls._format_score(row.get("bruto")))}</td></tr>',
                        f'<tr><td>Valor da norma</td><td class="num">{html.escape(cls._format_score(row.get("tscore")))}</td></tr>',
                        '<tr><td>Respostas faltantes</td><td class="num">0</td></tr>',
                        f'<tr><td>Intervalo de confiança</td><td class="num">{html.escape(cls._format_score(ci[0]))}–{html.escape(cls._format_score(ci[1]))}</td></tr>',
                        "</tbody></table>",
                        f'<p class="scale-note">{html.escape(notes.get(row.get("variável"), "Indicador técnico do protocolo SRS-2."))}</p>',
                        "</div>",
                        f'<div class="bell">{cls._technical_bell_svg(row.get("tscore"))}</div>',
                        "</div>",
                    ]
                )
            )
        return "\n".join(cards)

    @classmethod
    def _technical_response_stats_rows_html(cls, raw_payload: dict) -> str:
        responses = raw_payload.get("responses") or {}
        counts = {str(index): 0 for index in range(1, 5)}
        if isinstance(responses, dict):
            for value in responses.values():
                key = str(value)
                if key in counts:
                    counts[key] += 1
        total = sum(counts.values()) or 1

        return "".join(
            "\n".join(
                [
                    "<tr>",
                    f'<td class="num">{index}</td>',
                    f'<td class="num">{round((counts[str(index)] / total) * 100)}%</td>',
                    f'<td class="bar-cell"><span style="--w:{round((counts[str(index)] / total) * 100)}%"></span></td>',
                    "</tr>",
                ]
            )
            for index in range(1, 5)
        )

    @staticmethod
    def _format_total_profile_score(value) -> str:
        try:
            return f"{float(value):.1f}"
        except (TypeError, ValueError):
            return "-"

    @classmethod
    def _profile_card_head_html(cls, total: dict) -> str:
        return (
            '<div class="profile-head">'
            '<div><h2>Perfil dos Escores T</h2>'
            '<p>Distribuição dos escores T por dimensão, com média normativa em T=50 e marcação das faixas referenciais.</p></div>'
            '<div class="total-box"><span>Escore total</span>'
            f'<strong>T {html.escape(cls._format_score(total.get("tscore")))}</strong></div>'
            '</div>'
        )

    @classmethod
    def _score_table_rows_html(cls, rows: list[dict]) -> str:
        return "\n".join(
            "\n".join(
                [
                    f'<tr class="{"total" if row.get("variável") == "total" else ""}">',
                    f"<td>{html.escape(cls._display_name(row))}</td>",
                    f'<td class="num">{html.escape(cls._format_score(row.get("bruto")))}</td>',
                    f'<td class="num">{html.escape(cls._format_score(row.get("tscore")))}</td>',
                    f"<td>{html.escape(cls._classification_label(row.get('tscore')))}</td>",
                    "</tr>",
                ]
            )
            for row in rows
        )

    @classmethod
    def _domain_grid_html(cls, rows: list[dict]) -> str:
        items = []
        for row in rows:
            is_total = row.get("variável") == "total"
            position = cls._position_for_tscore(row.get("tscore"))
            status = cls._status_color(row.get("tscore"))
            row_class = "domain total" if is_total else "domain "
            items.append(
                "\n".join(
                    [
                        f'<div class="{row_class}">',
                        f'<div class="badge" style="--status:{status}">{html.escape(cls._format_score(row.get("tscore")))}</div>',
                        "<div>",
                        f"<strong>{html.escape(cls._display_name(row))}</strong>",
                        f"<span>PB {html.escape(cls._format_score(row.get('bruto')))} · IC {html.escape(cls._format_score(cls._ci_for_tscore(row.get('tscore'))[0]))}–{html.escape(cls._format_score(cls._ci_for_tscore(row.get('tscore'))[1]))} · {html.escape(cls._classification_label(row.get('tscore')))}</span>",
                        f'<div class="mini-axis" style="--pos:{position:.1f}%;--status:{status}"></div>',
                        "</div>",
                        "</div>",
                    ]
                )
            )
        return f'<div class="domain-grid">{"".join(items)}</div>'

    @classmethod
    def _profile_reading_html(cls, patient_name: str, total: dict, highest: dict) -> str:
        total_t = cls._format_score(total.get("tscore"))
        highest_t = cls._format_score(highest.get("tscore"))
        total_level = cls._classification_for_tscore(total.get("tscore"))
        highest_level = cls._classification_for_tscore(highest.get("tscore"))
        highest_name = cls._display_name(highest)

        if cls._is_normal_tscore(total.get("tscore")):
            global_sentence = (
                f"No protocolo de {html.escape(patient_name)}, o Escore Total foi T={html.escape(total_t)}, situando-se dentro dos limites normais."
            )
            implication = (
                "Neste caso, o perfil geral não indica elevação global clinicamente significativa, embora domínios específicos devam ser analisados quando se aproximam ou ultrapassam os pontos de corte."
            )
        else:
            global_sentence = (
                f"No protocolo de {html.escape(patient_name)}, o Escore Total foi T={html.escape(total_t)}, classificado em {html.escape(total_level)}."
            )
            implication = (
                "Neste caso, o perfil geral indica elevação clinicamente relevante da responsividade social e exige integração com anamnese, observação clínica e demais instrumentos."
            )

        return (
            '<section class="analysis-block">'
            "<h2>Leitura clínica do perfil</h2>"
            f"<p>O gráfico de perfil organiza os escores T do SRS-2 em uma régua normativa de 20 a 80 pontos, com média fixada em T=50. {global_sentence} "
            f"A maior elevação entre os domínios aparece em {html.escape(highest_name)}, com T={html.escape(highest_t)}, classificada em {html.escape(highest_level)}.</p>"
            f"<p>{implication} O gráfico deve ser lido como síntese visual do perfil, destacando quais áreas permanecem próximas da média normativa e quais exigem maior atenção clínica.</p>"
            "</section>"
        )

    @classmethod
    def _total_detail_html(cls, patient_name: str, total: dict, highest: dict) -> str:
        total_t = cls._format_score(total.get("tscore"))
        total_raw = cls._format_score(total.get("bruto"))
        total_level = cls._classification_for_tscore(total.get("tscore"))
        highest_t = cls._format_score(highest.get("tscore"))
        highest_name = cls._display_name(highest)

        if cls._is_normal_tscore(total.get("tscore")):
            second = (
                "A leitura por domínio deve verificar se existem elevações pontuais que, mesmo sem elevar o índice global, possam indicar aspectos específicos para investigação clínica."
            )
        else:
            second = (
                f"A leitura por domínio mostra que {html.escape(highest_name)} foi o domínio mais elevado (T={html.escape(highest_t)}), devendo ser analisado em conjunto com o Escore Total e com os dados clínicos do caso."
            )

        return (
            '<section class="analysis-block">'
            "<h2>Interpretação do Escore Total</h2>"
            f"<p>{html.escape(patient_name)} apresentou Escore Total bruto de {html.escape(total_raw)}, correspondente ao Escore T={html.escape(total_t)}. Esse resultado situa-se em {html.escape(total_level)} no SRS-2.</p>"
            f"<p>{second}</p>"
            "</section>"
        )

    @classmethod
    def _radar_reading_html(cls, patient_name: str, total: dict, highest: dict) -> str:
        total_t = cls._format_score(total.get("tscore"))
        highest_t = cls._format_score(highest.get("tscore"))
        highest_name = cls._display_name(highest)
        total_level = cls._classification_for_tscore(total.get("tscore"))

        if cls._is_normal_tscore(total.get("tscore")):
            profile_sentence = "O polígono sugere perfil globalmente preservado, com atenção a eventuais picos específicos."
        else:
            profile_sentence = f"O polígono sugere perfil global elevado em {html.escape(total_level)}, com maior expansão relativa no domínio {html.escape(highest_name)}."

        return (
            '<div class="clinical-box mt">'
            "<h2>Leitura do radar</h2>"
            f"<p>O radar apresenta a distribuição dos escores T entre os principais domínios do SRS-2. No protocolo de {html.escape(patient_name)}, o Escore Total foi T={html.escape(total_t)} e o domínio mais elevado foi {html.escape(highest_name)}, com T={html.escape(highest_t)}.</p>"
            f"<p>{profile_sentence} Esse gráfico deve ser usado para verificar se o perfil é homogêneo ou se existem picos específicos entre comunicação/interação social e padrões restritos ou repetitivos.</p>"
            "</div>"
        )

    @classmethod
    def _score_table_analysis_html(cls, patient_name: str, total: dict, highest: dict, rows: list[dict]) -> str:
        elevated = [row for row in rows if row.get("variável") != "total" and not cls._is_normal_tscore(row.get("tscore"))]
        normal = [row for row in rows if row.get("variável") != "total" and cls._is_normal_tscore(row.get("tscore"))]
        total_t = cls._format_score(total.get("tscore"))
        total_level = cls._classification_for_tscore(total.get("tscore"))
        highest_t = cls._format_score(highest.get("tscore"))
        highest_level = cls._classification_for_tscore(highest.get("tscore"))
        highest_name = cls._display_name(highest)

        if elevated:
            elevated_names = ", ".join(cls._display_name(row) for row in elevated)
            table_text = (
                f"O Escore Total foi T={total_t}, classificado em {total_level}. "
                f"Os domínios elevados foram {elevated_names}."
            )
        else:
            normal_names = ", ".join(cls._display_name(row) for row in normal)
            table_text = (
                f"O Escore Total foi T={total_t}, dentro dos limites normais. "
                f"Domínios em faixa normativa: {normal_names or 'não informado'}."
            )

        if cls._is_normal_tscore(total.get("tscore")):
            highlight_text = (
                f"Maior elevação: {highest_name}, T={highest_t}, {highest_level}. Interpretar como indicador dimensional, não como conclusão diagnóstica isolada."
            )
        else:
            highlight_text = (
                f"Maior elevação: {highest_name}, T={highest_t}, {highest_level}. Considerar padrão global e convergência clínica."
            )

        return (
            '<div class="analysis-grid">'
            '<div class="analysis-card">'
            "<span>Leitura da tabela</span>"
            "<strong>Resultados normativos</strong>"
            f"<p>{html.escape(table_text)}</p>"
            "</div>"
            '<div class="analysis-card">'
            "<span>Destaque clínico</span>"
            f"<strong>{html.escape(highest_name)}</strong>"
            f"<p>{html.escape(highlight_text)}</p>"
            "</div>"
            "</div>"
        )

    @classmethod
    def _conclusion_grid_html(cls, total: dict, highest: dict) -> str:
        total_t = cls._format_score(total.get("tscore"))
        total_level = cls._classification_for_tscore(total.get("tscore"))
        highest_t = cls._format_score(highest.get("tscore"))
        highest_level = cls._classification_for_tscore(highest.get("tscore"))
        highest_name = cls._display_name(highest)

        if cls._is_normal_tscore(total.get("tscore")):
            conclusion_title = "Perfil global normativo"
            conclusion_text = "O resultado geral do SRS-2 não indica elevação global clinicamente significativa, considerando o Escore Total."
        else:
            conclusion_title = f"Perfil global em {total_level}"
            conclusion_text = f"O resultado geral do SRS-2 apresenta elevação clinicamente relevante, com Escore Total T={total_t}."

        return (
            '<div class="analysis-grid">'
            '<div class="analysis-card">'
            "<span>Conclusão do teste</span>"
            f"<strong>{html.escape(conclusion_title)}</strong>"
            f"<p>{html.escape(conclusion_text)}</p>"
            "</div>"
            '<div class="analysis-card">'
            "<span>Ponto de atenção</span>"
            f"<strong>{html.escape(highest_name)}</strong>"
            f"<p>Maior elevação do perfil: T={html.escape(highest_t)}, classificada em {html.escape(highest_level)}.</p>"
            "</div>"
            '<div class="analysis-card">'
            "<span>Regra de segurança</span>"
            "<strong>Não fechar diagnóstico isolado</strong>"
            "<p>O SRS-2 é instrumento de rastreio e quantificação dimensional. A hipótese diagnóstica depende da integração com outros dados clínicos.</p>"
            "</div>"
            '<div class="analysis-card">'
            "<span>Hipótese diagnóstica</span>"
            "<strong>Investigar se houver convergência</strong>"
            "<p>A hipótese depende de anamnese, observação clínica, funcionamento adaptativo e prejuízos funcionais.</p>"
            "</div>"
            "</div>"
        )

    @classmethod
    def _system_note_html(cls, total: dict) -> str:
        if cls._is_normal_tscore(total.get("tscore")):
            text = "quando o Escore Total estiver dentro dos limites normais, mas houver domínio específico elevado, gerar conclusão cautelosa com integração clínica."
        else:
            text = "quando o Escore Total estiver em nível leve, moderado ou severo, não descrever o perfil global como normal; apontar a elevação global e exigir integração clínica antes de hipótese diagnóstica."
        return f'<p class="system-note"><strong>Regra para o NeuroAvalia:</strong> {html.escape(text)}</p>'

    @classmethod
    def _hypothesis_html(cls, total: dict) -> str:
        if cls._is_normal_tscore(total.get("tscore")):
            text = (
                "Considerando exclusivamente os resultados do SRS-2, não há sustentação psicométrica suficiente para estabelecer hipótese diagnóstica de Transtorno do Espectro Autista quando o Escore Total permanece dentro dos limites normais. Ainda assim, elevações específicas devem ser investigadas clinicamente quando houver queixas funcionais compatíveis."
            )
        else:
            text = (
                "Considerando exclusivamente os resultados do SRS-2, há indicadores psicométricos de elevação clinicamente relevante na responsividade social. Esse achado não confirma diagnóstico isoladamente, mas sustenta a necessidade de investigar características associadas ao Transtorno do Espectro Autista quando houver convergência com anamnese, observação clínica, histórico do desenvolvimento e prejuízos funcionais."
            )
        return (
            '<section class="analysis-block">'
            "<h2>Hipótese diagnóstica</h2>"
            f"<p>{html.escape(text)}</p>"
            "</section>"
        )

    @classmethod
    def _replace_dynamic_content(cls, source: str, application, rows: list[dict]) -> str:
        raw_payload = getattr(application, "raw_payload", None) or {}
        patient = getattr(application.evaluation, "patient", None)
        patient_name = cls._format_person_name(getattr(patient, "full_name", ""))
        patient_age = cls._patient_age(application)
        age_label = f"{patient_age} anos" if patient_age is not None else "Não informado"
        form = raw_payload.get("form") or (getattr(application, "computed_payload", None) or {}).get("form") or "idade_escolar"
        raw_gender = raw_payload.get("gender") or getattr(patient, "sex", None)
        norm_label = cls._normative_table_label(form, raw_gender)
        sex_label = cls._format_sex(raw_gender)
        schooling_label = cls._format_schooling(getattr(patient, "schooling", None))
        total = next((row for row in rows if row.get("variável") == "total"), {})
        highest = cls._highest_row(rows)
        total_t = total.get("tscore") or "-"
        highest_t = highest.get("tscore") or "-"
        total_classification = cls._classification_label(total.get("tscore"))
        highest_name = cls._display_name(highest) if highest else "-"

        replacements = {
            "Teste_01": patient_name,
            "Herick Freitas Rodrigues": patient_name,
            "Feminino": sex_label,
            "Não informado": sex_label,
            "Fundamental Incompleto": schooling_label,
            "escolar17 anos e 11 meses": schooling_label,
            "10 anos": age_label,
            "17 anos e 11 meses": age_label,
            "Idade Escolar</strong>": f"{norm_label}</strong>",
            "Dra. Jacqueline O. Caires · CRP09/6017": "Dra. Jacqueline O. Caires - CRP09/6017",
            "Profissional responsável": "Dra. Jacqueline O. Caires - CRP09/6017",
            "Idade Escolar · Escore T (50+10z)": norm_label,
            "Idade Escolar · Escore T": f"{norm_label} · Escore T",
            "Escolar · Escore T (50+10z)": norm_label,
            "T 61": f"T {total_t}",
            "T=61": f"T={total_t}",
            "T 54": f"T {total_t}",
            "T=54": f"T={total_t}",
            "Padrões Restritos e Repetitivos</strong>\n<strong>Padrões Restritos e Repetitivos": f"{html.escape(highest_name)}</strong>\n<strong>{html.escape(highest_name)}",
            "Padrões Restritos e Repetitivos</strong>\n<b>T 61": f"{html.escape(highest_name)}</strong>\n<b>T {highest_t}",
            "Exemplo com Herick": f"Protocolo de {patient_name}",
            "No exemplo de Herick": f"No protocolo de {patient_name}",
            "Em Herick": f"Em {patient_name}",
            "Herick apresentou": f"{patient_name} apresentou",
        }
        rendered = cls._replace_logo(source)
        for old, new in replacements.items():
            rendered = rendered.replace(old, str(new))

        rendered = re.sub(
            r"(<span>Classificação global</span>\s*)<strong>.*?</strong>\s*<b>.*?</b>",
            rf"\1<strong>{html.escape(str(total_classification))}</strong>\n<b>T={html.escape(cls._format_score(total.get('tscore')))}</b>",
            rendered,
            flags=re.S,
        )

        rendered = re.sub(r"const scales = \[.*?\];", cls._scales_script(rows), rendered, flags=re.S)
        rendered = re.sub(
            r'<svg[^>]*id="radarSvg"[^>]*>.*?</svg>',
            cls._radar_svg(rows),
            rendered,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div id="radarLegend">.*?</div>',
            f'<div id="radarLegend">{cls._radar_legend_html(rows)}</div>',
            rendered,
            flags=re.S,
        )
        rendered = re.sub(
            r'<(?:div|section) class="(?:pill-row|summary-cards)">.*?</(?:div|section)>\s*<(?:div|section) class="profile-card">',
            f'{cls._pill_row_html(total, highest)}\n    <section class="profile-card">',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="(?:card-head|profile-head)">.*?</div>\s*(?=<div class="profile-chart">)',
            cls._profile_card_head_html(total),
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="profile-chart">.*?</div>\s*</(?:div|section)>\s*<div class="footer"><span>NeuroAvalia · SRS-2</span><span>PÁGINA 2 DE 5</span></div>',
            f'{cls._profile_chart_html(rows)}\n    </section>\n    <div class="footer"><span>NeuroAvalia · SRS-2</span><span>PÁGINA 2 DE 5</span></div>',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<tbody>.*?</tbody>',
            f'<tbody>\n{cls._score_table_rows_html(rows)}\n</tbody>',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="domain-grid">.*?</div>\s*<div class="analysis-grid">',
            f'{cls._domain_grid_html(rows)}\n    <div class="analysis-grid">',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="radar-panel">.*?</div>\s*(?=<div class="clinical-box)',
            f'{cls._radar_panel_html(rows)}\n    ',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="clinical-box">\s*<h2>Síntese interpretativa</h2>.*?</div>',
            f'<div class="clinical-box"><h2>Síntese interpretativa</h2>\n{cls._paragraphs_html(getattr(application, "interpretation_text", ""))}</div>',
            rendered,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="clinical-box"[^>]*>\s*<h2>Leitura do radar</h2>.*?</div>',
            cls._radar_reading_html(patient_name, total, highest),
            rendered,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="analysis-grid">\s*<div class="analysis-card">\s*<span>Leitura da tabela</span>.*?</div>\s*<div class="footer"><span>NeuroAvalia · SRS-2</span><span>PÁGINA 3 DE 5</span></div>',
            f'{cls._score_table_analysis_html(patient_name, total, highest, rows)}\n    <div class="footer"><span>NeuroAvalia · SRS-2</span><span>PÁGINA 3 DE 5</span></div>',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="analysis-grid">\s*<div class="analysis-card">\s*<span>Conclusão do teste</span>.*?</div>\s*<div class="footer"><span>NeuroAvalia · SRS-2</span><span>PÁGINA 5 DE 5</span></div>',
            f'{cls._conclusion_grid_html(total, highest)}\n    <div class="footer"><span>NeuroAvalia · SRS-2</span><span>PÁGINA 5 DE 5</span></div>',
            rendered,
            count=1,
            flags=re.S,
        )
        return rendered

    @classmethod
    def _replace_complete_dynamic_content(cls, source: str, application, rows: list[dict]) -> str:
        raw_payload = getattr(application, "raw_payload", None) or {}
        patient = getattr(application.evaluation, "patient", None)
        patient_name = cls._format_person_name(getattr(patient, "full_name", ""))
        patient_age = cls._patient_age(application)
        age_label = f"{patient_age} anos" if patient_age is not None else "Não informado"
        form = raw_payload.get("form") or (getattr(application, "computed_payload", None) or {}).get("form") or "idade_escolar"
        raw_gender = raw_payload.get("gender") or getattr(patient, "sex", None)
        sex_label = cls._format_sex(raw_gender)
        schooling_label = cls._format_schooling(getattr(patient, "schooling", None))
        norm_label = cls._normative_table_label(form, raw_gender)
        total = next((row for row in rows if row.get("variável") == "total"), {})
        highest = cls._highest_row(rows)

        rendered = cls._replace_logo(source)
        replacements = {
            "Teste_01": patient_name,
            "Feminino": sex_label,
            "Fundamental Incompleto": schooling_label,
            "10 anos": age_label,
            "Dra. Jacqueline O. Caires · CRP09/6017": "Dra. Jacqueline O. Caires - CRP09/6017",
            "Idade Escolar</strong>": f"{norm_label}</strong>",
        }
        for old, new in replacements.items():
            rendered = rendered.replace(old, str(new))

        rendered = re.sub(
            r'<div class="grid-4 mt">.*?</div>\s*<div class="box mt">\s*<h2>Critérios interpretativos</h2>',
            f'{cls._technical_summary_pills_html(rows, raw_payload, total, highest)}\n  <div class="box mt">\n    <h2>Critérios interpretativos</h2>',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'(<h1>Perfil</h1>).*?(?=\s*<div class="footer"><span>NeuroAvalia · SRS-2 Técnico</span><span>PÁGINA 3 DE 9</span></div>)',
            rf'\1\n  {cls._technical_profile_section_html(rows, total, highest)}\n  ',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'(<h1>Tabela de escores</h1>).*?(?=\s*<div class="footer"><span>NeuroAvalia · SRS-2 Técnico</span><span>PÁGINA 4 DE 9</span></div>)',
            (
                r"\1\n  "
                '<div class="table-card"><table><thead><tr><th>Escala</th><th class="num">Pontuação bruta</th><th class="num">Escore T</th><th class="num">IC</th><th>Classificação</th></tr></thead>'
                f"<tbody>{cls._technical_score_table_rows_html(rows)}</tbody></table></div>"
                '<h2 class="mt">Mapa dos domínios</h2>'
                f"{cls._domain_grid_html(rows)}\n  "
            ),
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'(<h1>Radar clínico</h1>).*?(?=\s*<div class="footer"><span>NeuroAvalia · SRS-2 Técnico</span><span>PÁGINA 5 DE 9</span></div>)',
            rf'\1\n  <h3>Radar clínico dos domínios</h3>\n  {cls._radar_panel_html(rows)}\n  {cls._radar_reading_html(patient_name, total, highest)}\n  ',
            rendered,
            count=1,
            flags=re.S,
        )

        detail_cards = cls._technical_detail_cards_html(rows).split('<div class="detail-card">')
        detail_cards = [f'<div class="detail-card">{part}' for part in detail_cards if part.strip()]
        first_details = "\n".join(detail_cards[:3])
        second_details = "\n".join(detail_cards[3:])
        rendered = re.sub(
            r'(<h1>Detalhes da escala</h1>).*?(?=\s*<div class="footer"><span>NeuroAvalia · SRS-2 Técnico</span><span>PÁGINA 6 DE 9</span></div>)',
            rf'\1\n  {first_details}\n  ',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'(<h1>Detalhes da escala</h1>).*?(?=\s*<div class="footer"><span>NeuroAvalia · SRS-2 Técnico</span><span>PÁGINA 7 DE 9</span></div>)',
            rf'\1\n  {second_details}\n  ',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<tbody id="responseStatsRows">.*?</tbody>',
            f'<tbody id="responseStatsRows">\n{cls._technical_response_stats_rows_html(raw_payload)}\n</tbody>',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'(<h1>Síntese técnica</h1>\s*<div class="clinical-box">\s*<h2>Interpretação integrada</h2>).*?</div>\s*<div class="grid-2 mt">',
            rf'\1\n{cls._paragraphs_html(getattr(application, "interpretation_text", ""))}</div>\n  {cls._conclusion_grid_html(total, highest).replace("analysis-grid", "grid-2 mt", 1)}\n  <div class="grid-2 mt">',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="grid-2 mt">\s*<div class="analysis-card"><span>Conclusão do teste</span>.*?</div>\s*<div class="recommend">',
            '<div class="recommend">',
            rendered,
            count=1,
            flags=re.S,
        )
        return rendered

    @classmethod
    def generate_pdf_bytes(cls, application, report_type: str = "summary") -> bytes:
        template_path = cls.COMPLETE_TEMPLATE_PATH if report_type == "complete" else cls.TEMPLATE_PATH
        template = template_path.read_text(encoding="utf-8")
        rows = cls._ordered_results(application)
        if report_type == "complete":
            html_source = cls._replace_complete_dynamic_content(template, application, rows)
        else:
            html_source = cls._replace_dynamic_content(template, application, rows)
        return generate_pdf_from_html(html_source)
