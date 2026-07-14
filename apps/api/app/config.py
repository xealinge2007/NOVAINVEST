from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída de variables de entorno (.env en local, secrets en Render/Actions)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    # Secreto usado por Supabase Auth para firmar los JWT (Project Settings > API > JWT Secret)
    supabase_jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
