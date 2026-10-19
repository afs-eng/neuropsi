from openai import APIConnectionError, APIStatusError, APITimeoutError
from pydantic import ValidationError
from pydantic_ai.exceptions import ContentFilterError, ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded


VALIDATION_CODES = {
    "evidence_not_found", "ungrounded_number", "bpa2_semantics",
    "bpa2_missing_evidence", "bpa2_score_text", "invalid_schema",
}
GENERATION_CODES = {
    "output_validation_failed", "output_schema_invalid", "output_truncated", "provider_refusal",
    "provider_timeout", "provider_connection", "provider_rate_limit", "provider_auth",
    "provider_error", "usage_limit_exceeded", "generation_failed",
}
VALIDATION_SECTIONS = {"introducao", "ac", "ad", "aa", "ag", "analise_clinica"}


class SpecialistValidationError(ValueError):
    def __init__(self, code: str, message: str, *, section=None):
        self.code = code if code in VALIDATION_CODES else "invalid_schema"
        self.section = section if isinstance(section, str) and section in VALIDATION_SECTIONS else None
        super().__init__(message)


class SpecialistGenerationError(Exception):
    """Somente metadados selecionados; nunca inclui texto de exceções/respostas."""

    def __init__(self, code: str, *, usage=None, finish_reason=None, validation_code=None, validation_section=None):
        self.code = code if code in GENERATION_CODES else "generation_failed"
        self.diagnostics = safe_diagnostics(usage, finish_reason, validation_code, validation_section)
        super().__init__(self.code)


def safe_diagnostics(usage=None, finish_reason=None, validation_code=None, validation_section=None) -> dict:
    diagnostics = {}
    for key in ("requests", "input_tokens", "output_tokens"):
        value = getattr(usage, key, None)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            diagnostics[key] = value
    if isinstance(finish_reason, str) and finish_reason in {"stop", "length", "content_filter", "tool_call", "error"}:
        diagnostics["finish_reason"] = finish_reason
    if isinstance(validation_code, str) and validation_code in VALIDATION_CODES:
        diagnostics["validation_code"] = validation_code
        if isinstance(validation_section, str) and validation_section in VALIDATION_SECTIONS:
            diagnostics["validation_section"] = validation_section
    return diagnostics


def generation_error_code(exc: Exception, *, finish_reason=None, validation_code=None) -> str:
    seen = set()
    current = exc
    schema_error = False
    evidence_error = False
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, (APITimeoutError, TimeoutError)):
            return "provider_timeout"
        if isinstance(current, APIConnectionError):
            return "provider_connection"
        if isinstance(current, (APIStatusError, ModelHTTPError)):
            status = current.status_code
            if status in {401, 403}:
                return "provider_auth"
            if status == 429:
                return "provider_rate_limit"
            return "provider_error"
        if isinstance(current, ContentFilterError):
            return "provider_refusal"
        if isinstance(current, UsageLimitExceeded):
            return "usage_limit_exceeded"
        if isinstance(current, SpecialistValidationError):
            evidence_error = True
        if isinstance(current, (ValidationError, UnexpectedModelBehavior)):
            schema_error = True
        current = current.__cause__
    if finish_reason == "length":
        return "output_truncated"
    if finish_reason == "content_filter":
        return "provider_refusal"
    if validation_code in VALIDATION_CODES or evidence_error:
        return "output_validation_failed"
    if schema_error:
        return "output_schema_invalid"
    return "generation_failed"
