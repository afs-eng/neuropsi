"""Orientação de referências do FDT, sem alterar cálculo ou validação clínica."""

import re


FDT_SPECIALIST_VERSION = "pydantic-fdt-2"
# Só muda o grounding das novas gerações; sucessos anteriores continuam revisáveis.
FDT_COMPATIBLE_REVIEW_VERSIONS = {"pydantic-specialist-1", "pydantic-specialist-1-ollama-4k"}
FDT_CODES = ("leitura", "contagem", "escolha", "alternancia", "inibicao", "flexibilidade")

FDT_INSTRUCTIONS = """
FDT: distinga leitura/contagem, escolha/alternância e índices derivados de
inibição/flexibilidade; diferencie tempos de erros. Não declare funcionamento
executivo global preservado se houver fragilidades nos indicadores apresentados.
Use apenas os índices já calculados; não refaça cálculos ou conversões normativas.

facts é um mapa cujas CHAVES são os únicos evidence_ids válidos. Copie as chaves
completas, incluindo / inicial, computed_payload ou classified_payload e índices
numéricos. Exemplo de estrutura, não resultado: /computed_payload/metric_results/0/valor.
Use esse ID somente se ele realmente existir em facts e corresponder ao dado citado.
metric_results é uma lista: encontre a linha pelo campo codigo recebido. Não troque
o índice numérico pelo nome da etapa e não suponha que a ordem seja fixa.
reading_guide é somente um mapa de referências; os IDs são os VALORES desse mapa,
nunca caminhos começando por /reading_guide. stage_totals descreve tempos/erros das
etapas; metric_results contém valores/classificações e derived_scores os índices
derivados. Não cite /leitura/tempo, facts.leitura, nomes de etapas ou números como IDs.
Distinga classificações de tempo e de erros. Dados ausentes não têm ID e não devem
ser inventados. Preserve o contrato findings/limitations/review_questions e cite
os fatos de cada achado. Não transforme uma referência inválida em resultado válido.
"""


def fdt_reading_guide(facts: dict) -> dict:
    """Mapeia somente caminhos existentes; não cria ou renomeia os fatos."""
    metrics = {}
    for code in FDT_CODES:
        refs: dict[str, list[str]] = {}
        for source in ("computed_payload", "classified_payload"):
            rows = [key.rsplit("/", 1)[0] for key, value in facts.items()
                    if re.fullmatch(rf"/{source}/metric_results/\d+/codigo", key) and value == code]
            for field in ("valor", "classificacao", "percentil_num", "percentil_texto"):
                ids = [f"{row}/{field}" for row in rows if f"{row}/{field}" in facts]
                if ids:
                    refs.setdefault(field, []).extend(ids)
            for label, path in (
                ("tempo_etapa", f"/{source}/stage_totals/{code}/tempo"),
                ("erros_etapa", f"/{source}/stage_totals/{code}/erros"),
                ("indice_derivado", f"/{source}/derived_scores/{code}"),
                ("qtde_erros", f"/{source}/erros/{code}/qtde_erros"),
                ("classificacao_erros", f"/{source}/erros/{code}/classificacao_guilmette"),
            ):
                if path in facts:
                    refs.setdefault(label, []).append(path)
        if refs:
            metrics[code] = refs
    return {"metric_evidence_ids": metrics}
