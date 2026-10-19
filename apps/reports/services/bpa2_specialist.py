import json
import re

from .specialist_errors import SpecialistValidationError


BPA2_VERSION = "pydantic-bpa2-5"
# Mudança de grounding, sem mudar regras clínicas: rascunhos já válidos continuam revisáveis.
BPA2_COMPATIBLE_REVIEW_VERSIONS = {
    "pydantic-bpa2-3", "pydantic-bpa2-3-ollama-4k",
    "pydantic-bpa2-4", "pydantic-bpa2-4-ollama-4k",
}
BPA2_SECTIONS = ("introducao", "ac", "ad", "aa", "ag", "analise_clinica")

BPA2_INSTRUCTIONS = """
BPA-2 — modelo de redação por componentes, versão 5.
Siga a organização abaixo, não uma conclusão fixa. Redija em português técnico,
com parágrafos coesos e proporcionais aos resultados, sem listas de números soltos.
Retorne exatamente seis findings, nesta ordem, usando o campo section:
introducao, ac, ad, aa, ag, analise_clinica. Os títulos são montados pela interface.
Cada statement deve ser um parágrafo breve (aproximadamente 40–65 palavras nos
componentes; introdução e síntese podem ser menores). Não numere os parágrafos.

Introdução: apresente a Bateria Psicológica para Avaliação da Atenção – Segunda
Edição (BPA-2), o escopo desta aplicação e os componentes avaliados. Não use nomes.
Não é necessário repetir a idade; se a informar, use apenas a idade fornecida.
AC: descreva brevemente a seleção de estímulos relevantes diante de distratores;
informe escore em pontos, percentil e classificação quando fornecidos, depois
interprete o desempenho restrito a essa tarefa e ao grupo normativo informado.
AD: descreva a distribuição da atenção entre estímulos simultâneos e aplique a
mesma organização (escore, percentil, classificação, interpretação contextualizada).
AA: descreva alternância do foco entre estímulos/critérios; não conclua sobre toda
a flexibilidade executiva com base nessa modalidade.
AG: apresente a medida agregada de AC, AD e AA, NÃO um subteste independente.
Análise clínica: integre o perfil desta bateria, preservando eventuais fragilidades.
Não repita simplesmente os quatro parágrafos. Diferencie comparação normativa e
posição relativa entre modalidades; não atribua significância estatística a
diferenças sem uma análise de significância fornecida. Não converta percentis
em percentuais de acertos. Não generalize o teste para a vida cotidiana.

Use reading_guide para localizar os fatos. Campos total são ESCORES CALCULADOS,
não quantidade de itens apresentados, tentativas ou acertos. AG é agregado.
Não liste erros e omissões como foco da interpretação. Zero erros/omissões não
significa, isoladamente, atenção preservada. Não recalcule escores nem normas.
Copie a classificação fornecida, sem reclassificar. Cite em evidence_ids os
identificadores de TODOS os escores/percentis/classificações usados em cada
componente. Se um desses dados estiver ausente, informe a lacuna, sem inventá-lo.
Cada evidence_id deve ser uma chave EXATA do objeto facts, incluindo a barra
inicial e o índice numérico do resultado classificado. reading_guide é somente
um mapa: copie os IDs indicados nos seus valores, não o caminho do próprio mapa.
Não use 'ac', 'percentil', valores numéricos, notação com pontos, nem caminhos
abreviados como IDs. Não acrescente /facts ao início das chaves.
Para escores, são aceitos os IDs calculado ou classificado equivalentes indicados
em score_evidence_alternatives; basta citar um deles. Prefira a forma explícita
'X pontos, percentil Y, classificação Z', sem trocar os valores entre si.
Use section_evidence_requirements como checklist mínimo de cada seção:
inclua TODOS os required_ids e pelo menos UM ID de score_one_of quando a lista
não estiver vazia. Referências de outra modalidade não substituem essas listas.
Na síntese (analise_clinica), integre as QUATRO modalidades (AC, AD, AA e AG) e
cite TODOS os percentis/classificações disponíveis listados para essa seção,
mesmo quando não repetir números na redação. Citar apenas AC ou AG não basta.
Não use classificações automáticas de pontos fortes como conclusão
absoluta: destaque relativo não é desempenho superior à média normativa.

Exemplos SINTÉTICOS de estilo e raciocínio, nunca fatos deste paciente:
- Perfil AC 75/P40/Média, AD 79/P60/Média, AA 88/P50/Média, AG 242/P50/Média:
  'Os resultados situam-se na faixa Média nas medidas apresentadas. AD ocupa a
  maior posição percentílica entre as modalidades, como destaque relativo, sem
  classificação superior à média normativa. Os achados descrevem o desempenho
  nas tarefas e não excluem dificuldades no cotidiano.'
- Perfil AC 62/P10/Inferior, AD 85/P60/Média, AA 86/P40/Média, AG 233/P30/Média Inferior:
  'Há classificação Inferior em AC, enquanto AD e AA estão na faixa Média. AG
  está em Média Inferior. AD destaca-se relativamente neste perfil; esse resultado
  não elimina a fragilidade observada em AC nem estabelece diagnóstico.'
Não copie os números ou conclusões desses exemplos para outras aplicações.

Evite certezas como 'capacidade preservada', 'sem comprometimento' ou 'ausência
de prejuízo global'. Prefira 'desempenho dentro dos parâmetros normativos nessa
tarefa' quando sustentado pela classificação. Resultados baixos devem ser
descritos sem diagnóstico ou causalidade. Não cite WAIS, WISC, memória operacional,
velocidade de processamento, história clínica ou observações não fornecidas:
integração entre instrumentos pertence a outra etapa, não a este especialista.
Inclua limitations sobre escopo do instrumento, ausência de integração com
anamnese/observações e revisão profissional. Evite metacomentários como 'conforme
diretrizes do payload'. A saída é rascunho, não laudo final ou diagnóstico.
"""


