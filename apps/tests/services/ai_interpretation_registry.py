from __future__ import annotations

from apps.tests.ravlt.ai_interpretation import RAVLTAIInterpretationHandler


class TestAIInterpretationRegistry:
    _handlers = {
        RAVLTAIInterpretationHandler.instrument_code: RAVLTAIInterpretationHandler(),
    }

    @classmethod
    def get_handler(cls, instrument_code: str):
        return cls._handlers.get((instrument_code or "").lower())
