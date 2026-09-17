from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "darukaa"
    anthropic_api_key: str = ""
    chroma_persist_dir: str = "./chroma_store"

    class Config:
        env_file = ".env"


settings = Settings()
