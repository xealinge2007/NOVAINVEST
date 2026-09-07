from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta ABSOLUTA al .env, anclada a este archivo y no al directorio desde el
# que se lanza el proceso. `env_file=".env"` a secas lo resolvia contra el
# cwd, asi que los jobs de `jobs/` -- que se corren desde la raiz del repo --
# arrancaban sin credenciales y morian con "Faltan SUPABASE_URL /
# SUPABASE_SERVICE_KEY" aunque el archivo estuviera ahi. Las variables de
# entorno reales siguen ganando sobre el archivo (comportamiento de
# pydantic-settings), asi que Render y GitHub Actions no cambian.
RUTA_ENV = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Configuración leída de variables de entorno (.env en local, secrets en Render/Actions)."""

    model_config = SettingsConfigDict(env_file=RUTA_ENV, extra="ignore")

    # En proyectos nuevos de Supabase estas dos vienen del dashboard como
    # "Publishable key" y "Secret key" (reemplazan a anon key / service_role key).
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    cors_origins: list[str] = [
        "http://localhost:5173",
        "https://novainvest-seven.vercel.app",
    ]


settings = Settings()
