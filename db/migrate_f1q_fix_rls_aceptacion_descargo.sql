-- F1q (21-sep-2026) — hotfix: falta la política de UPDATE en
-- `aceptacion_descargo`. `POST /cuenta/aceptar-descargo` hace un
-- `upsert(..., on_conflict="user_id")` (cuenta.py); para un usuario que YA
-- tiene fila ahí, PostgREST lo traduce en un INSERT ... ON CONFLICT DO
-- UPDATE, y esa rama la evalúa la política de UPDATE (cláusula USING), no
-- la de INSERT (WITH CHECK) -- que es la única que existía
-- (migrate_f1_finanzas_personales.sql). Sin política de UPDATE, Postgres
-- deniega por defecto: "new row violates row-level security policy (USING
-- expression)". Afecta a cualquier usuario que reintente aceptar el
-- descargo teniendo ya una fila (found en producción 21-sep-2026, log del
-- backend local).
--
-- Aplicar en el SQL editor de Supabase.

create policy "usuario_actualiza_su_aceptacion" on aceptacion_descargo
    for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
