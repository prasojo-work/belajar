from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required, with no default on purpose: the app must fail fast when the
    # connection string is missing, instead of silently using a local database.
    # Provide it via an environment variable or a .env file (see .env.example).
    database_url: str


settings = Settings()
