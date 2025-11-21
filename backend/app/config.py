from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://app:app@db:5432/app"
    app_env: str = "dev"
    google_client_id: str = ""
    google_client_secret: str = ""
    frontend_url: str = "https://localhost:9443"


settings = Settings()
