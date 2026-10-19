import asyncio
import json
from contextlib import AsyncExitStack

from django.conf import settings
from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from pydantic_ai import Agent, ModelRetry, NativeOutput, PromptedOutput, capture_run_messages
from pydantic_ai.messages import ModelResponse
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import RunUsage, UsageLimits

from .specialist_contracts import bpa2_generation_model, specialist_output_model, validate_evidence
from .bpa2_specialist import validate_bpa2_editorial_layout
from .specialist_errors import SpecialistGenerationError, SpecialistValidationError, generation_error_code
from .specialist_instructions import BASE_INSTRUCTIONS, INSTRUMENT_INSTRUCTIONS


def _last_finish_reason(messages, request_count):
    responses = [message for message in messages if isinstance(message, ModelResponse)]
    # Apenas respostas desta execução; falhas de transporte são tratadas à parte.
    return responses[-1].finish_reason if responses and len(responses) == request_count else None


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
        max_output_tokens = settings.SPECIALIST_OLLAMA_MAX_TOKENS if local else settings.SPECIALIST_AI_MAX_TOKENS
        output_model = specialist_output_model(run.instrument_code)
        if local and run.instrument_code == "bpa2":
            output_model = bpa2_generation_model(run.input_payload["facts"])
        model_settings = OpenAIChatModelSettings(
            temperature=0.1, max_tokens=max_output_tokens,
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
            usage = RunUsage()
            last_validation_code = None
            last_validation_section = None
            last_validation_request = None
            if run.instrument_code == "bpa2":
                @agent.output_validator
                def validate_bpa2_output(output):
                    nonlocal last_validation_code, last_validation_request, last_validation_section
                    last_validation_code = None
                    last_validation_section = None
                    last_validation_request = usage.requests
                    try:
                        validate_evidence(output, run.input_payload["facts"], run.instrument_code)
                        validate_bpa2_editorial_layout(output)
                    except ValueError as exc:
                        if isinstance(exc, SpecialistValidationError):
                            last_validation_code = exc.code
                            last_validation_section = exc.section
                            if exc.code == "evidence_not_found":
                                raise ModelRetry(
                                    "evidence_ids deve conter apenas chaves EXATAS de facts. "
                                    "Não use nomes de componentes, caminhos do reading_guide nem valores. "
                                    "Consulte component_evidence_ids e copie os IDs apontados, "
                                    "incluindo / inicial e índices numéricos. IDs permitidos: "
                                    + json.dumps(sorted(run.input_payload["facts"]), ensure_ascii=False)
                                ) from None
                        raise ModelRetry(str(exc)) from None
                    return output
            with capture_run_messages() as messages:
                try:
                    async with asyncio.timeout(settings.SPECIALIST_AI_TIMEOUT * 2 + 30):
                        result = await agent.run(
                            json.dumps(run.input_payload, ensure_ascii=False),
                            usage_limits=UsageLimits(request_limit=2, output_tokens_limit=max_output_tokens * 2),
                            usage=usage,
                        )
                    finish_reason = _last_finish_reason(messages, usage.requests)
                    if finish_reason in {"length", "content_filter"}:
                        raise SpecialistGenerationError(
                            "output_truncated" if finish_reason == "length" else "provider_refusal",
                            usage=usage, finish_reason=finish_reason,
                        )
                    validate_evidence(result.output, run.input_payload["facts"], run.instrument_code)
                except SpecialistGenerationError:
                    raise
                except Exception as exc:
                    finish_reason = _last_finish_reason(messages, usage.requests)
                    validation_code = exc.code if isinstance(exc, SpecialistValidationError) else (
                        last_validation_code if last_validation_request == usage.requests else None
                    )
                    validation_section = exc.section if isinstance(exc, SpecialistValidationError) else (
                        last_validation_section if last_validation_request == usage.requests else None
                    )
                    code = generation_error_code(exc, finish_reason=finish_reason, validation_code=validation_code)
                    if code in {
                        "provider_timeout", "provider_connection", "provider_auth", "provider_rate_limit",
                        "provider_error", "usage_limit_exceeded",
                    }:
                        finish_reason = None
                    if code != "output_validation_failed":
                        validation_code = None
                        validation_section = None
                    raise SpecialistGenerationError(
                        code, usage=usage, finish_reason=finish_reason, validation_code=validation_code,
                        validation_section=validation_section,
                    ) from None
        usage = result.usage
        return result.output.model_dump(), {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "requests": usage.requests,
        }
