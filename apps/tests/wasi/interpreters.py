from __future__ import annotations


def _first_name(patient_name: str) -> str:
    return (patient_name or "Paciente").strip().split(" ", 1)[0] or "Paciente"


def _classify_qiv_qie_discrepancy(qiv: int, qie: int) -> dict:
    diff = abs(qiv - qie)
    if diff < 10:
        level = "sem discrepância clinicamente relevante"
    elif diff < 15:
        level = "discrepância discreta"
    elif diff < 23:
        level = "discrepância moderada"
    else:
        level = "discrepância acentuada"

    if qiv > qie:
        stronger_domain = "verbal"
    elif qie > qiv:
        stronger_domain = "execução"
    else:
        stronger_domain = "equilibrado"

    return {
        "difference": diff,
        "level": level,
        "stronger_domain": stronger_domain,
    }


_QIV_PHRASES = {
    "Muito Superior": "Esse resultado indica desempenho verbal acima do esperado, com recursos bem desenvolvidos de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere facilidade para compreender instruções verbais, elaborar respostas conceituais, utilizar conhecimento previamente adquirido e lidar com demandas que exigem organização linguística e abstração verbal.",
    "Superior": "Esse resultado indica desempenho verbal acima do esperado, com recursos bem desenvolvidos de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere facilidade para compreender instruções verbais, elaborar respostas conceituais, utilizar conhecimento previamente adquirido e lidar com demandas que exigem organização linguística e abstração verbal.",
    "Média Superior": "Esse resultado indica habilidades verbais acima da média esperada, com bons recursos de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere rendimento favorável em tarefas que exigem elaboração verbal, compreensão de conceitos e uso funcional da linguagem em situações estruturadas.",
    "Média": "Esse resultado indica funcionamento verbal dentro do esperado, com recursos adequados de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere capacidade funcional para lidar com demandas verbais compatíveis com sua faixa etária e escolaridade.",
    "Média Inferior": "Esse resultado indica que suas habilidades de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem encontram-se abaixo da média esperada, embora ainda preservadas em nível funcional. Tal desempenho sugere que {nome} tende a apresentar melhor rendimento em situações estruturadas, com linguagem clara e apoio contextual, podendo encontrar maior dificuldade diante de demandas verbais mais complexas, abstratas ou que exijam elaboração linguística mais refinada.",
    "Limítrofe": "Esse resultado indica fragilidade significativa nas habilidades de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere maior dificuldade para compreender informações verbais complexas, organizar respostas conceituais, utilizar vocabulário elaborado e lidar com tarefas que demandam abstração linguística.",
    "Extremamente Baixo": "Esse resultado indica prejuízo importante nas habilidades de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere dificuldade acentuada para compreender e elaborar informações verbais complexas, organizar conceitos, abstrair significados e responder a demandas que exigem mediação linguística mais elaborada.",
    "Extremamente Baixa": "Esse resultado indica prejuízo importante nas habilidades de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere dificuldade acentuada para compreender e elaborar informações verbais complexas, organizar conceitos, abstrair significados e responder a demandas que exigem mediação linguística mais elaborada.",
}

