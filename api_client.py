"""Azure OpenAI API wrapper for chat completions and embeddings."""

from __future__ import annotations

from typing import Iterable
from openai import AzureOpenAI

from config import Settings


class AzureAIClient:
    """Small wrapper around Azure OpenAI calls used by the chatbot."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AzureOpenAI(
            azure_endpoint=settings.azure_endpoint,
            api_key=settings.azure_api_key,
            api_version=settings.azure_api_version,
        )

    def create_embedding(self, text: str) -> list[float]:
        """Create an embedding vector using the assignment embedding model."""

        response = self.client.embeddings.create(
            model=self.settings.embedding_deployment_name,
            input=text,
        )
        return response.data[0].embedding

    def create_chat_completion(self, messages: Iterable[dict[str, str]]) -> str:
        """Generate a chatbot response using GPT-4.1-mini."""

        response = self.client.chat.completions.create(
            model=self.settings.chat_deployment_name,
            messages=list(messages),
            temperature=0.3,
            max_tokens=450,
        )

        content = response.choices[0].message.content
        return content.strip() if content else ""
