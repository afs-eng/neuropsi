"""BFP e E-TDAH-AD: contratos de leitura, não motores normativos."""

import math
import re
import unicodedata

from .specialist_errors import SpecialistValidationError


SELF_REPORT_VERSIONS = {"bfp": "pydantic-bfp-1", "etdah_ad": "pydantic-etdah-ad-1"}
BFP_FACTORS = {
    "NN": "Neuroticismo", "EE": "Extroversão", "SS": "Socialização",
    "RR": "Realização", "AA": "Abertura",
}
BFP_FACETS = {
    "N1": "Vulnerabilidade", "N2": "Instabilidade Emocional",
    "N3": "Passividade/Falta de Energia", "N4": "Depressão",
    "E1": "Comunicação", "E2": "Altivez", "E3": "Dinamismo", "E4": "Interações Sociais",
    "S1": "Amabilidade", "S2": "Pró-Sociabilidade", "S3": "Confiança",
    "R1": "Competência", "R2": "Ponderação", "R3": "Empenho",
    "A1": "Abertura a Ideias", "A2": "Liberalismo", "A3": "Busca por Novidades",
}
ETDAH_FACTORS = {
    "D": "Desatenção", "I": "Impulsividade", "AE": "Aspectos Emocionais",
    "AAMA": "Autorregulação da Atenção, Motivação e Ação", "H": "Hiperatividade",
    "escore_geral": "Escore Geral",
}
RESULT_FIELDS = {"raw_score", "weighted_score", "z_score", "percentile", "percentile_text", "classification"}
CLASSIFICATIONS = (
    "Muito Superior", "Muito Baixo", "Média Superior", "Média Inferior",
    "Médio Superior", "Médio Inferior", "Superior", "Inferior", "Baixo", "Média", "Médio",
)
DIAGNOSIS_ASSERTION = (
    r"\b(?:confirma|comprova|estabelece|determina|fecha|possui|apresenta|tem)\s+"
    r"(?:(?:o|um)\s+)?(?:diagnostico\b|tdah\b|transtorno\b)"
)
DIRECTION_ASSERTION = (
    r"\b(?:indica|sugere|demonstra|reflete|representa)\s+(?:maior|menor)\s+"
    r"(?:frequencia|intensidade|gravidade)|\b(?:melhor|pior)\s+(?:desempenho|funcionamento)"
    r"|\bsintomas\s+(?:elevados|reduzidos)"
)

SELF_REPORT_INSTRUCTIONS = """
Siga o guia reading_guide, que aponta para IDs exatos de facts desta aplicação.
Retorne de dois a cinco findings, cada um com um parágrafo técnico em statement,
scale_codes com os códigos das dimensões abordadas e evidence_ids com os fatos
dessas mesmas dimensões. Agrupe dimensões relacionadas, sem omitir as disponíveis.
Cada dimensão disponível precisa aparecer em scale_codes de pelo menos um achado.
Em cada achado, cite ao menos um classification_id por dimensão classificada e
apresente a classificação exata recebida, sem reclassificar. Se a classificação
estiver ausente, cite o escore disponível e descreva somente o dado, sem inferência
normativa. Não cite uma dimensão ausente nem complete lacunas com zero ou 'normal'.
Os códigos scale_codes são metadados; na prosa use nomes das dimensões, não códigos.
Não escreva percentis, centis, percentuais ou notação P seguida de número em NENHUM
campo textual da resposta. Os percentis ficam nos dados estruturados e evidências.
Prefira narrativa qualitativa; não enumere escores. Se um escore for indispensável,
cite o ID de escore correspondente, nunca use o percentil como escore.
Não copie interpretações antigas. Não use nomes, itens de teste, referências
bibliográficas não fornecidas ou fatos de outra aplicação. Não faça diagnóstico,
atribua CID, recomende tratamento ou declare causalidade, significância estatística
ou funcionamento global. Dados de autorrelato não são observação nem teste objetivo.
Registre limites em limitations; registre lacunas em review_questions (pendências
para a profissional, não resultados normais). Se missing_data não estiver vazio,
review_questions deve conter ao menos uma pergunta de conferência dos dados.
Ausência de versão/manual, referência normativa, validade ou contexto não autoriza
inferência: explicite essas limitações. Esta etapa não recebe anamnese/observações;
solicite sua integração posterior, sem inventar conteúdo. Exige revisão profissional.
O contrato JSON seguro usa findings, limitations e review_questions; não retorne
o JSON ilustrativo da skill nem acrescente campos de diagnóstico.
"""