_QIE_PHRASES = {
    "Muito Superior": "Esse resultado evidencia desempenho não verbal acima do esperado, com recursos bem desenvolvidos de raciocínio visuoespacial, organização perceptual, identificação de padrões e resolução prática de problemas. Esse perfil sugere facilidade para lidar com estímulos visuais, compreender relações espaciais e resolver tarefas novas com menor dependência da linguagem.",
    "Superior": "Esse resultado evidencia desempenho não verbal acima do esperado, com recursos bem desenvolvidos de raciocínio visuoespacial, organização perceptual, identificação de padrões e resolução prática de problemas. Esse perfil sugere facilidade para lidar com estímulos visuais, compreender relações espaciais e resolver tarefas novas com menor dependência da linguagem.",
    "Média Superior": "Esse resultado evidencia bom desempenho em raciocínio não verbal, organização perceptual, análise visuoespacial e resolução prática de problemas. Esse perfil sugere facilidade relativa em tarefas que envolvem identificação de padrões, organização visual e manejo de problemas novos com apoio perceptual.",
    "Média": "Esse resultado indica funcionamento não verbal dentro do esperado, com recursos adequados de raciocínio visuoespacial, organização perceptual, identificação de padrões e resolução prática de problemas. Esse desempenho sugere capacidade funcional para lidar com tarefas visuais e práticas compatíveis com sua faixa etária e escolaridade.",
    "Média Inferior": "Esse resultado indica desempenho abaixo da média esperada em habilidades de raciocínio não verbal, organização perceptual, análise visuoespacial e resolução prática de problemas. Esse achado sugere maior dificuldade em tarefas que demandam interpretação de estímulos visuais, identificação de padrões, organização espacial e manejo de situações novas com menor apoio verbal.",
    "Limítrofe": "Esse resultado revela fragilidade significativa em habilidades de raciocínio não verbal, organização perceptual, análise visuoespacial e resolução prática de problemas. Esse achado sugere dificuldade importante em tarefas que exigem análise visual, percepção de relações espaciais, identificação de padrões e adaptação a problemas novos.",
    "Extremamente Baixo": "Esse resultado revela prejuízo importante em habilidades de raciocínio não verbal, organização perceptual, análise visuoespacial e resolução prática de problemas. Esse achado sugere dificuldade accentuada em tarefas que demandam interpretação e organização de estímulos visuais, percepção de relações espaciais, identificação de padrões e manejo de problemas novos sem apoio direto da linguagem.",
    "Extremamente Baixa": "Esse resultado revela prejuízo importante em habilidades de raciocínio não verbal, organização perceptual, análise visuoespacial e resolução prática de problemas. Esse achado sugere dificuldade accentuada em tarefas que demandam interpretação e organização de estímulos visuais, percepção de relações espaciais, identificação de padrões e manejo de problemas novos sem apoio direto da linguagem.",
}

_QIT_PHRASES = {
    "Muito Superior": "O resultado indica funcionamento intelectual global acima do esperado para a população normativa, com recursos cognitivos amplos e bem desenvolvidos. Esse perfil sugere bom potencial para aprendizagem, resolução de problemas, abstração e adaptação cognitiva, respeitando-se as características específicas dos domínios verbal e de execução.",
    "Superior": "O resultado indica funcionamento intelectual global acima do esperado para a população normativa, com recursos cognitivos amplos e bem desenvolvidos. Esse perfil sugere bom potencial para aprendizagem, resolução de problemas, abstração e adaptação cognitiva, respeitando-se as características específicas dos domínios verbal e de execução.",
    "Média Superior": "O resultado indica funcionamento intelectual global acima da média esperada, sugerindo bons recursos cognitivos gerais para aprendizagem, compreensão, raciocínio e resolução de problemas, respeitando-se as variações observadas entre os domínios avaliados.",
    "Média": "O resultado indica funcionamento intelectual global dentro da faixa esperada para a população normativa, sugerindo recursos cognitivos gerais preservados para aprendizagem, compreensão, raciocínio e resolução de problemas, respeitando-se as variações entre os domínios avaliados.",
    "Média Inferior": "O resultado indica funcionamento intelectual global abaixo da média esperada, sugerindo vulnerabilidades cognitivas gerais que podem repercutir em tarefas acadêmicas, adaptativas ou ocupacionais que exijam raciocínio, aprendizagem, organização e resolução de problemas mais complexos.",
    "Limítrofe": "O resultado indica funcionamento intelectual global significativamente abaixo da média esperada, sugerindo limitações cognitivas relevantes que podem repercutir em aprendizagem, autonomia, adaptação funcional e resolução de problemas, especialmente em situações com maior complexidade ou menor apoio externo.",
    "Extremamente Baixo": "O resultado indica comprometimento significativo do funcionamento intelectual global. Esse desempenho sugere rendimento geral substancialmente inferior ao esperado para a população normativa, com impacto funcional variável conforme o grau de suporte ambiental, as demandas adaptativas e os recursos preservados em cada domínio.",
    "Extremamente Baixa": "O resultado indica comprometimento significativo do funcionamento intelectual global. Esse desempenho sugere rendimento geral substancialmente inferior ao esperado para a população normativa, com impacto funcional variável conforme o grau de suporte ambiental, as demandas adaptativas e os recursos preservados em cada domínio.",
}

