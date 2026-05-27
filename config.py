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
    chat_endpoint_url: str | None = None
    embedding_endpoint_url: str | None = None


def clean_env_value(value: str | None) -> str | None:
    """Remove accidental whitespace or quote characters from .env values."""

    if value is None:
        return None
    return value.strip().strip('"').strip("'").strip()


def validate_endpoint(endpoint: str, variable_name: str = "AZURE_OPENAI_ENDPOINT") -> None:
    """Fail early with a useful message if an endpoint is malformed."""

    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError(
            f"{variable_name} is malformed. It must start with https:// and include a valid host."
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

    chat_endpoint_url = clean_env_value(os.getenv("CHAT_ENDPOINT_URL"))
    embedding_endpoint_url = clean_env_value(os.getenv("EMBEDDING_ENDPOINT_URL"))

    if chat_endpoint_url:
        validate_endpoint(chat_endpoint_url, "CHAT_ENDPOINT_URL")
    if embedding_endpoint_url:
        validate_endpoint(embedding_endpoint_url, "EMBEDDING_ENDPOINT_URL")

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
        chat_endpoint_url=chat_endpoint_url,
        embedding_endpoint_url=embedding_endpoint_url,
    )
