"""The off-peak batch lane: bulk jobs that can wait, at the provider's half rate.

Every OpenAI-compatible provider that offers a batch queue speaks the same
shape the OpenAI cookbook documents: one JSONL file of chat-completions
requests keyed by ``custom_id``, uploaded to ``/v1/files`` with
``purpose=batch``, a ``/v1/batches`` job created over it, completion polled,
and an output file whose lines map back to the requests in any order. The
provider prices the queue at roughly half the real-time rate because nobody
is waiting on it.

This module speaks that shape with the same discipline as the interactive
client: one typed error, an injectable transport so tests need no network,
and every answered line booked into the same token and spend ledger at the
batch rate, so an overnight run never becomes a surprise invoice or an
invisible one. Jobs that can wait — regression-gate evals, bulk survey
scoring, document backfills — belong here; anything a respondent is waiting
on does not.
"""

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.llm import ledger
from app.llm.client import LLMError
from app.llm.ledger import economics_for

logger = logging.getLogger("app.llm.batch")

BATCH_ENDPOINT = "/v1/chat/completions"
COMPLETION_WINDOW = "24h"
# The provider's published batch discount, applied to every row booked here.
# OpenAI's list price for the batch queue is half the real-time one; a
# provider that prices differently should have its rows priced by its own
# tariff, which is a reason to make this a parameter, not a hidden constant.
BATCH_COST_MULTIPLIER = 0.5

_TERMINAL_FAILURES = {"failed", "expired", "cancelled"}


class BatchError(LLMError):
    """The batch lane failed in a way worth naming separately: the tier has no
    batch queue, the job expired, or results came back unmappable."""

    code = "llm_batch_error"


@dataclass(frozen=True)
class BatchJob:
    """One request in the file. ``payload`` is the full chat-completions body
    the interactive client would send, model included."""

    custom_id: str
    payload: dict[str, Any]
    op: str = "batch"


@dataclass
class BatchResult:
    """One answered line, mapped back to its job."""

    custom_id: str
    content: str | None
    usage: dict[str, Any] | None
    status: int


@dataclass
class BatchFailure:
    custom_id: str
    detail: str


@dataclass
class BatchCollection:
    """What a finished batch handed back, and what the ledger now says."""

    batch_id: str
    succeeded: list[BatchResult] = field(default_factory=list)
    failed: list[BatchFailure] = field(default_factory=list)
    booked_rows: int = 0


