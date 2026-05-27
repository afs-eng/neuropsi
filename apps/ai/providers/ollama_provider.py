import requests

from .base import BaseAIProvider


class OllamaProvider(BaseAIProvider):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> dict:
        timeout = kwargs.get("timeout", 180)
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": kwargs.get("model") or self.model,
                "system": system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.2),
                },
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        raw = (data.get("response") or "").strip()
        import re
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        return {
            "content": raw,
            "provider": "ollama",
            "model": data.get("model") or self.model,
            "finish_reason": "stop" if data.get("done") else "unknown",
            "usage": {
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
            },
            "warnings": [],
        }

    def check_available(self, timeout: int = 10) -> dict:
        response = requests.get(f"{self.base_url}/api/tags", timeout=timeout)
        response.raise_for_status()
        data = response.json()
        models = data.get("models") or []
        model_names = {item.get("name") for item in models if item.get("name")}
        if self.model not in model_names:
            raise ValueError(
                f"Modelo Ollama '{self.model}' nao esta instalado. Modelos disponiveis: {', '.join(sorted(model_names)) or 'nenhum'}."
            )
        return {
            "ok": True,
            "provider": "ollama",
            "model": self.model,
            "finish_reason": "ready",
        }
