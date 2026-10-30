"""Partial transcription supplied by the user; edition and form are unverified.

These domains must not be mapped to Vineland-3 subdomains or scored automatically.
"""

PROTOCOL_ID = "vineland_partial_transcription_v1"
SOURCE = "aux/vineland/Vineland3_Instrucoes_Corrigidas.md"
DESCRIPTION = (
    "Instrumento para avaliação do comportamento adaptativo, com registro de habilidades "
    "cotidianas nas áreas de Comunicação, Autonomia, Socialização e Habilidades Motoras, "
    "além do registro de comportamentos desajustados conforme o formulário aplicado."
)
LEGEND = {
    "2": "Sim, normalmente", "1": "Algumas vezes ou parcialmente", "0": "Não, nunca",
    "N": "Não teve oportunidade", "D": "Desconhecido",
}
DOMAIN_ITEMS = {
    "comunicacao": ("Comunicação", [
        "Volta os olhos e a cabeça em direção ao som.",
        "Ouve, pelo menos momentaneamente, quando o educador fala.",
        "Sorri como resposta à presença do educador.",
        "Sorri como resposta à presença de uma pessoa familiar, para além do educador.",
        "Estende os braços quando o educador diz: “Vem cá.” Ou “Upa.”",
        "Demonstra compreender a palavra “não”.",
        "Imita sons do adulto, imediatamente depois de os ouvir.",
        "Demonstra compreender o significado de pelo menos 10 palavras.",
        "Gesticula apropriadamente para indicar “Sim”, “Não”, “Eu quero”.",
        "Ouve atentamente as instruções.",
        "Demonstra compreender o significado de “Sim” e “Está bem”.",
        "Segue instruções que requerem uma acção e um objecto.",
        "Aponta correctamente para, pelo menos, uma parte principal do corpo.",
        "Utiliza o 1º nome, ou diminutivo dos irmãos, amigos ou colegas, ou diz os seus nomes quando se lhos perguntam.",
        "Utiliza frases com verbo e nome, ou com dois nomes.",
        "Nomeia, pelo menos, 20 objectos, sem se lhe perguntar.",
        "Ouve uma história, pelo menos durante 5 minutos.",
        "Indica preferência, quando se lhe proporcionam escolhas.",
        "Diz, pelo menos, 50 palavras reconhecíveis.",
        "Relata experiências espontaneamente e em termos simples.",
        "Transmite um recado simples.",
        "Utiliza frases com 4, ou mais, palavras.",
        "Aponta, a pedido, com precisão para todas as partes do corpo.",
        "Diz, pelo menos, 100 palavras reconhecíveis.",
        "Fala com frases completas.",
        "Utiliza “um(a)” e “o/a” nas frases.",
        "Segue instruções na forma “Se ... então”.",
        "Diz o 1º e o último nome, quando se lhe pergunta.",
        "Faz perguntas com: “O que é, Onde, Quem, Porque, Quando”.",
        "Diz qual o maior de dois objectos não presentes.",
        "Relata experiências com detalhe, quando se lhe pergunta.",
        "Utiliza frases com “atrás” ou “entre”, como preposição.",
        "Utiliza frases com “à volta”, como preposição, numa frase.",
    ]),
    "autonomia": ("Autonomia", [
        "Antecipa o comer quando vê a mamadeira, o peito ou comida.",
        "Abre a boca quando se lhe apresenta a colher com comida.",
        "Retira a comida da colher com a boca.",
        "Chupa ou mastiga bolachas.",
        "Come comida sólida.",
        "Bebe por canudo ou copo sem ajuda.",
        "Come sozinho com a colher.",
        "Demonstra compreender que as coisas quentes são perigosas.",
        "Indica que tem a fralda suja apontando, vocalizando ou puxando a fralda.",
        "Chupa pelo canudo.",
    ]),
    "socializacao": ("Socialização", [
        "Olha para a cara do educador.",
        "Responde à voz do educador ou de outra pessoa.",
        "Distingue o educador dos outros.",
        "Mostra interesse por pessoas ou objectos novos.",
        "Exprime 2 ou mais emoções reconhecíveis (prazer, tristeza, medo, aflição, etc.).",
    ]),
    "habilidades_motoras": ("Habilidades Motoras", [
        "Segura a cabeça quando está ao colo, pelo menos durante 15 segundos.",
        "Senta-se com apoio, durante pelo menos 1 minuto.",
        "Apanha com a mão pequenos objectos, de qualquer maneira.",
        "Transfere objectos de uma mão para a outra.",
        "Faz pinça.",
    ]),
    "comportamento_desajustado": ("Comportamento Desajustado (Parte 1)", [
        "Chupa no polegar ou noutro dedo.",
        "É excessivamente dependente.",
        "Isola-se.",
        "Molha a cama.",
        "Tem distúrbios alimentares.",
    ]),
}


def item_protocol():
    return {
        "id": PROTOCOL_ID, "source": SOURCE,
        "title": "Vineland — Escala de Comportamento Adaptativo (edição não confirmada)",
        "description": DESCRIPTION, "legend": LEGEND, "edition_verified": False,
        "complete": False, "scoring_enabled": False,
        "warning": "Banco parcial transcrito; conferir edição, formulário e regras no material licenciado antes de uso clínico. Sem conversão normativa ou laudo.",
        "domains": [{"code": code, "label": label, "items": [
            {"id": str(index), "text": text} for index, text in enumerate(items, 1)
        ]} for code, (label, items) in DOMAIN_ITEMS.items()],
    }


def normalize_item_responses(responses):
    """Validate a partial record without treating blanks, N or D as zero."""
    if not isinstance(responses, dict):
        raise ValueError("Informe respostas por domínio e item.")
    normalized = {}
    for domain, items in responses.items():
        if domain not in DOMAIN_ITEMS or not isinstance(items, dict):
            raise ValueError(f"Domínio inválido: {domain}.")
        allowed_ids = {str(i) for i in range(1, len(DOMAIN_ITEMS[domain][1]) + 1)}
        normalized[domain] = {}
        for item_id, entry in items.items():
            if item_id not in allowed_ids or not isinstance(entry, dict) or entry.keys() - {"response", "observation"}:
                raise ValueError(f"Item inválido: {domain}/{item_id}.")
            response = entry.get("response", "")
            observation = entry.get("observation", "")
            if not isinstance(response, str) or (response != "" and response.upper() not in LEGEND):
                raise ValueError(f"{domain}/{item_id}: digite somente 2, 1, 0, N ou D.")
            if not isinstance(observation, str) or len(observation) > 2000:
                raise ValueError(f"{domain}/{item_id}: observação deve ter até 2000 caracteres.")
            normalized[domain][item_id] = {"response": response.upper(), "observation": observation}
    return normalized
