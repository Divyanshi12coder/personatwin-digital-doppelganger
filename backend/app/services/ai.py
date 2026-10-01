"""LLM provider abstraction.

    AIService
    ├── AnthropicProvider   (Claude via the official ``anthropic`` SDK)
    ├── OpenAIProvider      (OpenAI Chat Completions, or any compatible gateway)
    └── DemoProvider        (no key: grounded composer built from retrieved memories)

The provider is chosen from ``AI_PROVIDER`` / ``AI_API_KEY``. If a real provider is
configured but fails at request time, the service degrades to the demo composer
and says so in the reply metadata, so the user is never left with a blank screen.
The frontend never talks to any LLM provider directly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

import httpx

from app.core.config import Settings, get_settings
from app.services.context import AssembledContext
from app.services.demo_composer import compose_demo_response
from app.services.persona import PersonaSnapshot
from app.services.query_understanding import QueryAnalysis

logger = logging.getLogger(__name__)


class AIProviderError(RuntimeError):
    """A provider failure with a message that is safe to show to end users."""


@dataclass
class GenerationRequest:
    system: str
    messages: list[dict[str, str]]  # alternating user/assistant turns, last one is the user
    creativity: float
    # Structured inputs, used by the demo composer (real providers use the prompts above).
    persona: PersonaSnapshot
    analysis: QueryAnalysis
    context: AssembledContext
    query: str


@dataclass
class GenerationResult:
    text: str
    provider: str
    model: str
    degraded: bool = False
    notice: str | None = None


class LLMProvider(Protocol):
    name: str
    model: str

    def generate(self, request: GenerationRequest) -> GenerationResult: ...


class DemoProvider:
    name = "demo"
    model = "demo-composer"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        text = compose_demo_response(request.persona, request.analysis, request.context, request.query)
        return GenerationResult(text=text, provider=self.name, model=self.model)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, settings: Settings) -> None:
        import anthropic

        self._anthropic = anthropic
        kwargs: dict[str, object] = {
            "api_key": settings.AI_API_KEY,
            "timeout": settings.AI_TIMEOUT_SECONDS,
            "max_retries": 2,
        }
        if settings.AI_BASE_URL:
            kwargs["base_url"] = settings.AI_BASE_URL
        self.client = anthropic.Anthropic(**kwargs)  # type: ignore[arg-type]
        self.model = settings.resolved_ai_model
        self.max_tokens = settings.AI_MAX_TOKENS
        self.effort = settings.AI_EFFORT
        self.enable_fallbacks = settings.AI_ENABLE_FALLBACKS

    def _supports_adaptive_thinking(self) -> bool:
        return not self.model.startswith(("claude-haiku", "claude-3"))

    def _supports_fallbacks(self) -> bool:
        return self.model.startswith(("claude-opus-5", "claude-fable"))

    def generate(self, request: GenerationRequest) -> GenerationResult:
        anthropic = self._anthropic
        params: dict[str, object] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": request.system,
            "messages": request.messages,
        }
        if self._supports_adaptive_thinking():
            params["thinking"] = {"type": "adaptive"}
            params["output_config"] = {"effort": self.effort}
        try:
            if self.enable_fallbacks and self._supports_fallbacks():
                # Server-side refusal fallbacks: a declined request is retried on the
                # model Anthropic recommends for that refusal category.
                response = self.client.beta.messages.create(
                    **params,  # type: ignore[arg-type]
                    betas=["server-side-fallback-2026-07-01"],
                    fallbacks="default",
                )
            else:
                response = self.client.messages.create(**params)  # type: ignore[arg-type]
        except anthropic.AuthenticationError as exc:
            logger.error("Anthropic authentication failed: %s", exc)
            raise AIProviderError("The AI provider rejected the configured API key.") from exc
        except anthropic.NotFoundError as exc:
            logger.error("Anthropic model not found: %s", exc)
            raise AIProviderError(f"The configured AI model '{self.model}' was not found.") from exc
        except anthropic.RateLimitError as exc:
            raise AIProviderError("The AI provider is rate-limiting requests. Please retry shortly.") from exc
        except anthropic.APIStatusError as exc:
            logger.error("Anthropic API error %s: %s", exc.status_code, exc.message)
            raise AIProviderError("The AI provider returned an error.") from exc
        except anthropic.APIConnectionError as exc:
            raise AIProviderError("Could not reach the AI provider.") from exc

        if response.stop_reason == "refusal":
            raise AIProviderError("The AI model declined to answer this request.")
        text = "".join(block.text for block in response.content if block.type == "text")
        return GenerationResult(text=text, provider=self.name, model=getattr(response, "model", self.model))


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.AI_API_KEY
        self.model = settings.resolved_ai_model
        self.base_url = (settings.AI_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        self.max_tokens = settings.AI_MAX_TOKENS
        self.timeout = settings.AI_TIMEOUT_SECONDS

    def generate(self, request: GenerationRequest) -> GenerationResult:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": request.system}, *request.messages],
            "temperature": round(0.2 + 0.8 * request.creativity, 2),
            "max_tokens": self.max_tokens,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise AIProviderError("Could not reach the AI provider.") from exc
        if resp.status_code == 401:
            raise AIProviderError("The AI provider rejected the configured API key.")
        if resp.status_code == 429:
            raise AIProviderError("The AI provider is rate-limiting requests. Please retry shortly.")
        if resp.status_code >= 400:
            logger.error("OpenAI API error %s: %s", resp.status_code, resp.text[:500])
            raise AIProviderError("The AI provider returned an error.")
        try:
            text = resp.json()["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, ValueError) as exc:
            raise AIProviderError("The AI provider returned an unexpected response.") from exc
        return GenerationResult(text=text, provider=self.name, model=self.model)


class AIService:
    def __init__(self, provider: LLMProvider, fallback: LLMProvider | None = None) -> None:
        self.provider = provider
        self.fallback = fallback

    @property
    def mode(self) -> str:
        return "demo" if self.provider.name == "demo" else "live"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            return self.provider.generate(request)
        except AIProviderError as exc:
            if self.fallback is None:
                raise
            logger.warning("Provider %s failed (%s); degrading to demo composer", self.provider.name, exc)
            result = self.fallback.generate(request)
            result.degraded = True
            result.notice = f"{exc} This reply was composed directly from your memories instead."
            return result


def build_ai_service(settings: Settings) -> AIService:
    demo = DemoProvider()
    if settings.AI_PROVIDER == "anthropic" and settings.AI_API_KEY:
        return AIService(AnthropicProvider(settings), fallback=demo)
    if settings.AI_PROVIDER == "openai" and settings.AI_API_KEY:
        return AIService(OpenAIProvider(settings), fallback=demo)
    if settings.AI_PROVIDER != "demo":
        logger.warning("AI_PROVIDER=%s but AI_API_KEY is empty; running in demo mode", settings.AI_PROVIDER)
    return AIService(demo)


@lru_cache
def get_ai_service() -> AIService:
    return build_ai_service(get_settings())
