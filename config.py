from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MOD: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env")
    # class Config:
    #     env_file = ".env"


settings = Settings()
test_settings = Settings(_env_file=".test.env")