BFP_INSTRUCTIONS = """
BFP — Bateria Fatorial de Personalidade. Instruções adaptadas da skill gopsi-bfp.
Descreva os cinco fatores e as facetas disponíveis como traços dimensionais de
personalidade, contextualizando diferenças entre fator e facetas sem atribuir
significância estatística. Agrupe facetas com seus fatores em até cinco parágrafos.
Não patologize extremos, não conclua transtornos de personalidade nem considere
a faceta Depressão um diagnóstico depressivo. Altivez não prova autoestima baixa;
Realização não é inteligência; Pró-Sociabilidade não autoriza juízo moral, conduta
antissocial ou desonestidade; Liberalismo não indica posição política ou religiosa.
Não afirme validade da aplicação, estabilidade temporal ou prejuízo cotidiano sem
dados específicos. Amostra normativa recebida não equivale a manual homologado.
""" + SELF_REPORT_INSTRUCTIONS

ETDAH_AD_INSTRUCTIONS = """
E-TDAH-AD — escala de autorrelato. Instruções adaptadas da skill gopsi-etdah-ad.
Descreva separadamente os fatores Desatenção, Impulsividade, Aspectos Emocionais,
Autorregulação da Atenção, Motivação e Ação e Hiperatividade; escore geral é agregado,
não um fator independente nem apresentação diagnóstica. Não confunda E-TDAH-PAIS.
Classificação normativa Superior NÃO significa desempenho melhor. Não suponha
também que toda elevação representa pior funcionamento: o payload atual não fornece
direção clínica validada por fator/manual. Limite-se à classificação e ao construto;
não converta faixas em frequência, intensidade de sintomas ou prejuízo funcional.
Registre a falta de direção clínica como pendência antes de inferir significado.
Início, persistência, contextos e prejuízo devem ser investigados na integração
clínica posterior; não afirme esses elementos como presentes. A escala isolada
não estabelece nem exclui TDAH ou comorbidades. Nunca misture outras aplicações.
""" + SELF_REPORT_INSTRUCTIONS


def _normalized(text: str) -> str:
    return " ".join("".join(
        char for char in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(char)
    ).split()).replace("medio", "media")


def _affirmative(text: str, pattern: str) -> bool:
    for match in re.finditer(pattern, text):
        if not re.search(r"\b(?:nao|nem|sem)\s*$", text[:match.start()]):
            return True
    return False


