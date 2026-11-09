"""Parent/caregiver domain-level form; separate from the legacy partial bank.

Text checked against the supplied scanned form, pages 4–12. Normative scoring
and clinical approval of the complete scoring criteria remain out of scope.
"""

PROTOCOL_ID = "vineland3_parent_domain_180_v1"
SOURCE = "aux/vineland/Vineland3_Todas_As_Areas_180_Itens.md"
PDF_SOURCE = "aux/vineland/Vineland-formulario.pdf"

DOMAIN_ITEMS = {
    "comunicacao": ("Comunicação", [
        "Sabe como dizer mais de um de alguma coisa. Exemplos: “Dois gatos”, “Mais bolachas”, “Aquelas flores”.",
        "Usa e em frases. Exemplos: “Mamãe e papai estão aqui”, “Eu quero sorvete e bolo”.",
        "Segue as instruções “se — então”. Exemplos: “Se você está com sede, então pegue uma bebida”; “Se você está com frio, então pegue um moletom”.",
        "Responde a perguntas que usam quando. Exemplo: você pergunta “Quando você toma café da manhã?” Diz “De manhã”.",
        "Presta atenção a uma história por pelo menos 15 minutos.",
        "Responde a perguntas que usam o porquê. Exemplo: você pergunta “Por que você está chorando?” Ele diz “Meu brinquedo quebrou”.",
        "Faz pelo menos três gestos mais avançados, como estes: (1) vir aqui com a mão, (2) colocar um dedo sobre os lábios para dizer silêncio, (3) separar as mãos para mostrar o desse tamanho, (4) balançar os ombros para dizer que não sei.",
        "Usa adjetivos para descrever as coisas. Exemplos: “Retrato bonito”, “Cachorrinho grande”.",
        "Diz seu nome e sobrenome quando você pergunta.",
        "Segue instruções para fazer a mesma ação com dois objetos diferentes. Exemplos: “Traga-me os lápis e a bola”, “Coloque sua camisa e seus sapatos”.",
        "Segue as instruções para fazer duas coisas que não estão relacionadas. Exemplo: “Desligue a TV e pegue minhas chaves”.",
        "Usa todos os pronomes (palavras que se referem a si e aos outros) corretamente. Exemplos: eu, ela, nós, eles, seus, nossos, deles.",
        "Usa sentenças de duas partes unidas por e ou mas. Exemplos: “Ela me perguntou e eu disse não”; “Julio queria ir, mas eu não quis”.",
        "Sabe como dizer que algo aconteceu no passado. Exemplos: “Eu andei até a loja”, “Maria assou um bolo”.",
        "Identifica a esquerda e a direita em seu corpo.",
        "Conta as partes básicas de uma história familiar: os personagens, o que acontece, como termina, etc.",
        "Segue instruções de três passos. Exemplo: “Vista-se, tome o café da manhã e escove os dentes”.",
        "Fala sobre seus eventos cotidianos em detalhes. Exemplo: quando você pergunta o que aconteceu na casa de um amigo hoje.",
        "Copia o seu primeiro nome sem erros.",
        "Segue as direções envolvendo esquerda e direita. Exemplos: “Vá para a esquerda”, “Olhe para a direita”.",
        "Diz algo de uma maneira diferente se necessário para ajudar alguém a entender o que ele(a) quer dizer.",
        "Presta atenção a uma aula informativa de 15 minutos e compreende o que está sendo dito.",
        "Escreve frases simples com três ou mais palavras.",
        "Escreve letras do alfabeto corretamente, e não de trás para frente ou de cabeça para baixo.",
        "Quando solicitado a fazer algo um pouco mais tarde, lembra-se de fazer isso. Exemplo: “Quando seu programa acabar, coloque seus pratos na pia”.",
        "Escreve pelo menos 10 palavras de cabeça. Exemplos: Chapéu, Bola, etc.",
        "Entende o que as pessoas realmente querem dizer quando estão sendo sarcásticas. Exemplo: sabe quando “Isso é ótimo!” significa “Isso é horrível!”.",
        "Lê sentenças simples com três ou mais palavras em voz alta.",
        "Compreende a ordem alfabética. Exemplos: localiza um nome em um catálogo de endereços ou lista de números de telefone, localiza uma palavra em um dicionário.",
        "Presta atenção a uma palestra informativa de 30 minutos e compreende o que está sendo dito.",
        "Diz seu endereço completo corretamente quando você pergunta. Deve incluir cidade e estado.",
        "Quando solicitado/a a fazer algo muito mais tarde naquele dia, lembra-se de fazê-lo. Exemplo: “Quando você chegar em casa da escola, deixe o cachorro sair para passear”.",
        "Lê em um nível de segundo ano ou superior.",
        "Dá direções complexas com três ou mais etapas. Exemplos: “Vá até o final desta rua, vire à direita e siga por meio quarteirão até ver o prédio branco de dois andares”; “Primeiro, cozinhe o macarrão, despeje-o em uma tigela com o molho, e coloque migalhas de pão por cima e asse por 10 minutos”.",
        "Escreve ou desenha instruções para os outros. Exemplos: como fazer algo, como chegar a algum lugar.",
        "Usa a internet ou uma biblioteca para encontrar informações para escrever um trabalho ou concluir uma tarefa.",
        "Verifica e corrige seu trabalho escrito antes de entregá-lo. Exemplo: verifica a ortografia usando o computador.",
        "Preencher formulários de papel ou eletrônicos de uma página ou menos. Exemplo: formulários para escola ou trabalho.",
        "Lê em um nível de sexto ano ou superior.",
        "Escreve relatórios com pelo menos três páginas. Deve usar palavras próprias e não copiar.",
    ]),
    "vida_diaria": ("Atividades de Vida Diária", [
        "Usa o banheiro durante o dia. Pode precisar de ajuda como abaixar a calça, mas deve identificar quando precisa ir.",
        "Conta pelo menos 10 objetos, um por um.",
        "Compreende que o dinheiro é usado para comprar coisas. Não precisa usar dinheiro sozinho(a).",
        "Limpa o rosto e as mãos quando come algo melequento.",
        "Fica perto em locais públicos. Se carregado(a), empurrado(a) em um carrinho, etc., não conta.",
        "Coloca roupas de vestir pela cabeça. Exemplos: camiseta, camisa, vestido.",
        "Tem cuidado com coisas que poderiam queimá-lo. Exemplos: fogão, forno, fogo.",
        "Coloca a roupa com o lado correto para a frente e o lado correto para trás.",
        "Compreende as regras de segurança dos passageiros e segue-as. Exemplos: mantém o cinto de segurança afivelado, não distrai o motorista.",
        "Usa o banheiro durante o dia e à noite sem ajuda. Deve se limpar, dar descarga e lavar as mãos sozinho/a.",
        "Escova seus dentes. Deve colocar pasta de dente na escova, escovar bem e enxaguar.",
        "Coloca botões grandes nos buracos corretos. Exemplo: botões de casaco.",
        "Liga as torneiras e ajusta a temperatura da água.",
        "Tem cuidado ao usar objetos pontiagudos. Exemplos: facas, tesouras.",
        "Olha para os dois lados ao atravessar ruas ou estradas.",
        "Limpa quando derrama algo.",
        "Sabe quais são os alimentos saudáveis e não saudáveis.",
        "Sabe o que fazer em situações perigosas. Exemplos: quando obter ajuda, quando ligar para o 190, como fugir do perigo.",
        "Faz seu próprio lanche ou refeição simples. Exemplos: sanduíche, queijo e bolachas, alimentos de microondas.",
        "Liga para outras pessoas usando um telefone, computador ou outro dispositivo eletrônico.",
        "Localiza uma data em um calendário quando você pergunta. Exemplos: data de hoje, o dia de seu aniversário.",
        "Age com segurança ao trabalhar e/ou se divertir. Exemplos: usa equipamento de segurança, é cuidadoso ao operar ferramentas e maquinaria.",
        "Coloca suas roupas limpas onde elas pertencem. Exemplos: em gavetas ou armário, em cabides.",
        "Utiliza pelo menos dois utensílios de cozinha simples. Exemplos: torradeira, microondas, abridor de latas elétrico.",
        "Lava frutas e verduras antes de comê-las ou cozinhá-las.",
        "Escolhe se exercitar por saúde ou prazer.",
        "Muda de roupa conforme o clima, identifica quando usar um guarda-chuva ou casaco por exemplo.",
        "Opera tecnologia para executar pelo menos dois tipos de tarefas. Exemplos: escrever documentos escolares ou de trabalho, enviar e-mails para a escola ou o trabalho, organizar informações, encontrar informações na internet.",
        "Mantém em segurança, quando fora de casa, dinheiro, carteira, telefone, etc. Exemplos: ao fazer compras, comer fora ou durante uma viagem.",
        "Usa produtos domésticos corretamente. Exemplos: sabão em pó para roupas, polidor de móveis, limpador de vidro.",
        "Lava a louça. Pode lavar manualmente ou usar a máquina de lavar louça.",
        "Mantém a casa segura quando sai. Exemplos: tranca as portas, fecha as janelas, liga o alarme.",
        "Corta alimentos mais difíceis de cortar com uma faca afiada. Exemplos: carne, vegetais crus.",
        "Considera qualidade e preço ao decidir o que comprar.",
        "Entende o direito de relatar um problema com um produto, um serviço, sua moradia, etc.",
        "Estabelece um objetivo que pode ser feito em seis meses ou mais e o alcança. Exemplos: trabalha e economiza dinheiro para comprar algo caro, fica em melhor forma física.",
        "Usa o fogão ou forno para cozinhar ou assar. Deve ligar e desligar sozinho.",
        "Limpa o banheiro: vaso sanitário, pia, banheira ou chuveiro, etc.",
        "Mede a própria temperatura, quando necessário.",
        "Trabalhou fora de casa para ganhar dinheiro. Exemplos: trabalho de babá ou trabalho no quintal para um vizinho, ter um emprego.",
    ]),
    "socializacao": ("Habilidades Sociais e Relacionamentos", [
        "Diz como os membros da família estão relacionados a ele(a). Exemplos: “Essa é minha mãe”, “Ele é meu irmão”.",
        "Percebe quando outros estão felizes, tristes, com medo, chateados, etc.",
        "Usa palavras para expressar suas emoções. Exemplos: “Eu estou feliz”, “Eu estou com medo”, “Eu não gosto dele”.",
        "Tem um melhor amigo ou alguns bons amigos.",
        "Usa ações ou palavras para mostrar aos outros que ele(a) se sente feliz por eles, triste por eles, ou preocupado com eles. Exemplos: dá abraços, dá a mão, pergunta “Você está bem?”.",
        "Brinca com uma ou mais crianças por pelo menos 30 minutos, com alguém mais velho supervisionando.",
        "Divide seus brinquedos ou outras coisas quando alguém pede para ele(a) fazê-lo.",
        "Muda facilmente de uma atividade para outra. Exemplos: muda da hora de brincar para o banho sem ficar muito chateado.",
        "Faz bom contato visual quando interage com as pessoas.",
        "Prefere brincar com outras crianças ao invés de só observá-las ou brincar sozinha(o).",
        "Brinca de brincadeiras simples, de faz de conta, com outras crianças. Exemplos: brinca de se fantasiar, finge ser super-herói.",
        "Tenta fazer amizade com outros de sua idade. Exemplos: convida para um jogo, pede para ir em algum lugar com outra criança.",
        "Desculpa-se depois de ferir os sentimentos de alguém, e de forma genuína.",
        "Conversa com o volume, velocidade e nível de empolgação corretos para uma conversa.",
        "Imita uma criança brincando por perto, mesmo que não estejam brincando juntas. Exemplo: vê outra criança empilhando blocos e então começa a empilhar blocos.",
        "Aceita revezar quando brinca de jogos ou pratica esportes.",
        "Usa palavras ou gestos quando está chateado em vez de gritar, bater, jogar algo, etc.",
        "Está disposto a fazer concessões para se dar bem com outras pessoas da sua idade.",
        "Faz coisas para tentar agradar os outros. Exemplos: faz um cartão ou presente para alguém, oferece ajuda sem ser solicitado.",
        "Muda facilmente de um assunto para outro em uma conversa quando necessário. Não fica “preso” em um só assunto.",
        "Demonstra bom senso esportivo em jogos ou esportes: joga de maneira justa, não é excessivamente agressivo, parabeniza jogadores vencedores, não age mal quando perde, etc.",
        "Segue os limites de tempo fornecidos pelos pais, avô, etc. Exemplos: por quanto tempo pode assistir TV, jogar, usar a internet, brincar fora de casa, etc.",
        "É cauteloso(a) quando alguém que ele(a) não conhece bem tenta fazer com que ele(a) faça algo arriscado. Pode ser pessoalmente ou pela internet.",
        "Junta-se com dois ou mais indivíduos de sua idade na casa de outra pessoa.",
        "Conversa com os outros sobre coisas nas quais eles estão interessados, mesmo que ele(a) não esteja.",
        "Percebe quando alguém precisa de alguma explicação para acompanhar o que ele(a) está dizendo.",
        "Fica de fora de um grupo quando deixam transparecer, sem palavras, que ele(a) não é bem-vindo(a). Exemplo: ignorando-o/a.",
        "Engaja em jogos de tabuleiro, cartas ou jogos eletrônicos que requeiram decisões e habilidades. Exemplos: Banco Imobiliário, pôquer, damas, videogames interativos.",
        "Controla a sua raiva ou mágoa quando os planos mudam por razões que não podem ser controladas. Exemplos: não chora nem fica bravo/a quando um evento é cancelado devido ao mau tempo ou quando uma viagem é adiada devido a problemas no carro.",
        "Respeita o tempo das outras pessoas. Exemplos: não deixa os outros esperando, não interrompe os outros quando estão ocupados.",
        "Impede que os outros o/a controlem ou tirem vantagem dele(a).",
        "Faz coisas que seus amigos querem fazer, mesmo quando preferiria fazer outra coisa.",
        "Pensa nas consequências de seus atos antes de fazer alguma coisa.",
        "Entende que uma pessoa agindo amigavelmente pode estar querendo tirar vantagem dele(a).",
        "Deixa que você saiba sobre os seus planos quando vai sair. Exemplo: informa ou deixa uma mensagem sobre onde está indo e quando estará em casa.",
        "Entende que algumas coisas veiculadas à publicidade podem não ser verdadeiras.",
        "Pega dicas implícitas durante a conversa. Exemplos: sabe que alguém que boceja pode estar entediado; que as pessoas podem mudar o assunto para evitar falar sobre algo; que olhar para o relógio pode significar que a pessoa precisa terminar a conversa.",
        "Planeja ou toma a iniciativa de fazer coisas com outros da mesma idade sozinho(a). Exemplos: planeja um jantar com um amigo, planeja ir ao cinema com amigos(as) no final de semana.",
        "Obtém informações de programação para filmes, eventos esportivos, shows, etc. Exemplos: olha no jornal ou na internet, telefona a um estabelecimento para obter informações.",
        "Vai a lugares com outros indivíduos de sua idade durante o dia sem alguém supervisionando. Exemplos: shopping, parque, centro comunitário.",
    ]),
    "atividade_fisica": ("Atividade Física — opcional", [
        "Desembrulha pequenos objetos. Exemplos: pedaço de doce ou chiclete.",
        "Desce escadas, colocando um pé em cada degrau. Pode usar corrimão.",
        "Sobe um conjunto de oito ou mais degraus em um ritmo normal. Pode usar corrimão.",
        "Corre sem dificuldade, mudando sua velocidade e direção. Exemplos: brincar de pega-pega ou praticar esportes, perseguir um animal de estimação.",
        "Salta para a frente pelo menos três vezes com os dois pés sem cair.",
        "Segura um giz de cera, caneta ou lápis corretamente para escrever ou desenhar. Não segura com preensão palmar.",
        "Anda duas quadras ou mais sem precisar de ajuda ou descansar.",
        "Desenha um círculo à mão enquanto olha um modelo.",
        "Pedala um triciclo ou outro veículo com três rodas por pelo menos 2 metros.",
        "Pega uma bola do tamanho de uma bola de praia a uma distância de 2 metros. Pode usar uma ou duas mãos.",
        "Pula com um pé só com facilidade, sem cair.",
        "Pinta formas simples ou animais. Deve pintar mais dentro do que fora da linha.",
        "Pedala uma bicicleta com rodinha ou bicicleta de equilíbrio por pelo menos 3 metros.",
        "Desenha mais de uma forma que você consegue reconhecer. Exemplos: pessoa, casa, árvore.",
        "Transfere líquido de um recipiente para outro com pouco ou nenhum derramamento. Exemplo: coloca leite ou suco em um copo.",
        "Pega uma bola do tamanho de uma bola de tênis ou beisebol a uma distância de 0,5 a 1 metro. Pode usar uma ou ambas as mãos, mas deve pegar longe do corpo em vez de agarrar a bola junto ao corpo.",
        "Recorta formas simples. Exemplos: círculos, quadrados, retângulos.",
        "Faz construções complexas usando brinquedos de montar, materiais de arte e artesanato, etc.",
        "Desenha uma linha reta com uma régua.",
        "Pega uma bola do tamanho de uma bola de tênis ou beisebol a uma distância de 3 metros, movendo-se para pegá-la se necessário. Pode usar uma ou ambas as mãos.",
        "Amarra um nó.",
        "Recorta formas complexas. Exemplos: estrelas, animais, letras do alfabeto.",
        "Trabalha com objetos bem pequenos. Exemplos: ajusta um relógio com as mãos, coloca a linha em uma agulha, cola pequenas peças.",
        "Pedala uma bicicleta regular, sem rodinhas, sem cair.",
        "Faz um laço apertado. Exemplos: cadarço de sapato, embalagem de presente.",
    ]),
    "comportamento_a": ("Problemas de Comportamento — Seção A (opcional)", [
        "É excessivamente carente ou dependente. Exemplos: insiste em ajudar, mesmo quando não é necessário; é excessivamente apegado aos membros da família, cuidador ou professor.",
        "Tem problemas alimentares. Exemplos: come em excesso, se recusa a comer, come apenas uma ou duas coisas, acumula comida.",
        "Tem problemas de sono. Exemplos: anda enquanto dorme, tem longos pesadelos, dorme mais ou menos que as crianças de sua idade.",
        "Recusa-se a ir à escola ou ao trabalho ou precisa voltar para casa por causa de preocupações, tristeza, nervosismo, etc.",
        "É extremamente ansioso(a) ou nervoso(a).",
        "Chora ou fica triste por motivos não aparentes.",
        "Evita interagir com os outros (se retira do ambiente, prefere ficar sozinho(a), etc.).",
        "Falta interesse para fazer as coisas que ele(a) gosta ou costumava gostar.",
        "Tem medo excessivo de um ou mais objetos ou situações comuns. Exemplos: altura, cobras, elevador.",
        "Preocupa-se demasiadamente por nenhuma razão clara.",
        "É muito irritável ou mal-humorado(a).",
        "Sente-se desamparado(a) ou sem esperança. Exemplo: diz que as coisas estão ruins e nunca melhoram.",
        "Reclama de estar se sentindo doente, exausto ou com dor, mesmo que não haja motivo médico.",
    ]),
    "comportamento_b": ("Problemas de Comportamento — Seção B (opcional)", [
        "Faz birras: grita, chora, chuta, etc.",
        "Desobedece à figura de autoridade.",
        "Faz bullying com outros psicologicamente ou fisicamente.",
        "Mente, trapaceia ou rouba.",
        "É fisicamente agressivo(a). Exemplos: bate, chuta, morde.",
        "É teimoso(a) ou discute excessivamente.",
        "É abusivo verbalmente. Exemplos: machuca outros de propósito com insultos, humilhações, etc.",
        "Quebra regras ou leis por pressão dos colegas.",
        "É muito mais ativo ou inquieto do que outros da sua idade. Exemplos: se movimenta o tempo todo, não consegue ficar sentado, está sempre inquieto.",
        "Pega ou usa pertences escolares quando não é permitido. Exemplos: livros, materiais de escritório.",
        "Destrói itens pessoais ou de outras pessoas de propósito.",
    ]),
    "comportamento_c": ("Problemas de Comportamento — Seção C / Itens críticos (opcional)", [
        "Fixa-se em um único objeto ou parte deles. Exemplos: foca as rodinhas girando ou as pás do ventilador, alinha objetos, liga e desliga a luz repetidamente.",
        "Fala sobre ouvir vozes que outros não ouvem ou sobre ver coisas que outros não veem.",
        "Se machuca. Exemplos: bate a cabeça, se bate ou se morde, se corta, se arranha, arranca o cabelo.",
        "Apresenta fala estranha ou repetitiva. Exemplos: fala sozinho(a) em público, fala coisas que não fazem sentido, repete a mesma coisa várias vezes seguidas.",
        "Apresenta movimentos físicos repetitivos. Exemplos: balançar para frente e para trás, girar em torno do próprio eixo, abanar as mãos.",
        "Come itens que não são comidas, como sujeira, pasta ou sabão.",
        "Fica tão fixado em um único assunto que chega a irritar os outros. Exemplos: trens, mapas, sistema de metrô.",
        "Fala sobre se matar ou tentou se matar.",
        "Perambula para longe de um grupo da escola ou sai da escola sem se preocupar com sua segurança.",
        "Ameaça machucar ou matar outra pessoa.",
        "É influenciado/a por outros a fazer algo que poderia prejudicar seriamente a si mesmo ou à outra pessoa.",
    ]),
}

