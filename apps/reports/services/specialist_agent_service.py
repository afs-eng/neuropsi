import asyncio
import json
from contextlib import AsyncExitStack

from django.conf import settings
from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from pydantic_ai import Agent, ModelRetry, NativeOutput, PromptedOutput
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from .specialist_contracts import specialist_output_model, validate_evidence
from .specialist_instructions import BASE_INSTRUCTIONS, INSTRUMENT_INSTRUCTIONS


class SpecialistAgentService:
    @classmethod
    def generate(cls, run, *, model_override=None) -> tuple[dict, dict]:
        return asyncio.run(cls._generate(run, model_override=model_override))

    @staticmethod
    async def _generate(run, *, model_override=None) -> tuple[dict, dict]:
        instructions = INSTRUMENT_INSTRUCTIONS.get(run.instrument_code)
        if not instructions:
            raise ValueError("Instrumento ainda não configurado para execução.")
        from .specialist_run_service import SpecialistRunService

        configured_model, configured_url = SpecialistRunService.configuration()
        if (run.provider_name, run.model_name, run.provider_base_url) != (
            SpecialistRunService.provider_name(), configured_model, configured_url,
        ):
            raise ValueError("Configuração do provedor mudou; execução bloqueada.")
        local = run.provider_name == "ollama"
        output_model = specialist_output_model(run.instrument_code)
        model_settings = OpenAIChatModelSettings(
            temperature=0.1, max_tokens=settings.SPECIALIST_AI_MAX_TOKENS,
        )
        if local:
            model_settings["openai_reasoning_effort"] = "none"
        async with AsyncExitStack() as stack:
            model = model_override
            if model is None:
                client_options = {}
                if local:
                    client_options["http_client"] = DefaultAsyncHttpxClient(
                        trust_env=False, follow_redirects=False,
                    )
                client = await stack.enter_async_context(AsyncOpenAI(
                    api_key="ollama-local" if local else settings.OPENAI_API_KEY,
                    base_url=run.provider_base_url,
                    timeout=settings.SPECIALIST_AI_TIMEOUT,
                    max_retries=0,
                    **client_options,
                ))
                provider = OllamaProvider(openai_client=client) if local else OpenAIProvider(openai_client=client)
                model = OpenAIChatModel(run.model_name, provider=provider)
            agent = Agent(
                model,
                name=f"specialist_{run.instrument_code}",
                instructions=f"{BASE_INSTRUCTIONS}\n{instructions}",
                output_type=NativeOutput(output_model) if local else PromptedOutput(output_model),
                retries=1,
                # Não encaminhar dados clínicos a plataformas de tracing.
                model_settings=model_settings,
            )
            if run.instrument_code == "bpa2":
                @agent.output_validator
                def validate_bpa2_output(output):
                    try:
                        validate_evidence(output, run.input_payload["facts"], run.instrument_code)
                    except ValueError as exc:
                        raise ModelRetry(str(exc)) from None
                    return output
            async with asyncio.timeout(settings.SPECIALIST_AI_TIMEOUT * 2 + 30):
                result = await agent.run(
                    json.dumps(run.input_payload, ensure_ascii=False),
                    usage_limits=UsageLimits(request_limit=2, output_tokens_limit=4000),
                )
        validate_evidence(result.output, run.input_payload["facts"], run.instrument_code)
        usage = result.usage
        return result.output.model_dump(), {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "requests": usage.requests,
        }
