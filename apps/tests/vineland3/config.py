CODE = "vineland3"
NAME = "Vineland-3 — Escalas de Comportamento Adaptativo"
FORMS = {
    "entrevista": "Entrevista extensiva",
    "pais_cuidadores": "Pais/Cuidadores extensivo",
    "professores": "Professores extensivo",
}
SUBDOMAINS = {
    "rec": "Receptiva", "exp": "Expressiva", "esc": "Escrita", "pes": "Pessoal",
    "dom": "Doméstico", "com": "Comunidade", "num": "Numérico",
    "cme": "Comunidade Escolar", "rin": "Relacionamentos Interpessoais",
    "bri": "Brincar e Lazer", "enf": "Habilidades de Enfrentamento",
    "cmg": "Coordenação Motora Grossa", "cmf": "Coordenação Motora Fina",
}
DOMAINS = {
    "COM": "Comunicação", "AVD": "Atividades da Vida Diária", "SOC": "Socialização",
    "ABC": "Composto de Comportamento Adaptativo", "HMOT": "Habilidades Motoras",
}
TECHNICAL_NOTES = [
    "Normas americanas dos apêndices B, C e D do manual Vineland-3, edição em português (2019).",
    "Entrada por pontuações brutas do protocolo, já corrigidas pelo profissional responsável.",
    "Nos totais extensivos, classificação qualitativa, intervalos de confiança, equivalentes etários e comportamento mal adaptado ainda não estão habilitados neste fluxo.",
    "Registros antigos preservam o banco parcial de edição não confirmada e seus códigos N/D, sem cálculo normativo ou laudo; não são migrados para o novo formulário.",
    "Níveis de Domínio: Entrevista, Pais/Cuidadores e Professores por totais brutos de domínio, com IC95%, classificações e revisão profissional explícita; não misturar com brutos de subdomínios extensivos.",
    "Questionário de 180 itens disponível somente para Pais/Cuidadores — Níveis de Domínio; 0/1/2, sem basal/teto; finalização calcula resultados, mas não valida automaticamente.",
    "Resultados quantitativos exigem revisão clínica e não constituem diagnóstico isolado.",
]
