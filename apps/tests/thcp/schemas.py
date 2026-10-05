from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class THCPRawInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    norm_type: Literal["idade", "geral"] = "idade"
    hpm: Annotated[int, Field(strict=True, ge=0, le=30)]
    linguagem: Annotated[int, Field(strict=True, ge=0, le=12)]
    pq: Annotated[int, Field(strict=True, ge=0, le=11)]
    memoria: Annotated[int, Field(strict=True, ge=0, le=10)]
    atencao_acertos: Annotated[int, Field(strict=True, ge=0, le=28)]
    atencao_erros: Annotated[int, Field(strict=True, ge=0, le=62)]