BINARY_ITEMS = {"comunicacao": {26, 33, 39}, "vida_diaria": {40}, "socializacao": {4}}
PAGES = {"comunicacao": [4, 5], "vida_diaria": [6, 7], "socializacao": [8, 9],
         "atividade_fisica": [10], "comportamento_a": [11], "comportamento_b": [11], "comportamento_c": [12]}
HINTS = {
    ("comunicacao", 19): "Pontue 2 se ele fez isso quando era mais novo, mas agora já adquiriu a habilidade.",
    ("comunicacao", 40): "Pontue 2 se ele/ela fez isso quando mais jovem, mas agora não precisa escrever artigos.",
    ("vida_diaria", 5): "Marque 2 se ele fez isso quando era mais novo.",
    ("socializacao", 6): "Pontue 2 se ele(a) fez isso quando mais jovem, e agora não precisa de supervisão.",
    ("socializacao", 11): "Pontue 2 se ele(a) fez isso quando mais jovem, e agora não brinca mais de faz de conta.",
    ("socializacao", 15): "Pontue 2 se ele(a) fez isso quando mais jovem, não brinca mais de empilhar.",
    ("socializacao", 22): "Pontue 2 se ele(a) fez isso quando mais jovem.",
    ("socializacao", 23): "Se você não sabe, estime uma pontuação. Marque também a Caixa de Estimativa.",
    ("socializacao", 32): "Se você não souber, estime sua pontuação. Marque também a Caixa de Estimativa.",
    ("atividade_fisica", 9): "Pontue 2 se ele(a) fez isso quando mais jovem, e agora já adquiriu a habilidade.",
    ("atividade_fisica", 12): "Pontue 2 se ele(a) fez isso quando mais jovem, e agora não pinta mais.",
    ("atividade_fisica", 13): "Pontue 2 se ele(a) fez isso quando mais jovem, e agora já adquiriu a habilidade.",
}


