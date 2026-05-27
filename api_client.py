"""IFB220 Azure AI API wrapper for chat completions and embeddings."""

from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin
import httpx

from config import Settings


class AzureAIClient:
    """Small wrapper around the IFB220 Azure AI API endpoints."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.http_client = httpx.Client(timeout=httpx.Timeout(60.0, connect=20.0))

    def create_embedding(self, text: str) -> list[float]:
        """Create an embedding vector using the assignment embedding model."""

        endpoint = self._embedding_url()
        response = self.http_client.post(
            endpoint,
            headers=self._headers(),
            json={"input": text},
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

    def create_chat_completion(self, messages: Iterable[dict[str, str]]) -> str:
        """Generate a chatbot response using GPT-4.1-mini."""

        endpoint = self._chat_url()
        response = self.http_client.post(
            endpoint,
            headers=self._headers(),
            json={
                "messages": list(messages),
                "temperature": 0.3,
                "max_tokens": 450,
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"].get("content", "")
        return content.strip()

    def _headers(self) -> dict[str, str]:
        # IFB220's API Management gateway may accept either api-key or
        # Ocp-Apim-Subscription-Key depending on how the class portal exposes keys.
        return {
            "Content-Type": "application/json",
            "api-key": self.settings.azure_api_key,
            "Ocp-Apim-Subscription-Key": self.settings.azure_api_key,
        }

    def _chat_url(self) -> str:
        if self.settings.chat_endpoint_url:
            return self.settings.chat_endpoint_url
        path = (
            f"openai/deployments/{self.settings.chat_deployment_name}"
            f"/chat/completions?api-version={self.settings.azure_api_version}"
        )
        return urljoin(self._base_endpoint(), path)

    def _embedding_url(self) -> str:
        if self.settings.embedding_endpoint_url:
            return self.settings.embedding_endpoint_url
        path = (
            f"openai/deployments/{self.settings.embedding_deployment_name}"
            f"/embeddings?api-version={self.settings.azure_api_version}"
        )
        return urljoin(self._base_endpoint(), path)

    def _base_endpoint(self) -> str:
        return self.settings.azure_endpoint.rstrip("/") + "/"
