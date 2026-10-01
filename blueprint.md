# Blueprint — novainvest
<!-- Actualizado: 2026-09-30 17:56 -->

## 1. Qué quiero lograr
Cerrar los huecos reales de `deuda_financiera` en `fundamentales_reportados` que otra sesión
marcó como "nadie los miró" (lista de 26 emisor/periodo con tipo/entidad SIMEV). Alex ubica los
PDF y me los pasa uno por uno; yo verifico que el balance cuadre y publico en Supabase.

## 2. En qué punto está
BVC 2019-ANUAL publicado (`fundamentales_reportados` id 652), balance cuadra exacto. Faltan
BVC 2020-T1/T2/T3 y el resto de la lista de 26 (BANCO_DE_BOGOTA, CORFICOLOMBIANA, EL_CONDOR,
CELSIA, ENKA, ETB, CEMENTOS_ARGOS, DAVIVIENDA_GROUP, ECOPETROL, FABRICATO, CONSTRUCTORA_CONCONCRETO).
**Ojo**: `TRASPASO_DEUDA_FINANCIERA.md` (25-sep, otra sesión) ya llevó la cobertura global a
82,1% y recomienda dar por cerrado el resto por bajo impacto — puede solapar con esta lista de
26; falta reconciliar cuáles siguen siendo huecos reales. Mi búsqueda automatizada en SIMEV
falla de forma intermitente (misma consulta a veces vacía, a veces con datos), causa no resuelta
— Alex busca los PDF en su propio navegador y me los pasa.

## 3. Archivos en juego
- TRASPASO_DEUDA_FINANCIERA.md — estado más reciente de todo el universo de deuda_financiera, leer antes de seguir
- VERIFICAR_EN_SIMEV.csv — qué se verificó en SIMEV y qué no, por emisor/tipo/entidad
- PROGRESO_DESCARGA_2026-09-23.txt — bitácora de la sesión de descarga anterior (canal C, ya cerrada)
- C:\Proyectos\BVC\SIMEV_BVC\BVC\2019-ANUAL_Estados-Financieros-Consolidados.pdf — recién agregado
- apps/api/app/services/extraccion/lector_xbrl.py — DEUDA_FINANCIERA_POR_EMISOR, fórmula por emisor, no generalizar

## 4. Cambios hechos
- BVC 2019-ANUAL: insertado en `reportes_archivo` (id 437) y `fundamentales_reportados` (id 652)
  vía Supabase directo, balance verificado exacto (Activo 625.073,596 = Pasivo 117.311,577 +
  Patrimonio 507.762,019, miles de millones). No es cambio de git (el corpus de PDF vive fuera
  del repo, en C:\Proyectos\BVC).

## 5. Intentos fallidos — no repetir
- [2026-09-25] Probé navegar SIMEV (BVC tipo 082/entidad 000004) para 2019-ANUAL y 2020-T1 con
  el navegador automatizado → falló porque el mismo filtro devuelve "No hay información
  reportada" de forma inconsistente (a veces vacío, a veces con datos); no se determinó la
  causa raíz. No repetir con navegador automatizado — Alex lo hace a mano en su Chrome.
- [2026-09-25] Probé buscar estados financieros de BVC en su propio sitio (bvc.com.co,
  secciones "informacion-y-presentaciones-ir", "accion-bvc") → falló porque esas páginas solo
  tienen presentaciones corporativas, no estados financieros trimestrales/anuales.

## 6. Siguientes pasos
- Leer TRASPASO_DEUDA_FINANCIERA.md (§7-8) y VERIFICAR_EN_SIMEV.csv para saber cuáles de los 26
  ya quedaron resueltos por la otra sesión antes de seguir pidiendo archivos.
- Procesar BVC 2020-T1/T2/T3 en cuanto Alex pase los PDF (mismo método de verificación).
- Seguir con el resto de la lista de 26 en el orden que Alex vaya encontrando los archivos.
- Confirmar con Alex si el "dar por cerrado" del TRASPASO aplica también a esta lista de 26.
