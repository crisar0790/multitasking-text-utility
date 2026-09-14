import os
from pathlib import Path
import math

from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "30"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "250"))

def get_openai_temperature() -> float | None:
    """
    Read temperature, or omit it when explicitly left blank.
    """
    raw_value = os.getenv("OPENAI_TEMPERATURE", "0").strip()

    if not raw_value:
        return None

    try:
        temperature = float(raw_value)
    except ValueError as error:
        raise ValueError(
            "OPENAI_TEMPERATURE must be a number or an empty value."
        ) from error

    if not math.isfinite(temperature) or not 0 <= temperature <= 2:
        raise ValueError(
            "OPENAI_TEMPERATURE must be between 0 and 2."
        )

    return temperature

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

    if not math.isfinite(OPENAI_TIMEOUT) or OPENAI_TIMEOUT <= 0:
        raise ValueError(
            "OPENAI_TIMEOUT must be a positive number."
        )

    if MAX_OUTPUT_TOKENS <= 0:
        raise ValueError(
            "MAX_OUTPUT_TOKENS must be a positive integer."
        )

    return OpenAI(
        api_key=api_key,
        timeout=OPENAI_TIMEOUT,
    )