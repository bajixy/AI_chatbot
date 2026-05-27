"""Configuration helpers for the topic-constrained chatbot."""

from dataclasses import dataclass
import os
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


def get_settings() -> Settings:
    """Load settings and fail early when required values are missing."""

    required_values = {
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
        "CHAT_DEPLOYMENT_NAME": os.getenv("CHAT_DEPLOYMENT_NAME"),
        "EMBEDDING_DEPLOYMENT_NAME": os.getenv("EMBEDDING_DEPLOYMENT_NAME"),
    }

    missing = [key for key, value in required_values.items() if not value]
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variable(s): {missing_text}. "
            "Copy .env.example to .env and fill in your IFB220 API details."
        )

    return Settings(
        azure_endpoint=required_values["AZURE_OPENAI_ENDPOINT"],
        azure_api_key=required_values["AZURE_OPENAI_API_KEY"],
        azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        chat_deployment_name=required_values["CHAT_DEPLOYMENT_NAME"],
        embedding_deployment_name=required_values["EMBEDDING_DEPLOYMENT_NAME"],
        allowed_topic=os.getenv("ALLOWED_TOPIC", "gardening").strip().lower(),
        similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.72")),
        max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES", "8")),
    )
