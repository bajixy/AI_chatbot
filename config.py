"""Configuration helpers for the topic-constrained chatbot."""

from dataclasses import dataclass
import os
from urllib.parse import urlparse
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    azure_endpoint: str
    azure_api_key: str
    azure_api_version: str
    chat_deployment_name: str
    embedding_deployment_name: str
    allowed_topic: str
    similarity_threshold: float
    max_history_messages: int


def clean_env_value(value: str | None) -> str | None:
    """Remove accidental whitespace or quote characters from .env values."""

    if value is None:
        return None
    return value.strip().strip('"').strip("'").strip()


def validate_endpoint(endpoint: str) -> None:
    """Fail early with a useful message if the endpoint is malformed."""

    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError(
            "AZURE_OPENAI_ENDPOINT is malformed. Use only the base endpoint, for example:\n"
            "AZURE_OPENAI_ENDPOINT=https://prd-ifb220-apim.azure-api.net/ifb220-ai\n"
            "Do not include /chat/completions or ?api-version= in this value."
        )


def get_settings() -> Settings:
    """Load settings and fail early when required values are missing."""

    required_values = {
        "AZURE_OPENAI_ENDPOINT": clean_env_value(os.getenv("AZURE_OPENAI_ENDPOINT")),
        "AZURE_OPENAI_API_KEY": clean_env_value(os.getenv("AZURE_OPENAI_API_KEY")),
        "CHAT_DEPLOYMENT_NAME": clean_env_value(os.getenv("CHAT_DEPLOYMENT_NAME")),
        "EMBEDDING_DEPLOYMENT_NAME": clean_env_value(os.getenv("EMBEDDING_DEPLOYMENT_NAME")),
    }

    missing = [key for key, value in required_values.items() if not value]
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variable(s): {missing_text}. "
            "Copy .env.example to .env and fill in your IFB220 API details."
        )

    validate_endpoint(required_values["AZURE_OPENAI_ENDPOINT"])

    return Settings(
        azure_endpoint=required_values["AZURE_OPENAI_ENDPOINT"],
        azure_api_key=required_values["AZURE_OPENAI_API_KEY"],
        azure_api_version=clean_env_value(os.getenv("AZURE_OPENAI_API_VERSION"))
        or "2024-02-15-preview",
        chat_deployment_name=required_values["CHAT_DEPLOYMENT_NAME"],
        embedding_deployment_name=required_values["EMBEDDING_DEPLOYMENT_NAME"],
        allowed_topic=(clean_env_value(os.getenv("ALLOWED_TOPIC")) or "gardening").lower(),
        similarity_threshold=float(clean_env_value(os.getenv("SIMILARITY_THRESHOLD")) or "0.72"),
        max_history_messages=int(clean_env_value(os.getenv("MAX_HISTORY_MESSAGES")) or "8"),
    )