def item_protocol():
    return {
        "id": PROTOCOL_ID, "source": SOURCE, "pdf_source": PDF_SOURCE,
        "title": "Vineland-3 — Pais/Cuidadores dos Níveis de Domínio",
        "description": "Avalie o comportamento que a pessoa realiza sozinha, sem ajuda ou lembretes. Registre as informações do pai/cuidador. Responda todos os itens das seções aplicadas; não há basal ou teto.",
        "legend": {"2": "Usualmente ou frequentemente", "1": "Às vezes", "0": "Nunca"},
        "edition_verified": True, "complete": True, "scoring_enabled": False,
        "supports_estimates": True, "item_observations": True,
        "warning": "Cadastro de 180 itens para preenchimento profissional. Conferir os critérios das páginas 2 e 15 do formulário antes do uso clínico. Correção normativa, interpretação e inclusão no laudo ainda não habilitadas. Seções opcionais podem permanecer vazias; não preencher zeros fictícios.",
        "domains": [{
            "code": code, "label": label, "pages": PAGES[code],
            "behavior_problems": code.startswith("comportamento_"),
            "items": [{"id": str(index), "text": text, "hint": HINTS.get((code, index), ""),
                       "allowed_responses": ["2", "0"] if index in BINARY_ITEMS.get(code, set()) else ["2", "1", "0"]}
                      for index, text in enumerate(items, 1)],
        } for code, (label, items) in DOMAIN_ITEMS.items()],
    }