def self_report_sources(code: str, computed: dict, classified: dict) -> tuple[dict, dict]:
    """Allowlist local: não encaminhar respostas, chaves de correção ou prosa antiga."""
    if code not in SELF_REPORT_VERSIONS:
        raise ValueError("Especialista de autorrelato desconhecido.")
    if not isinstance(computed, dict) or not isinstance(classified, dict):
        raise ValueError("Formato dos resultados do especialista inválido.")

    def scales(source, key, known):
        rows = source.get(key, {})
        if not isinstance(rows, dict):
            raise ValueError("Formato das dimensões do especialista inválido.")
        if set(rows) - set(known):
            raise ValueError("Dimensão desconhecida nos resultados do especialista.")
        result = {}
        for scale, row in rows.items():
            if not isinstance(row, dict):
                raise ValueError("Formato de resultado dimensional inválido.")
            result[scale] = {field: value for field, value in row.items() if field in RESULT_FIELDS}
            if any(isinstance(value, (dict, list)) for value in result[scale].values()):
                raise ValueError("Valor dimensional inválido.")
        return result

    if code == "bfp":
        clean_computed = {
            "factors": scales(computed, "factors", BFP_FACTORS),
            "facets": scales(computed, "facets", BFP_FACETS),
        }
        clean_classified = {}
        for key, known in (("factor_classifications", BFP_FACTORS), ("facet_classifications", BFP_FACETS)):
            values = classified.get(key, {})
            if not isinstance(values, dict) or set(values) - set(known):
                raise ValueError("Classificações dimensionais inválidas.")
            if any(value is not None and not isinstance(value, str) for value in values.values()):
                raise ValueError("Valor de classificação inválido.")
            clean_classified[key] = values
        for source, target in ((computed, clean_computed), (classified, clean_classified)):
            for key in ("sample", "sample_label"):
                if key in source:
                    target[key] = source[key]
    else:
        clean_computed, clean_classified = {}, {"results": scales(classified, "results", ETDAH_FACTORS)}
        for source, target in ((computed, clean_computed), (classified, clean_classified)):
            values = source.get("raw_scores", {})
            if not isinstance(values, dict) or set(values) - set(ETDAH_FACTORS):
                raise ValueError("Escores dimensionais inválidos.")
            target["raw_scores"] = values
            if "schooling" in source:
                target["schooling"] = source["schooling"]
    return clean_computed, clean_classified


def self_report_reading_guide(code: str, facts: dict) -> dict:
    if code not in SELF_REPORT_VERSIONS:
        raise ValueError("Especialista de autorrelato desconhecido.")
    dimensions = {}
    missing = ["version_and_manual", "application_validity", "clinical_context"]
    if "/application/age_months" not in facts:
        missing.append("age")
    if code == "bfp":
        known = {**BFP_FACTORS, **BFP_FACETS}
        for key in ("sample", "sample_label"):
            left, right = f"/computed_payload/{key}", f"/classified_payload/{key}"
            if left in facts and right in facts and facts[left] != facts[right]:
                raise ValueError("BFP com amostras normativas divergentes.")
        if not any(f"/{source}/sample" in facts for source in ("computed_payload", "classified_payload")):
            missing.append("normative_sample")
    else:
        known = ETDAH_FACTORS
        missing.append("clinical_direction_by_factor")
        left, right = "/computed_payload/schooling", "/classified_payload/schooling"
        if left in facts and right in facts and facts[left] != facts[right]:
            raise ValueError("E-TDAH-AD com escolaridades normativas divergentes.")
        if left not in facts and right not in facts:
            missing.append("normative_schooling")

    for scale, name in known.items():
        if code == "bfp":
            group = "factors" if scale in BFP_FACTORS else "facets"
            row = f"/computed_payload/{group}/{scale}"
            class_group = "factor_classifications" if group == "factors" else "facet_classifications"
            class_ids = [f"{row}/classification", f"/classified_payload/{class_group}/{scale}"]
            score_ids = [f"{row}/raw_score"]
        else:
            row = f"/classified_payload/results/{scale}"
            class_ids = [f"{row}/classification"]
            score_ids = [f"/{source}/raw_scores/{scale}" for source in ("computed_payload", "classified_payload")]
            score_ids.append(f"{row}/raw_score")
        class_ids = [key for key in class_ids if key in facts]
        score_ids = [key for key in score_ids if key in facts]
        if not class_ids and not score_ids:
            # E-TDAH-AD nem sempre possui agregado; não exigir sua invenção.
            if scale != "escore_geral":
                missing.append(f"dimension:{scale}")
            continue
        classes = [facts[key] for key in class_ids]
        valid_classes = {_normalized(value) for value in CLASSIFICATIONS}
        if any(not isinstance(value, str) or _normalized(value) not in valid_classes for value in classes):
            raise ValueError("Classificação desconhecida nos resultados do especialista.")
        if len({_normalized(value) for value in classes}) > 1:
            raise ValueError("Classificações calculadas e classificadas divergentes.")
        scores = [facts[key] for key in score_ids]
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in scores):
            raise ValueError("Escore dimensional inválido.")
        if len(set(scores)) > 1:
            raise ValueError("Escores calculados e classificados divergentes.")
        if not class_ids:
            missing.append(f"classification:{scale}")
        if not score_ids:
            missing.append(f"score:{scale}")
        dimensions[scale] = {
            "name": name, "classification_ids": class_ids, "score_ids": score_ids,
            "percentile_ids": [f"{row}/{field}" for field in ("percentile", "percentile_text") if f"{row}/{field}" in facts],
        }
    if not dimensions:
        raise ValueError("Aplicação sem dimensões calculadas/classificadas utilizáveis.")
    return {"dimensions": dimensions, "missing_data": missing, "percentiles_in_narrative": False}


