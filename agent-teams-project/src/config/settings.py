from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

# class Settings(BaseSettings):
#     # OpenAI
#     OPENAI_API_KEY: str
    
#     # Teams
#     TEAMS_BOT_ID: str
#     TEAMS_BOT_PASSWORD: str
    
#     # Base de datos para análisis SQL
#     DATABASE_URL: str = "sqlite:///./data/company_data.db"
    
#     # Bases de datos adicionales (opcional)
#     POSTGRES_URL: Optional[str] = None
#     MYSQL_URL: Optional[str] = None
    
#     # Redis para cache
#     REDIS_URL: str = "redis://localhost:6379"
    
#     # GCP
#     GCP_PROJECT_ID: str
#     GCP_REGION: str = "us-central1"
    
#     # Configuración del modelo
#     LLM_MODEL: str = "gpt-4o-mini"
#     LLM_TEMPERATURE: float = 0.0
    
#     # Configuración de logging
#     LOG_LEVEL: str = "INFO"
    
#     class Config:
#         env_file = ".env"

# @lru_cache()
# def get_settings():
#     return Settings()

# settings = get_settings()

### ---------------------------------------------------------------------- ###

# En tu archivo src/config/settings.py, agregar esta línea:

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ## OpenAI
    #OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

    # Gemini (cambiar de OpenAI)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/company_data.db")
    #LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    
    # Teams Bot (mantener para futuro)
    TEAMS_BOT_ID: str = os.getenv("TEAMS_BOT_ID", "temp")
    TEAMS_BOT_PASSWORD: str = os.getenv("TEAMS_BOT_PASSWORD", "temp")
    
    # Telegram Bot - NUEVO
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "temp")
    
    # GCP
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "temp")

settings = Settings()