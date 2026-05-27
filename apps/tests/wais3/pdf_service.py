from __future__ import annotations

import csv
import html
import re
from datetime import date
from pathlib import Path

from apps.tests.services.playwright_pdf_service import generate_pdf_from_html


class WAIS3PdfService:
    TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "layout_relatorio_wais_3.html"
    B2_PATH = Path(__file__).resolve().parent / "tabelas" / "supplementary" / "b2_frequencia_diferencas_qi_indices.csv"

    INDEX_ORDER = [
        ("qi_verbal", "QIV"),
        ("qi_execucao", "QIE"),
        ("qi_total", "QIT"),
        ("compreensao_verbal", "ICV"),
        ("organizacao_perceptual", "IOP"),
        ("memoria_operacional", "IMO"),
        ("velocidade_processamento", "IVP"),
    ]
    VERBAL_PROFILE = [
        ("vocabulario", "V"),
        ("semelhancas", "S"),
        ("informacao", "I"),
        ("compreensao", "C"),
        ("aritmetica", "A"),
        ("digitos", "D"),
        ("sequencia_numeros_letras", "SNL"),
    ]
    EXECUTION_PROFILE = [
        ("arranjo_figuras", "AF"),
        ("completar_figuras", "CF"),
        ("cubos", "CB"),
        ("raciocinio_matricial", "RM"),
        ("codigos", "CD"),
        ("procurar_simbolos", "PS"),
        ("armar_objetos", "AO"),
    ]
    CLUSTER_ORDER = [
        ("Gf", "Gf", "Raciocínio Fluido (RM + AF + AR)", ["raciocinio_matricial", "arranjo_figuras", "aritmetica"]),
        ("Gv", "Gv", "Processamento Visual (CB + CF)", ["cubos", "completar_figuras"]),
        ("Gf_nonverbal", "Gf-nv", "Raciocínio Fluido Não Verbal (RM + AF)", ["raciocinio_matricial", "arranjo_figuras"]),
        ("Gf_verbal", "Gf-v", "Raciocínio Fluido Verbal (SM + CO)", ["semelhancas", "compreensao"]),
        ("Gc_LK", "Gc-VL", "Conhecimento Lexical (SM + VC)", ["semelhancas", "vocabulario"]),
        ("Gc_K0", "Gc-K0", "Informações Gerais (CO + IN)", ["compreensao", "informacao"]),
        ("Gc_LTM", "Gc-LTM", "Memória de Longo Prazo (VC + IN)", ["vocabulario", "informacao"]),
        ("Gsm_WM", "Gsm-WM", "Memória de Curto Prazo (SNL + DG)", ["sequencia_numeros_letras", "digitos"]),
    ]
    CLINICAL_COMPARISONS = [
        ("Gf x Gv", "Gf", "Gv", 21),
        ("Gf-nonverbal x Gv", "Gf_nonverbal", "Gv", 24),
        ("Gf-nonverbal x Gf-verbal", "Gf_nonverbal", "Gf_verbal", 24),
        ("Gc-VL x Gc-K0", "Gc_LK", "Gc_K0", 17),
        ("Gc-LTM x Gsm-WM", "Gc_LTM", "Gsm_WM", 24),
        ("Gc-LTM x Gf-verbal", "Gc_LTM", "Gf_verbal", 17),
    ]
    DISCREPANCY_PAIRS = [
        ("QI Verbal - QI de Execução", "qi_verbal", "qi_execucao", "qiv_qie"),
        ("Compreensão Verbal - Organização Perceptual", "compreensao_verbal", "organizacao_perceptual", "icv_iop"),
        ("Compreensão Verbal - Memória Operacional", "compreensao_verbal", "memoria_operacional", "icv_imo"),
        ("Organização Perceptual - Velocidade de Processamento", "organizacao_perceptual", "velocidade_processamento", "iop_ivp"),
        ("Compreensão Verbal - Velocidade de Processamento", "compreensao_verbal", "velocidade_processamento", "icv_ivp"),
        ("Organização Perceptual - Memória Operacional", "organizacao_perceptual", "memoria_operacional", "iop_imo"),
        ("Memória Operacional - Velocidade de Processamento", "memoria_operacional", "velocidade_processamento", "imo_ivp"),
    ]
    B2_COLUMNS = {
        "qiv_qie": "col_1",
        "icv_iop": "col_2",
        "icv_imo": "col_3",
        "iop_ivp": "col_4",
        "icv_ivp": "col_5",
        "iop_imo": "col_6",
        "imo_ivp": "col_7",
    }

    @classmethod
    def generate_pdf_bytes(cls, application) -> bytes:
        template = cls.TEMPLATE_PATH.read_text(encoding="utf-8")
        html_source = cls._render_html(template, application)
        return generate_pdf_from_html(html_source)

    @classmethod
    def _render_html(cls, source: str, application) -> str:
        context = cls._build_context(application)
        rendered = source.replace("    $1\n\n", "")

        replacements = {
            "Nome do Avaliado": context["patient_name"],
            "Masculino": context["patient_sex"],
            "32 anos e 4 meses": context["patient_age"],
            "Ensino superior completo": context["patient_schooling"],
            "Andre Alekhine": context["professional"],
            "WAIS-III / Brasil / Faixa etária correspondente": context["normative_table"],
            "AVL-102": context["application_code"],
            "13/05/2026": context["applied_on"],
        }
        for old, new in replacements.items():
            rendered = rendered.replace(old, html.escape(str(new)))

        rendered = re.sub(
            r"<tbody>\s*<tr><td>Soma dos escores ponderados</td>.*?</tbody>",
            f"<tbody>\n{cls._index_matrix_rows_html(context['index_rows'])}\n          </tbody>",
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="ruler-col rc1"></div>.*?<div class="ruler-col rc7"></div>',
            cls._ruler_cols_html(context["index_rows"]),
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="mini-body"><i class="dot-standard v1"></i>.*?</div>',
            f'<div class="mini-body">{cls._subtest_dots_html(context["verbal_profile"])}</div>',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="mini-body"><i class="dot-standard e1"></i>.*?</div>',
            f'<div class="mini-body">{cls._subtest_dots_html(context["execution_profile"])}</div>',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r"<tbody>\s*<tr><td>QI Verbal</td>.*?</tbody>",
            f"<tbody>\n{cls._summary_rows_html(context['index_rows'])}\n          </tbody>",
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r"<tbody>\s*<tr><td>QI Verbal - QI de Execução</td>.*?</tbody>",
            f"<tbody>\n{cls._discrepancy_rows_html(context['discrepancy_rows'])}\n        </tbody>",
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r"<tbody>\s*<tr><td>Maior Sequência Dígitos Ordem Direta</td>.*?</tbody>",
            f"<tbody>\n{cls._digit_rows_html(context['digit_rows'])}\n        </tbody>",
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'(<table aria-label="Análise de Clusters">.*?<tbody>\s*).*?(\s*</tbody>)',
            lambda match: f"{match.group(1)}\n{cls._cluster_rows_html(context['cluster_rows'])}\n        {match.group(2)}",
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'(<table aria-label="Comparações Clínicas">.*?<tbody>\s*).*?(\s*</tbody>)',
            lambda match: f"{match.group(1)}\n{cls._clinical_comparison_rows_html(context['clinical_comparison_rows'])}\n        {match.group(2)}",
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="clinical">.*?</div>\s*<div class="summary-title">Síntese Interpretativa para o Laudo</div>',
            f'<div class="clinical">\n{cls._paragraphs_html(context["clinical_paragraphs"])}\n    </div>\n\n    <div class="summary-title">Síntese Interpretativa para o Laudo</div>',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = re.sub(
            r'<div class="note-box">Em análise clínica, o avaliado apresenta funcionamento intelectual global.*?</div>',
            f'<div class="note-box">{html.escape(context["synthesis_text"])}</div>',
            rendered,
            count=1,
            flags=re.S,
        )
        rendered = cls._replace_clinical_pages(rendered, context)
        return cls._standardize_footers(rendered)

    @classmethod
    def _build_context(cls, application) -> dict:
        evaluation = getattr(application, "evaluation", None)
        patient = getattr(evaluation, "patient", None)
        raw_payload = getattr(application, "raw_payload", None) or {}
        computed = getattr(application, "computed_payload", None) or {}
        classified = getattr(application, "classified_payload", None) or {}
        indices = classified.get("indices") or computed.get("indices") or {}
        subtests = classified.get("subtestes") or computed.get("subtestes") or {}
        interpretation_text = getattr(application, "interpretation_text", None) or ""

        index_rows = cls._index_rows(indices)
        verbal_profile = cls._profile_rows(subtests, cls.VERBAL_PROFILE)
        execution_profile = cls._profile_rows(subtests, cls.EXECUTION_PROFILE)
        clinical_paragraphs = cls._clinical_paragraphs(interpretation_text)

        return {
            "application_code": cls._application_code(application),
            "report_code": cls._report_code(application),
            "patient_name": getattr(patient, "full_name", None) or "Não informado",
            "patient_sex": cls._sex_label(getattr(patient, "sex", None)),
            "patient_age": cls._age_label(patient, raw_payload, getattr(application, "applied_on", None)),
            "patient_schooling": cls._schooling_label(getattr(patient, "schooling", None)),
            "professional": cls._professional_label(getattr(evaluation, "examiner", None)),
            "normative_table": cls._normative_table_label(computed, raw_payload),
            "applied_on": cls._format_date(getattr(application, "applied_on", None)),
            "index_rows": index_rows,
            "verbal_profile": verbal_profile,
            "execution_profile": execution_profile,
            "discrepancy_rows": cls._discrepancy_rows(indices, classified.get("discrepancias") or computed.get("discrepancias") or []),
            "digit_rows": cls._digit_rows(classified.get("digitos") or computed.get("digitos") or {}),
            "cluster_rows": cls._cluster_rows(classified.get("clusters") or computed.get("clusters") or {}, subtests),
            "clinical_comparison_rows": cls._clinical_comparison_rows(classified.get("clusters") or computed.get("clusters") or {}, subtests),
            "clinical_paragraphs": clinical_paragraphs,
            "synthesis_text": cls._synthesis_text(getattr(patient, "full_name", None), index_rows, clinical_paragraphs),
        }

    @staticmethod
    def _application_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"AVL-{int(base_id):03d}" if isinstance(base_id, int) else f"AVL-{base_id}"

    @staticmethod
    def _report_code(application) -> str:
        base_id = getattr(application, "id", None) or getattr(application, "pk", None) or getattr(application, "evaluation_id", None) or 0
        return f"RPT-WAIS3-{int(base_id):03d}" if isinstance(base_id, int) else f"RPT-WAIS3-{base_id}"

    @staticmethod
    def _sex_label(value: str | None) -> str:
        if value == "M":
            return "Masculino"
        if value == "F":
            return "Feminino"
        return value or "Não informado"

    @staticmethod
    def _schooling_label(value: str | None) -> str:
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
    def _professional_label(examiner) -> str:
        if examiner:
            name = getattr(examiner, "full_name", None) or getattr(examiner, "name", None)
            registration = getattr(examiner, "registration", None) or getattr(examiner, "crp", None)
            if name and registration:
                return f"{name} - {registration}"
            if name:
                return str(name)
        return "Dra. Jacqueline O. Caires - CRP09/6017"

    @classmethod
    def _age_label(cls, patient, raw_payload: dict, applied_on: date | None) -> str:
        age = raw_payload.get("idade") or {}
        years = age.get("anos")
        months = age.get("meses") or 0
        if years is not None:
            return f"{years} anos" + (f" e {months} meses" if months else "")

        explicit_age = getattr(patient, "age", None)
        if explicit_age is not None:
            return f"{explicit_age} anos"

        birth_date = getattr(patient, "birth_date", None)
        if birth_date:
            reference = applied_on or date.today()
            months_total = (reference.year - birth_date.year) * 12 + reference.month - birth_date.month
            if reference.day < birth_date.day:
                months_total -= 1
            years, months = divmod(max(months_total, 0), 12)
            return f"{years} anos" + (f" e {months} meses" if months else "")
        return "Não informado"

    @staticmethod
    def _format_date(value) -> str:
        if not value:
            return "Não informado"
        return value.strftime("%d/%m/%Y") if hasattr(value, "strftime") else str(value)

    @staticmethod
    def _normative_table_label(computed: dict, raw_payload: dict) -> str:
        age_key = computed.get("idade_normativa") or raw_payload.get("idade_normativa")
        if not age_key:
            return "WAIS-III / Brasil / Faixa etária correspondente"
        return f"WAIS-III / Brasil / {str(age_key).replace('idade_', '').replace('-', ' a ')} anos"

    @classmethod
    def _index_rows(cls, indices: dict) -> list[dict]:
        rows = []
        for key, abbreviation in cls.INDEX_ORDER:
            item = indices.get(key) or {}
            rows.append(
                {
                    "key": key,
                    "abbreviation": abbreviation,
                    "name": item.get("nome") or abbreviation,
                    "scaled_sum": cls._format_number(item.get("soma_ponderada")),
                    "score": cls._format_number(item.get("pontuacao_composta")),
                    "score_raw": cls._float(item.get("pontuacao_composta")),
                    "percentile": cls._format_number(item.get("percentil")),
                    "confidence_interval": item.get("ic_95") or item.get("ic_90") or "—",
                    "classification": item.get("classificacao") or "Não classificado",
                }
            )
        return rows

    @classmethod
    def _profile_rows(cls, subtests: dict, profile: list[tuple[str, str]]) -> list[dict]:
        rows = []
        total = len(profile)
        for index, (key, abbreviation) in enumerate(profile):
            item = subtests.get(key) or {}
            score = cls._float(item.get("escore_ponderado"))
            left = ((index + 0.5) / total) * 100.0
            clamped_score = max(1.0, min(19.0, score or 1.0))
            top = ((19.0 - clamped_score + 0.5) / 19.0) * 100.0
            rows.append({"abbreviation": abbreviation, "score": score, "left": left, "top": top})
        return rows

    @classmethod
    def _discrepancy_rows(cls, indices: dict, discrepancy_groups: list[dict]) -> list[dict]:
        significant_pairs = set()
        pair_data = {}
        for group in discrepancy_groups:
            for pair in group.get("pares") or []:
                pair_label = pair.get("par")
                significant_pairs.add(pair_label)
                pair_data[pair_label] = pair

        rows = []
        for label, first, second, frequency_key in cls.DISCREPANCY_PAIRS:
            first_item = indices.get(first) or {}
            second_item = indices.get(second) or {}
            first_score = cls._float(first_item.get("pontuacao_composta"))
            second_score = cls._float(second_item.get("pontuacao_composta"))
            difference = abs(first_score - second_score) if first_score is not None and second_score is not None else None
            pair_label = f"{first_item.get('nome') or first} × {second_item.get('nome') or second}"
            stored_pair = pair_data.get(pair_label) or {}
            rows.append(
                {
                    "label": label,
                    "first": cls._abbreviation_for(first),
                    "second": cls._abbreviation_for(second),
                    "difference": cls._format_number(difference),
                    "significant": "Sim" if pair_label in significant_pairs else "Não" if difference is not None else "—",
                    "frequency": cls._format_frequency(stored_pair.get("frequencia") or stored_pair.get("frequency") or cls._b2_frequency(difference, frequency_key)),
                }
            )
        return rows

    @classmethod
    def _b2_frequency(cls, difference: float | None, frequency_key: str):
        if difference is None:
            return None
        column = cls.B2_COLUMNS.get(frequency_key)
        if not column or not cls.B2_PATH.exists():
            return None
        target = "≥40" if difference >= 40 else str(int(round(difference)))
        with cls.B2_PATH.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if str(row.get("col_0") or "").strip() == target:
                    return row.get(column)
        return None

    @classmethod
    def _digit_rows(cls, digitos: dict) -> list[dict]:
        def raw(key: str, field: str = "raw_score") -> str:
            item = digitos.get(key) or {}
            return cls._format_number(item.get(field))

        def value_or_fallback(value: str, fallback) -> str:
            return value if value != "—" else cls._format_number(fallback)

        def frequency(key: str) -> str:
            item = digitos.get(key) or {}
            return cls._format_number(item.get("cumulative_frequency"), decimals=1)

        return [
            {"label": "Maior Sequência Dígitos Ordem Direta", "first": value_or_fallback(raw("maior_sequencia_direta"), digitos.get("maximo_ordem_direta")), "second": "—", "difference": "—", "frequency": frequency("maior_sequencia_direta")},
            {"label": "Maior Sequência Dígitos Ordem Inversa", "first": value_or_fallback(raw("maior_sequencia_inversa"), digitos.get("maximo_ordem_inversa")), "second": "—", "difference": "—", "frequency": frequency("maior_sequencia_inversa")},
            {"label": "Dígitos Ordem Direta - Ordem Inversa", "first": raw("ordem_direta"), "second": raw("ordem_inversa"), "difference": cls._format_number((digitos.get("diferenca_maior_sequencia") or {}).get("difference") or digitos.get("diferenca_direta_inversa")), "frequency": frequency("diferenca_maior_sequencia")},
        ]

    @classmethod
    def _cluster_rows(cls, clusters: dict, subtests: dict) -> list[dict]:
        rows = []
        for key, code, label, subtest_keys in cls.CLUSTER_ORDER:
            cluster = clusters.get(key) or {}
            span = cls._subtest_span(subtests, subtest_keys)
            interpretable = span is not None and span < 5
            has_score = bool(cluster) and interpretable
            classification = cluster.get("classificacao") if has_score else "Não interpretável" if span is not None and not interpretable else "—"
            rows.append(
                {
                    "key": key,
                    "label": label,
                    "code": code,
                    "span": cls._format_number(span),
                    "interpretable": "SIM" if interpretable else "NÃO" if span is not None else "—",
                    "interpretable_raw": interpretable if span is not None else None,
                    "sum": cls._format_number(cluster.get("soma")) if has_score else "—",
                    "score": cls._format_number(cluster.get("escore")) if has_score else "—",
                    "score_raw": cls._float(cluster.get("escore")) if has_score else None,
                    "confidence_interval": str(cluster.get("ic_95") or "—") if has_score else "—",
                    "percentile": cls._format_number(cluster.get("percentil")) if has_score else "—",
                    "classification": classification,
                }
            )
        return rows

    @classmethod
    def _clinical_comparison_rows(cls, clusters: dict, subtests: dict) -> list[dict]:
        cluster_rows = {row["key"]: row for row in cls._cluster_rows(clusters, subtests)}
        rows = []
        for label, first_key, second_key, critical in cls.CLINICAL_COMPARISONS:
            first = cluster_rows.get(first_key) or {}
            second = cluster_rows.get(second_key) or {}
            first_score = first.get("score_raw")
            second_score = second.get("score_raw")
            difference = first_score - second_score if first_score is not None and second_score is not None else None
            if difference is None:
                rarity = "—"
                relation = "—"
            else:
                rarity = "Raro" if abs(difference) >= critical else "Não raro"
                relation = ">" if difference > 0 else "<" if difference < 0 else "="
            rows.append(
                {
                    "label": label,
                    "first_code": first.get("code") or cls._cluster_code(first_key),
                    "first_score": cls._format_number(first_score),
                    "second_code": second.get("code") or cls._cluster_code(second_key),
                    "second_score": cls._format_number(second_score),
                    "difference": cls._format_number(difference),
                    "difference_raw": difference,
                    "critical": cls._format_number(critical),
                    "rarity": rarity,
                    "relation": relation,
                }
            )
        return rows

    @classmethod
    def _subtest_span(cls, subtests: dict, keys: list[str]) -> float | None:
        scores = []
        for key in keys:
            score = cls._float((subtests.get(key) or {}).get("escore_ponderado"))
            if score is None:
                return None
            scores.append(score)
        return max(scores) - min(scores) if scores else None

    @classmethod
    def _cluster_code(cls, key: str) -> str:
        for cluster_key, code, _label, _subtests in cls.CLUSTER_ORDER:
            if cluster_key == key:
                return code
        return key

    @staticmethod
    def _abbreviation_for(key: str) -> str:
        return dict(WAIS3PdfService.INDEX_ORDER).get(key, key)

    @staticmethod
    def _float(value) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _format_number(cls, value, decimals: int = 0) -> str:
        number = cls._float(value)
        if number is None:
            return "—"
        text = f"{number:.{decimals}f}" if decimals else str(int(round(number)))
        return text.replace(".", ",")

    @classmethod
    def _format_frequency(cls, value) -> str:
        return cls._format_number(value, decimals=1)

    @staticmethod
    def _chart_position(value: float | None, minimum: float, maximum: float) -> float:
        if value is None:
            return 50.0
        clamped = max(minimum, min(maximum, value))
        return ((maximum - clamped) / (maximum - minimum)) * 100.0

    @classmethod
    def _index_matrix_rows_html(cls, rows: list[dict]) -> str:
        def cells(field: str) -> str:
            return "".join(
                f'<td class="sep-left">{html.escape(str(row[field]))}</td>' if index == 3 else f"<td>{html.escape(str(row[field]))}</td>"
                for index, row in enumerate(rows)
            )

        return "\n".join(
            [
                f"<tr><td>Soma dos escores ponderados</td>{cells('scaled_sum')}</tr>",
                f"<tr><td>QI / Índices Fatoriais</td>{cells('score')}</tr>",
                f"<tr><td>Percentil</td>{cells('percentile')}</tr>",
                f"<tr><td>Intervalo de Confiança 95%</td>{cells('confidence_interval')}</tr>",
            ]
        )

    @classmethod
    def _summary_rows_html(cls, rows: list[dict]) -> str:
        return "\n".join(
            f"<tr><td>{html.escape(row['name'])}</td><td>{html.escape(row['scaled_sum'])}</td><td>{html.escape(row['abbreviation'])} {html.escape(row['score'])}</td><td>{html.escape(row['percentile'])}</td><td>{html.escape(str(row['confidence_interval']))}</td></tr>"
            for row in rows
        )

    @classmethod
    def _ruler_cols_html(cls, rows: list[dict]) -> str:
        return "".join(
            f'<div class="ruler-col" style="--score:{cls._chart_position(row.get("score_raw"), 45, 155):.2f}%"></div>'
            for row in rows
        )

    @staticmethod
    def _subtest_dots_html(rows: list[dict]) -> str:
        return "".join(
            f'<i class="dot-standard" style="left:{row["left"]:.2f}%;top:{row["top"]:.2f}%"></i>'
            for row in rows
            if row.get("score") is not None
        )

    @staticmethod
    def _discrepancy_rows_html(rows: list[dict]) -> str:
        return "\n".join(
            f"<tr><td>{html.escape(row['label'])}</td><td>{html.escape(row['first'])}</td><td>{html.escape(row['second'])}</td><td>{html.escape(row['difference'])}</td><td>{html.escape(row['significant'])}</td><td>{html.escape(row['frequency'])}</td></tr>"
            for row in rows
        )

    @staticmethod
    def _digit_rows_html(rows: list[dict]) -> str:
        return "\n".join(
            f"<tr><td>{html.escape(row['label'])}</td><td>{html.escape(row['first'])}</td><td>{html.escape(row['second'])}</td><td>{html.escape(row['difference'])}</td><td>{html.escape(row['frequency'])}</td></tr>"
            for row in rows
        )

    @staticmethod
    def _cluster_rows_html(rows: list[dict]) -> str:
        def classification_class(row: dict) -> str:
            if row.get("interpretable_raw") is False:
                return ' class="not-interpretable"'
            if row.get("classification") in {"Média Superior", "Superior", "Muito Superior"}:
                return ' class="classification-high"'
            return ""

        def interpretable_class(row: dict) -> str:
            return ' class="not-interpretable"' if row.get("interpretable_raw") is False else ""

        return "\n".join(
            f"<tr><td>{html.escape(row['label'])}</td><td class=\"abbr\">{html.escape(row['code'])}</td><td>{html.escape(row['span'])}</td><td{interpretable_class(row)}>{html.escape(row['interpretable'])}</td><td>{html.escape(row['sum'])}</td><td>{html.escape(row['score'])}</td><td>{html.escape(row['confidence_interval'])}</td><td>{html.escape(row['percentile'])}</td><td{classification_class(row)}>{html.escape(row['classification'])}</td></tr>"
            for row in rows
        )

    @staticmethod
    def _clinical_comparison_rows_html(rows: list[dict]) -> str:
        def difference_class(row: dict) -> str:
            return ' class="negative"' if row.get("difference_raw") is not None and row["difference_raw"] < 0 else ""

        return "\n".join(
            f"<tr><td>{html.escape(row['label'])}</td><td class=\"abbr\">{html.escape(row['first_code'])}</td><td>{html.escape(row['first_score'])}</td><td class=\"abbr\">{html.escape(row['second_code'])}</td><td>{html.escape(row['second_score'])}</td><td{difference_class(row)}>{html.escape(row['difference'])}</td><td>{html.escape(row['critical'])}</td><td>{html.escape(row['rarity'])}</td><td class=\"abbr\">{html.escape(row['first_code'])}</td><td class=\"relation\">{html.escape(row['relation'])}</td><td class=\"abbr\">{html.escape(row['second_code'])}</td></tr>"
            for row in rows
        )

    @staticmethod
    def _clinical_paragraphs(text: str) -> list[str]:
        paragraphs = []
        for paragraph in re.split(r"\n\s*\n", text or ""):
            cleaned = re.sub(r"\s+", " ", paragraph).strip()
            cleaned = re.sub(r"^Interpretação e Observações Clínicas\s*:?\s*", "", cleaned, flags=re.I).strip()
            cleaned = re.sub(r"(?:^|(?<=[.!?])\s+)\S*\s*CPI\b[^.!?]*(?:[.!?]|$)", " ", cleaned, flags=re.I).strip()
            cleaned = re.sub(r"(?:^|(?<=[.!?])\s+)\S*\s*Índice de Produtividade Cognitiva[^.!?]*(?:[.!?]|$)", " ", cleaned, flags=re.I).strip()
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if cleaned and cleaned.lower() != "interpretação e observações clínicas":
                paragraphs.append(cleaned)
        return paragraphs or ["Os resultados do WAIS-III devem ser interpretados de forma integrada à entrevista clínica, observações comportamentais, histórico funcional e demais instrumentos utilizados na avaliação neuropsicológica."]

    @staticmethod
    def _paragraphs_html(paragraphs: list[str]) -> str:
        return "\n".join(f"      <p>{html.escape(paragraph)}</p>" for paragraph in paragraphs)

    @classmethod
    def _replace_clinical_pages(cls, rendered: str, context: dict) -> str:
        match = re.search(r'(<section class="page clinical-page">.*?</section>)\s*</body>', rendered, flags=re.S)
        if not match:
            return rendered

        section = match.group(1)
        title_match = re.search(r'<div class="clinical-title">', section)
        if not title_match:
            return rendered

        header_html = section[: title_match.start()]
        blocks = cls._clinical_content_blocks(context)
        pages = cls._paginate_clinical_blocks(blocks)
        total_pages = 3 + len(pages)

        clinical_pages = "\n\n".join(
            cls._clinical_page_html(header_html, page_blocks, page_number=4 + index, total_pages=total_pages)
            for index, page_blocks in enumerate(pages)
        )
        rendered = rendered[: match.start(1)] + clinical_pages + rendered[match.end(1) :]
        return re.sub(r"PÁGINA ([1-3]) DE 4", rf"PÁGINA \1 DE {total_pages}", rendered)

    @classmethod
    def _standardize_footers(cls, rendered: str) -> str:
        return re.sub(
            r'<div class="footer"><span>.*?</span><span>PÁGINA (\d+) DE (\d+)</span></div>',
            lambda match: cls._footer_html(int(match.group(1)), int(match.group(2))),
            rendered,
        )

    @staticmethod
    def _footer_html(page_number: int, total_pages: int) -> str:
        return (
            '    <div class="footer" aria-label="Rodapé Neuroavalia">'
            '<div class="footer-logo">Neuro<span>avalia</span></div>'
            f'<div class="footer-right">Página {page_number} de {total_pages}</div>'
            '</div>'
        )

    @classmethod
    def _clinical_content_blocks(cls, context: dict) -> list[str]:
        blocks = ['    <div class="clinical-title">Interpretação Clínica</div>']
        blocks.extend(f"    <div class=\"clinical\"><p>{html.escape(paragraph)}</p></div>" for paragraph in context["clinical_paragraphs"])
        blocks.append(
            '    <div class="summary-title">Síntese Interpretativa para o Laudo</div>\n'
            f'    <div class="note-box">{html.escape(context["synthesis_text"])}</div>'
        )
        blocks.append(
            '    <div class="summary-title">Pontos de Atenção Clínica</div>\n'
            '    <div class="note-box">O WAIS-III não deve ser utilizado isoladamente para estabelecimento de hipótese diagnóstica. Quando houver queixas de lentificação, desatenção, baixa produtividade, fadiga cognitiva ou dificuldade em tarefas cronometradas, recomenda-se integrar estes achados com medidas específicas de atenção, funções executivas, memória, humor, comportamento adaptativo e histórico funcional.</div>'
        )
        return blocks

    @staticmethod
    def _paginate_clinical_blocks(blocks: list[str]) -> list[list[str]]:
        pages = []
        current = []
        current_size = 0
        page_limit = 2600
        for block in blocks:
            block_size = len(re.sub(r"<[^>]+>", "", block)) + 180
            if current and current_size + block_size > page_limit:
                pages.append(current)
                current = []
                current_size = 0
            current.append(block)
            current_size += block_size
        if current:
            pages.append(current)
        return pages or [[]]

    @staticmethod
    def _clinical_page_html(header_html: str, blocks: list[str], *, page_number: int, total_pages: int) -> str:
        content = "\n\n".join(blocks)
        return (
            f"{header_html}\n"
            f"{content}\n\n"
            f'{WAIS3PdfService._footer_html(page_number, total_pages)}\n'
            "  </section>"
        )

    @classmethod
    def _synthesis_text(cls, patient_name: str | None, index_rows: list[dict], paragraphs: list[str]) -> str:
        qit = next((row for row in index_rows if row["key"] == "qi_total"), {})
        scored = [row for row in index_rows if row.get("score_raw") is not None]
        highest = max(scored, key=lambda row: row["score_raw"], default={})
        lowest = min(scored, key=lambda row: row["score_raw"], default={})
        first_name = (patient_name or "Paciente").strip().split()[0] or "Paciente"
        if paragraphs:
            base = paragraphs[0]
        else:
            base = f"Em análise clínica, {first_name} apresentou funcionamento intelectual global na faixa {qit.get('classification', 'não classificada')}."
        if highest and lowest and highest is not lowest:
            return f"{base} O perfil deve considerar maior desempenho relativo em {highest['name']} e menor desempenho relativo em {lowest['name']}, exigindo integração com dados clínicos e funcionais."
        return f"{base} Os achados devem ser integrados aos demais dados clínicos e funcionais antes de qualquer conclusão diagnóstica."