def validate_self_report_findings(output, facts: dict, code: str) -> None:
    guide = self_report_reading_guide(code, facts)
    dimensions = guide["dimensions"]
    all_text = " ".join([finding.statement for finding in output.findings] + output.limitations + output.review_questions)
    if re.search(r"\b(?:percent\w*|centil\w*|centis|por\s+cento)\b|%|\bp\s*\d", _normalized(all_text)):
        raise SpecialistValidationError(
            "self_report_percentile_text",
            "Não escreva percentis ou percentuais na narrativa; mantenha-os nas evidências.",
        )
    covered: set[str] = set()
    labels_pattern = r"\b(?:" + "|".join(re.escape(_normalized(value)) for value in CLASSIFICATIONS) + r")\b"
    for finding in output.findings:
        text = _normalized(finding.statement)
        if _affirmative(text, DIAGNOSIS_ASSERTION) or re.search(r"\bcid\s*[-:]?\s*(?:\d|[a-z]\d)", text):
            raise SpecialistValidationError(
                "self_report_clinical_scope", "Não estabeleça diagnóstico nem atribua CID a partir deste instrumento.",
            )
        if code == "etdah_ad" and _affirmative(text, DIRECTION_ASSERTION):
            raise SpecialistValidationError(
                "self_report_clinical_scope",
                "A fonte não fornece direção clínica validada: não converta classificação em intensidade de sintomas ou desempenho.",
            )
        if len(finding.scale_codes) != len(set(finding.scale_codes)) or set(finding.scale_codes) - dimensions.keys():
            raise SpecialistValidationError("self_report_dimension", "Use scale_codes únicos e presentes em reading_guide.dimensions.")
        covered.update(finding.scale_codes)
        expected: set[str] = set()
        for scale in finding.scale_codes:
            refs = dimensions[scale]
            required = refs["classification_ids"] or refs["score_ids"]
            if not set(required) & set(finding.evidence_ids):
                raise SpecialistValidationError(
                    "self_report_missing_evidence",
                    "Cite a classificação de cada dimensão abordada; quando ausente, cite seu escore disponível.",
                )
            expected.update(_normalized(str(facts[key])) for key in refs["classification_ids"])
        mentioned = set(re.findall(labels_pattern, _normalized(finding.statement)))
        if mentioned != expected:
            raise SpecialistValidationError("self_report_classification", "Apresente as classificações exatas das dimensões abordadas, sem omitir ou acrescentar faixas.")
        # Percentis podem ser evidências, mas nunca autorizar números de escores na prosa.
        score_values = [facts[key] for scale in finding.scale_codes for key in dimensions[scale]["score_ids"] if key in finding.evidence_ids]
        allowed_numbers = {number for value in score_values for number in re.findall(r"-?\d+(?:\.\d+)?", str(value))}
        if not set(re.findall(r"-?\d+(?:\.\d+)?", finding.statement.replace(",", "."))) <= allowed_numbers:
            raise SpecialistValidationError("ungrounded_number", "Use apenas escores citados das dimensões abordadas; não use percentis como escores.")
    if covered != dimensions.keys():
        raise SpecialistValidationError("self_report_dimension", "Aborde todas as dimensões disponíveis, agrupadas em dois a cinco achados.")
    if guide["missing_data"] and not output.review_questions:
        raise SpecialistValidationError("self_report_missing_data", "Registre em review_questions as pendências indicadas em missing_data.")
