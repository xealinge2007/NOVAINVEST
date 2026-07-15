from pydantic import BaseModel, Field


class PosicionNueva(BaseModel):
    ticker: str
    clase: str = Field(..., pattern="^(accion|etf|indice_proxy|cripto|renta_fija|fx|efectivo)$")
    cantidad: float = Field(..., gt=0)
    precio_promedio_compra: float = Field(..., gt=0)
    moneda_compra: str = Field("COP", pattern="^(COP|USD)$")
    cuenta: str = "manual"
    horizonte: str = Field("largo", pattern="^(corto|largo)$")


class OptimizadorRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=2)
    meta: str = Field("max_sharpe", pattern="^(max_sharpe|min_volatilidad)$")
