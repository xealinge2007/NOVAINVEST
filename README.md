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

## Notas sobre las keys de Supabase

Los proyectos nuevos de Supabase muestran **Publishable key** / **Secret key**
en vez de los antiguos `anon key` / `service_role key` — van en las mismas
variables (`SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_KEY`), supabase-py no
distingue el formato. `auth.py` valida el JWT del usuario contra el propio
servidor de Supabase (`auth.get_user()`), no con un secreto local — por eso
ya no existe `SUPABASE_JWT_SECRET`.

## Estado F0 (14-jul-2026)

Proyecto Supabase creado, `db/schema.sql` aplicado, criterio de aceptación
verificado contra la base real:
- 18/18 activos (10 US + 5 BVC + proxy COLCAP + BTC + TRM), 13.773 filas de
  precios, 3 años de historia — en Supabase.
- `db/test_rls.py` con 2 usuarios reales: **OK, usuario B no ve el perfil de A**.
- `/salud/fuentes` responde con los registros reales del último refresco.

## Pendiente de Alex

1. Insertar el primer admin: `insert into roles_usuario (user_id, rol) values ('<uuid>', 'admin');`
2. Terminar el deploy en [Render](https://render.com) (`apps/api`) y
   [Vercel](https://vercel.com) (`apps/web`) — pegar `SUPABASE_URL`,
   `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` como variables de entorno en
   Render (Vercel solo necesita `VITE_SUPABASE_URL`/`VITE_SUPABASE_ANON_KEY`,
   nunca la secret key en el frontend).
3. Cargar en GitHub → repo `NOVAINVEST` → Settings → Secrets and variables →
   Actions: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` — para que
   `refresco_diario.yml` corra solo cada madrugada.
