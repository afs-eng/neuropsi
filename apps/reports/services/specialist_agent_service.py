import asyncio
import json
from contextlib import AsyncExitStack

from django.conf import settings
from openai import AsyncOpenAI
from pydantic_ai import Agent, PromptedOutput
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from .specialist_contracts import SpecialistOutput, validate_evidence
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
        async with AsyncExitStack() as stack:
            model = model_override
            if model is None:
                client = await stack.enter_async_context(AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=run.provider_base_url,
                    timeout=settings.SPECIALIST_AI_TIMEOUT,
                    max_retries=0,
                ))
                model = OpenAIChatModel(run.model_name, provider=OpenAIProvider(openai_client=client))
            agent = Agent(
                model,
                name=f"specialist_{run.instrument_code}",
                instructions=f"{BASE_INSTRUCTIONS}\n{instructions}",
                output_type=PromptedOutput(SpecialistOutput),
                retries=1,
                # Não encaminhar dados clínicos a plataformas de tracing.
                model_settings={"temperature": 0.1, "max_tokens": settings.SPECIALIST_AI_MAX_TOKENS},
            )
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
