from pydantic import BaseModel, Field


class ParametrosRebalanceo(BaseModel):
    comision_pct: float = Field(0.001, ge=0, le=0.1)
    gmf_pct: float = Field(0.004, ge=0, le=0.1)