_DISCREPANCY_PHRASES = {
    "sem discrepância clinicamente relevante": "um perfil cognitivo relativamente homogêneo entre os domínios verbal e de execução, sem discrepância clinicamente relevante entre as habilidades avaliadas. Esse padrão sugere distribuição mais equilibrada dos recursos cognitivos, ainda que a interpretação deva considerar a classificação obtida em cada índice.",
    "discrepância discreta": "um perfil cognitivo com pequenas diferenças entre os domínios verbal e de execução. Esse padrão sugere distribuição relativamente equilibrada dos recursos cognitivos, ainda que a interpretação deva considerar a classificação obtida em cada índice.",
    "discrepância moderada": "um perfil cognitivo heterogêneo entre os domínios verbal e de execução. Esse padrão pode refletir diferentes formas de-processamento cognitivo, com um domínio relativamente mais preservado que o outro.",
    "discrepância acentuada": "um perfil cognitivo claramente heterogêneo entre os domínios verbal e de execução. Esse padrão reflete diferenças importantes na forma como o indivíduo processa informações verbais versus não verbais.",
}

_DISCREPANCY_DIRECTION_PHRASES = {
    ("verbal", "sem discrepância clinicamente relevante"): "Observa-se, portanto, um perfil cognitivo relativamente homogêneo entre os domínios verbal e de execução, sem discrepância clinicamente relevante entre as habilidades avaliadas.",
    ("verbal", "discrepância discreta"): "Observa-se, portanto, um perfil cognitivo com leve vantagem nas habilidades verbais quando comparadas às habilidades de execução.",
    ("verbal", "discrepância moderada"): "Observa-se, portanto, um perfil cognitivo heterogêneo, com desempenho relativamente mais preservado nas habilidades verbais quando comparado ao desempenho não verbal. A discrepância entre os domínios avaliados sugere que {nome} apresenta melhores recursos em tarefas mediadas pela linguagem do que em atividades que exigem organização perceptual, raciocínio visuoespacial e resolução prática de problemas.",
    ("verbal", "discrepância accentuada"): "Observa-se, portanto, um perfil cognitivo heterogêneo, com desempenho significativamente mais preservado nas habilidades verbais quando comparado ao desempenho não verbal. A discrepância acentuada entre os domínios avaliados sugere que {nome} apresenta recursos claramente superiores em tarefas mediadas pela linguagem quando comparadas às atividades que exigem organização perceptual, raciocínio visuoespacial e resolução prática de problemas.",
    ("execução", "sem discrepância clinicamente relevante"): "Observa-se, portanto, um perfil cognitivo relativamente homogêneo entre os domínios verbal e de execução, sem discrepância clinicamente relevante entre as habilidades avaliadas.",
    ("execução", "discrepância discreta"): "Observa-se, portanto, um perfil cognitivo com leve vantagem nas habilidades de execução quando comparadas às habilidades verbais.",
    ("execução", "discrepância moderada"): "Observa-se, portanto, um perfil cognitivo heterogêneo, com desempenho relativamente mais preservado nas habilidades de execução quando comparado ao desempenho verbal. A discrepância entre os domínios avaliados sugere que {nome} apresenta melhores recursos em tarefas visuais, perceptuais e práticas do que em atividades que exigem compreensão verbal, elaboração linguística e raciocínio abstrato mediado pela linguagem.",
    ("execução", "discrepância accentuada"): "Observa-se, portanto, um perfil cognitivo heterogêneo, com desempenho significativamente mais preservado nas habilidades de execução quando comparado ao desempenho verbal. A discrepância accentuada entre os domínios avaliados sugere que {nome} apresenta recursos claramente superiores em tarefas visuais, perceptuais e práticas quando comparadas às atividades que exigem compreensão verbal, elaboração linguística e raciocínio abstrato mediado pela linguagem.",
    ("equilibrado", "sem discrepância clinicamente relevante"): "Observa-se, portanto, um perfil cognitivo relativamente homogêneo entre os domínios verbal e de execução, sem discrepância clinicamente relevante entre as habilidades avaliadas.",
}