def build_jsonl(jobs: Sequence[BatchJob]) -> bytes:
    """Serialise jobs to the provider's batch file format, validating locally.

    A malformed line is rejected here rather than discovered by the provider
    after the whole file is charged for: missing or duplicated ``custom_id``s
    and an empty job list are the mistakes that reach the file intact.
    """

    if not jobs:
        raise BatchError("The batch lane was given no jobs; an empty file is a rejected file.")
    seen: set[str] = set()
    lines: list[str] = []
    for job in jobs:
        if not job.custom_id:
            raise BatchError("Every batch job needs a custom_id; one is blank.")
        if job.custom_id in seen:
            raise BatchError(f"Duplicated custom_id {job.custom_id!r} in one batch file.")
        if not job.payload.get("model"):
            raise BatchError(f"Batch job {job.custom_id!r} has no model in its payload.")
        seen.add(job.custom_id)
        lines.append(
            json.dumps(
                {
                    "custom_id": job.custom_id,
                    "method": "POST",
                    "url": BATCH_ENDPOINT,
                    "body": job.payload,
                }
            )
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def parse_results(text: str) -> tuple[list[BatchResult], list[BatchFailure]]:
    """Split an output or error file into answered lines and failures.

    Lines that arrive unmappable — unparseable JSON, no ``custom_id`` — are
    counted as failures with the raw line attached, never silently dropped:
    the ledger's honesty rule applies to batch output too.
    """

    succeeded: list[BatchResult] = []
    failed: list[BatchFailure] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            failed.append(
                BatchFailure(custom_id="", detail=f"unparseable output line: {line[:120]}")
            )
            continue
        custom_id = row.get("custom_id", "")
        if not custom_id:
            failed.append(
                BatchFailure(custom_id="", detail=f"output line without custom_id: {line[:120]}")
            )
            continue
        response = row.get("response") or {}
        body = response.get("body") or {}
        status = int(response.get("status_code") or 0)
        error = row.get("error")
        if error or status >= 400:
            detail = (error or {}).get("message", "") if isinstance(error, dict) else str(error)
            failed.append(BatchFailure(custom_id=custom_id, detail=detail or f"status {status}"))
            continue
        choices = body.get("choices") or []
        content = None
        if choices:
            content = (choices[0].get("message") or {}).get("content")
        succeeded.append(
            BatchResult(
                custom_id=custom_id, content=content, usage=body.get("usage"), status=status or 200
            )
        )
    return succeeded, failed


class BatchLane:
    """The batch queue of one hosted, priced tier.

    Local tiers are refused on purpose: their marginal cost is electricity and
    wall clock, a provider queue does not apply, and a batch row priced from
    latency_ms=0 would book as free, which the ledger exists to prevent.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        tier: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not base_url or not model:
            raise BatchError("The batch lane needs the tier's base_url and model.")
        economics = economics_for(tier)
        if economics is None or economics.local:
            raise BatchError(
                f"Tier {tier} has no hosted price: the batch lane only makes sense "
                "against a hosted, priced tier."
            )
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._tier = tier
        self._transport = transport

    def _headers(self, *, json_body: bool = True) -> dict[str, str]:
        headers: dict[str, str] = {}
        if json_body:
            headers["Content-Type"] = "application/json"
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        # The file upload is multipart: httpx owns that Content-Type, boundary
        # included, so the lane only sets the JSON one for JSON bodies.
        headers = self._headers(json_body="files" not in kwargs)
        try:
            async with httpx.AsyncClient(transport=self._transport) as client:
                return await client.request(
                    method, f"{self._base_url}{path}", headers=headers, **kwargs
                )
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not reach the batch lane: {exc!r}") from exc

    async def submit(self, jobs: Sequence[BatchJob]) -> str:
        """Upload the JSONL file and create the batch job. Submission books
        nothing: the provider charges for processed lines, not for queueing."""

        content = build_jsonl(jobs)
        upload = await self._request(
            "POST",
            "/files",
            data={"purpose": "batch"},
            files={"file": ("seamly-batch.jsonl", content, "application/jsonl")},
        )
        if upload.status_code >= 400:
            raise BatchError(
                f"The batch file upload was rejected ({upload.status_code}): {upload.text[:200]}"
            )
        file_id = upload.json().get("id")
        if not file_id:
            raise BatchError(f"The batch file upload answered without an id: {upload.text[:200]}")
        created = await self._request(
            "POST",
            "/batches",
            json={
                "input_file_id": file_id,
                "endpoint": BATCH_ENDPOINT,
                "completion_window": COMPLETION_WINDOW,
            },
        )
        if created.status_code >= 400:
            raise BatchError(
                f"The batch job was rejected ({created.status_code}): {created.text[:200]}"
            )
        batch_id = created.json().get("id")
        if not batch_id:
            raise BatchError(f"The batch job was created without an id: {created.text[:200]}")
        return str(batch_id)

    async def poll(self, batch_id: str) -> dict[str, Any]:
        response = await self._request("GET", f"/batches/{batch_id}")
        if response.status_code == 404:
            raise BatchError(f"Batch {batch_id!r} is unknown to the provider.")
        if response.status_code >= 400:
            raise LLMError(
                f"Polling batch {batch_id!r} failed ({response.status_code}): {response.text[:200]}"
            )
        body: dict[str, Any] = response.json()
        return body

    async def collect(self, batch_id: str) -> BatchCollection:
        """Book a finished batch: every answered line into the ledger at the
        batch rate, every failed line named. Requires a terminal success; a
        failed or expired job is raised, not quietly returned as empty."""

        status_body = await self.poll(batch_id)
        status = str(status_body.get("status"))
        if status in _TERMINAL_FAILURES:
            raise BatchError(
                f"Batch {batch_id!r} ended in {status!r}: "
                f"{(status_body.get('error') or {}).get('message', 'no provider detail')}"
            )
        if status != "completed":
            raise BatchError(
                f"Batch {batch_id!r} is not finished (status {status!r}); "
                "collect only a completed batch."
            )
        output_file_id = status_body.get("output_file_id")
        if not output_file_id:
            raise BatchError(f"Batch {batch_id!r} completed without an output file.")

        output = await self._request("GET", f"/files/{output_file_id}/content")
        if output.status_code >= 400:
            raise LLMError(
                f"Downloading batch output {output_file_id!r} failed "
                f"({output.status_code}): {output.text[:200]}"
            )
        succeeded, failed = parse_results(output.text)

        collection = BatchCollection(batch_id=batch_id)
        for result in succeeded:
            ledger.record(
                tier=self._tier,
                model=self._model,
                op="batch",
                usage=result.usage,
                latency_ms=0,
                status=result.status,
                error=None,
                cost_multiplier=BATCH_COST_MULTIPLIER,
            )
            collection.succeeded.append(result)
            collection.booked_rows += 1
        collection.failed = failed

        error_file_id = status_body.get("error_file_id")
        if error_file_id:
            error_file = await self._request("GET", f"/files/{error_file_id}/content")
            if error_file.status_code < 400:
                _, provider_failures = parse_results(error_file.text)
                known = {f.custom_id for f in collection.failed}
                for provider_failure in provider_failures:
                    if provider_failure.custom_id not in known:
                        collection.failed.append(provider_failure)

        logger.info(
            "batch %s collected: %d answered, %d failed, %d ledger rows",
            batch_id,
            len(collection.succeeded),
            len(collection.failed),
            collection.booked_rows,
        )
        return collection
