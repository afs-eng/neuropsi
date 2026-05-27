INTRO_TEMPLATE = (
    "Interpretação e Observações Clínicas: A avaliação da atenção de {name} foi "
    "realizada por meio da Bateria Psicológica para Avaliação da Atenção – BPA-2, "
    "instrumento destinado à investigação dos principais componentes do "
    "funcionamento atencional, incluindo atenção concentrada, dividida, alternada e "
    "atenção geral, domínios associados à sustentação do foco, à distribuição dos "
    "recursos atencionais e ao controle executivo."
)

NOMES_SUBTESTES = {
    "ac": "Atenção Concentrada",
    "ad": "Atenção Dividida",
    "aa": "Atenção Alternada",
    "ag": "Atenção Geral",
}

SECTION_TITLES = {
    "ac": "Atenção Concentrada (AC)",
    "ad": "Atenção Dividida (AD)",
    "aa": "Atenção Alternada (AA)",
    "ag": "Atenção Geral (AG)",
}

SUBTEST_OPENINGS = {
    "ac": {
        "opening": "Avalia a capacidade de selecionar estímulos relevantes e manter o foco atencional diante de estímulos distratores.",
        "Muito Inferior": "{name} apresentou desempenho classificado como muito inferior (percentil {percentil}), indicando comprometimento relevante nesse domínio, com prejuízo atencional clinicamente significativo. Esse resultado sugere dificuldade importante para sustentar a atenção, manter constância do foco e inibir interferências distratoras durante tarefas contínuas.",
        "Inferior": "{name} apresentou desempenho classificado como inferior (percentil {percentil}), sugerindo comprometimento relevante nesse domínio, com prejuízo atencional clinicamente significativo. Esse resultado sugere dificuldade importante para sustentar a atenção, manter constância do foco e inibir interferências distratoras durante tarefas contínuas.",
        "Média Inferior": "{name} apresentou desempenho classificado como média inferior (percentil {percentil}), indicando rebaixamento leve nesse domínio, com sinais de menor eficiência atencional quando comparado ao esperado para a faixa etária. Esse resultado sugere maior suscetibilidade a oscilações do foco atencional em tarefas que exigem concentração prolongada.",
        "Média": "{name} apresentou desempenho classificado como médio (percentil {percentil}), indicando funcionamento atencional dentro dos limites esperados para sua faixa etária, sem evidências de prejuízo significativo nesse domínio. Esse resultado sugere capacidade adequada de concentração sustentada e manutenção do foco diante de demandas contínuas.",
        "Média Superior": "{name} apresentou desempenho classificado como média superior (percentil {percentil}), sugerindo funcionamento atencional acima do esperado, com boa eficiência nesse domínio. Esse resultado sugere boa sustentação do foco e adequada resistência à interferência de estímulos distratores.",
        "Superior": "{name} apresentou desempenho classificado como superior (percentil {percentil}), indicando habilidade muito desenvolvida nesse domínio, com eficiência acima do esperado para sua faixa etária. Esse resultado sugere excelente capacidade de sustentação do foco, elevada resistência à distração e boa constância atencional em tarefas prolongadas.",
        "Muito Superior": "{name} apresentou desempenho classificado como muito superior (percentil {percentil}), indicando desempenho excepcional na capacidade de sustentar a atenção de forma contínua e direcionada, com elevada estabilidade do foco mesmo em contextos de alta exigência.",
    },
    "ad": {
        "opening": "Refere-se à habilidade de distribuir os recursos atencionais entre múltiplos estímulos ou demandas simultâneas.",
        "Muito Inferior": "O desempenho de {name} foi classificado como muito inferior (percentil {percentil}), sugerindo comprometimento relevante nesse domínio, com prejuízo atencional clinicamente significativo. Esse desempenho sugere prejuízo importante na habilidade de processar simultaneamente mais de uma demanda, com possível impacto em situações que exigem monitoramento concorrente de informações.",
        "Inferior": "O desempenho de {name} foi classificado como inferior (percentil {percentil}), sugerindo comprometimento relevante nesse domínio, com prejuízo atencional clinicamente significativo. Esse desempenho sugere prejuízo importante na habilidade de processar simultaneamente mais de uma demanda, com possível impacto em situações que exigem monitoramento concorrente de informações.",
        "Média Inferior": "O desempenho de {name} foi classificado como média inferior (percentil {percentil}), indicando rebaixamento leve nesse domínio, com sinais de menor eficiência atencional quando comparado ao esperado para a faixa etária. Esse desempenho sugere dificuldade discreta a moderada na distribuição dos recursos atencionais entre múltiplas demandas, podendo reduzir a eficiência em situações complexas.",
        "Média": "O desempenho de {name} foi classificado como médio (percentil {percentil}), indicando funcionamento atencional dentro dos limites esperados para sua faixa etária, sem evidências de prejuízo significativo nesse domínio. Esse desempenho indica capacidade preservada para dividir a atenção entre diferentes estímulos ou tarefas simultâneas.",
        "Média Superior": "O desempenho de {name} foi classificado como média superior (percentil {percentil}), sugerindo funcionamento atencional acima do esperado, com boa eficiência nesse domínio. Esse desempenho sugere boa distribuição dos recursos atencionais entre estímulos múltiplos, sem prejuízos relevantes.",
        "Superior": "O desempenho de {name} foi classificado como superior (percentil {percentil}), indicando habilidade muito desenvolvida nesse domínio, com eficiência acima do esperado para sua faixa etária. Esse desempenho evidencia notável capacidade de acompanhar simultaneamente diferentes estímulos e lidar com múltiplas demandas cognitivas com eficiência.",
        "Muito Superior": "O desempenho de {name} foi classificado como muito superior (percentil {percentil}), sugerindo capacidade excepcional para distribuir os recursos atencionais entre estímulos múltiplos, com funcionamento diferenciado em situações de alta complexidade.",
    },
    "aa": {
        "opening": "Mede a capacidade de alternar o foco atencional entre tarefas ou estímulos distintos, exigindo flexibilidade cognitiva e monitoramento contínuo.",
        "Muito Inferior": "{name} apresentou desempenho na faixa muito inferior (percentil {percentil}), sugerindo comprometimento relevante nesse domínio, com prejuízo atencional clinicamente significativo. Esse resultado indica comprometimento importante da alternância atencional, com dificuldade para ajustar o foco mental diante de mudanças de tarefa, regra ou estímulo.",
        "Inferior": "{name} apresentou desempenho na faixa inferior (percentil {percentil}), sugerindo comprometimento relevante nesse domínio, com prejuízo atencional clinicamente significativo. Esse resultado indica comprometimento importante da alternância atencional, com dificuldade para ajustar o foco mental diante de mudanças de tarefa, regra ou estímulo.",
        "Média Inferior": "{name} apresentou desempenho na faixa média inferior (percentil {percentil}), indicando rebaixamento leve nesse domínio, com sinais de menor eficiência atencional quando comparado ao esperado para a faixa etária. Esse resultado indica redução na flexibilidade atencional e menor eficiência para mudar o foco entre diferentes demandas cognitivas.",
        "Média": "{name} apresentou desempenho na faixa média (percentil {percentil}), indicando funcionamento atencional dentro dos limites esperados para sua faixa etária, sem evidências de prejuízo significativo nesse domínio. Esse resultado indica capacidade preservada para alternar o foco atencional entre diferentes demandas, sem prejuízos significativos.",
        "Média Superior": "{name} apresentou desempenho na faixa média superior (percentil {percentil}), sugerindo funcionamento atencional acima do esperado, com boa eficiência nesse domínio. Esse resultado sugere boa flexibilidade cognitiva e eficiência na alternância do foco entre tarefas ou estímulos distintos.",
        "Superior": "{name} apresentou desempenho na faixa superior (percentil {percentil}), indicando habilidade muito desenvolvida nesse domínio, com eficiência acima do esperado para sua faixa etária. Esse resultado evidencia elevada flexibilidade atencional, com boa capacidade de ajustar-se rapidamente a mudanças de regras, estímulos ou exigências da tarefa.",
        "Muito Superior": "{name} apresentou desempenho na faixa muito superior (percentil {percentil}), indicando flexibilidade atencional excepcional e elevada eficiência para mudar rapidamente o foco entre diferentes demandas cognitivas.",
    },
    "ag": {
        "opening": "Representa a integração global dos componentes atencionais avaliados, sintetizando o funcionamento geral da atenção.",
        "Muito Inferior": "O desempenho foi classificado como muito inferior (percentil {percentil}), sugerindo comprometimento relevante nesse domínio, com prejuízo atencional clinicamente significativo. De forma global, observa-se comprometimento do funcionamento atencional, com impacto conjunto sobre a sustentação, distribuição e alternância do foco atencional.",
        "Inferior": "O desempenho foi classificado como inferior (percentil {percentil}), sugerindo comprometimento relevante nesse domínio, com prejuízo atencional clinicamente significativo. De forma global, observa-se comprometimento do funcionamento atencional, com impacto conjunto sobre a sustentação, distribuição e alternância do foco atencional.",
        "Média Inferior": "O desempenho foi classificado como média inferior (percentil {percentil}), indicando rebaixamento leve nesse domínio, com sinais de menor eficiência atencional quando comparado ao esperado para a faixa etária. De forma global, observa-se funcionamento atencional discretamente rebaixado, sugerindo fragilidade na integração entre os diferentes componentes da atenção.",
        "Média": "O desempenho foi classificado como médio (percentil {percentil}), indicando funcionamento atencional dentro dos limites esperados para sua faixa etária, sem evidências de prejuízo significativo nesse domínio. De forma global, o funcionamento atencional encontra-se preservado, com integração adequada entre os diferentes componentes avaliados.",
        "Média Superior": "O desempenho foi classificado como média superior (percentil {percentil}), sugerindo funcionamento atencional acima do esperado, com boa eficiência nesse domínio. De forma global, o funcionamento atencional mostra-se acima do esperado, com boa integração entre os diferentes componentes da atenção.",
        "Superior": "O desempenho foi classificado como superior (percentil {percentil}), indicando habilidade muito desenvolvida nesse domínio, com eficiência acima do esperado para sua faixa etária. De forma global, o funcionamento atencional mostra-se muito bem desenvolvido, com integração eficiente entre os diferentes componentes avaliados.",
        "Muito Superior": "O desempenho foi classificado como muito superior (percentil {percentil}), sugerindo funcionamento atencional global excepcional, com integração diferenciada entre os diversos componentes avaliados.",
    },
}