_FUNCTIONAL_PHRASES = {
    "Muito Superior": "esse padrão sugere recursos intelectuais globais preservados, com possíveis facilidades ou vulnerabilidades específicas conforme a distribuição entre os domínios verbal e de execução. A interpretação deve considerar a compatibilidade entre os resultados objetivos, as observações clínicas e o funcionamento adaptativo cotidiano.",
    "Superior": "esse padrão sugere recursos intelectuais globais preservados, com possíveis facilidades ou vulnerabilidades específicas conforme a distribuição entre os domínios verbal e de execução. A interpretação deve considerar a compatibilidade entre os resultados objetivos, as observações clínicas e o funcionamento adaptativo cotidiano.",
    "Média Superior": "esse padrão sugere recursos intelectuais globais preservados, com possíveis facilidades ou vulnerabilidades específicas conforme a distribuição entre os domínios verbal e de execução. A interpretação deve considerar a compatibilidade entre os resultados objetivos, as observações clínicas e o funcionamento adaptativo cotidiano.",
    "Média": "esse padrão sugere recursos intelectuais globais preservados, com possíveis facilidades ou vulnerabilidades específicas conforme a distribuição entre os domínios verbal e de execução. A interpretação deve considerar a compatibilidade entre os resultados objetivos, as observações clínicas e o funcionamento adaptativo cotidiano.",
    "Média Inferior": "esse padrão pode repercutir no cotidiano em situações que envolvam aprendizagem, organização, autonomia, compreensão de demandas complexas e resolução de problemas novos. A magnitude do impacto funcional deve ser compreendida de forma integrada aos dados da anamnese, observação clínica, escolaridade, contexto sociocultural e demais instrumentos aplicados.",
    "Limítrofe": "esse padrão pode repercutir no cotidiano em situações que envolvam aprendizagem, organização, autonomia, compreensão de demandas complexas e resolução de problemas novos. A magnitude do impacto funcional deve ser compreendida de forma integrada aos dados da anamnese, observação clínica, escolaridade, contexto sociocultural e demais instrumentos aplicados.",
    "Extremamente Baixo": "esse padrão pode repercutir de forma significativa no cotidiano, especialmente em situações que envolvam autonomia para resolver problemas novos, lidar com informações complexas, organizar-se diante de demandas práticas e adaptar-se a tarefas com menor mediação externa. O rebaixamento global do desempenho intelectual indica limitações cognitivas relevantes, que devem ser compreendidas em conjunto com a funcionalidade adaptativa, a história do desenvolvimento, os dados escolares ou ocupacionais e as demais evidências clínicas.",
    "Extremamente Baixa": "esse padrão pode repercutir de forma significativa no cotidiano, especialmente em situações que envolvam autonomia para resolver problemas novos, lidar com informações complexas, organizar-se diante de demandas práticas e adaptar-se a tarefas com menor mediação externa. O rebaixamento global do desempenho intelectual indica limitações cognitivas relevantes, que devem ser compreendidas em conjunto com a funcionalidade adaptativa, a história do desenvolvimento, os dados escolares ou ocupacionais e as demais evidências clínicas.",
}


def _normalize_classification(classification: str) -> str:
    mapping = {
        "Muito Superior": "Muito Superior",
        "Superior": "Superior",
        "Média Superior": "Média Superior",
        "Média": "Média",
        "Média Inferior": "Média Inferior",
        "Limítrofe": "Limítrofe",
        "Extremamente Baixo": "Extremamente Baixo",
        "Extremamente Baixa": "Extremamente Baixa",
    }
    return mapping.get(classification, classification)