def normalize_item_responses(responses):
    """Validate a draft, preserving blanks, estimates and per-item notes."""
    if not isinstance(responses, dict):
        raise ValueError("Informe respostas por domínio e item.")
    normalized = {}
    for domain, items in responses.items():
        if domain not in DOMAIN_ITEMS or not isinstance(items, dict):
            raise ValueError(f"Domínio inválido: {domain}.")
        allowed_ids = {str(i) for i in range(1, len(DOMAIN_ITEMS[domain][1]) + 1)}
        normalized[domain] = {}
        for item_id, entry in items.items():
            if item_id not in allowed_ids or not isinstance(entry, dict) or entry.keys() - {"response", "observation", "estimated"}:
                raise ValueError(f"Item inválido: {domain}/{item_id}.")
            response = entry.get("response", "")
            observation = entry.get("observation", "")
            estimated = entry.get("estimated", False)
            allowed = {"", "2", "0"} if int(item_id) in BINARY_ITEMS.get(domain, set()) else {"", "2", "1", "0"}
            if not isinstance(response, str) or response not in allowed:
                raise ValueError(f"{domain}/{item_id}: resposta inválida; use {'0 ou 2' if '1' not in allowed else '0, 1 ou 2'}.")
            if type(estimated) is not bool or (estimated and response == ""):
                raise ValueError(f"{domain}/{item_id}: Est. exige uma resposta numérica e uma marcação booleana.")
            if not isinstance(observation, str) or len(observation) > 2000:
                raise ValueError(f"{domain}/{item_id}: observação deve ter até 2000 caracteres.")
            normalized[domain][item_id] = {"response": response, "observation": observation, "estimated": estimated}
    return normalized


