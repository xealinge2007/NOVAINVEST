from pydantic import BaseModel, Field


class GastoManual(BaseModel):
    fecha: str
    monto: float = Field(..., gt=0)
    categoria: str
    descripcion: str | None = None
