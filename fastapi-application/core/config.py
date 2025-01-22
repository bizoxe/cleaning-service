"""
Main application settings.
"""

from pathlib import Path

from pydantic import (
    BaseModel,
    PostgresDsn,
    computed_field,
    EmailStr,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


BASE_DIR = Path(__file__).parent.parent


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    auth: str = "/auth"
    users: str = "/users"
    cleanings: str = "/cleanings"


class ApiBaseConfig(BaseModel):
    name: str = "Cleaning service web app"
    version: str = "0.1.0"
    prefix: str = "/api"
    environment: str = "dev"
    v1: ApiV1Prefix = ApiV1Prefix()
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
    ]
    cors_allow_headers: list[str] = ["*"]


class DataBaseConfig(BaseModel):
    echo: bool = False
    echo_pool: bool = False
    pool_pre_ping: bool = True
    pool_size: int = 50
    max_overflow: int = 10

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_pwd: str
    postgres_db: str

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @computed_field  # type: ignore
    @property
    def postgres_connection_string(self) -> str:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            host=self.postgres_host,
            port=self.postgres_port,
            username=self.postgres_user,
            password=self.postgres_pwd,
            path=self.postgres_db,
        ).unicode_string()


class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30


class RolesConfig(BaseModel):
    admin_email: EmailStr
    editor_email: EmailStr
    admin_pwd: str
    editor_pwd: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    run: RunConfig = RunConfig()
    api: ApiBaseConfig = ApiBaseConfig()
    db: DataBaseConfig
    auth_jwt: AuthJWT = AuthJWT()
    roles: RolesConfig


settings = Settings()
