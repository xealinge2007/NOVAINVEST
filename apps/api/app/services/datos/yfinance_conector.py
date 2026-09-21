"""Conector primario para acciones, ETFs, cripto (vía ticker -USD) y BVC.

Verificación F0 (14-jul-2026): a diferencia de lo previsto en el plan, yfinance
SÍ cubre BVC de forma confiable usando el sufijo '.CL' (currency=COP,
exchange=BVC en los metadatos) — no se necesitó conector propio a bvc.com.co.
Ver novainvest/db/NOTAS_F0.md para el detalle de la verificación.
"""

import base64
import os
import ssl
import sys
import tempfile
from datetime import date
from pathlib import Path


def _fijar_ca_bundle_windows() -> None:
    """yfinance usa curl_cffi por debajo, que NO hereda el almacén de
    certificados del SO como sí hace `truststore` para supabase-py (ver
    database.py) -- en Windows, si un antivirus intercepta HTTPS y
    sustituye el certificado del servidor (verificado real: Avast),
    yfinance falla con CERTIFICATE_VERIFY_FAILED aunque el resto de la app
    conecte bien. Se arma un bundle combinado (certifi + raíces/intermedios
    de Windows) una sola vez por máquina, cacheado en disco, y se apunta
    CURL_CA_BUNDLE/SSL_CERT_FILE ahí. No-op en cualquier otro SO, si ya
    está fijado por fuera, o si algo falla -- nunca debe tumbar el import."""
    if sys.platform != "win32" or os.environ.get("CURL_CA_BUNDLE"):
        return
    try:
        import certifi

        cache = Path(tempfile.gettempdir()) / "novainvest_ca_bundle.pem"
        if not cache.exists():
            base = Path(certifi.where()).read_bytes()
            extra = []
            for almacen in ("ROOT", "CA"):
                for der, _tipo, _confianza in ssl.enum_certificates(almacen):
                    b64 = base64.encodebytes(der).decode("ascii")
                    extra.append(f"-----BEGIN CERTIFICATE-----\n{b64}-----END CERTIFICATE-----\n".encode())
            cache.write_bytes(base + b"\n" + b"".join(extra))
        os.environ["CURL_CA_BUNDLE"] = str(cache)
        os.environ["SSL_CERT_FILE"] = str(cache)
    except Exception:
        pass


_fijar_ca_bundle_windows()

import yfinance as yf  # noqa: E402 -- después de fijar el CA bundle, a propósito

from .base import FuenteDatos, PrecioDiario, Vela4h


class YfinanceConector(FuenteDatos):
    nombre = "yfinance"

    def obtener_precios(self, ticker: str, desde: date, hasta: date) -> list[PrecioDiario]:
        hist = yf.Ticker(ticker).history(start=desde, end=hasta, auto_adjust=False)
        if hist.empty:
            return []
        precios = []
        for fecha_ts, fila in hist.iterrows():
            cierre = fila.get("Close")
            if cierre != cierre:  # NaN: la sesión del día aún no cierra (visto en BVC intradía) — se descarta
                continue
            volumen = fila.get("Volume")
            precios.append(
                PrecioDiario(
                    fecha=fecha_ts.date(),
                    apertura=float(fila["Open"]) if fila.get("Open") == fila.get("Open") else None,
                    alto=float(fila["High"]) if fila.get("High") == fila.get("High") else None,
                    bajo=float(fila["Low"]) if fila.get("Low") == fila.get("Low") else None,
                    cierre=float(fila["Close"]),
                    cierre_ajustado=float(fila["Adj Close"]) if "Adj Close" in fila and fila["Adj Close"] == fila["Adj Close"] else None,
                    volumen=int(volumen) if volumen == volumen else None,
                )
            )
        return precios

    def disponible(self) -> bool:
        try:
            hist = yf.Ticker("AAPL").history(period="5d")
            return not hist.empty
        except Exception:
            return False

    def obtener_velas_4h(self, ticker: str, dias: int = 730) -> list[Vela4h]:
        """`dias` topa en ~730 por límite de yfinance para intervalos
        intradía (verificado F3: pide más y devuelve igual el máximo
        disponible, no falla, pero no hay que asumir más de 2 años reales).
        """
        hist = yf.Ticker(ticker).history(period=f"{min(dias, 730)}d", interval="4h", auto_adjust=False)
        if hist.empty:
            return []
        velas = []
        for fecha_ts, fila in hist.iterrows():
            cierre = fila.get("Close")
            if cierre != cierre:  # NaN
                continue
            volumen = fila.get("Volume")
            velas.append(
                Vela4h(
                    fecha_hora=fecha_ts.to_pydatetime(),
                    apertura=float(fila["Open"]) if fila.get("Open") == fila.get("Open") else None,
                    alto=float(fila["High"]) if fila.get("High") == fila.get("High") else None,
                    bajo=float(fila["Low"]) if fila.get("Low") == fila.get("Low") else None,
                    cierre=float(cierre),
                    volumen=int(volumen) if volumen == volumen else None,
                )
            )
        return velas
