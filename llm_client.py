import os

from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    Groq,
    RateLimitError,
)

load_dotenv()

DEFAULT_MODEL = "openai/gpt-oss-20b"
REQUEST_TIMEOUT_SECONDS = 60.0
MAX_OUTPUT_TOKENS = 4096


class GenerationError(Exception):
    """A user-presentable failure while talking to or validating the model."""


class ConfigError(GenerationError):
    """Local configuration problem (for example a missing API key)."""


def get_model_name() -> str:
    return os.getenv("GROQ_MODEL", "").strip() or DEFAULT_MODEL


def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_groq_api_key_here":
        raise ConfigError(
            "GROQ_API_KEY is missing. Add your key to the .env file "
            "(see .env.example) and restart the app."
        )
    return Groq(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=1)


def ask_model(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
    """Send one prompt to Groq and return the reply text."""
    client = get_client()
    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_completion_tokens=MAX_OUTPUT_TOKENS,
        )
    except AuthenticationError as exc:
        raise GenerationError(
            "Groq rejected the API key. Check GROQ_API_KEY in your .env file."
        ) from exc
    except RateLimitError as exc:
        raise GenerationError(
            "Groq rate limit reached. Please wait a moment and try again."
        ) from exc
    except APITimeoutError as exc:
        raise GenerationError(
            "The request to Groq timed out. Please try again."
        ) from exc
    except APIConnectionError as exc:
        raise GenerationError(
            "Could not reach Groq. Check your internet connection and try again."
        ) from exc
    except APIStatusError as exc:
        raise GenerationError(
            f"Groq returned an error (status {exc.status_code}). Please try again."
        ) from exc

    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise GenerationError("The model returned an empty response. Please try again.")
    return text
