from pydantic import BaseModel, Field


class ObjetivoNuevo(BaseModel):
    nombre: str
    monto_objetivo: float = Field(..., gt=0)
    fecha_objetivo: str  # YYYY-MM-DD
    prioridad: str = Field("media", pattern="^(alta|media|baja)$")
    monto_actual: float = Field(0, ge=0)


class ActualizarAvance(BaseModel):
    monto_actual: float = Field(..., ge=0)