def build_report_intro(name: str) -> str:
    return INTRO_TEMPLATE.format(name=name)


def get_report_interpretation(code: str, classificacao: str, nome: str) -> str:
    return build_subtest_paragraph(code, classificacao, 0, nome.split(" ", 1)[0])


def get_synthesis(classificacao: str) -> str:
    if classificacao in {"Muito Inferior", "Inferior", "Média Inferior"}:
        return (
            "Perfil atencional global rebaixado, com prejuízo clinicamente relevante."
        )
    if classificacao == "Média":
        return "Perfil atencional global compatível com o esperado para a faixa etária."
    return "Perfil atencional global acima do esperado, com recursos atencionais preservados."


def build_subtest_paragraph(
    code: str, classificacao: str, percentil: int | float, name: str
) -> str:
    descriptions = SUBTEST_OPENINGS.get(code, {})
    opening = descriptions.get("opening")
    description = descriptions.get(classificacao)
    title = SECTION_TITLES.get(code)
    if not title or not opening or not description:
        return "Interpretação não disponível."
    return f"{title}\n{opening} {description.format(name=name, percentil=percentil)}"


def build_clinical_summary(subtests: list[dict], name: str) -> str:
    by_code = {item.get("codigo"): item for item in subtests}
    ag_classificacao = (by_code.get("ag") or {}).get("classificacao", "")
    ac = (by_code.get("ac") or {}).get("classificacao", "")
    ad = (by_code.get("ad") or {}).get("classificacao", "")
    aa = (by_code.get("aa") or {}).get("classificacao", "")

    preserved = {"Média", "Média Superior", "Superior"}
    lowered = {"Média Inferior", "Inferior", "Muito Inferior"}
    specific = [ac, ad, aa]
    lowered_count = sum(1 for item in specific if item in lowered)
    preserved_count = sum(1 for item in specific if item in preserved)

    if ag_classificacao in preserved and preserved_count == 3:
        return (
            f"Em análise clínica, o perfil atencional de {name} revela funcionamento global dentro ou acima do esperado para a faixa etária, "
            "com adequada integração entre sustentação do foco, divisão dos recursos atencionais e alternância entre estímulos. "
            "Os achados não indicam prejuízo atencional clinicamente relevante no momento da avaliação."
        )

    if ag_classificacao in {"Média", "Média Superior"} and lowered_count >= 1:
        return (
            f"Em análise clínica, o perfil atencional de {name} revela funcionamento global preservado, embora com fragilidades pontuais em componentes específicos da atenção. "
            "Esse padrão sugere que, apesar da integração global mostrar-se adequada, determinadas exigências cognitivas podem ser realizadas com maior esforço, especialmente em contextos de maior complexidade ou sobrecarga ambiental."
        )

    if ag_classificacao in {"Média Inferior", "Inferior"} and preserved_count >= 1:
        return (
            f"Em análise clínica, o perfil atencional de {name} revela que, embora alguns componentes específicos tenham se mantido dentro da faixa esperada, a integração global desses recursos mostrou-se menos eficiente. "
            "Esse padrão sugere fragilidade no funcionamento atencional como um todo, com possível oscilação no desempenho diante de tarefas prolongadas, múltiplas demandas ou necessidade de adaptação rápida."
        )

    if ag_classificacao == "Média Inferior" and lowered_count >= 2:
        return (
            f"Em análise clínica, o perfil atencional de {name} revela funcionamento global discretamente rebaixado, com fragilidades mais abrangentes nos mecanismos de sustentação, distribuição e alternância do foco atencional. "
            "Os achados sugerem menor eficiência para lidar com tarefas contínuas, múltiplos estímulos e situações que exigem ajuste mental frequente."
        )

    if ag_classificacao == "Inferior" and lowered_count >= 2:
        return (
            f"Em análise clínica, o perfil atencional de {name} revela funcionamento global rebaixado, com prejuízo clinicamente relevante nos mecanismos de sustentação do foco, distribuição dos recursos atencionais e alternância entre estímulos. "
            "Em contexto funcional, esse padrão pode se associar a dificuldades para manter a concentração em tarefas prolongadas, acompanhar comandos com múltiplas etapas, alternar entre atividades e sustentar desempenho consistente diante de demandas cognitivas contínuas."
        )

    if (
        ag_classificacao in {"Superior", "Média Superior"}
        and sum(1 for item in specific if item in {"Superior", "Média Superior"}) >= 2
    ):
        return (
            f"Em análise clínica, o perfil atencional de {name} revela funcionamento global eficiente, com bom controle do foco atencional, adequada distribuição dos recursos cognitivos e flexibilidade para alternar entre diferentes demandas. "
            "Os achados sugerem recursos atencionais bem desenvolvidos e funcionalmente adaptativos."
        )

    return (
        f"Em análise clínica, o perfil atencional de {name} deve ser interpretado de forma integrada, considerando o peso maior da atenção geral e a variação observada nos componentes específicos. "
        "Os achados sugerem que o funcionamento atencional pode oscilar conforme a complexidade da tarefa, a necessidade de sustentar o foco e a exigência de adaptação entre diferentes demandas cognitivas."
    )


