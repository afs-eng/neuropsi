from __future__ import annotations

import re

from apps.tests.services.ai_interpretation_types import TestAIInterpretationDraft


class RAVLTAIInterpretationHandler:
    instrument_code = "ravlt"
    prompt_name = "tests/clinical_interpretation_agent_prompt.txt"
    skill_path = "tests/skills/ravlt_interpretation_skill.txt"

    PRESERVED = {"Média", "Média Superior", "Superior", "Muito Superior"}
    LOW = {"Média Inferior", "Inferior", "Muito Inferior", "Deficitário"}
    VALID_CLASSIFICATIONS = {
        "Superior",
        "Média Superior",
        "Média",
        "Média Inferior",
        "Inferior",
        "Deficitário",
    }

    def build_payload(self, application) -> dict:
        patient = application.evaluation.patient
        classified = application.classified_payload or {}
        raw_payload = application.raw_payload or {}
        results = classified.get("resultados") or []
        result_map = {item.get("variavel"): item for item in results}
        a1 = self._num(raw_payload.get("a1"))
        a5 = self._num(raw_payload.get("a5"))
        a6 = self._num(raw_payload.get("a6"))
        a7 = self._num(raw_payload.get("a7"))
        gain = a5 - a1
        profile = self._profile(result_map)
        return {
            "patient": {
                "name": patient.full_name or "Paciente",
                "short_name": (patient.full_name or "Paciente").split(" ", 1)[0],
                "age": classified.get("idade"),
                "sex": self._sex_label(getattr(patient, "sex", None)),
                "education": self._education_label(patient),
            },
            "test": {
                "name": "RAVLT",
                "normative_table": self._normative_label(classified),
                "application_status": "Válida",
            },
            "profile": profile,
            "detected_patterns": {
                "gain": gain,
                "late_loss": a6 - a7,
                "curve_pattern": self._curve_pattern(raw_payload),
                "structural_fragility": self._has_structural_fragility(result_map, gain),
                "interference_fragility": self._has_interference_fragility(result_map),
            },
            "results": {
                "A1": self._result_entry(result_map, "A1"),
                "A2": self._result_entry(result_map, "A2"),
                "A3": self._result_entry(result_map, "A3"),
                "A4": self._result_entry(result_map, "A4"),
                "A5": self._result_entry(result_map, "A5"),
                "B1": self._result_entry(result_map, "B1"),
                "A6": self._result_entry(result_map, "A6"),
                "A7": self._result_entry(result_map, "A7"),
                "R": self._result_entry(result_map, "Reconhecimento Lista A"),
                "Escore Total": self._result_entry(result_map, "Escore Total"),
                "Aprend. longo das tentativas": self._result_entry(result_map, "Aprend. longo das Tentativas"),
                "Velocidade de esquecimento": self._result_entry(result_map, "Velocidade de Esquecimento"),
                "I.P.": self._result_entry(result_map, "Interferência Proativa"),
                "I.R.": self._result_entry(result_map, "Interferência Retroativa"),
                "Ganho de aprendizagem": {"score": gain},
                "Perda tardia": {"score": a6 - a7},
            },
            "constraints": [
                "usar somente classificacoes e fatos fornecidos",
                "nao inventar valores, sintomas ou inferencias fora do instrumento",
                "manter exatamente 5 paragrafos clinicos",
                "clinical_box_text deve iniciar com 'o RAVLT'",
                "summary_for_report deve iniciar com 'O RAVLT'",
                "nao deixar placeholders ou frases vazias",
                "gerar inconsistency_alerts somente quando houver incoerencia real entre resultados e texto proposto",
            ],
        }

    def validate_response(self, response: dict, payload: dict) -> list[str]:
        errors: list[str] = []
        paragraphs = response.get("clinical_paragraphs")
        if not isinstance(paragraphs, list) or len(paragraphs) != 5:
            errors.append("A resposta da IA precisa conter exatamente 5 paragrafos clinicos.")
        else:
            for index, paragraph in enumerate(paragraphs, start=1):
                if not isinstance(paragraph, str) or not paragraph.strip():
                    errors.append(f"Paragrafo clinico {index} vazio ou invalido.")

        clinical_box_text = str(response.get("clinical_box_text") or "").strip()
        summary_for_report = str(response.get("summary_for_report") or "").strip()
        if not clinical_box_text.startswith("o RAVLT"):
            errors.append("clinical_box_text precisa iniciar com 'o RAVLT'.")
        if not summary_for_report.startswith("O RAVLT"):
            errors.append("summary_for_report precisa iniciar com 'O RAVLT'.")

        full_text = "\n".join([*(paragraphs or []), clinical_box_text, summary_for_report])
        final_text = "\n".join([clinical_box_text, summary_for_report]).lower()
        forbidden = [
            "Contudo, observou-se .",
            "vulnerabilidade na ,",
            "em dentro da média",
            "{{",
            "}}",
            "[]",
        ]
        for token in forbidden:
            if token in full_text:
                errors.append(f"Texto invalido contem trecho proibido: {token}")

        results = payload.get("results") or {}
        actual_classes = {
            str(item.get("classification") or "")
            for item in results.values()
            if isinstance(item, dict)
        }
        if "Muito Superior" in full_text:
            errors.append("A IA utilizou 'Muito Superior', mas deve repetir literalmente a classificacao da tabela.")
        if "Muito Inferior" in full_text:
            errors.append("A IA utilizou 'Muito Inferior', mas deve repetir literalmente a classificacao da tabela.")
        if "Deficitário" in actual_classes and "Muito Inferior" in full_text:
            errors.append("A IA converteu 'Deficitário' em 'Muito Inferior'.")
        if "Superior" in actual_classes and re.search(r"\bMuito Superior\b", full_text):
            errors.append("A IA converteu 'Superior' em 'Muito Superior'.")

        recognition_class = self._payload_class(results, "R")
        a1_class = self._payload_class(results, "A1")
        a7_class = self._payload_class(results, "A7")
        forgetting_class = self._payload_class(results, "Velocidade de esquecimento")
        if recognition_class in self.PRESERVED and re.search(r"(vulnerab|fragil|rebaixad)[^\n\.]{0,40}reconhecimento|reconhecimento[^\n\.]{0,40}(vulnerab|fragil|rebaixad)", final_text):
            errors.append("O reconhecimento verbal foi descrito como vulnerabilidade apesar de estar em classificacao preservada.")
        if recognition_class in self.LOW and re.search(r"reconhecimento[^\n\.]{0,30}(preservad|funcional|adequad)|acesso[^\n\.]{0,30}(preservad|funcional)", final_text):
            errors.append("O reconhecimento verbal foi descrito como preservado apesar de estar rebaixado.")
        if a1_class in self.PRESERVED and re.search(r"fragil[^\n\.]{0,40}aquisi|dificuldade inicial de codifica|preju[ií]zo[^\n\.]{0,20}curto prazo verbal", full_text.lower()):
            errors.append("A aquisicao inicial foi descrita como fragil apesar de A1 estar em classificacao preservada.")
        if a7_class in self.PRESERVED and forgetting_class in self.PRESERVED and re.search(r"fragil[^\n\.]{0,40}consolida|d[ée]ficit[^\n\.]{0,20}consolida|preju[ií]zo[^\n\.]{0,20}consolida", full_text.lower()):
            errors.append("O texto descreveu fragilidade de consolidacao apesar de A7 e velocidade de esquecimento estarem preservados.")

        alt_class = self._payload_class(results, "Aprend. longo das tentativas")
        a6_class = self._payload_class(results, "A6")
        ir_class = self._payload_class(results, "I.R.")
        b1_class = self._payload_class(results, "B1")
        ip_class = self._payload_class(results, "I.P.")

        if alt_class in self.LOW and not any(token in final_text for token in ["aprendizagem ao longo das tentativas", "repetição sucessiva", "curva de aprendizagem"]):
            errors.append("Ha fragilidade em aprendizagem ao longo das tentativas sem mencao no fechamento clinico.")
        if a6_class in self.LOW and ir_class in self.LOW and not any(token in final_text for token in ["retroativ", "a6", "recuperação imediata após interferência"]):
            errors.append("Ha sensibilidade retroativa (A6/I.R.) sem mencao suficiente no fechamento clinico.")
        if b1_class in self.LOW and ip_class in self.LOW and not any(token in final_text for token in ["proativ", "b1"]):
            errors.append("Ha sensibilidade proativa (B1/I.P.) sem mencao suficiente no fechamento clinico.")

        if payload.get("profile") == "interferencia_isolada" and "interfer" not in full_text.lower():
            errors.append("Perfil de interferencia isolada precisa mencionar interferencia no texto final.")
        alerts = response.get("inconsistency_alerts") or []
        if alerts and not isinstance(alerts, list):
            errors.append("inconsistency_alerts precisa ser uma lista quando informado.")
        return errors

    def normalize_response(self, response: dict, payload: dict) -> TestAIInterpretationDraft:
        alerts = [str(item).strip() for item in response.get("inconsistency_alerts") or [] if str(item).strip()]
        return TestAIInterpretationDraft(
            clinical_paragraphs=[str(item).strip() for item in response.get("clinical_paragraphs") or []],
            clinical_box_text=str(response.get("clinical_box_text") or "").strip(),
            summary_for_report=str(response.get("summary_for_report") or "").strip(),
            warnings=alerts,
        )

    def _profile(self, result_map: dict) -> str:
        alt = self._class(result_map, "Aprend. longo das Tentativas")
        a7 = self._class(result_map, "A7")
        recognition = self._class(result_map, "Reconhecimento Lista A")
        ip = self._class(result_map, "Interferência Proativa")
        ir = self._class(result_map, "Interferência Retroativa")
        if alt in self.PRESERVED and a7 in self.PRESERVED and recognition in self.PRESERVED and ip not in self.LOW and ir not in self.LOW:
            return "preservado"
        if alt in self.PRESERVED and a7 in self.PRESERVED and recognition in self.PRESERVED and (ip in self.LOW or ir in self.LOW):
            return "interferencia_isolada"
        if alt in self.LOW and recognition in self.LOW:
            return "fragilidade_aprendizagem"
        if a7 in self.LOW and recognition in self.PRESERVED:
            return "dificuldade_recuperacao"
        return "perfil_misto"

    def _curve_pattern(self, raw_payload: dict) -> str:
        a1 = self._num(raw_payload.get("a1"))
        a2 = self._num(raw_payload.get("a2"))
        a3 = self._num(raw_payload.get("a3"))
        a4 = self._num(raw_payload.get("a4"))
        a5 = self._num(raw_payload.get("a5"))
        gain = a5 - a1
        monotonic = a5 >= a4 >= a3 >= a2 >= a1
        if gain >= 4 and monotonic:
            return "ascendente_consistente"
        if gain >= 2:
            return "progressiva"
        return "inconsistente"

    def _has_structural_fragility(self, result_map: dict, gain: float) -> bool:
        return (
            self._class(result_map, "Aprend. longo das Tentativas") in self.LOW
            or self._class(result_map, "Reconhecimento Lista A") in self.LOW
            or gain < 0
        )

    def _has_interference_fragility(self, result_map: dict) -> bool:
        return (
            self._class(result_map, "Interferência Proativa") in self.LOW
            or self._class(result_map, "Interferência Retroativa") in self.LOW
        )

    @staticmethod
    def _class(result_map: dict, key: str) -> str:
        return result_map.get(key, {}).get("classificacao") or "Média"

    @staticmethod
    def _result_entry(result_map: dict, key: str) -> dict:
        item = result_map.get(key, {})
        return {
            "score": item.get("bruto"),
            "classification": RAVLTAIInterpretationHandler._table_classification(item.get("classificacao")),
            "percentile": item.get("percentil"),
        }

    @staticmethod
    def _table_classification(classification: str | None) -> str | None:
        mapping = {
            "Muito Superior": "Superior",
            "Superior": "Superior",
            "Média Superior": "Média Superior",
            "Média": "Média",
            "Média Inferior": "Média Inferior",
            "Inferior": "Inferior",
            "Muito Inferior": "Deficitário",
            "Deficitário": "Deficitário",
        }
        if not classification:
            return classification
        return mapping.get(classification, classification)

    @staticmethod
    def _payload_class(results: dict, key: str) -> str:
        item = results.get(key) or {}
        return str(item.get("classification") or "")

    @staticmethod
    def _sex_label(value: str | None) -> str:
        if value == "M":
            return "Masculino"
        if value == "F":
            return "Feminino"
        return value or "Não informado"

    @staticmethod
    def _education_label(patient) -> str:
        value = getattr(patient, "schooling", None) or getattr(patient, "grade_year", None) or "Não informado"
        return str(value).replace("_", " ").strip().capitalize()

    @staticmethod
    def _normative_label(classified: dict) -> str:
        faixa = classified.get("faixa_etaria")
        idade = classified.get("idade")
        if idade is not None and idade != "":
            stage = "Infantil" if int(idade) < 18 else "Adulto"
        else:
            stage = "Adulto"
        return f"{stage} / {faixa}" if faixa else stage

    @staticmethod
    def _num(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
