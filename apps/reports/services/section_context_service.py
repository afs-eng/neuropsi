from .section_registry import get_ai_section_config


class SectionContextService:
    WISC_SECTION_SUBTEST_CODES = {
        "funcoes_executivas": {"SM", "CO", "CN", "RM"},
        "linguagem": {"SM", "VC", "CO"},
        "gnosias_praxias": {"RM", "CB"},
        "memoria_aprendizagem": {"DG", "SNL"},
    }
    WISC_DOMAIN_SUMMARIES = {
        "funcoes_executivas": {
            "intro": "Considere apenas os subtestes do WISC-IV ligados a planejamento, abstração, monitoramento cognitivo, flexibilidade mental, controle inibitório e resolução de problemas.",
            "preserved": "Os achados sugerem funcionamento executivo globalmente preservado, com recursos adequados para organização do pensamento, abstração e manejo de demandas cognitivas mais complexas.",
            "mixed": "Os achados sugerem perfil executivo heterogêneo, com áreas preservadas e fragilidades relativas em componentes específicos do funcionamento executivo.",
            "low": "Os achados sugerem fragilidades no funcionamento executivo, com possível repercussão sobre planejamento, controle mental, flexibilidade cognitiva e organização do comportamento dirigido a objetivos.",
        },
        "linguagem": {
            "intro": "Considere apenas os subtestes do WISC-IV ligados a compreensão verbal, abstração mediada pela linguagem, repertório lexical e uso funcional da linguagem.",
            "preserved": "Os achados sugerem funcionamento linguístico preservado, com repertório verbal compatível com a faixa etária e recursos adequados para compreensão, expressão e elaboração conceitual.",
            "mixed": "Os achados sugerem perfil linguístico relativamente heterogêneo, com preservação de alguns componentes da linguagem e fragilidades pontuais em outros aspectos do processamento verbal.",
            "low": "Os achados sugerem fragilidades no domínio da linguagem, com possível impacto sobre compreensão verbal, abstração conceitual, repertório lexical e uso funcional da linguagem.",
        },
        "gnosias_praxias": {
            "intro": "Considere apenas os subtestes do WISC-IV ligados a percepção visual, organização visuoespacial e integração visuoconstrutiva.",
            "preserved": "Os achados sugerem funcionamento preservado em gnosias e praxias, com recursos adequados para análise perceptual, organização espacial e execução visuoconstrutiva.",
            "mixed": "Os achados sugerem perfil misto, com habilidades perceptuais relativamente preservadas, mas com fragilidades em componentes específicos da organização visuoespacial e da praxia construtiva.",
            "low": "Os achados sugerem fragilidades em gnosias e praxias, com possível repercussão sobre organização visuoespacial, percepção de relações espaciais, planejamento construtivo e execução motora organizada.",
        },
        "memoria_aprendizagem": {
            "intro": "Considere apenas os subtestes do WISC-IV ligados a retenção imediata, memória operacional e manipulação mental de informações, integrando com outros instrumentos mnésicos quando existirem.",
            "preserved": "Os achados sugerem funcionamento preservado da memória e da aprendizagem, com recursos adequados para retenção, manipulação mental e consolidação de informações.",
            "mixed": "Os achados sugerem perfil heterogêneo, com preservação de alguns processos mnésicos e fragilidades relativas em componentes específicos da aprendizagem e da recuperação de informações.",
            "low": "Os achados sugerem fragilidades nos processos de memória e aprendizagem, com possível impacto sobre retenção ativa de informações, evocação e desempenho em tarefas que exigem aquisição progressiva de conteúdo.",
        },
    }

    @classmethod
    def build_for_section(cls, report, section_key: str, context: dict) -> dict:
        patient = context.get("patient") or {}
        evaluation = context.get("evaluation") or {}
        tests = context.get("validated_tests") or []
        config = get_ai_section_config(section_key)
        include_structured_results = config["kind"] == "test"
        allowed_codes = set(config.get("codes") or [])

        filtered_tests = [
            cls._build_test_payload(item, section_key, include_structured_results)
            for item in tests
            if not allowed_codes or item.get("instrument_code") in allowed_codes
        ]

        progress_entries = [
            {
                "entry_type": item.get("entry_type"),
                "objective": item.get("objective") or "",
                "observed_behavior": item.get("observed_behavior") or "",
                "clinical_notes": item.get("clinical_notes") or "",
            }
            for item in (context.get("progress_entries") or [])[:3]
        ]

        if config["kind"] == "test":
            return {
                "section": section_key,
                "section_kind": config["kind"],
                "report_rules": {
                    "report_language": "pt-BR",
                    "clinical_style": "tecnico_objetivo",
                    "use_first_name_only": True,
                    **cls._wais3_model_rules(section_key, context),
                },
                "patient": {
                    "first_name": (patient.get("full_name") or "").split(" ", 1)[0],
                    "sex": patient.get("sex"),
                },
                "evaluation": {
                    "referral_reason": evaluation.get("referral_reason") or "",
                    "evaluation_purpose": evaluation.get("evaluation_purpose") or "",
                },
                "validated_tests": filtered_tests,
            }

        payload = {
            "section": section_key,
            "section_kind": config["kind"],
            "report_rules": {
                "report_language": "pt-BR",
                "clinical_style": "tecnico_objetivo",
                "use_first_name_only": False,
                **cls._wais3_model_rules(section_key, context),
            },
            "patient": {
                "first_name": (patient.get("full_name") or "").split(" ", 1)[0],
                "full_name": patient.get("full_name") or "",
                "age": patient.get("birth_date"),
                "sex": patient.get("sex"),
                "schooling": patient.get("schooling"),
            },
            "evaluation": {
                "referral_reason": evaluation.get("referral_reason") or "",
                "evaluation_purpose": evaluation.get("evaluation_purpose") or "",
                "clinical_hypothesis": evaluation.get("clinical_hypothesis") or "",
            },
            "anamnesis": (context.get("anamnesis") or {}).get("current_response") or {},
            "progress_entries": progress_entries,
            "validated_tests": filtered_tests,
        }

        if section_key == "conclusao":
            payload["generated_sections"] = cls.build_generated_sections_context(report)
            payload["report_rules"]["use_first_name_only"] = False

        return payload

    @staticmethod
    def _wais3_model_rules(section_key: str, context: dict) -> dict:
        if not any(test.get("instrument_code") == "wais3" for test in context.get("validated_tests") or []):
            return {}
        outline = ["Objetivo e domínios do instrumento", "Resultados por domínio", "Em análise clínica: integração dos achados", "Limites da interpretação e correlação com o contexto clínico"]
        if section_key == "conclusao":
            outline = ["Funcionamento intelectual", "Atenção, memória e funções executivas", "Aspectos emocionais e personalidade", "Convergências e discrepâncias entre métodos e respondentes", "Formulação clínica sustentada pelos dados disponíveis", "Limitações e caráter dinâmico da avaliação"]
        return {"document_model": "wais3_aprovado", "clinical_outline": outline,
                "preserve_all_respondents": True, "compare_only_compatible_scores": True,
                "do_not_copy_example_diagnoses": True, "do_not_invent_functional_impairment": True}

    @classmethod
    def build_generated_sections_context(cls, report) -> list[dict]:
        relevant_keys = {
            "capacidade_cognitiva_global",
            "linguagem",
            "funcoes_executivas",
            "atencao",
            "memoria_aprendizagem",
            "gnosias_praxias",
            "aspectos_emocionais_comportamentais",
            "scared",
            "srs2",
            "epq_j",
            "ebadep",
            "etdah_pais",
            "etdah_ad",
        }
        return [
            {
                "key": section.key,
                "title": section.title,
                "content": str(section.content_edited or section.content_generated or ""),
            }
            for section in report.sections.all().order_by("order")
            if section.key in relevant_keys
        ]

    @classmethod
    def build_for_audit(cls, report, context: dict) -> dict:
        patient = context.get("patient") or {}
        evaluation = context.get("evaluation") or {}
        tests = context.get("validated_tests") or []

        return {
            "patient": {
                "first_name": (patient.get("full_name") or "").split(" ", 1)[0],
                "full_name": patient.get("full_name") or "",
                "sex": patient.get("sex"),
                "schooling": patient.get("schooling") or "",
            },
            "evaluation": {
                "referral_reason": evaluation.get("referral_reason") or "",
                "evaluation_purpose": evaluation.get("evaluation_purpose") or "",
                "clinical_hypothesis": evaluation.get("clinical_hypothesis") or "",
            },
            "anamnesis": (context.get("anamnesis") or {}).get("current_response") or {},
            "generated_sections": cls.build_generated_sections_context(report),
            "validated_tests": [
                {
                    "instrument_code": item.get("instrument_code"),
                    "instrument_name": item.get("instrument_name") or item.get("instrument"),
                    "clinical_interpretation": (item.get("clinical_interpretation") or "").strip(),
                    "summary": item.get("summary") or "",
                    "warnings": item.get("warnings") or [],
                }
                for item in tests
            ],
        }

    @classmethod
    def _build_test_payload(
        cls, item: dict, section_key: str, include_structured_results: bool
    ) -> dict:
        clinical_interpretation = (item.get("clinical_interpretation") or "").strip()
        structured_results = item.get("structured_results") or {}

        payload = {
            "instrument_code": item.get("instrument_code"),
            "instrument_name": item.get("instrument_name") or item.get("instrument"),
            "clinical_interpretation": clinical_interpretation,
            "warnings": item.get("warnings") or [],
        }
        if item.get("instrument_code") == "srs2":
            payload["application_id"] = item.get("application_id")
            payload["form"] = (item.get("classified_payload") or {}).get("form") or (item.get("raw_payload") or {}).get("form")
            payload["respondent_name"] = (item.get("raw_payload") or {}).get("respondent_name")
            payload["structured_results"] = structured_results

        if not clinical_interpretation:
            payload["summary"] = item.get("summary") or ""

        should_include_structured = (
            include_structured_results and not clinical_interpretation
        )

        if (
            item.get("instrument_code") == "wisc4"
            and section_key in cls.WISC_SECTION_SUBTEST_CODES
        ):
            should_include_structured = True
            filtered_structured_results = cls._filter_wisc_structured_results(
                structured_results, section_key
            )
            payload["structured_results"] = filtered_structured_results
            payload["clinical_interpretation"] = ""
            payload["technical_basis"] = cls._build_wisc_domain_basis(
                filtered_structured_results, section_key
            )
        elif should_include_structured:
            payload["structured_results"] = structured_results

        if should_include_structured:
            payload["result_rows"] = item.get("result_rows") or []

        return payload

    @classmethod
    def _filter_wisc_structured_results(
        cls, structured_results: dict, section_key: str
    ) -> dict:
        allowed_codes = cls.WISC_SECTION_SUBTEST_CODES.get(section_key, set())
        if not structured_results or not allowed_codes:
            return structured_results or {}

        filtered_subtests = [
            subtest
            for subtest in (structured_results.get("subtestes") or [])
            if subtest.get("codigo") in allowed_codes
        ]
        filtered_indices = []
        for index in structured_results.get("indices") or []:
            index_subtests = [
                subtest
                for subtest in (index.get("subtestes") or [])
                if subtest.get("codigo") in allowed_codes
            ]
            if index_subtests:
                filtered_indices.append({**index, "subtestes": index_subtests})

        return {
            "confidence_level": structured_results.get("confidence_level"),
            "subtestes": filtered_subtests,
            "indices": filtered_indices,
        }

    @classmethod
    def _build_wisc_domain_basis(
        cls, structured_results: dict, section_key: str
    ) -> str:
        summary = cls.WISC_DOMAIN_SUMMARIES.get(section_key)
        subtests = structured_results.get("subtestes") or []
        if not summary:
            return ""
        if not subtests:
            return summary["intro"]

        low_labels = {
            "Dificuldade Leve",
            "Dificuldade Moderada",
            "Dificuldade Grave",
            "Média Inferior",
            "Limítrofe",
            "Inferior",
            "Extremamente Baixo",
        }
        low_count = sum(
            1 for item in subtests if item.get("classificacao") in low_labels
        )
        if low_count == 0:
            profile = summary["preserved"]
        elif low_count < len(subtests):
            profile = summary["mixed"]
        else:
            profile = summary["low"]

        lines = []
        for item in subtests:
            details = []
            if item.get("escore_padrao") is not None:
                details.append(f"escore padrão {item.get('escore_padrao')}")
            if item.get("percentil") is not None:
                details.append(f"percentil {item.get('percentil')}")
            suffix = f" ({', '.join(details)})" if details else ""
            lines.append(
                f"{item.get('subteste')}: {item.get('classificacao')}{suffix}."
            )

        return "\n\n".join(
            [
                summary["intro"],
                profile,
                "Subtestes relevantes do domínio: " + " ".join(lines),
            ]
        )
