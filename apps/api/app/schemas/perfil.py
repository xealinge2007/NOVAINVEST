from pydantic import BaseModel, Field


class CuestionarioPerfil(BaseModel):
    respuestas: dict[str, int] = Field(..., description="q1..q14 -> 1..4")
    disparadores_gasto: list[str] = Field(default_factory=list)
