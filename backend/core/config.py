"""
Configuration module for the Medical Scheduler Backend.
Loads environment variables and sets up application configuration.
"""

import os
from typing import Optional, List
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = "medical-scheduler-crewai"
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    
    # Gemini API
    GEMINI_API_KEY: str = ""
    
    # JWT Configuration
    SECRET_KEY: str = "medical-scheduler-jwt-secret-key-2024-arya-aditya-rv-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CrewAI Configuration
    USE_MOCK_AI: bool = True
    CREWAI_MODEL: str = "ollama/llama2"
    CREWAI_API_KEY: Optional[str] = None
    
    # Email/SMS Mock
    USE_MOCK_SMS: bool = True
    USE_MOCK_EMAIL: bool = True
    
    # SMTP (for real emails when USE_MOCK_EMAIL=false)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # Clinic details used in emails
    CLINIC_NAME: str = "Aurora Health Clinic"
    CLINIC_PHONE: str = "+1 (555) 014-8892"
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()

