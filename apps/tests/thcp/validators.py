from pydantic import ValidationError

from apps.tests.base.types import TestContext

from .schemas import THCPRawInput


def validate_thcp_input(context: TestContext) -> list[str]:
    errors = []
    if not 4 <= context.patient_age <= 7:
        errors.append("O THCP pode ser aplicado apenas entre 4 e 7 anos; informe a data de nascimento.")
    try:
        THCPRawInput.model_validate(context.raw_scores)
    except ValidationError as exc:
        errors.extend(f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors())
    return errors