def build_wasi_interpretation(merged_data: dict, patient_name: str | None = None, include_diagnostic_hypothesis: bool = True) -> str:
    name = _first_name(patient_name or "Paciente")

    composites = merged_data.get("composites", {})
    qiv_data = composites.get("qi_verbal", {})
    qie_data = composites.get("qi_execucao", {})
    qit4_data = composites.get("qit_4", {})
    qit2_data = composites.get("qit_2", {})
    qiv = qiv_data.get("qi")
    qie = qie_data.get("qi")
    qit = qit4_data.get("qi") or qit2_data.get("qi")

    qiv_classification = _normalize_classification(qiv_data.get("classification", "Média"))
    qie_classification = _normalize_classification(qie_data.get("classification", "Média"))
    qit_classification = _normalize_classification(qit4_data.get("classification") or qit2_data.get("classification") or "Média")

    qiv_text = _QIV_PHRASES.get(qiv_classification, "").format(nome=name)
    qie_text = _QIE_PHRASES.get(qie_classification, "").format(nome=name)
    qit_text = _QIT_PHRASES.get(qit_classification, "").format(nome=name)

    discrepancy = _classify_qiv_qie_discrepancy(qiv or 0, qie or 0)
    discrepancy_key = (discrepancy["stronger_domain"], discrepancy["level"])
    discrepancy_text = _DISCREPANCY_DIRECTION_PHRASES.get(discrepancy_key, "").format(nome=name)

    if not discrepancy_text and discrepancy["level"] != "sem discrepância clinicamente relevante":
        if discrepancy["stronger_domain"] == "verbal":
            discrepancy_text = "Observa-se, portanto, um perfil cognitivo heterogêneo, com desempenho relativamente mais preservado nas habilidades verbais quando comparado ao desempenho não verbal."
        elif discrepancy["stronger_domain"] == "execução":
            discrepancy_text = "Observa-se, portanto, um perfil cognitivo heterogêneo, com desempenho relativamente mais preservado nas habilidades de execução quando comparado ao desempenho verbal."
        else:
            discrepancy_text = "Observa-se, portanto, um perfil cognitivo relativamente homogêneo entre os domínios verbal e de execução."

    functional_text = _FUNCTIONAL_PHRASES.get(qit_classification, "")

    diagnostic_hypothesis = ""
    if include_diagnostic_hypothesis and qit is not None:
        if qit <= 69:
            diagnostic_hypothesis = "Há hipótese diagnóstica de Deficiência Intelectual, a ser compreendida de forma integrada aos dados da anamnese, da funcionalidade adaptativa e das demais evidências clínicas."
        elif 70 <= qit <= 79:
            diagnostic_hypothesis = "Há hipótese diagnóstica de funcionamento intelectual limítrofe, a ser compreendida de forma integrada aos dados da anamnese, da funcionalidade adaptativa e das demais evidências clínicas."

    paragraphs = [
        f"A avaliação neuropsicológica de {name}, por meio da Escala Wechsler Abreviada de Inteligência – WASI, possibilitou a análise do funcionamento intelectual global e de domínios cognitivos centrais, oferecendo indicadores objetivos acerca de seu perfil intelectual.",
        f"{name} obteve Quociente de Inteligência Verbal (QI Verbal) igual a {qiv}, classificado na faixa {qiv_classification}. {qiv_text}",
        f"No Quociente de Inteligência de Execução (QI Execucao), {name} obteve escore {qie}, classificado na faixa {qie_classification}. {qie_text}",
        f"O Quociente de Inteligência Total foi {qit}, classificado na faixa {qit_classification}. {qit_text}",
    ]

    if discrepancy_text:
        paragraphs.append(discrepancy_text)

    if functional_text or diagnostic_hypothesis:
        final_text = f"Em análise clínica, {functional_text}"
        if diagnostic_hypothesis:
            final_text += f" {diagnostic_hypothesis}"
        paragraphs.append(final_text)

    return "\n\n".join(paragraphs)
