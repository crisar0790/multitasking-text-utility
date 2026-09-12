import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT = os.getenv("OPENAI_TIMEOUT", 30)
MAX_OUTPUT_TOKENS = os.getenv("MAX_OUTPUT_TOKENS", 500)

def get_openai_client() -> OpenAI:
    """
    Crea y devuelve el cliente de OpenAI.

    Raises:
        ValueError: Si OPENAI_API_KEY no está configurada.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY no está configurada. "
            "Crea el archivo .env basándote en .env.example."
        )

    return OpenAI(
        api_key=api_key,
        timeout=OPENAI_TIMEOUT,
    )