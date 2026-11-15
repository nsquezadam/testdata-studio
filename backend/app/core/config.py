import os
from dataclasses import dataclass

from dotenv import load_dotenv


# Carga las variables definidas en backend/.env
load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "TestData Studio API")
    app_env: str = os.getenv("APP_ENV", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api")

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/testdata_studio",
    )

    jwt_secret: str = os.getenv(
        "JWT_SECRET",
        "CAMBIAR_ESTA_CLAVE_EN_DESARROLLO",
    )
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_minutes: int = int(
        os.getenv("ACCESS_TOKEN_MINUTES", "60")
    )

    frontend_origin: str = os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5173",
    )


settings = Settings()