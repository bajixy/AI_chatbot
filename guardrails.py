"""Layered guardrails for the topic-constrained chatbot."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from api_client import AzureAIClient
from config import Settings


REFUSAL_MESSAGE = (
    "Sorry, I can only help with gardening-related questions. "
    "You can ask me about plants, soil, watering, composting, pruning, pests, "
    "garden tools, or seasonal planting."
)

PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|above|your) instructions",
    r"forget (all )?(previous|prior|above|your) instructions",
    r"disregard (all )?(previous|prior|above|your) instructions",
    r"reveal (the )?(system|developer) prompt",
    r"show (me )?(the )?(system|developer) prompt",
    r"what (is|are) your hidden instructions",
    r"bypass (the )?(rules|guardrails|restrictions)",
    r"jailbreak",
    r"developer mode",
    r"pretend you are not restricted",
    r"you are now unrestricted",
]

UNSAFE_PATTERNS = [
    r"make poison",
    r"poison someone",
    r"toxic extract",
    r"harm someone",
    r"hide evidence",
    r"hack (a|the|this)?",
    r"steal (passwords|credentials|data)",
]

TOPIC_DESCRIPTION_TEMPLATE = """
Gardening and garden care, including plants, flowers, vegetables, herbs,
soil, composting, fertiliser, mulch, watering, pruning, pests, plant diseases,
seeds, seedlings, garden tools, seasonal planting, indoor plants, outdoor gardens,
climate-aware planting, sustainable gardening, and practical plant maintenance.
"""


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str
    similarity: float | None = None


class Guardrails:
    """Combines rule-based, embedding-based, and output guardrails."""

    def __init__(self, settings: Settings, api_client: AzureAIClient) -> None:
        self.settings = settings
        self.api_client = api_client
        self.topic_reference = self._build_topic_reference(settings.allowed_topic)
        self.topic_embedding = api_client.create_embedding(self.topic_reference)

    def check_user_input(self, user_input: str) -> GuardrailResult:
        """Validate user input before it reaches the chat model."""

        cleaned = user_input.strip()
        if not cleaned:
            return GuardrailResult(False, "empty_input")

        lowered = cleaned.lower()

        if self._matches_any(lowered, PROMPT_INJECTION_PATTERNS):
            return GuardrailResult(False, "prompt_injection_detected")

        if self._matches_any(lowered, UNSAFE_PATTERNS):
            return GuardrailResult(False, "unsafe_request_detected")

        similarity = self._topic_similarity(cleaned)
        if similarity < self.settings.similarity_threshold:
            return GuardrailResult(False, "off_topic_embedding_check", similarity)

        return GuardrailResult(True, "allowed", similarity)

    def check_model_output(self, output: str) -> GuardrailResult:
        """Validate the model response before showing it to the user."""

        lowered = output.lower()

        if not output.strip():
            return GuardrailResult(False, "empty_model_output")

        if self._matches_any(lowered, PROMPT_INJECTION_PATTERNS):
            return GuardrailResult(False, "model_output_leaked_guardrail_content")

        if self._matches_any(lowered, UNSAFE_PATTERNS):
            return GuardrailResult(False, "unsafe_model_output")

        similarity = self._topic_similarity(output)
        if similarity < max(0.55, self.settings.similarity_threshold - 0.15):
            return GuardrailResult(False, "off_topic_output_embedding_check", similarity)

        return GuardrailResult(True, "allowed", similarity)

    def _topic_similarity(self, text: str) -> float:
        text_embedding = self.api_client.create_embedding(text)
        return cosine_similarity(self.topic_embedding, text_embedding)

    def _build_topic_reference(self, topic: str) -> str:
        if topic.lower() == "gardening":
            return TOPIC_DESCRIPTION_TEMPLATE
        return (
            f"The chatbot is only allowed to discuss {topic}. "
            f"Relevant questions should be directly related to {topic}, practical advice about {topic}, "
            f"or safe educational explanations about {topic}."
        )

    @staticmethod
    def _matches_any(text: str, patterns: list[str]) -> bool:
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """Calculate cosine similarity between two embedding vectors."""

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    magnitude_a = math.sqrt(sum(a * a for a in vector_a))
    magnitude_b = math.sqrt(sum(b * b for b in vector_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)
