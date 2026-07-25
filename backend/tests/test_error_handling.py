"""An exhausted or failing LLM reads as a calm 503, never a raw provider error.

Exercises the registered exception handler directly — no database or network — so it
stays fast and asserts exactly what a caller receives.
"""

import json

from starlette.requests import Request

from app.llm.client import LLMError, NoToolCallError
from app.main import app


def _request() -> Request:
    return Request({"type": "http", "method": "POST", "path": "/api/v1/runs", "headers": []})


async def test_llm_failure_becomes_a_calm_503_without_raw_detail():
    handler = app.exception_handlers[LLMError]
    raw = 'Backup LLM rejected the request (429): {"error":{"code":429,"message":"quota exceeded"}}'

    response = await handler(_request(), LLMError(raw))
    body = json.loads(response.body)

    assert response.status_code == 503
    assert body["error"]["code"] == "llm_unavailable"
    assert "unavailable" in body["error"]["message"].lower()
    # the raw upstream detail never reaches the respondent
    assert "429" not in body["error"]["message"]
    assert "quota" not in body["error"]["message"].lower()


def test_llm_error_subclasses_resolve_to_the_same_handler():
    # Starlette matches on the exception's MRO, so a NoToolCallError (a subclass of
    # LLMError) lands on the LLMError handler too, not the generic AppError one.
    assert issubclass(NoToolCallError, LLMError)
    assert LLMError in app.exception_handlers
