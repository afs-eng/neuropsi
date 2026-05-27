from __future__ import annotations

from django.conf import settings

from .provider_factory import ProviderFactory


class AIHealthcheckService:
    HEALTHCHECK_SYSTEM_PROMPT = (
        "Voce esta executando uma verificacao tecnica de disponibilidade. "
        "Responda apenas com OK."
    )
    HEALTHCHECK_USER_PROMPT = "Responda apenas OK."

    @staticmethod
    def _timeout(timeout: int | None) -> int:
        if timeout is not None:
            return timeout
        return int(getattr(settings, "AI_HEALTHCHECK_TIMEOUT", 180))

    @classmethod
    def check(cls, provider: str | None = None, timeout: int | None = None) -> dict:
        provider_name = provider or settings.AI_PROVIDER
        client = ProviderFactory.create(provider_name)
        
        if client is None:
            return {"status": "disabled", "provider": provider_name}
        if provider_name == "ollama" and hasattr(client, "check_available"):
            return client.check_available(timeout=cls._timeout(timeout))
        result = client.generate(
            system_prompt=cls.HEALTHCHECK_SYSTEM_PROMPT,
            user_prompt=cls.HEALTHCHECK_USER_PROMPT,
            temperature=0,
            timeout=cls._timeout(timeout),
            max_tokens=8,
        )
        return {
            "ok": True,
            "provider": result.get("provider") or provider_name,
            "model": result.get("model") or getattr(client, "model", None),
            "finish_reason": result.get("finish_reason") or "unknown",
        }

    @classmethod
    def ensure_available(
        cls, provider: str | None = None, timeout: int | None = None
    ) -> dict:
        try:
            return cls.check(provider=provider, timeout=timeout)
        except Exception as exc:
            provider_name = provider or settings.AI_PROVIDER
            raise ValueError(
                "A IA configurada nao esta disponivel no momento "
                f"(provider: {provider_name}). Detalhes: {exc}"
            ) from exc