def build_gold_standard_interpretation(subtests: list[dict], name: str) -> dict:
    by_code = {item.get("codigo"): item for item in subtests}
    ac = by_code.get("ac") or {}
    ad = by_code.get("ad") or {}
    aa = by_code.get("aa") or {}
    ag = by_code.get("ag") or {}
    short_name = (name or "Paciente").split(" ", 1)[0]
    total_errors = sum(_num((by_code.get(code) or {}).get("erros")) for code in ["ac", "ad", "aa"])
    specific_classes = [_classification(ac), _classification(ad), _classification(aa)]
    heterogeneous = _has_relevant_discrepancy(specific_classes)

    paragraphs = [
        _opening_paragraph(ag, heterogeneous),
        _domain_paragraph("Atenção Concentrada", ac, _ac_interpretation),
        _domain_paragraph("Atenção Dividida", ad, _ad_interpretation),
        _domain_paragraph("Atenção Alternada", aa, _aa_interpretation),
        _ag_and_qualitative_paragraph(ag, total_errors, heterogeneous),
    ]
    clinical_box_text = _clinical_box_text(short_name, ac, ad, aa, ag, total_errors)
    synthesis_text = _synthesis_text(short_name, ac, ad, aa, ag, total_errors)
    return {
        "clinical_paragraphs": paragraphs,
        "clinical_box_text": clinical_box_text,
        "synthesis_text": synthesis_text,
    }


