from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://clearnote:clearnote@localhost:5432/clearnote"
    redis_url: str = "redis://localhost:6379/0"
    clerk_jwks_url: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket_name: str = "clearnote-audio"
    aws_region: str = "us-east-1"
    cors_origins: str = "http://localhost:5173"
    openai_api_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        # Strip whitespace from each element to handle "http://a.com, http://b.com"
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
