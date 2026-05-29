"""IFB220 Azure AI API wrapper for chat completions and embeddings."""

from __future__ import annotations

from typing import Iterable, Any
from urllib.parse import urljoin
import httpx

from config import Settings
from monitoring import TokenUsage


class AzureAIClient:
    """Small wrapper around the IFB220 Azure AI API endpoints."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.http_client = httpx.Client(
            timeout=httpx.Timeout(120.0, connect=60.0),
            follow_redirects=True,
        )

    def create_embedding(self, text: str) -> list[float]:
        """Create an embedding vector using the assignment embedding model."""

        endpoint = self._embedding_url()
        data = self._post_json(
            endpoint,
            json_body={"input": text},
            operation_name="embedding",
        )
        return data["data"][0]["embedding"]

    def create_chat_completion(self, messages: Iterable[dict[str, str]]) -> tuple[str, TokenUsage]:
        """Generate a chatbot response using GPT-4.1-mini and return token usage."""

        endpoint = self._chat_url()
        data = self._post_json(
            endpoint,
            json_body={
                "messages": list(messages),
                "temperature": 0.3,
                "max_tokens": 450,
            },
            operation_name="chat completion",
        )
        content = data["choices"][0]["message"].get("content", "")
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens"),
            completion_tokens=usage_data.get("completion_tokens"),
            total_tokens=usage_data.get("total_tokens"),
        )
        return content.strip(), usage

    def _post_json(self, endpoint: str, json_body: dict[str, Any], operation_name: str) -> dict[str, Any]:
        """Send a POST request and convert common connection errors into readable messages."""

        try:
            response = self.http_client.post(
                endpoint,
                headers=self._headers(),
                json=json_body,
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectTimeout as error:
            raise RuntimeError(
                f"The {operation_name} request timed out while connecting to the IFB220 API. "
                "This usually means the API gateway is slow, your internet connection is blocking it, "
                "or a VPN/proxy/firewall is interfering. Try again, switch networks, or test the endpoint with curl."
            ) from error
        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                f"The {operation_name} request reached the IFB220 API but failed with "
                f"HTTP {error.response.status_code}: {error.response.text}"
            ) from error
        except httpx.RequestError as error:
            raise RuntimeError(
                f"The {operation_name} request could not reach the IFB220 API: {error}"
            ) from error

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
        # Normal value should be https://.../ifb220-ai. This also protects
        # against accidentally pasting https://.../ifb220-ai/openai/responses...
        endpoint = self.settings.azure_endpoint.strip().rstrip("/")
        marker = "/openai"
        if marker in endpoint:
            endpoint = endpoint.split(marker, maxsplit=1)[0]
        return endpoint + "/"