def _opening_paragraph(ag: dict, heterogeneous: bool) -> str:
    ag_class = _classification(ag)
    if heterogeneous:
        caution = (
            " Contudo, esse índice deve ser interpretado com cautela, pois houve variação entre os domínios específicos avaliados. "
            "Assim, a análise clínica deve priorizar o perfil por domínio, uma vez que a medida geral pode mascarar fragilidades ou pontos fortes específicos."
        )
    else:
        caution = " Esse resultado evidencia desempenho convergente entre atenção concentrada, atenção dividida e atenção alternada."
    return (
        f"A BPA-2 indicou desempenho atencional geral situado na faixa {ag_class}, sugerindo funcionamento atencional global {_global_level_text(ag_class)} para a faixa etária e tabela normativa utilizada. "
        f"Esse resultado deve ser compreendido como indicador do desempenho em contexto estruturado de avaliação.{caution}"
    )


def _domain_paragraph(title: str, result: dict, interpretation_builder) -> str:
    classification = _classification(result)
    percentile = _format_number(result.get("percentil"))
    points = _format_number(result.get("total"))
    errors = _format_number(result.get("erros"))
    return (
        f"Na {title}, o desempenho foi classificado como {classification} (pontuação {points}; percentil {percentile}), {interpretation_builder(classification)} "
        f"{_domain_error_sentence(_num(result.get('erros')), title)}"
    )


