from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .protocol import PROTOCOL, protocol_totals


class THCPItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: Annotated[int, Field(strict=True)] | None = None
    score: Annotated[int, Field(strict=True, ge=0)]


class THCPRawInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    norm_type: Literal["idade", "geral"] = "idade"
    hpm: Annotated[int, Field(strict=True, ge=0, le=30)]
    linguagem: Annotated[int, Field(strict=True, ge=0, le=12)]
    pq: Annotated[int, Field(strict=True, ge=0, le=11)]
    memoria: Annotated[int, Field(strict=True, ge=0, le=10)]
    atencao_acertos: Annotated[int, Field(strict=True, ge=0, le=28)]
    atencao_erros: Annotated[int, Field(strict=True, ge=0, le=62)]
    item_responses: dict[str, dict[str, THCPItemResponse]] | None = None

    @model_validator(mode="after")
    def validate_item_responses(self):
        if self.item_responses is None:
            return self
        if set(self.item_responses) != set(PROTOCOL):
            raise ValueError("Preencha todos os grupos de itens do THCP.")
        for group, definitions in PROTOCOL.items():
            entries = self.item_responses[group]
            if set(entries) != {item["key"] for item in definitions}:
                raise ValueError(f"{group}: preencha todos os itens do protocolo.")
            for item in definitions:
                response = entries[item["key"]]
                if item["options"] and response.answer is not None:
                    if response.answer not in [0, *item["options"]]:
                        raise ValueError(f"{group}, {item['label']}: selecione uma alternativa válida.")
                    if response.answer == 0 and response.score != 0:
                        raise ValueError(f"{group}, {item['label']}: sem resposta deve ter zero pontos.")
                elif response.answer is not None:
                    raise ValueError(f"{group}, {item['label']}: informe apenas a pontuação.")
                if response.score > item["max_score"]:
                    raise ValueError(f"{group}, {item['label']}: pontuação inválida.")
        totals = protocol_totals({group: {key: response.model_dump() for key, response in entries.items()} for group, entries in self.item_responses.items()})
        for group, total in totals.items():
            if getattr(self, group) != total:
                raise ValueError(f"{group}: o total não corresponde à soma dos itens.")
        return self
