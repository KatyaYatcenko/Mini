"""
Централізоване зчитування налаштувань з .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

TG_API_ID = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH = os.getenv("TG_API_HASH", "")
TG_SESSION_NAME = os.getenv("TG_SESSION_NAME", "assist_session")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() == "true"


def validate():
    """Перевіряє, що ключові налаштування задані, і одразу підказує що виправити."""
    missing = []
    if not TG_API_ID:
        missing.append("TG_API_ID")
    if not TG_API_HASH:
        missing.append("TG_API_HASH")
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if missing:
        raise RuntimeError(
            "Не задані обов'язкові налаштування у .env: " + ", ".join(missing) +
            "\nСкопіюй .env.example у .env і заповни ці поля."
        )