def _ag_and_qualitative_paragraph(ag: dict, total_errors: int, heterogeneous: bool) -> str:
    ag_class = _classification(ag)
    if heterogeneous:
        profile_text = "perfil heterogêneo entre os componentes atencionais"
        integration = "Esse índice deve ser interpretado com cautela e integrado ao padrão específico de AC, AD e AA."
    else:
        profile_text = f"desempenho global {_global_level_text(ag_class)}"
        integration = "Como os domínios específicos apresentaram padrão homogêneo e convergente, esse índice pode ser considerado representativo do funcionamento atencional global no contexto estruturado de avaliação."
    return (
        f"A Atenção Geral apresentou classificação {ag_class}, refletindo {profile_text} na bateria. "
        f"{integration} {_errors_text(total_errors)}"
    )


def _clinical_box_text(short_name: str, ac: dict, ad: dict, aa: dict, ag: dict, total_errors: int) -> str:
    strengths = _domain_labels_by_level([("atenção concentrada", ac), ("atenção dividida", ad), ("atenção alternada", aa)], high=True)
    fragilities = _domain_labels_by_level([("atenção concentrada", ac), ("atenção dividida", ad), ("atenção alternada", aa)], high=False)
    ag_class = _classification(ag)

    if fragilities:
        profile = f"funcionamento atencional com fragilidades específicas em {_join(fragilities)}"
    elif strengths:
        profile = f"funcionamento atencional global preservado, com maior eficiência em {_join(strengths)}"
    else:
        profile = "funcionamento atencional preservado e compatível com o esperado para a tabela normativa utilizada"

    discrepancy_note = (
        "A Atenção Geral deve ser integrada ao padrão dos domínios específicos para evitar que a medida global mascare discrepâncias clínicas relevantes. "
        if fragilities else ""
    )
    return (
        f"Em análise clínica, o perfil atencional de {short_name} sugere {profile}. "
        f"{discrepancy_note}O conjunto dos resultados aponta para {_global_outcome(ag_class, bool(fragilities))}. "
        f"{_clinical_error_closing(total_errors)}"
    )


