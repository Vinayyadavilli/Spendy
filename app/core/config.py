import os
import urllib.parse
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Spend Tracker API"
    API_V1_STR: str = "/api"
    
    # DB configs
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "Admin@123")
    DB_NAME: str = os.getenv("DB_NAME", "spent_tracker_db")
    
    @property
    def DATABASE_URL(self) -> str:
        # 1. Direct cloud DATABASE_URL override (Render, Railway, TiDB, Aiven, Supabase, Neon)
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            if env_url.startswith("postgres://"):
                env_url = env_url.replace("postgres://", "postgresql://", 1)
            elif env_url.startswith("mysql://"):
                env_url = env_url.replace("mysql://", "mysql+pymysql://", 1)
            return env_url

        # 2. Local/configured MySQL server
        encoded_user = urllib.parse.quote_plus(self.DB_USER)
        encoded_password = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{encoded_user}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # JWT Configs
    SECRET_KEY: str = os.getenv("SECRET_KEY", "spend_tracker_super_secret_jwt_key_998877665544332211")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))

settings = Settings()
