"""
Configuration module for GymOS AI Revenue Recovery Engine.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server settings
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = True

    # Razorpay Test Mode Credentials
    RAZORPAY_KEY_ID: str = "mock"
    RAZORPAY_KEY_SECRET: str = "mock"
    RAZORPAY_WEBHOOK_SECRET: str = "mock"

    # LLM Diagnostics
    LLM_PROVIDER: str = "mock_heuristic"  # 'openai', 'gemini', or 'mock_heuristic'
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Policy Guardrails & Limits
    MAX_DISCOUNT_PERCENT: float = 15.0
    MAX_RECOVERY_ATTEMPTS: int = 3
    MIN_COOLDOWN_HOURS: int = 24
    VIP_ESCALATION_THRESHOLD_INR: float = 50000.0


settings = Settings()
