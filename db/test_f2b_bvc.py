"""Verificación de los criterios de aceptación F2b (§11 del plan) contra
Supabase real: crea un usuario de prueba, ejercita la API real (FastAPI
TestClient, no mocks) y confirma:

1. Crear una posición clase='accion' con un ticker fuera de la BVC (AAPL)
   devuelve error 422.
2. El portafolio conserva ETF (VOO) y cripto (BTC-USD) sin problema.
3. Una acción BVC real (ECOPETROL.CL) se acepta.
4. `emisores` / `instrumentos` están poblados y ordinaria/preferencial del
   mismo emisor (CIBEST.CL / PFCIBEST.CL) comparten emisor_id.
5. Si hay historial de precios para ambos instrumentos, la alerta de
   concentración los agrupa como una sola empresa (§3.4).

Requiere `db/migrate_f2b_bvc_emisores_instrumentos.sql` ya aplicado y
`jobs/seed_emisores_instrumentos.py` ya corrido. Borra el usuario de
prueba al final (éxito o fallo).

Uso: python db/test_f2b_bvc.py
"""

import os
import sys
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

FALLAS: list[str] = []


def check(condicion: bool, descripcion: str):
    estado = "OK" if condicion else "FALLO"
    print(f"[{estado}] {descripcion}")
    if not condicion:
        FALLAS.append(descripcion)


def main():
    if not (SUPABASE_URL and SERVICE_KEY and ANON_KEY):
        print("Faltan SUPABASE_URL / SUPABASE_SERVICE_KEY / SUPABASE_ANON_KEY.")
        sys.exit(2)

    from supabase import create_client

    admin = create_client(SUPABASE_URL, SERVICE_KEY)

    # --- 1. Verificación a nivel de esquema (emisores / instrumentos) ---
    emisores = admin.table("emisores").select("id,slug").execute().data
    instrumentos = admin.table("instrumentos").select("ticker,emisor_id,clase").execute().data
    check(len(emisores) >= 15, f"emisores poblados (>=15, hay {len(emisores)})")
    check(len(instrumentos) >= 19, f"instrumentos poblados (>=19, hay {len(instrumentos)})")

    por_ticker = {i["ticker"]: i for i in instrumentos}
    ordinaria = por_ticker.get("CIBEST.CL")
    preferencial = por_ticker.get("PFCIBEST.CL")
    check(
        bool(ordinaria and preferencial and ordinaria["emisor_id"] == preferencial["emisor_id"]),
        "CIBEST.CL y PFCIBEST.CL son instrumentos distintos del mismo emisor_id",
    )
    check(
        bool(ordinaria and ordinaria["clase"] == "ordinaria" and preferencial and preferencial["clase"] == "preferencial"),
        "clase correcta: CIBEST.CL=ordinaria, PFCIBEST.CL=preferencial",
    )

    # --- 2. Usuario de prueba + API real (TestClient, sin mocks) ---
    from fastapi.testclient import TestClient

    from app.main import app

    sufijo = uuid.uuid4().hex[:8]
    email = f"prueba-f2b-{sufijo}@novainvest.test"
    password = "Prueba-F2b-2026!"
    user_id = admin.auth.admin.create_user({"email": email, "password": password, "email_confirm": True}).user.id

    try:
        anon = create_client(SUPABASE_URL, ANON_KEY)
        jwt = anon.auth.sign_in_with_password({"email": email, "password": password}).session.access_token
        headers = {"Authorization": f"Bearer {jwt}"}
        cliente = TestClient(app)

        r_aapl = cliente.post(
            "/portafolio/posiciones",
            json={"ticker": "AAPL", "clase": "accion", "cantidad": 1, "precio_promedio_compra": 100, "horizonte": "largo"},
            headers=headers,
        )
        check(r_aapl.status_code == 422, f"AAPL clase=accion rechazado con 422 (vino {r_aapl.status_code}: {r_aapl.text[:150]})")

        r_voo = cliente.post(
            "/portafolio/posiciones",
            json={"ticker": "VOO", "clase": "etf", "cantidad": 1, "precio_promedio_compra": 500, "moneda_compra": "USD", "horizonte": "largo"},
            headers=headers,
        )
        check(r_voo.status_code == 200, f"VOO clase=etf aceptado (vino {r_voo.status_code}: {r_voo.text[:150]})")

        r_btc = cliente.post(
            "/portafolio/posiciones",
            json={"ticker": "BTC-USD", "clase": "cripto", "cantidad": 0.01, "precio_promedio_compra": 60000, "moneda_compra": "USD", "horizonte": "largo"},
            headers=headers,
        )
        check(r_btc.status_code == 200, f"BTC-USD clase=cripto aceptado (vino {r_btc.status_code}: {r_btc.text[:150]})")

        r_eco = cliente.post(
            "/portafolio/posiciones",
            json={"ticker": "ECOPETROL.CL", "clase": "accion", "cantidad": 10, "precio_promedio_compra": 2500, "horizonte": "largo"},
            headers=headers,
        )
        check(r_eco.status_code == 200, f"ECOPETROL.CL clase=accion aceptado (vino {r_eco.status_code}: {r_eco.text[:150]})")

        r_lista = cliente.get("/portafolio/posiciones", headers=headers)
        tickers_devueltos = {p["ticker"] for p in r_lista.json()} if r_lista.status_code == 200 else set()
        check("AAPL" not in tickers_devueltos, "ningún endpoint devuelve AAPL (acción mundial rechazada)")
        check({"VOO", "BTC-USD", "ECOPETROL.CL"}.issubset(tickers_devueltos), "el portafolio conserva ETF, cripto y la acción BVC")

        # --- 3. Concentración "misma empresa" (requiere precios ya cargados) ---
        activo_cibest = admin.table("activos").select("id").eq("ticker", "CIBEST.CL").execute().data
        activo_pfcibest = admin.table("activos").select("id").eq("ticker", "PFCIBEST.CL").execute().data
        tiene_precios = False
        if activo_cibest and activo_pfcibest:
            p1 = admin.table("precios").select("fecha").eq("activo_id", activo_cibest[0]["id"]).limit(1).execute().data
            p2 = admin.table("precios").select("fecha").eq("activo_id", activo_pfcibest[0]["id"]).limit(1).execute().data
            tiene_precios = bool(p1 and p2)

        if not tiene_precios:
            print("[SKIP] concentración misma-empresa: falta correr refresco_diario.py para CIBEST.CL/PFCIBEST.CL")
        else:
            for ticker, precio in (("CIBEST.CL", 87000), ("PFCIBEST.CL", 75000)):
                cliente.post(
                    "/portafolio/posiciones",
                    json={"ticker": ticker, "clase": "accion", "cantidad": 50, "precio_promedio_compra": precio, "horizonte": "largo"},
                    headers=headers,
                )
            r_metricas = cliente.get("/portafolio/metricas", headers=headers)
            body = r_metricas.json() if r_metricas.status_code == 200 else {}
            grupos = body.get("concentracion_pct_por_grupo", {})
            check(
                "GRUPO_CIBEST_BANCOLOMBIA" in grupos and "CIBEST.CL" not in grupos,
                f"CIBEST.CL + PFCIBEST.CL se agrupan como una sola empresa en concentración (grupos: {list(grupos.keys())})",
            )
    finally:
        admin.auth.admin.delete_user(user_id)

    print()
    if FALLAS:
        print(f"{len(FALLAS)} verificación(es) fallida(s):")
        for f in FALLAS:
            print(f" - {f}")
        sys.exit(1)
    print("Todas las verificaciones F2b pasaron.")


if __name__ == "__main__":
    main()
