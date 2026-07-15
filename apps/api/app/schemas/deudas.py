from pydantic import BaseModel, Field


class Deuda(BaseModel):
    nombre: str
    saldo: float = Field(..., gt=0)
    tasa_anual_pct: float = Field(..., ge=0)
    pago_minimo: float = Field(..., gt=0)


class ComparadorRequest(BaseModel):
    extra_mensual: float = Field(..., ge=0)
