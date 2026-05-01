from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    tavily_api_key: str
    google_sheet_id: str
    google_credentials_path: str = "credentials.json"

    model_config = {"env_file": ".env"}


settings = Settings()