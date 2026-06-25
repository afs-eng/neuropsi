from .config import FATORES_DISPLAY_NAMES


def _first_name(patient_name: str) -> str:
    return (patient_name or "Paciente").strip().split(" ", 1)[0] or "Paciente"


def _is_clinical(row: dict, form_type: str) -> bool:
    classification = (row.get("classificacao") or "").strip().lower()
    if form_type == "parent":
        return classification == "clínico" or classification == "clinico"
    return classification in {"elevado", "muito elevado"}


def _source_phrase(form_type: str) -> str:
    if form_type == "parent":
        return "segundo o relato dos pais/cuidadores"
    return "no autorrelato"


def _opening_paragraph(form_type: str) -> str:
    if form_type == "parent":
        return (
            "SCARED - Pais/Cuidadores. Interpretação e Observações Clínicas: A Escala SCARED foi aplicada com o objetivo de rastrear sintomas ansiosos em crianças e adolescentes, a partir do relato dos pais/cuidadores, investigando manifestações relacionadas à ansiedade generalizada, ansiedade de separação, ansiedade social, sintomas de pânico/somatização e evitação escolar."
        )
    return (
        "SCARED - Autorrelato. Interpretação e Observações Clínicas: A Escala SCARED foi aplicada com o objetivo de rastrear sintomas ansiosos em crianças e adolescentes, a partir do autorrelato, investigando manifestações relacionadas à ansiedade generalizada, ansiedade de separação, ansiedade social, sintomas de pânico/somatização e evitação escolar."
    )