def _synthesis_text(short_name: str, ac: dict, ad: dict, aa: dict, ag: dict, total_errors: int) -> str:
    strengths = _domain_labels_by_level([("atenção concentrada", ac), ("atenção dividida", ad), ("atenção alternada", aa)], high=True)
    fragilities = _domain_labels_by_level([("atenção concentrada", ac), ("atenção dividida", ad), ("atenção alternada", aa)], high=False)
    complement = f"com pontos fortes em {_join(strengths)}" if strengths else "sem pontos fortes normativos destacados"
    if fragilities:
        complement += f" e fragilidades em {_join(fragilities)}"
    else:
        complement += " e sem fragilidades normativas nos domínios específicos"

    return (
        f"A BPA-2 indicou desempenho atencional geral na faixa {_classification(ag)}, com atenção concentrada classificada como {_classification(ac)}, atenção dividida como {_classification(ad)} e atenção alternada como {_classification(aa)}. "
        f"Em análise clínica, o perfil de {short_name} sugere funcionamento atencional {_global_level_text(_classification(ag))}, {complement}. "
        f"{_synthesis_error_closing(total_errors)}"
    )


def _ac_interpretation(classification: str) -> str:
    if classification in {"Muito Inferior", "Inferior"}:
        return "sugerindo dificuldade na seleção de estímulos relevantes e na manutenção do foco diante de distratores em tempo determinado. Esse resultado pode indicar fragilidade em atenção seletiva, monitoramento visual e controle da resposta."
    if classification in {"Média Inferior", "Médio Inferior"}:
        return "sugerindo rendimento reduzido em tarefa que exige seleção de estímulos relevantes e manutenção do foco diante de distratores. Esse resultado pode indicar vulnerabilidade em atenção seletiva ou sustentação do desempenho quando integrado a outros achados clínicos."
    if classification == "Média":
        return "indicando capacidade adequada para selecionar estímulos relevantes, manter o foco e responder diante de distratores em tempo determinado."
    return "indicando boa eficiência na seleção de estímulos relevantes e na manutenção do foco diante de distratores. Esse resultado sugere preservação e/ou maior eficiência dos mecanismos de atenção seletiva no contexto estruturado da tarefa."


def _ad_interpretation(classification: str) -> str:
    if classification in {"Muito Inferior", "Inferior"}:
        return "sugerindo dificuldade para monitorar simultaneamente mais de uma fonte de informação e distribuir recursos atencionais diante de estímulos concorrentes."
    if classification in {"Média Inferior", "Médio Inferior"}:
        return "indicando rendimento reduzido em tarefa que exige monitoramento simultâneo de estímulos, podendo sugerir vulnerabilidade na distribuição dos recursos atencionais em situações com múltiplas demandas."
    if classification == "Média":
        return "indicando capacidade adequada para monitorar mais de um estímulo simultaneamente e distribuir recursos atencionais em tempo determinado."
    return "indicando boa ou elevada eficiência para monitorar estímulos simultâneos, distribuir recursos atencionais e responder diante de demandas concorrentes."


def _aa_interpretation(classification: str) -> str:
    if classification in {"Muito Inferior", "Inferior"}:
        return "sugerindo dificuldade na alternância do foco entre estímulos ou critérios distintos, com possível fragilidade em flexibilidade atencional, mudança de estratégia e adaptação às regras da tarefa."
    if classification in {"Média Inferior", "Médio Inferior"}:
        return "indicando rendimento reduzido em tarefa que exige alternância do foco e adaptação a critérios distintos de resposta, podendo sugerir vulnerabilidade em flexibilidade atencional."
    if classification == "Média":
        return "indicando capacidade adequada para alternar o foco entre estímulos ou critérios distintos, com adaptação funcional às regras da tarefa."
    return "indicando boa flexibilidade atencional, eficiência na mudança de foco e capacidade preservada para adaptar-se a critérios distintos de resposta."