def bpa2_reading_guide(facts: dict) -> dict:
    """Mapeia fatos existentes; não recalcula nem cria escores/normas."""
    components = {}
    score_alternatives = {}
    for code in ("ac", "ad", "aa", "ag"):
        rows = [key.rsplit("/", 1)[0] for key, value in facts.items()
                if re.fullmatch(r"/classified_payload/subtestes/\d+/codigo", key) and value == code]
        if len(rows) > 1:
            raise ValueError("BPA-2 com modalidade duplicada nos resultados classificados.")
        row = rows[0] if rows else ""
        refs = {}
        computed_score = f"/computed_payload/{code}/total"
        classified_score = f"{row}/total"
        if computed_score in facts and classified_score in facts and facts[computed_score] != facts[classified_score]:
            raise ValueError("BPA-2 com escore calculado e classificado divergentes.")
        for label, candidates in {
            "escore_pontos": (computed_score, classified_score),
            "percentil": (f"{row}/percentil",),
            "classificacao": (f"{row}/classificacao",),
        }.items():
            refs[label] = next((key for key in candidates if key in facts), None)
        components[code] = refs
        score_alternatives[code] = [key for key in (computed_score, classified_score) if key in facts]
    requirements = {"introducao": {"required_ids": [], "score_one_of": []}}
    synthesis_ids = []
    for code, refs in components.items():
        required_ids = [refs[label] for label in ("percentil", "classificacao") if refs[label] is not None]
        requirements[code] = {"required_ids": required_ids, "score_one_of": score_alternatives[code]}
        synthesis_ids.extend(required_ids)
    requirements["analise_clinica"] = {"required_ids": synthesis_ids, "score_one_of": []}
    return {
        "total_significa": "escore calculado em pontos; não é quantidade de itens",
        "ag_significa": "medida agregada de AC, AD e AA; não é subteste independente",
        "component_evidence_ids": components,
        "score_evidence_alternatives": score_alternatives,
        "section_evidence_requirements": requirements,
    }


def bpa2_evidence_gaps(output, facts: dict) -> dict:
    """Reporta ausências; nunca altera a saída nem cria citações."""
    requirements = bpa2_reading_guide(facts)["section_evidence_requirements"]
    gaps = {}
    for finding in output.findings:
        required = requirements[finding.section]
        missing = [key for key in required["required_ids"] if key not in finding.evidence_ids]
        score_ids = required["score_one_of"]
        missing_score = score_ids if score_ids and not set(score_ids).intersection(finding.evidence_ids) else []
        if missing or missing_score:
            gaps[finding.section] = {"missing_required_ids": missing, "missing_score_one_of": missing_score}
    return gaps


def validate_bpa2_findings(output, facts: dict) -> None:
    reading_guide = bpa2_reading_guide(facts)
    guide = reading_guide["component_evidence_ids"]
    gaps = bpa2_evidence_gaps(output, facts)
    if gaps:
        raise SpecialistValidationError(
            "bpa2_missing_evidence",
            "BPA-2: faltam evidências específicas. Corrija TODAS as seções indicadas; "
            "inclua missing_required_ids e pelo menos um missing_score_one_of quando não vazio. "
            "Releia os fatos para sustentar o texto, sem inventar dados. Ausências por seção: "
            + json.dumps(gaps, ensure_ascii=False),
            section=next(iter(gaps)),
        )
    for finding in output.findings:
        statement = finding.statement.casefold()
        if re.search(r"\b\d+\s+itens\b|\bsubteste\s+(?:de\s+)?atenção geral\b|\b(?:wais|wisc)\b", statement):
            raise SpecialistValidationError("bpa2_semantics", "BPA-2: redação confunde escore/AG ou inclui outro instrumento.", section=finding.section)
        codes = (finding.section,) if finding.section in guide else (
            ("ac", "ad", "aa", "ag") if finding.section == "analise_clinica" else ()
        )
        for code in codes:
            refs = guide[code]
            if finding.section in guide:
                for label in ("escore_pontos", "percentil", "classificacao"):
                    key = refs[label]
                    if key is None:
                        continue
                    value = re.escape(str(facts[key]).casefold())
                    if label == "escore_pontos":
                        pattern = rf"(?<![\d.,]){value}\s+pontos\b"
                    elif label == "percentil":
                        pattern = rf"\bpercentil\s+(?:de\s+)?{value}(?!\d|[.,]\d)"
                    else:
                        pattern = rf"(?<!\w){value}(?!\w|\s+(?:inferior|superior)\b)"
                    if not re.search(pattern, statement):
                        raise SpecialistValidationError("bpa2_score_text", "BPA-2: componente não apresenta escore em pontos, percentil ou classificação fornecidos.", section=finding.section)
