import re

from django.utils import timezone

from apps.ai.services.ai_healthcheck_service import AIHealthcheckService
from apps.evaluations.models import EvaluationStatus
from apps.reports.models import Report, ReportSection, ReportStatus
from apps.reports.builders.references_builder import build_references_text
from apps.reports.services.report_ai_service import ReportAIService
from apps.reports.services.report_context_service import ReportContextService
from apps.reports.services.ptbr_text_service import PtBrTextService
from apps.reports.services.report_review_service import ReportReviewService
from apps.reports.services.wisc4_standardization import WISC4StandardizationService
from apps.reports.services.wais3_standardization import WAIS3StandardizationService
from apps.tests.srs2.interpreters import interpret_srs2_results
from apps.reports.services.section_registry import (
    get_section_config,
    list_section_configs,
)
from apps.reports.services.report_version_service import ReportVersionService


class ReportGenerationService:
    FIXED_AUTHOR = "Jacqueline Oliveira Caires (CRP 09/6017)"
    FIXED_PURPOSE = "Averiguação das capacidades cognitivas para auxílio diagnóstico"
    PROCEDURE_CATALOG = {
        "anamnese": "Entrevista clínica inicial destinada ao levantamento da história do desenvolvimento, queixas atuais, antecedentes médicos, escolares, familiares, emocionais e comportamentais, com o objetivo de contextualizar os dados obtidos nos demais instrumentos.",
        "wisc4": "Utilizada para avaliar o funcionamento intelectual global, os índices fatoriais (Compreensão Verbal, Organização Perceptual, Memória Operacional e Velocidade de Processamento) e fornecer indicadores sobre o perfil cognitivo.",
        "bpa2": "Avalia a capacidade geral de atenção, incluindo atenção concentrada, alternada, dividida e atenção global.",
        "fdt": "Investiga a velocidade de processamento, controle inibitório, alternância e flexibilidade cognitiva.",
        "ravlt": "Avalia memória verbal episódica, aquisição, retenção, recuperação e resistência à interferência.",
        "etdah_pais": "Questionário para identificação de sintomas de desatenção, impulsividade, hiperatividade, regulação emocional e comportamento adaptativo, a partir da percepção dos responsáveis.",
        "scared": "Avalia sintomas ansiosos em crianças e adolescentes, incluindo ansiedade generalizada, ansiedade de separação, fobia social, pânico e sintomas somáticos, com base no autorrelato.",
        "epq_j": "Avalia traços de personalidade em crianças e adolescentes, contemplando dimensões como extroversão, neuroticismo, psicoticismo e sinceridade.",
    }
    PROCEDURE_NAMES = {
        "anamnese": "Anamnese",
        "wisc4": "Escala Wechsler de Inteligência para Crianças – Quarta Edição (WISC-IV)",
        "bpa2": "Bateria Psicológica para Avaliação da Atenção – Segunda Edição (BPA-2)",
        "fdt": "Teste dos Cinco Dígitos (FDT)",
        "ravlt": "Teste de Aprendizagem Auditivo-Verbal de Rey (RAVLT)",
        "etdah_pais": "Escala para Transtorno de Déficit de Atenção e Hiperatividade – Versão Pais (E-TDAH-PAIS)",
        "scared": "SCARED – Autorrelato (Screen for Child Anxiety Related Emotional Disorders)",
        "epq_j": "Inventário de Personalidade de Eysenck para Jovens (EPQ-J)",
    }
    PROCEDURE_ORDER = ["anamnese", "wisc4", "bpa2", "fdt", "ravlt", "etdah_pais", "scared", "epq_j"]
    AI_FALLBACK_WARNING = "A IA nao esta disponivel no momento; o texto foi gerado pelo fallback deterministico."
    EMPTY_INTERPRETATION_MESSAGES = {
        "Nenhum instrumento específico deste domínio apresentou interpretação clínica consolidada.",
    }

    SECTION_GROUPS = {
        "capacidade_cognitiva_global": {"eficiencia_intelectual"},
        "linguagem": {"linguagem"},
        "gnosias_praxias": {"gnosias_praxias"},
        "atencao": {"atencao"},
        "memoria_aprendizagem": {"memoria_aprendizagem"},
        "funcoes_executivas": {"funcoes_executivas"},
        "aspectos_emocionais_comportamentais": {"escalas_complementares"},
    }

    @staticmethod
    def construct_clinical_context(evaluation):
        return ReportContextService.build_context(evaluation)

    @staticmethod
    def get_sections_config():
        return [(key, config["title"]) for key, config in list_section_configs()]

    @staticmethod
    def _has_ai_section(section_key: str) -> bool:
        return bool(get_section_config(section_key).get("supports_ai"))

    @classmethod
    def _has_test(cls, context: dict, *codes: str) -> bool:
        available = {
            item.get("instrument_code") for item in context.get("validated_tests") or []
        }
        return any(code in available for code in codes)

    @classmethod
    def _enabled_sections_config(cls, context: dict):
        is_adolescent = cls._is_adolescent_case(context)
        base = []
        for key, title in cls.get_sections_config():
            config = get_section_config(key)
            required_any_codes = tuple(config.get("required_any_codes") or ())
            enabled = True
            if required_any_codes:
                enabled = cls._has_test(context, *required_any_codes)
            if not enabled and config.get("enable_when_adolescent"):
                enabled = is_adolescent
            if enabled:
                base.append((key, title))
        renumbered = []
        for index, (key, title) in enumerate(base, start=1):
            clean_title = title.split(". ", 1)[1] if ". " in title else title
            renumbered.append((key, f"{index}. {clean_title}"))
        return renumbered

    @classmethod
    def generate_full_report(cls, report: Report, user=None):
        context = cls.construct_clinical_context(report.evaluation)
        sections_config = cls._enabled_sections_config(context)
        from apps.reports.services.report_pipeline_service import ReportPipelineService

        ReportPipelineService.generate_full_report(report, context, user=user)
        report.refresh_from_db()
        return report

    @classmethod
    def _generate_section_payload(cls, report: Report, key: str, context: dict):
        if WISC4StandardizationService.supports(key, context):
            return (
                PtBrTextService.normalize(WISC4StandardizationService.build(key, context)),
                {
                    "provider": "deterministic",
                    "model": "standardized-wisc4",
                    "section": key,
                    "used_fallback": False,
                    "generation_path": "deterministic_wisc4_standardized",
                },
                [],
            )

        if WAIS3StandardizationService.supports(key, context):
            return (
                PtBrTextService.normalize(WAIS3StandardizationService.build(key, context)),
                {
                    "provider": "deterministic",
                    "model": "standardized-wais3",
                    "section": key,
                    "used_fallback": False,
                    "generation_path": "deterministic_wais3_standardized",
                },
                [],
            )

        if ReportAIService.supports_section(key):
            try:
                generation_result = ReportAIService.generate_section(
                    report, key, context
                )
                content = generation_result.get("content") or ""
                if content.strip():
                    return (
                        PtBrTextService.normalize(content),
                        generation_result.get("metadata") or {},
                        generation_result.get("warnings") or [],
                    )
            except Exception as exc:
                fallback_content = cls._generate_section_text(report, key, context)
                return (
                    PtBrTextService.normalize(fallback_content),
                    {
                        "provider": "deterministic",
                        "model": "rules-based",
                        "section": key,
                        "fallback_reason": str(exc),
                        "used_fallback": True,
                        "generation_path": "deterministic_fallback",
                    },
                    [cls.AI_FALLBACK_WARNING],
                )

        return (
            PtBrTextService.normalize(cls._generate_section_text(report, key, context)),
            {
                "provider": "deterministic",
                "model": "rules-based",
                "section": key,
                "used_fallback": False,
                "generation_path": "deterministic_only",
            },
            [],
        )

    @staticmethod
    def _format_sex(value: str | None) -> str:
        if not value:
            return "Não informado"
        mapping = {"M": "Masculino", "F": "Feminino", "O": "Outro"}
        return mapping.get(value, value)

    @staticmethod
    def _format_date(value: str | None) -> str:
        if not value:
            return "Não informado"
        try:
            year, month, day = value.split("-")
            return f"{day}/{month}/{year}"
        except ValueError:
            return value

    @staticmethod
    def _format_age(context: dict) -> str:
        birth_date = context["patient"].get("birth_date")
        if not birth_date:
            return "Não informada"
        try:
            from datetime import date

            year, month, day = map(int, birth_date.split("-"))
            born = date(year, month, day)
            today = date.today()
            years = (
                today.year
                - born.year
                - ((today.month, today.day) < (born.month, born.day))
            )
            months = (today.month - born.month) % 12
            return f"{years} anos e {months} meses"
        except ValueError:
            return "Não informada"

    @staticmethod
    def _age_years(context: dict) -> int | None:
        birth_date = context["patient"].get("birth_date")
        if not birth_date:
            return None
        try:
            from datetime import date

            year, month, day = map(int, birth_date.split("-"))
            born = date(year, month, day)
            today = date.today()
            return (
                today.year
                - born.year
                - ((today.month, today.day) < (born.month, born.day))
            )
        except ValueError:
            return None

    @staticmethod
    def _build_filiation(patient: dict) -> str:
        names = [patient.get("father_name"), patient.get("mother_name")]
        names = [
            name.strip() for name in names if isinstance(name, str) and name.strip()
        ]
        if names:
            return " e ".join(names)
        if patient.get("responsible_name"):
            return str(patient.get("responsible_name"))
        return "Não informada"

    @classmethod
    def _is_adolescent_case(cls, context: dict) -> bool:
        template_code = (
            (context.get("anamnesis") or {}).get("current_response") or {}
        ).get("template_code") or ""
        age = cls._age_years(context)
        return "adolescent" in template_code or (age is not None and 12 <= age < 18)

    @staticmethod
    def _answers_payload(context: dict) -> dict:
        return ((context.get("anamnesis") or {}).get("current_response") or {}).get(
            "answers_payload"
        ) or {}

    @classmethod
    def _pick_answer(cls, context: dict, *keys: str) -> str:
        answers = cls._answers_payload(context)
        for key in keys:
            value = answers.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, (int, float)):
                return str(value)
            if isinstance(value, list) and value:
                parts = [str(item).strip() for item in value if str(item).strip()]
                if parts:
                    return "; ".join(parts)
        return ""

    @classmethod
    def _adolescent_history_sections(cls, context: dict) -> list[tuple[str, str]]:
        sections = [
            (
                "Gestação e parto",
                cls._pick_answer(context, "pregnancy_birth_intercurrences"),
            ),
            (
                "Desenvolvimento motor",
                cls._pick_answer(context, "motor_development_notes", "motor_delay"),
            ),
            (
                "Desenvolvimento linguístico",
                cls._pick_answer(
                    context, "language_development_notes", "language_delay"
                ),
            ),
            (
                "Desenvolvimento socioemocional",
                cls._pick_answer(
                    context,
                    "social_emotional_development",
                    "relationship_mother",
                    "relationship_father",
                    "relationship_siblings",
                ),
            ),
            (
                "Histórico médico",
                cls._pick_answer(
                    context, "medical_history", "medical_notes", "medical_specialties"
                ),
            ),
            (
                "Sono e alimentação",
                cls._pick_answer(context, "sleep_pattern", "eating_pattern"),
            ),
            (
                "Histórico educacional",
                cls._pick_answer(
                    context,
                    "school_history",
                    "learning_difficulties",
                    "school_observations",
                ),
            ),
            (
                "Rotina atual",
                cls._pick_answer(
                    context, "daily_routine", "screen_time", "leisure_activities"
                ),
            ),
            (
                "Informações adicionais",
                cls._pick_answer(context, "additional_notes", "current_main_concern"),
            ),
        ]
        return [(title, text) for title, text in sections if text]

    @classmethod
    def _procedure_lines(cls, context: dict) -> list[str]:
        validated_codes = []
        seen_codes = {"anamnese"}
        for test in context.get("validated_tests") or []:
            code = test.get("instrument_code")
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)
            validated_codes.append(code)

        ordered_codes = [
            code for code in cls.PROCEDURE_ORDER if code == "anamnese" or code in validated_codes
        ]

        lines = []
        for code in ordered_codes:
            name = cls.PROCEDURE_NAMES.get(code)
            description = cls.PROCEDURE_CATALOG.get(code)
            if not name or not description:
                continue
            lines.append(f"• {name}: {description}")

        return lines

    @staticmethod
    def _anamnesis_summary(context: dict) -> str:
        payload = context.get("anamnesis", {}).get("current_response") or {}
        summary_payload = payload.get("summary_payload") or {}
        if isinstance(summary_payload, dict):
            values = [str(value).strip() for value in summary_payload.values() if value]
            if values:
                return " ".join(values[:3])
        answers = payload.get("answers_payload") or {}
        if isinstance(answers, dict):
            values = [
                str(value).strip()
                for value in answers.values()
                if isinstance(value, (str, int, float)) and value
            ]
            if values:
                return " ".join(values[:4])
        return "Não houve anamnese estruturada suficiente registrada até o momento da geração do laudo."

    @staticmethod
    def _progress_summary(context: dict) -> str:
        entries = context.get("progress_entries") or []
        if not entries:
            return "Não há registros evolutivos incluídos no laudo até o momento."
        parts = []
        for entry in entries[:3]:
            chunk = " ".join(
                filter(
                    None,
                    [
                        entry.get("objective", ""),
                        entry.get("observed_behavior", ""),
                        entry.get("clinical_notes", ""),
                        entry.get("next_steps", ""),
                    ],
                )
            ).strip()
            if chunk:
                parts.append(chunk)
        return (
            " ".join(parts)
            if parts
            else "Há registros evolutivos, porém sem síntese clínica adicional."
        )

    @classmethod
    def _tests_for_section(cls, context: dict, section_key: str) -> list[dict]:
        target_sections = cls.SECTION_GROUPS.get(section_key, set())
        tests = context.get("validated_tests") or []
        filtered = [
            test for test in tests if test.get("report_section") in target_sections
        ]
        if filtered:
            return filtered
        if section_key in {
            "linguagem",
            "gnosias_praxias",
            "capacidade_cognitiva_global",
        }:
            return [
                test
                for test in tests
                if test.get("instrument_code") in {"wisc4", "wasi", "wais3"}
            ]
        return filtered

    @staticmethod
    def _tests_bullet_list(tests: list[dict]) -> str:
        if not tests:
            return (
                "Nenhum instrumento específico deste domínio foi validado na avaliação."
            )
        lines = []
        for test in tests:
            summary = (
                test.get("summary")
                or test.get("clinical_interpretation")
                or "Sem interpretação clínica consolidada."
            )
            lines.append(f"- {test.get('instrument_name')}: {summary}")
        return "\n".join(lines)

    @staticmethod
    def _tests_detailed_blocks(tests: list[dict]) -> str:
        if not tests:
            return (
                "Nenhum instrumento específico deste domínio foi validado na avaliação."
            )

        blocks = []
        for test in tests:
            lines = [f"Instrumento: {test.get('instrument_name')}"]
            if test.get("applied_on"):
                lines.append(
                    f"Data de aplicação: {ReportGenerationService._format_date(test.get('applied_on'))}"
                )

            result_rows = test.get("result_rows") or []
            if result_rows:
                lines.append("Resultados estruturados:")
                lines.extend(result_rows)

            interpretation = test.get("clinical_interpretation") or test.get("summary")
            if interpretation:
                lines.append(f"Interpretação clínica: {interpretation}")

            for warning in test.get("warnings") or []:
                lines.append(f"Observação técnica: {warning}")

            blocks.append("\n".join(lines))

        return "\n\n".join(blocks)

    @staticmethod
    def _clean_clinical_interpretation(text: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return ""

        for prefix in (
            "Interpretação clínica:",
            "Interpretação e Observações Clínicas:",
        ):
            if cleaned.casefold().startswith(prefix.casefold()):
                cleaned = cleaned[len(prefix):].strip()

        cleaned = re.sub(
            r"={20,}\s*\n"
            r"Fator\s+Pts\s*Brts\s+T-Score\s+Percentil\s+Classifica(?:ç|c)ão\s*\n"
            r"={20,}\s*\n"
            r".*?"
            r"\n={20,}",
            "",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()

        if cleaned in ReportGenerationService.EMPTY_INTERPRETATION_MESSAGES:
            return ""

        return cleaned

    @staticmethod
    def _fallback_test_interpretation(test: dict) -> str:
        if test.get("instrument_code") != "srs2":
            return ""

        merged_data = {
            **(test.get("computed_payload") or {}),
            **(test.get("classified_payload") or test.get("structured_results") or {}),
        }
        return (interpret_srs2_results(merged_data) or "").strip()

    @staticmethod
    def _test_report_payload(test: dict | None) -> dict:
        return (test or {}).get("report_payload") or {}

    @classmethod
    def _test_interpretation(cls, test: dict | None) -> str:
        payload = cls._test_report_payload(test)
        return (
            payload.get("interpretation")
            or payload.get("summary_for_report")
            or (test or {}).get("clinical_interpretation")
            or (test or {}).get("interpretation_text")
            or (test or {}).get("summary")
            or cls._fallback_test_interpretation(test or {})
            or ""
        )

    @staticmethod
    def _patient_name(context: dict) -> str:
        return ((context.get("patient") or {}).get("full_name") or "Paciente").strip() or "Paciente"

    @staticmethod
    def _patient_first_name(context: dict) -> str:
        full_name = ReportGenerationService._patient_name(context)
        return full_name.split(" ", 1)[0] or full_name

    @staticmethod
    def _foreign_patient_names_in_text(text: str | None, patient_name: str | None) -> list[str]:
        patient_name = (patient_name or "").strip()
        if not patient_name:
            return []
        allowed_tokens = {token for token in patient_name.split() if token}
        technical_tokens = {
            "Raciocínio", "Matricial", "Execução", "Tabela", "Rey", "Auditory", "Verbal",
            "Learning", "Test", "Flexibilidade", "Cognitiva", "Big", "Five", "Interações",
            "Sociais", "Espectro", "Autista", "Pontuação", "Total", "Vocabulário",
            "Semelhanças", "Cubos", "Pânico", "Sintomas", "Somáticos", "Ansiedade",
            "Generalizada", "Separação", "Fobia", "Social", "Evitação", "Escolar",
            "Percepção", "Cognição", "Comunicação", "Motivação", "Realização", "Abertura",
        }
        ignored_names = {
            patient_name,
            "Conselho Federal",
            "Microsoft Word",
            "Escala Wechsler",
            "Bateria Psicológica",
            "Teste dos",
            "Rey Auditory",
            "Escala Baptista",
            "Bateria Fatorial",
            "Social Responsiveness",
            "Screen for Child",
            "Rey Auditory Verbal Learning Test",
            "Raciocínio Matricial",
            "Flexibilidade Cognitiva",
            "Interações Sociais",
            "Espectro Autista",
            "Pontuação Total",
            "Big Five",
            "Execução Tabela",
        }
        candidates = re.findall(
            r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)+\b",
            text or "",
        )
        foreign_names = []
        for name in candidates:
            if name in ignored_names:
                continue
            words = name.split()
            if len(words) < 2 or len(words) > 5:
                continue
            if all(word in technical_tokens for word in words):
                continue
            if name == patient_name or words[0] in allowed_tokens:
                continue
            if name not in foreign_names:
                foreign_names.append(name)
        return foreign_names

    @classmethod
    def _section_text(cls, report: Report, key: str, context: dict) -> str:
        section = report.sections.filter(key=key).first()
        if not section:
            return ""
        text = str(section.content_edited or section.content_generated or "").strip()
        patient_name = (context.get("patient") or {}).get("full_name") if isinstance(context, dict) else ""
        if cls._foreign_patient_names_in_text(text, patient_name):
            return ""
        return text

    @staticmethod
    def _has_any_keyword(text: str, keywords: tuple[str, ...]) -> bool:
        lowered = (text or "").casefold()
        return any(keyword.casefold() in lowered for keyword in keywords)

    @classmethod
    def _domain_clause(cls, text: str, label: str) -> str:
        if not text:
            return f"dados insuficientes para definição mais precisa do domínio de {label.lower()}"

        if cls._has_any_keyword(text, ("preservad", "adequad", "dentro dos limites", "compatível")):
            mapping = {
                "Linguagem": "recursos de linguagem globalmente preservados, com boa sustentação da compreensão e da expressão verbal",
                "Funções executivas": "funcionamento executivo globalmente preservado, com recursos adequados para planejamento, monitoramento e controle cognitivo",
                "Atenção": "funcionamento atencional sem indicativos de comprometimento global expressivo em contexto estruturado",
                "Memória": "recursos de memória e aprendizagem globalmente preservados para retenção, evocação e manejo de informações",
                "Gnosias e praxias": "habilidades de gnosias e praxias preservadas, com adequada organização perceptual e construtiva",
            }
            return mapping.get(label, f"funcionamento de {label.lower()} globalmente preservado")

        if cls._has_any_keyword(text, ("heterog", "misto", "oscil", "variável", "fragilidades pontuais")):
            mapping = {
                "Linguagem": "perfil de linguagem relativamente heterogêneo, com recursos preservados e fragilidades pontuais no processamento verbal",
                "Funções executivas": "perfil executivo heterogêneo, com variabilidade entre organização, flexibilidade e controle mental",
                "Atenção": "perfil atencional oscilante, com melhor desempenho em algumas condições e vulnerabilidade em outras",
                "Memória": "desempenho mnésico heterogêneo, com variação entre retenção, aprendizagem e recuperação das informações",
                "Gnosias e praxias": "perfil visuoperceptivo e praxico heterogêneo, com recursos preservados coexistindo com fragilidades específicas",
            }
            return mapping.get(label, f"funcionamento de {label.lower()} heterogêneo")

        mapping = {
            "Linguagem": "fragilidades no domínio da linguagem, com possível impacto sobre a compreensão, a elaboração verbal e o uso funcional da comunicação",
            "Funções executivas": "fragilidades executivas com repercussão potencial sobre planejamento, flexibilidade cognitiva, autorregulação e organização do comportamento",
            "Atenção": "fragilidades atencionais com potencial repercussão sobre sustentação do foco, monitoramento e consistência do desempenho",
            "Memória": "fragilidades em memória e aprendizagem, com repercussão possível sobre retenção ativa, consolidação e evocação de conteúdos",
            "Gnosias e praxias": "fragilidades em gnosias e praxias, com possível impacto sobre a organização visuoespacial e a execução construtiva",
        }
        return mapping.get(label, f"fragilidades clinicamente relevantes no domínio de {label.lower()}")

    @classmethod
    def _build_conclusion_text(cls, report: Report, context: dict) -> str:
        if cls._is_adolescent_case(context) and any(
            item.get("instrument_code") == "wisc4"
            for item in (context.get("validated_tests") or [])
        ):
            return cls._build_wisc4_adolescent_conclusion(report, context)

        name = cls._patient_name(context)
        first_name = cls._patient_first_name(context)
        evaluation = context.get("evaluation") or {}
        patient = context.get("patient") or {}
        referral_reason = (evaluation.get("referral_reason") or "").strip()
        hypothesis = (evaluation.get("clinical_hypothesis") or "").strip()
        validated_tests = context.get("validated_tests") or []

        cognitive_text = cls._section_text(report, "capacidade_cognitiva_global", context)
        language_text = cls._section_text(report, "linguagem", context)
        executive_text = cls._section_text(report, "funcoes_executivas", context)
        attention_text = cls._section_text(report, "atencao", context)
        memory_text = cls._section_text(report, "memoria_aprendizagem", context)
        praxis_text = cls._section_text(report, "gnosias_praxias", context)
        emotional_text = cls._section_text(report, "aspectos_emocionais_comportamentais", context)
        social_text = cls._section_text(report, "srs2", context)

        test_names = [
            item.get("instrument_name") or item.get("instrument") or item.get("instrument_code")
            for item in validated_tests
            if item.get("instrument_name") or item.get("instrument") or item.get("instrument_code")
        ]
        unique_test_names = list(dict.fromkeys(test_names))
        if len(unique_test_names) == 1:
            tests_sentence = f"Na integração dos achados, os resultados do instrumento {unique_test_names[0]} foram considerados em conjunto com a observação clínica e os dados anamnésticos."
        elif unique_test_names:
            tests_sentence = (
                "Na integração dos achados, foram considerados de forma articulada os resultados de "
                f"{', '.join(unique_test_names[:-1])} e {unique_test_names[-1]}, sempre em correlação com a observação clínica e os dados da anamnese."
            )
        else:
            tests_sentence = (
                "Na integração dos achados, os dados dos instrumentos aplicados foram considerados em conjunto com a observação clínica e as informações anamnésticas disponíveis."
            )

        if cls._has_any_keyword(cognitive_text, ("superior", "muito superior", "alta capacidade")):
            cognitive_sentence = (
                f"{name} apresenta funcionamento intelectual global acima do esperado, com desempenho intelectual situado em faixa superior e evidenciando recursos consistentes para raciocínio, elaboração conceitual e resolução de demandas complexas."
            )
        elif cls._has_any_keyword(cognitive_text, ("heterog", "variável", "misto")):
            cognitive_sentence = (
                f"{name} apresenta funcionamento intelectual global heterogêneo, com desempenho intelectual situado em faixa variável entre os domínios avaliados, evidenciando dissociação entre recursos preservados e áreas de maior vulnerabilidade funcional."
            )
        elif cls._has_any_keyword(cognitive_text, ("inferior", "limítrofe", "baixo", "fragil")):
            cognitive_sentence = (
                f"{name} apresenta funcionamento intelectual global com fragilidades clinicamente relevantes, com desempenho intelectual situado abaixo do esperado para parte das demandas avaliadas, evidenciando impacto potencial sobre autonomia, aprendizagem e adaptação a exigências complexas."
            )
        else:
            cognitive_sentence = (
                f"{name} apresenta funcionamento intelectual global globalmente preservado, com desempenho intelectual situado dentro da faixa esperada para o contexto avaliado, evidenciando recursos adequados para o manejo de demandas cognitivas gerais em ambiente estruturado."
            )

        domain_sentence = (
            f"{first_name} demonstra, no plano dos domínios cognitivos específicos, "
            f"{cls._domain_clause(language_text, 'Linguagem')}; "
            f"{cls._domain_clause(executive_text, 'Funções executivas')}; "
            f"{cls._domain_clause(attention_text, 'Atenção')}; "
            f"{cls._domain_clause(memory_text, 'Memória')}; e "
            f"{cls._domain_clause(praxis_text, 'Gnosias e praxias')}."
        )

        executive_attention_sentence = (
            f"No eixo executivo-atencional, a integração entre dados de funções executivas, atenção sustentada e observação clínica sugere que {first_name} "
            "responde melhor em contexto estruturado do que em situações cotidianas de maior exigência autorregulatória, especialmente quando há aumento da demanda de organização, monitoramento e flexibilidade mental."
        )

        memory_sentence = (
            f"No campo da memória e da aprendizagem, os achados sugerem que {first_name} apresenta desempenho que deve ser compreendido de forma integrada entre retenção imediata, manipulação mental de informações e consolidação de conteúdo, sem reduzir a análise a um único instrumento isolado."
        )

        emotional_sentence = (
            f"No âmbito emocional e comportamental, a leitura integrada dos instrumentos complementares e da observação clínica indica que fatores afetivos, sociais e autorregulatórios participam da expressão funcional do desempenho de {first_name}, modulando a adaptação às exigências escolares, sociais e cotidianas."
        )

        social_sentence = (
            f"Na responsividade social, os achados do SRS-2 devem ser compreendidos em conjunto com a observação clínica direta, contribuindo para a análise qualitativa da interação social recíproca, da comunicação pragmática e de eventuais padrões comportamentais mais rígidos ou repetitivos apresentados por {first_name}."
            if social_text or any(item.get("instrument_code") == "srs2" for item in validated_tests)
            else f"Na responsividade social, os dados disponíveis sugerem que a análise do funcionamento interpessoal de {first_name} deve permanecer integrada à observação clínica e ao histórico do desenvolvimento."
        )

        if cls._has_any_keyword(emotional_text, ("ansied", "depress", "social", "comportament", "emocion")) and cls._has_any_keyword(cognitive_text, ("preservad", "esperad", "média", "adequad")):
            dissociation_sentence = (
                "Evidencia-se dissociação clínica entre o desempenho obtido em ambiente estruturado de avaliação e as exigências adaptativas do cotidiano, sugerindo que fatores emocionais, comportamentais e contextuais podem modular de forma relevante a expressão funcional do repertório cognitivo."
            )
        else:
            dissociation_sentence = (
                "Evidencia-se dissociação clínica entre áreas relativamente preservadas e domínios de maior vulnerabilidade, o que reforça a necessidade de leitura integrada entre desempenho psicométrico, observação comportamental e impacto funcional no cotidiano."
            )

        context_target = "escolar" if patient.get("schooling") or patient.get("school_name") else "cotidiano"
        ecological_sentence = (
            f"Em contexto ecológico, verifica-se que os achados descritos tendem a repercutir sobre a organização da rotina, o manejo das demandas de {context_target}, a autorregulação e a consistência do desempenho diante de situações que exigem autonomia, flexibilidade e adaptação."
        )
        if referral_reason:
            ecological_sentence = (
                f"Em contexto ecológico, verifica-se que os achados descritos dialogam diretamente com a demanda de avaliação, especialmente no que se refere a {referral_reason[0].lower() + referral_reason[1:] if len(referral_reason) > 1 else referral_reason.lower()}, com possível repercussão sobre rotina, desempenho funcional e autorregulação."
            )

        if emotional_text:
            psycho_sentence = (
                f"A integração dos dados psicocomportamentais indica que aspectos emocionais, sociais e comportamentais devem ser considerados como moduladores do funcionamento global de {first_name}, sobretudo na expressão cotidiana das habilidades cognitivas e na qualidade do ajustamento adaptativo."
            )
        else:
            psycho_sentence = (
                f"A integração dos dados psicocomportamentais não afasta a influência de fatores emocionais e contextuais sobre o funcionamento de {first_name}, motivo pelo qual o desempenho deve ser sempre interpretado de forma contextualizada e não exclusivamente psicométrica."
            )

        summary_profile = (
            "um perfil neuropsicológico heterogêneo, com integração entre recursos preservados e áreas de vulnerabilidade"
            if cls._has_any_keyword(cognitive_sentence, ("heterogêneo", "fragilidades", "dissociação"))
            else "um perfil neuropsicológico globalmente preservado em ambiente estruturado, mas dependente de integração com os dados funcionais e comportamentais"
        )
        conclusion_sentence = (
            f"Diante da análise dos resultados das testagens, das observações clínicas e dos dados da anamnese, conclui-se que {first_name} apresenta {summary_profile}."
        )

        if hypothesis:
            hypothesis_sentence = (
                f"Há hipótese diagnóstica de {hypothesis}, conforme critérios do DSM-5-TR™, sustentada pela integração entre o desempenho cognitivo, os achados comportamentais, o histórico do desenvolvimento e o impacto funcional descrito ao longo da avaliação."
            )
        else:
            hypothesis_sentence = (
                "Há hipótese diagnóstica em investigação clínica, conforme referenciais do DSM-5-TR™, devendo sua formulação final permanecer vinculada à integração entre achados neuropsicológicos, observação clínica, histórico do desenvolvimento e evolução funcional."
            )

        impact_sentence = (
            f"As alterações identificadas repercutem funcionalmente sobre o contexto {context_target}, as interações sociais, a organização do comportamento e a adaptação às exigências ambientais, com intensidade dependente da complexidade das demandas e do nível de suporte disponível."
        )
        prognosis_sentence = (
            f"O perfil apresentado sugere prognóstico dependente da articulação entre fatores de proteção, como recursos cognitivos preservados, possibilidade de intervenção precoce e suporte familiar/escolar, e fatores de risco, como persistência das vulnerabilidades identificadas, impacto emocional e sobrecarga adaptativa."
        )
        dynamic_sentence = (
            "Ressalta-se que o ser humano possui uma natureza dinâmica, não definitiva e não cristalizada, de modo que o funcionamento descrito refere-se ao momento atual da avaliação e pode modificar-se conforme desenvolvimento, intervenções, condições contextuais e resposta terapêutica."
        )

        return "\n\n".join(
            [
                cognitive_sentence,
                tests_sentence,
                domain_sentence,
                executive_attention_sentence,
                memory_sentence,
                emotional_sentence,
                social_sentence,
                dissociation_sentence,
                ecological_sentence,
                psycho_sentence,
                conclusion_sentence,
                hypothesis_sentence,
                impact_sentence,
                prognosis_sentence,
                dynamic_sentence,
                "Em análise clínica.",
            ]
        )

    @classmethod
    def _build_wisc4_adolescent_conclusion(cls, report: Report, context: dict) -> str:
        name = cls._patient_name(context)
        first_name = cls._patient_first_name(context)
        evaluation = context.get("evaluation") or {}
        hypothesis = (evaluation.get("clinical_hypothesis") or "em investigação clínica").strip()
        validated_tests = context.get("validated_tests") or []
        wisc4_test = next(
            (item for item in validated_tests if item.get("instrument_code") == "wisc4"),
            {},
        )
        structured = wisc4_test.get("structured_results") or {}
        qit = structured.get("qit_data") or {}
        indices = {item.get("indice"): item for item in structured.get("indices") or []}

        cognitive_text = cls._section_text(report, "capacidade_cognitiva_global", context)
        language_text = cls._section_text(report, "linguagem", context)
        executive_text = cls._section_text(report, "funcoes_executivas", context)
        attention_text = cls._section_text(report, "atencao", context)
        memory_text = cls._section_text(report, "memoria_aprendizagem", context)
        praxis_text = cls._section_text(report, "gnosias_praxias", context)
        emotional_text = cls._section_text(report, "aspectos_emocionais_comportamentais", context)
        social_text = cls._section_text(report, "srs2", context)

        qit_class = qit.get("classificacao") or "não informada"
        if cls._has_any_keyword(cognitive_text, ("heterog", "variável", "misto")):
            general_summary = "funcionamento neuropsicológico heterogêneo"
            preserved = "recursos preservados em parte do raciocínio verbal e da mediação estruturada"
            impaired = "fragilidades em eficiência cognitiva, autorregulação e adaptação a demandas complexas"
            profile = "heterogêneo"
            wisc_synthesis = "dissociação entre raciocínio verbal relativamente mais preservado e maior vulnerabilidade em organização perceptual, memória operacional e velocidade de processamento"
            functional_impact = "impacto sobre aprendizagem, autonomia e ritmo de resposta diante de tarefas mais complexas"
        elif cls._has_any_keyword(cognitive_text, ("inferior", "limítrofe", "baixo", "fragil")) or qit_class in {"Limítrofe", "Extremamente Baixo", "Inferior", "Média Inferior"}:
            general_summary = "funcionamento neuropsicológico com fragilidades cognitivas clinicamente relevantes"
            preserved = "recursos relativamente mais preservados em tarefas mediadas por estrutura e apoio"
            impaired = "vulnerabilidades em raciocínio, memória operacional, velocidade de processamento e adaptação funcional"
            profile = "heterogêneo"
            wisc_synthesis = "rebaixamento do funcionamento intelectual global com maior vulnerabilidade nos índices de eficiência cognitiva"
            functional_impact = "repercussões sobre o desempenho acadêmico, a autonomia e a organização do comportamento"
        else:
            general_summary = "funcionamento neuropsicológico globalmente preservado"
            preserved = "recursos cognitivos compatíveis com a faixa esperada"
            impaired = "fragilidades pontuais de menor intensidade"
            profile = "relativamente homogêneo"
            wisc_synthesis = "distribuição relativamente estável entre os índices fatoriais"
            functional_impact = "repercussões mais circunscritas em situações de maior exigência"

        intellectual_sentence = (
            f"{name} apresenta funcionamento neuropsicológico caracterizado por {general_summary}, com {preserved} e {impaired}."
        )

        indices_sentence = (
            f"Na Escala Wechsler de Inteligência para Crianças – Quarta Edição (WISC-IV), apresentou Quociente de Inteligência Total classificado como {qit_class}, com perfil {profile}, evidenciando {wisc_synthesis}. Esse padrão sugere {functional_impact}."
        )

        attention_sentence = (
            f"No domínio atencional e executivo, os resultados indicam {cls._domain_summary(attention_text, executive_text, 'atencionais e executivas')}, com repercussões em organização, monitoramento, flexibilidade cognitiva e consistência do desempenho cotidiano."
        )

        memory_sentence = (
            f"A avaliação da memória e aprendizagem evidenciou {cls._single_domain_summary(memory_text, 'recursos oscilantes em retenção, manipulação mental de informações e aprendizagem verbal')}, sugerindo impacto sobre seguimento de instruções, memorização sequencial e consolidação de conteúdos."
        )

        language_sentence = (
            f"Nos domínios de linguagem, gnosias e praxias, observou-se {cls._domain_summary(language_text, praxis_text, 'recursos mistos entre linguagem e organização visuoconstrutiva')}, devendo tais achados ser interpretados em conjunto com o desempenho acadêmico e a observação clínica."
        )

        emotional_sentence = (
            f"Nos aspectos emocionais e comportamentais, os instrumentos aplicados indicaram {cls._single_domain_summary(emotional_text, 'participação de fatores afetivos e autorregulatórios na expressão funcional do caso')}, compondo um perfil que exige leitura integrada com a anamnese e com o contexto escolar e familiar."
        )

        if social_text or any(item.get("instrument_code") == "srs2" for item in validated_tests):
            social_sentence = (
                f"Na avaliação do funcionamento social, os resultados da SRS-2 indicaram {cls._single_domain_summary(social_text, 'indicadores que devem ser correlacionados à comunicação social, à reciprocidade e ao contexto do desenvolvimento')}, devendo ser interpretados em conjunto com observação clínica, história do desenvolvimento e fatores contextuais."
            )
        else:
            social_sentence = (
                f"Na avaliação do funcionamento social, os dados disponíveis sugerem que a análise da comunicação social e da reciprocidade interpessoal de {first_name} deve permanecer articulada à observação clínica e à história do desenvolvimento."
            )

        integrated_sentence = (
            f"Diante da integração dos resultados das testagens, das observações clínicas e dos dados da anamnese, conclui-se que {name} apresenta um funcionamento neuropsicológico compatível com {hypothesis}."
        )

        hypothesis_lines = [
            "Hipótese Diagnóstica:",
            f"- há hipótese diagnóstica de {hypothesis}, conforme critérios do DSM-5-TR™;",
        ]

        dynamic_sentence = (
            "Ressalta-se que o ser humano possui natureza dinâmica, não definitiva e não cristalizada. Sendo assim, os resultados aqui expostos dizem respeito ao funcionamento cognitivo, emocional, comportamental e adaptativo no momento presente, podendo haver alterações posteriores, a depender das contingências ambientais vivenciadas e do acompanhamento recebido."
        )

        return "\n\n".join(
            [
                intellectual_sentence,
                indices_sentence,
                attention_sentence,
                memory_sentence,
                language_sentence,
                emotional_sentence,
                social_sentence,
                integrated_sentence,
                "\n".join(hypothesis_lines),
                dynamic_sentence,
            ]
        )

    @classmethod
    def _single_domain_summary(cls, text: str, fallback: str) -> str:
        if cls._has_any_keyword(text, ("preservad", "adequad", "esperad", "média")):
            return "recursos globalmente preservados dentro da faixa esperada"
        if cls._has_any_keyword(text, ("heterog", "oscil", "misto", "vari")):
            return "perfil heterogêneo, com oscilação entre recursos preservados e fragilidades específicas"
        if cls._has_any_keyword(text, ("inferior", "limítrofe", "baixo", "fragil", "preju")):
            return "fragilidades clinicamente relevantes"
        return fallback

    @classmethod
    def _domain_summary(cls, primary_text: str, secondary_text: str, fallback: str) -> str:
        combined = f"{primary_text} {secondary_text}".strip()
        return cls._single_domain_summary(combined, fallback)

    @classmethod
    def _tests_interpretation_blocks(cls, tests: list[dict]) -> str:
        if not tests:
            return (
                "Nenhum instrumento específico deste domínio foi validado na avaliação."
            )

        blocks = []
        include_instrument_name = len(tests) > 1
        for test in tests:
            interpretation = cls._clean_clinical_interpretation(cls._test_interpretation(test))
            if not interpretation:
                continue

            lines = []
            if include_instrument_name:
                lines.append(f"{test.get('instrument_name')}.")
            lines.append(interpretation)

            warnings = test.get("warnings") or []
            if warnings:
                lines.extend(f"Observação técnica: {warning}" for warning in warnings)

            blocks.append("\n".join(lines))

        return "\n\n".join(blocks) if blocks else (
            "Nenhum instrumento específico deste domínio apresentou interpretação clínica consolidada."
        )

    @staticmethod
    def _document_summary(context: dict) -> str:
        documents = context.get("documents") or []
        if not documents:
            return "Não foram anexados documentos complementares relevantes para composição do laudo."
        return "; ".join(
            f"{item.get('title')} ({item.get('document_type_display') or item.get('document_type')})"
            for item in documents[:5]
        )

    @classmethod
    def _generate_section_text(cls, report: Report, key: str, context: dict) -> str:
        patient = context["patient"]
        evaluation = context["evaluation"]
        is_adolescent = cls._is_adolescent_case(context)
        professional = cls.FIXED_AUTHOR

        if key == "identificacao":
            interested_party = report.interested_party or patient["full_name"]
            if (
                patient.get("responsible_name")
                and interested_party == patient["full_name"]
            ):
                interested_party = patient.get("responsible_name")
            return "\n".join(
                [
                    "1.1. Identificação do laudo:",
                    f"Autora: {professional}",
                    f"Interessado: {interested_party}",
                    f"Finalidade: {cls.FIXED_PURPOSE}",
                    "",
                    "1.2. Identificação do paciente:",
                    f"Nome: {patient['full_name']}",
                    f"Sexo: {cls._format_sex(patient.get('sex'))}",
                    f"Data de nascimento: {cls._format_date(patient.get('birth_date'))}",
                    f"Idade: {cls._format_age(context)}",
                    f"Filiação: {cls._build_filiation(patient)}",
                    f"Escolaridade: {patient.get('schooling') or 'Não informada'}",
                ]
            )

        if key == "descricao_demanda":
            if is_adolescent:
                referral_source = cls._pick_answer(context, "referral_source")
                main_complaint = cls._pick_answer(context, "main_complaint")
                main_contexts = cls._pick_answer(context, "main_contexts")
                concern = cls._pick_answer(context, "current_main_concern")
                goal = cls._pick_answer(context, "evaluation_goal")
                parts = []
                if referral_source:
                    parts.append(f"O adolescente foi encaminhado por {referral_source}")
                else:
                    parts.append(
                        "O adolescente foi encaminhado para avaliação neuropsicológica"
                    )
                parts.append(
                    f"em razão de {evaluation.get('referral_reason') or main_complaint or 'queixas cognitivas, emocionais e escolares em investigação clínica'}."
                )
                if main_contexts:
                    parts.append(
                        f"As dificuldades são descritas sobretudo no contexto {main_contexts}."
                    )
                if concern:
                    parts.append(
                        f"A principal preocupação atual refere-se a {concern}."
                    )
                parts.append(
                    f"A finalidade clínica da avaliação é {report.purpose or goal or evaluation.get('evaluation_purpose') or 'auxiliar o raciocínio diagnóstico, o planejamento terapêutico e a orientação familiar e escolar'}."
                )
                return " ".join(parts)
            return (
                f"A avaliação neuropsicológica foi solicitada em razão de {evaluation.get('referral_reason') or 'queixas cognitivas e comportamentais em investigação clínica'}. "
                f"A finalidade principal do processo é {report.purpose or evaluation.get('evaluation_purpose') or 'subsidiar o raciocínio diagnóstico e o planejamento terapêutico'}. "
                "O presente laudo considera as informações disponíveis no contexto clínico estruturado, integrando entrevista, registros evolutivos, documentos e resultados dos testes já validados."
            )

        if key == "procedimentos":
            return "\n".join(cls._procedure_lines(context))

        if key == "historia_pessoal":
            if is_adolescent:
                adolescent_sections = cls._adolescent_history_sections(context)
                if adolescent_sections:
                    return "\n\n".join(
                        f"{title}: {text}" for title, text in adolescent_sections
                    )
            return (
                f"{cls._anamnesis_summary(context)} "
                f"Registros evolutivos relevantes: {cls._progress_summary(context)}"
            )

        if key in cls.SECTION_GROUPS:
            tests = cls._tests_for_section(context, key)
            intro_map = {
                "capacidade_cognitiva_global": "A análise da capacidade cognitiva global foi baseada nos instrumentos com maior sensibilidade para estimativa do funcionamento intelectual e raciocínio geral.",
                "linguagem": "A análise da linguagem considera compreensão verbal, repertório lexical, organização semântica e impacto funcional na comunicação cotidiana e acadêmica.",
                "gnosias_praxias": "A análise de gnosias e praxias considera integração visuoespacial, raciocínio não verbal e organização construtiva.",
                "atencao": "A análise da atenção considera os sistemas atencionais sustentado, seletivo, alternado e dividido, conforme os dados já validados.",
                "memoria_aprendizagem": "A análise da memória e da aprendizagem contempla aquisição, retenção, evocação e reconhecimento, conforme os instrumentos aplicados.",
                "funcoes_executivas": "A análise das funções executivas considera controle inibitório, flexibilidade cognitiva, planejamento, monitoramento e velocidade de processamento.",
                "aspectos_emocionais_comportamentais": "A análise dos aspectos emocionais e comportamentais integra escalas complementares e observações clínicas descritas ao longo da avaliação.",
            }
            closing_map = {
                "capacidade_cognitiva_global": "Em síntese, os resultados devem ser interpretados em conjunto com os demais domínios cognitivos e com a funcionalidade observada no cotidiano.",
                "linguagem": "Os achados de linguagem precisam ser compreendidos em articulação com escolaridade, repertório sociocultural e demais funções cognitivas.",
                "gnosias_praxias": "Esses resultados contribuem para a compreensão do modo como o paciente organiza informações visuais e executa respostas motoras dirigidas a metas.",
                "atencao": "Os resultados atencionais ajudam a explicar dificuldades funcionais relativas à manutenção de foco, alternância entre demandas e organização da rotina.",
                "memoria_aprendizagem": "O perfil mnésico deve ser interpretado junto à atenção, à interferência emocional e às exigências ambientais cotidianas.",
                "funcoes_executivas": "As funções executivas influenciam diretamente o desempenho acadêmico, profissional e adaptativo, especialmente em contextos complexos e pouco estruturados.",
                "aspectos_emocionais_comportamentais": "Os aspectos emocionais e comportamentais podem atuar como fatores moduladores do desempenho cognitivo observado na avaliação.",
            }
            return "\n".join(
                [
                    intro_map[key],
                    "",
                    cls._tests_interpretation_blocks(tests),
                    "",
                    closing_map[key],
                ]
            )

        if key == "bpa2":
            tests = [
                test
                for test in context.get("validated_tests") or []
                if test.get("instrument_code") == "bpa2"
            ]
            return "\n".join(
                [
                    "A BPA-2 foi utilizada para mensurar atenção concentrada, dividida, alternada e capacidade geral de atenção.",
                    "",
                    cls._tests_interpretation_blocks(tests),
                    "",
                    "Em análise clínica, o desempenho atencional deve ser integrado às demandas escolares, ao ritmo de trabalho mental e às observações comportamentais registradas nas sessões.",
                ]
            )

        if key == "ravlt":
            tests = [
                test
                for test in context.get("validated_tests") or []
                if test.get("instrument_code") == "ravlt"
            ]
            return "\n\n".join(
                [
                    "O Rey Auditory Verbal Learning Test (RAVLT) é um teste neuropsicológico amplamente utilizado para avaliar a memória verbal, a capacidade de aprendizado auditivo e a retenção de informações ao longo do tempo. Desenvolvido por Rey (1958). O RAVLT permite analisar diferentes aspectos da memória, como a curva de aprendizado, interferência, esquecimento e reconhecimento verbal (Lezak et al., 2004). Ele é frequentemente utilizado na investigação de déficits cognitivos associados a doenças neurodegenerativas, lesões cerebrais traumáticas e transtornos psiquiátricos (Strauss, Sherman & Spreen, 2006). Os resultados do teste auxiliam no diagnóstico diferencial de condições como Alzheimer e TDAH, além de fornecerem subsídios para o planejamento de intervenções cognitivas (Salthouse, 2010). Assim, o RAVLT é uma ferramenta essencial para a avaliação da memória e da aprendizagem verbal.",
                    cls._tests_interpretation_blocks(tests),
                ]
            )

        if key == "fdt":
            tests = [
                test
                for test in context.get("validated_tests") or []
                if test.get("instrument_code") == "fdt"
            ]
            return cls._tests_interpretation_blocks(tests)

        if key == "etdah_pais":
            tests = [
                test
                for test in context.get("validated_tests") or []
                if test.get("instrument_code") == "etdah_pais"
            ]
            return "\n".join(
                [
                    "A escala E-TDAH-PAIS oferece a perspectiva dos responsáveis sobre regulação emocional, hiperatividade/impulsividade, comportamento adaptativo e atenção no cotidiano.",
                    "",
                    cls._tests_detailed_blocks(tests),
                    "",
                    "A interpretação deve ser integrada à anamnese, à observação clínica e aos achados objetivos das testagens neuropsicológicas, sem uso isolado do instrumento para diagnóstico.",
                ]
            )

        if key == "etdah_ad":
            tests = [
                test
                for test in context.get("validated_tests") or []
                if test.get("instrument_code") == "etdah_ad"
            ]
            return "\n".join(
                [
                    "A escala E-TDAH-AD oferece a perspectiva do próprio adolescente ou adulto sobre desatenção, impulsividade, aspectos emocionais, autorregulação e hiperatividade no cotidiano.",
                    "",
                    cls._tests_detailed_blocks(tests),
                    "",
                    "A interpretação do autorrelato exige integração com o relato familiar quando disponível, desempenho nos testes, observação clínica e impacto funcional do caso.",
                ]
            )

        if key == "scared":
            tests = [
                test
                for test in context.get("validated_tests") or []
                if test.get("instrument_code") == "scared"
            ]
            return cls._tests_interpretation_blocks(tests)

        if key == "srs2":
            tests = [
                test
                for test in context.get("validated_tests") or []
                if test.get("instrument_code") == "srs2"
            ]
            return cls._tests_interpretation_blocks(tests)

        if key == "epq_j":
            tests = [
                test
                for test in context.get("validated_tests") or []
                if test.get("instrument_code") == "epq_j"
            ]
            return "\n".join(
                [
                    "O EPQ-J descreve traços de personalidade nos domínios Psicoticismo, Extroversão, Neuroticismo e Sinceridade, devendo ser interpretado como dado complementar e não como ferramenta diagnóstica isolada.",
                    "",
                    cls._tests_detailed_blocks(tests),
                    "",
                    "O perfil de personalidade deve ser articulado ao funcionamento emocional, aos recursos adaptativos, ao contexto relacional e aos demais achados da avaliação neuropsicológica.",
                ]
            )

        if key == "ebadep":
            tests = [
                test
                for test in context.get("validated_tests") or []
                if test.get("instrument_code") in {"ebadep_a", "ebadep_ij", "ebaped_ij"}
            ]
            return "\n".join(
                [
                    "A EBADEP auxilia na investigação de sintomas depressivos e seu possível impacto no humor, motivação, engajamento e funcionalidade global.",
                    "",
                    cls._tests_detailed_blocks(tests),
                    "",
                    "Os resultados devem ser sempre compreendidos em conjunto com a história clínica, comorbidades e contexto psicossocial atual.",
                ]
            )

        if key == "conclusao":
            return cls._build_conclusion_text(report, context)

        if key == "hipotese_diagnostica":
            hypothesis = evaluation.get("clinical_hypothesis")
            if hypothesis:
                return (
                    f"A hipótese diagnóstica preliminar registrada para o caso é: {hypothesis}. "
                    "Os achados da avaliação oferecem subsídios para discussão clínica, sem substituir a decisão diagnóstica final do profissional responsável."
                )
            return "Até o presente momento, os dados sustentam hipóteses clínicas em investigação, recomendando-se correlação com história do desenvolvimento, exames complementares e acompanhamento multiprofissional quando pertinente."

        if key == "sugestoes_conduta":
            if is_adolescent:
                return (
                    "Sugere-se devolutiva estruturada com adolescente e responsáveis, psicoeducação sobre o perfil cognitivo e emocional observado, articulação com a escola para adaptações quando necessárias e acompanhamento multiprofissional conforme as hipóteses clínicas em investigação. "
                    "Recomenda-se monitoramento longitudinal do funcionamento acadêmico, social e emocional, bem como orientação familiar para manejo das áreas de maior vulnerabilidade identificadas."
                )
            return (
                "Sugere-se devolutiva clínica estruturada ao paciente e/ou responsáveis, articulação com profissionais assistentes, e planejamento de intervenções voltadas às áreas de maior vulnerabilidade identificadas. "
                "Também se recomenda acompanhamento longitudinal para monitoramento da funcionalidade e resposta às estratégias terapêuticas adotadas."
            )

        if key == "referencias_bibliograficas":
            return build_references_text(context.get("validated_tests") or [])

        return (
            "Seção em elaboração a partir do contexto clínico estruturado da avaliação."
        )