def interpret_scared_results(merged_data: dict, patient_name: str = "") -> str:
    rows = {row.get("fator"): row for row in merged_data.get("analise_geral", [])}
    if not rows:
        return "Sem resultados para interpretação."

    form_type = merged_data.get("form_type") or "child"
    source_phrase = _source_phrase(form_type)
    name = _first_name(patient_name)

    total_row = rows.get("total", {})
    total_clinical = _is_clinical(total_row, form_type)

    paragraphs = [_opening_paragraph(form_type)]

    if total_clinical:
        paragraphs.append(
            f"Os resultados indicaram presença de sintomas ansiosos em nível global, conforme evidenciado pelo escore total em faixa clínica, sugerindo comprometimento emocional mais abrangente {source_phrase}."
        )
    else:
        paragraphs.append(
            f"Os resultados indicaram ausência de quadro ansioso global, conforme evidenciado pelo escore total abaixo do ponto de corte ou sem elevação clínica relevante, sugerindo funcionamento emocional geral dentro dos limites esperados {source_phrase}."
        )

    panic = rows.get("panico_sintomas_somaticos", {})
    if _is_clinical(panic, form_type):
        paragraphs.append(
            "No domínio de Pânico/Sintomas Somáticos, observou-se classificação clínica, sugerindo presença de manifestações físicas associadas à ansiedade, como desconfortos somáticos recorrentes, sensação de tensão corporal, medo intenso ou sintomas compatíveis com episódios de pânico."
        )
    else:
        paragraphs.append(
            "No domínio de Pânico/Sintomas Somáticos, a pontuação situou-se na faixa não clínica, não indicando presença relevante de sintomas físicos associados à ansiedade, crises de pânico ou desconfortos somáticos recorrentes relacionados ao estado emocional."
        )

    generalized = rows.get("ansiedade_generalizada", {})
    if _is_clinical(generalized, form_type):
        paragraphs.append(
            "Em Ansiedade Generalizada, observou-se classificação clínica, sugerindo presença de preocupações excessivas, tendência à apreensão constante, dificuldade de relaxamento e antecipação ansiosa diante de diferentes demandas do cotidiano."
        )
    else:
        paragraphs.append(
            "Em Ansiedade Generalizada, o resultado foi classificado como não clínico, não indicando preocupações excessivas, estado persistente de apreensão ou antecipação ansiosa significativa diante de múltiplas situações do cotidiano."
        )

    separation = rows.get("ansiedade_separacao", {})
    if _is_clinical(separation, form_type):
        paragraphs.append(
            "No domínio de Ansiedade de Separação, observou-se classificação clínica, sugerindo presença de insegurança emocional em situações de afastamento das figuras de apego, com possível necessidade aumentada de proximidade, previsibilidade e suporte emocional em contextos de separação. Esse resultado pode estar relacionado a maior desconforto diante de afastamentos, preocupação com a ausência dos cuidadores ou necessidade intensificada de segurança emocional para lidar com situações de autonomia."
        )
    else:
        paragraphs.append(
            "No domínio de Ansiedade de Separação, a pontuação foi classificada como não clínica, afastando indicativos de insegurança emocional relevante diante do afastamento das figuras de apego."
        )

    social = rows.get("fobia_social", {})
    if _is_clinical(social, form_type):
        paragraphs.append(
            "Em Fobia Social, observou-se classificação clínica, indicando presença de desconforto relevante em situações de exposição, interação social ou avaliação por outras pessoas, com possível tendência à inibição, evitação ou sofrimento em contextos interpessoais."
        )
    else:
        paragraphs.append(
            "Em Fobia Social, o resultado foi classificado como não clínico, afastando indicativos de inibição social importante, medo acentuado de exposição ou desconforto significativo em interações sociais."
        )

    school = rows.get("evitacao_escolar", {})
    if _is_clinical(school, form_type):
        paragraphs.append(
            "O domínio de Evitação Escolar apresentou classificação clínica, sugerindo desconforto emocional relevante diante do contexto escolar, com possível tendência à recusa, resistência ou sofrimento associado à frequência e permanência na escola."
        )
    else:
        paragraphs.append(
            "O domínio de Evitação Escolar apresentou pontuação não clínica, não sugerindo recusa escolar ou ansiedade relevante associada ao ambiente escolar."
        )

    altered_domains = [
        FATORES_DISPLAY_NAMES.get(key, key)
        for key, row in rows.items()
        if key != "total" and _is_clinical(row, form_type)
    ]

    if not altered_domains:
        final_paragraph = (
            f"Em análise clínica, o perfil emocional de {name} não revela indicadores consistentes de quadro ansioso clinicamente significativo, mantendo-se dentro dos limites esperados no conjunto dos domínios investigados."
        )
    elif len(altered_domains) == 1:
        domain_name = altered_domains[0]
        final_paragraph = (
            f"Em análise clínica, o perfil emocional de {name} revela sintomas ansiosos específicos e circunscritos ao domínio de {domain_name}, sem evidências de comprometimento ansioso amplo nos demais eixos avaliados. Esse padrão sugere manifestação ansiosa mais focal, relacionada a situações específicas do funcionamento emocional."
        )
    else:
        final_paragraph = (
            f"Em análise clínica, o perfil emocional de {name} revela sintomatologia ansiosa distribuída em múltiplos domínios, indicando sofrimento emocional mais abrangente e com potencial repercussão sobre o funcionamento adaptativo, relacional e acadêmico."
        )

    hypothesis = ""
    if len(altered_domains) > 1 or total_clinical:
        hypothesis = (
            " Há hipótese diagnóstica de sintomatologia ansiosa clinicamente relevante, com manifestações em múltiplos domínios, devendo o quadro ser interpretado de forma integrada à anamnese, à observação clínica e aos demais instrumentos aplicados."
        )
    elif altered_domains:
        domain_key = next(
            key
            for key, row in rows.items()
            if key != "total" and _is_clinical(row, form_type)
        )
        domain_hypotheses = {
            "ansiedade_separacao": " Há hipótese diagnóstica de sintomatologia ansiosa relacionada à ansiedade de separação, em nível circunscrito, devendo esse achado ser interpretado de forma integrada aos demais dados clínicos e contextuais da avaliação.",
            "fobia_social": " Há hipótese diagnóstica de sintomatologia ansiosa relacionada à fobia social, devendo esse achado ser interpretado em conjunto com os dados observacionais, escolares e clínicos da avaliação.",
            "ansiedade_generalizada": " Há hipótese diagnóstica de sintomatologia ansiosa com predomínio de ansiedade generalizada, considerando a presença de preocupações excessivas e apreensão persistente com repercussão funcional.",
        }
        hypothesis = domain_hypotheses.get(
            domain_key,
            " Há hipótese diagnóstica de sintomatologia ansiosa em nível circunscrito, devendo esse achado ser interpretado de forma integrada aos demais dados clínicos e contextuais da avaliação.",
        )

    paragraphs.append(final_paragraph + hypothesis)
    return "\n\n".join(paragraphs)
