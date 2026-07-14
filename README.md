# NOVAINVEST

Ver `../PLAN-ASESOR-FINANCIERO.md` para el plan completo. Este README solo
cubre cómo levantar lo que ya existe (F0).

## Backend (FastAPI)

```
cd apps/api
pip install -r requirements.txt
cp .env.example .env   # completar tras crear el proyecto Supabase
uvicorn app.main:app --reload
```

## Frontend (React + Vite + PWA)

```
cd apps/web
npm install
cp .env.example .env   # completar tras crear el proyecto Supabase
npm run dev
```

## Job de refresco diario

```
python jobs/refresco_diario.py --anios 3
```

Sin `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` en el entorno escribe en
`jobs/_cache_local/` (parquet) en vez de fallar — sirve para probar el
pipeline sin credenciales.

## Pendiente de Alex antes de que F0 quede desplegado de verdad

1. Crear proyecto en [Supabase](https://supabase.com) (free tier) y aplicar
   `db/schema.sql` completo en el SQL editor.
2. Insertar el primer admin: `insert into roles_usuario (user_id, rol) values ('<uuid>', 'admin');`
3. Crear servicio en [Render](https://render.com) apuntando a `apps/api`
   (build: `pip install -r requirements.txt`, start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
4. Crear proyecto en [Vercel](https://vercel.com) apuntando a `apps/web`.
5. Cargar en GitHub → Settings → Secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`.
6. Con las 3 cuentas activas, correr `python db/test_rls.py` para confirmar
   el aislamiento de datos entre usuarios (criterio de aceptación F0).
