from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída de variables de entorno (.env en local, secrets en Render/Actions)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # En proyectos nuevos de Supabase estas dos vienen del dashboard como
    # "Publishable key" y "Secret key" (reemplazan a anon key / service_role key).
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