def build_item_summary(responses):
    """Finalize this form with descriptive sums only, never normative scores."""
    responses = normalize_item_responses(responses)
    sections = []
    critical_items = []
    for code, (label, items) in DOMAIN_ITEMS.items():
        entries = responses.get(code, {})
        answered = {item_id: entry for item_id, entry in entries.items() if entry["response"] != ""}
        applied = code in {"comunicacao", "vida_diaria", "socializacao"} or bool(answered)
        missing = [str(index) for index in range(1, len(items) + 1) if str(index) not in answered]
        if applied and missing:
            raise ValueError(f"{label}: faltam respostas nos itens {', '.join(missing)}. Salve parcialmente para continuar depois.")
        critical = code == "comportamento_c"
        sections.append({
            "code": code, "label": label, "applied": applied,
            "kind": "critical" if critical else "behavior" if code.startswith("comportamento_") else "adaptive",
            "answered": len(answered), "total": len(items),
            "raw_score": sum(int(entry["response"]) for entry in answered.values()) if applied and not critical else None,
            "max_score": len(items) * 2 if not critical else None,
            "response_counts": {value: sum(entry["response"] == value for entry in answered.values()) for value in ("0", "1", "2")},
        })
        if critical:
            critical_items = [{"id": item_id, "text": items[int(item_id) - 1], "response": entry["response"]}
                              for item_id, entry in answered.items() if entry["response"] in {"1", "2"}]
            critical_items.sort(key=lambda item: int(item["id"]))
    return {"protocol_id": PROTOCOL_ID, "normative_scoring": False,
            "sections": sections, "critical_items": critical_items,
            "answered": sum(section["answered"] for section in sections),
            "applied_total": sum(section["total"] for section in sections if section["applied"])}
