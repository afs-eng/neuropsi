from __future__ import annotations

import re


class PatientIdentityService:
    FIXED_AUTHOR = "Jacqueline Oliveira Caires (CRP 09/6017)"
    REFERENCE_SECTION_HEADINGS = (
        "17. REFERÊNCIAS BIBLIOGRÁFICAS",
        "REFERÊNCIAS BIBLIOGRÁFICAS",
        "REFERENCIA BIBLIOGRÁFICA",
        "REFERÊNCIAS",
    )
    SKIP_PATTERNS = (
        "Laudo", "Neuropsicológico", "Documento", "Familiares", "Finalidade",
        "Masculino", "Feminino", "Data", "Segunda", "Edição", "Dígitos",
        "Child", "Anxiety", "Related", "Emotional", "Disorders",
        "Aprendizagem", "Auditivo", "Versão", "Pais", "História", "Pessoal",
        "Não", "Sim", "Resultado", "Observação", "Índice", "Nota", "Tabela",
        "Autorrelato", "Fator", "Mãe",
        "Encaminhamento", "Interessado", "Autora", "Filiação", "Escolaridade",
        "Profissão", "Gênero", "Paciente", "Capacidade Cognitiva", "Global",
        "Wechsler", "Abreviada", "Escala", "Psicológica", "Conselho",
        "Média", "Inferior", "Superior", "Média Superior", "Média Inferior",
        "Abaixo", "Acima", "Faixa", "Limítrofe", "Muito Superior", "Muito Baixo",
        "Quociente", "Inteligência", "Escalas", "Primárias",
        "Atenção", "Concentrada", "Dividida", "Alternada", "Processos",
        "Automáticos", "Gráfico", "Cinco", "Grandes", "Fatores",
        "Interpretação", "Clínica", "Cognição", "Social", "Comunicação",
        "Análise", "Integrada", "Os", "Na", "Em", "Entre", "Diferenças",
        "Hipótese", "Diagnóstica", "Conduta", "Sugerida", "Intervenção",
        "Considerações", "Finais", "Síntese", "Conclusão", "Terapêutica",
    )
    TECHNICAL_TOKENS = {
        "Raciocínio", "Matricial", "Execução", "Tabela", "Rey", "Auditory", "Verbal",
        "Learning", "Test", "Flexibilidade", "Cognitiva", "Big", "Five", "Interações",
        "Sociais", "Espectro", "Autista", "Pontuação", "Total", "Vocabulário",
        "Semelhanças", "Cubos", "Pânico", "Sintomas", "Somáticos", "Ansiedade",
        "Generalizada", "Separação", "Fobia", "Social", "Evitação", "Escolar",
        "Percepção", "Cognição", "Comunicação", "Motivação", "Realização", "Abertura",
        "Comportamento", "Adaptativo", "Evitamento", "São", "Paulo", "Second",
        "Edition", "Western", "Psychological", "Services", "Adolescent", "Psychiatry",
        "American", "Academy", "Childhood", "Autism", "Rating", "Scale", "High",
        "Functioning", "Version", "Modified", "Checklist", "Toddlers", "Compreensão",
        "Organização", "Perceptual", "Habilidade", "Geral", "Função", "Executiva",
        "Saúde", "Mental", "Referências", "Bibliográficas", "Vetor", "Editora",
        "Times", "New", "Roman",
    }
    IGNORED_NAME_PHRASES = {
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
        "Escala Wechsler Abreviada",
        "Segunda Edição",
        "Versão Adulto",
        "Capacidade Cognitiva Global",
        "Inteligência Verbal",
        "Inteligência Total",
        "Observações Clínicas",
        "Interpretação Integrada",
        "Análise Clínica",
        "Avaliação Neuropsicológica",
        "Comunicação Social",
        "Cognição Social",
        "Interação Social",
        "Percepção Social",
        "Motivação Social",
        "Responsividade Social",
        "Padrões Restritos",
        "Escore Geral",
        "Escore Total",
        "Processos Automáticos",
        "Processos Controlados",
        "Instabilidade Emocional",
        "Ética Profissional",
        "Média Inferior",
        "Média Superior",
        "Muito Baixo",
        "Atenção Concentrada",
        "Atenção Dividida",
        "Atenção Alternada",
        "Atenção Geral",
        "Cinco Dígitos",
        "Cinco Grandes Fatores",
        "Child Anxiety Related Emotional Disorders",
        "Comportamento Adaptativo",
        "Evitamento Escolar",
        "São Paulo",
        "Second Edition",
        "Western Psychological Services",
        "Adolescent Psychiatry",
        "Childhood Autism Rating Scale",
        "High Functioning Version",
        "Modified Checklist",
        "Autism in Toddlers",
    }

    @classmethod
    def foreign_patient_names_in_text(
        cls, text: str | None, patient_name: str | None
    ) -> list[str]:
        patient_name = (patient_name or "").strip()
        if not patient_name:
            return []

        allowed_tokens = {token for token in patient_name.split() if token}
        ignored_names = cls._ignored_names(patient_name)
        candidates = re.findall(
            r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:[ \t]+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)+\b",
            text or "",
        )

        foreign_names = []
        for name in candidates:
            if cls._is_ignored_name(name, patient_name, allowed_tokens, ignored_names):
                continue
            if name not in foreign_names:
                foreign_names.append(name)
        return foreign_names

    @classmethod
    def sanitize_section_text_for_patient(cls, text: str | None, context: dict) -> str:
        patient_name = ((context or {}).get("patient") or {}).get("full_name") or ""
        cleaned = str(text or "").strip()
        if not cleaned:
            return ""
        if cls.foreign_patient_names_in_text(cleaned, patient_name):
            return ""
        return cleaned

    @classmethod
    def validate_document_identity(cls, document, report, context: dict) -> None:
        patient_name = cls._patient_name(report, context)
        if not patient_name:
            return

        foreign_names = cls.foreign_patient_names_in_text(
            cls.document_text_before_references(document),
            patient_name,
        )
        if foreign_names:
            raise ValueError(
                "Exportação bloqueada: o laudo contém nomes divergentes de pacientes: "
                + ", ".join(foreign_names)
            )

    @classmethod
    def document_text_before_references(cls, document) -> str:
        lines = []
        for paragraph in document.paragraphs:
            text = (paragraph.text or "").strip()
            if any(heading in text.upper() for heading in cls.REFERENCE_SECTION_HEADINGS):
                break
            if text.startswith(("Autora:", "Filiação:")):
                continue
            lines.append(text)
        return "\n".join(lines)

    @classmethod
    def _ignored_names(cls, patient_name: str) -> set[str]:
        return {
            patient_name,
            cls.FIXED_AUTHOR.split("(", 1)[0].strip(),
            *cls.IGNORED_NAME_PHRASES,
        }

    @classmethod
    def _is_ignored_name(
        cls,
        name: str,
        patient_name: str,
        allowed_tokens: set[str],
        ignored_names: set[str],
    ) -> bool:
        if name in ignored_names:
            return True
        if any(pattern.lower() in name.lower() for pattern in cls.SKIP_PATTERNS):
            return True

        words = name.split()
        if len(words) < 2 or len(words) > 5:
            return True
        if all(word in cls.TECHNICAL_TOKENS for word in words):
            return True

        first_name = words[0]
        return name == patient_name or first_name in allowed_tokens

    @staticmethod
    def _patient_name(report, context: dict) -> str:
        patient_name = ((context or {}).get("patient") or {}).get("full_name")
        if not patient_name and getattr(report, "patient", None) is not None:
            patient_name = getattr(report.patient, "full_name", "")
        return (patient_name or "").strip()
