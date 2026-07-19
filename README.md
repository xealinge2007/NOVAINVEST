# NOVAINVEST

Ver `../PLAN-ASESOR-FINANCIERO.md` para el plan completo y
**[ESTADO_PROYECTO.md](ESTADO_PROYECTO.md) para el estado actual, la
infraestructura en vivo y cómo continuar** (léelo primero si vas a seguir
trabajando en esto). Este README solo cubre cómo levantar el proyecto en
local.

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

## Estado y despliegue

Ver [ESTADO_PROYECTO.md](ESTADO_PROYECTO.md) — infraestructura en vivo, qué
fases están hechas, cómo sincronizar cambios al repo de GitHub (el repo local
no tiene remoto propio), y gotchas ya resueltos que no hay que repetir.