def _errors_text(total_errors: int) -> str:
    if total_errors <= 2:
        return "A ausência ou baixa ocorrência de erros sugere boa precisão, seletividade e monitoramento da resposta ao longo da execução."
    if total_errors <= 9:
        return "A presença de erros em quantidade moderada deve ser analisada qualitativamente, podendo refletir oscilações pontuais de precisão, monitoramento ou controle da resposta."
    return "A quantidade elevada de erros sugere redução da precisão durante a tarefa, podendo estar associada a falhas de seletividade, impulsividade de resposta, baixa inibição ou análise insuficiente antes da marcação."


def _domain_error_sentence(errors: int, title: str) -> str:
    domain = title.replace("Atenção ", "").lower()
    if errors == 0:
        return f"A ausência de erros nesse domínio sugere boa precisão na execução da tarefa, com adequado monitoramento da resposta e controle sobre marcações em estímulos não alvo."
    if errors <= 3:
        return f"Os erros observados nesse domínio devem ser compreendidos como indicadores qualitativos complementares de precisão e monitoramento da resposta durante a tarefa."
    return f"A quantidade de erros nesse domínio deve ser analisada qualitativamente, podendo indicar maior oscilação de precisão, seletividade ou controle da resposta em tarefas de {domain}."


def _clinical_error_closing(total_errors: int) -> str:
    if total_errors == 0:
        return "A ausência de erros reforça a precisão e o monitoramento adequado da resposta, sem evidências, neste instrumento, de prejuízo atencional clinicamente significativo."
    return f"Os erros observados ({_format_number(total_errors)}) devem ser compreendidos como indicadores qualitativos complementares de precisão e monitoramento da resposta, não devendo ser interpretados de forma isolada."


def _synthesis_error_closing(total_errors: int) -> str:
    if total_errors == 0:
        return "A ausência de erros indica boa precisão e adequado monitoramento da resposta, não havendo, neste instrumento, evidências de prejuízo atencional clinicamente significativo."
    return f"Os erros observados ({_format_number(total_errors)}) devem ser compreendidos como indicadores qualitativos de precisão, seletividade e monitoramento da resposta, não devendo ser interpretados de forma isolada."


def _has_relevant_discrepancy(classifications: list[str]) -> bool:
    levels = [_class_level(item) for item in classifications]
    return max(levels) - min(levels) >= 2 if levels else False


def _class_level(classification: str) -> int:
    levels = {
        "Muito Inferior": 1,
        "Inferior": 2,
        "Média Inferior": 3,
        "Médio Inferior": 3,
        "Média": 4,
        "Média Superior": 5,
        "Superior": 6,
        "Muito Superior": 7,
    }
    return levels.get(classification, 4)


def _global_level_text(classification: str) -> str:
    if classification in {"Muito Inferior", "Inferior", "Média Inferior", "Médio Inferior"}:
        return "abaixo do esperado"
    if classification == "Média":
        return "preservado"
    return "preservado e acima da média normativa"


def _global_outcome(classification: str, has_fragility: bool) -> str:
    if has_fragility:
        return "perfil heterogêneo, com necessidade de análise por domínio"
    if classification in {"Muito Inferior", "Inferior", "Média Inferior", "Médio Inferior"}:
        return "desempenho global reduzido no contexto estruturado da tarefa"
    return "funcionamento preservado no contexto estruturado da tarefa"


def _domain_labels_by_level(items: list[tuple[str, dict]], high: bool) -> list[str]:
    if high:
        return [label for label, result in items if _classification(result) in {"Média Superior", "Superior", "Muito Superior"}]
    return [label for label, result in items if _classification(result) in {"Média Inferior", "Médio Inferior", "Inferior", "Muito Inferior"}]


def _classification(result: dict) -> str:
    return result.get("classificacao") or result.get("classification") or "Não classificado"


def _num(value) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _format_number(value) -> str:
    if value is None or value == "":
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}".replace(".", ",")


def _join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} e {items[1]}"
    return f"{', '.join(items[:-1])} e {items[-1]}"
