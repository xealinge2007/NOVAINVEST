from pydantic import BaseModel, Field, model_validator


class Presupuesto(BaseModel):
    ingreso_mensual: float = Field(..., ge=0)
    pct_necesidades: float = Field(50, ge=0, le=100)
    pct_deseos: float = Field(30, ge=0, le=100)
    pct_ahorro: float = Field(20, ge=0, le=100)

    @model_validator(mode="after")
    def _porcentajes_suman_100(self):
        total = self.pct_necesidades + self.pct_deseos + self.pct_ahorro
        if abs(total - 100) > 0.01:
            raise ValueError(f"Los porcentajes deben sumar 100 (suman {total})")
        return self


class SnapshotPatrimonio(BaseModel):
    fecha: str
    activos_total: float = Field(..., ge=0)
    pasivos_total: float = Field(..., ge=0)


class FondoEmergencia(BaseModel):
    gastos_mensuales_estimados: float = Field(..., ge=0)
    meses_objetivo: int = Field(6, ge=3, le=6)
    monto_actual: float = Field(0, ge=0)
