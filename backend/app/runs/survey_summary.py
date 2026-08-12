"""The author-facing recap of a whole survey.

``summary.py`` summarises one response. This summarises all of them, which is the
question a survey is actually run to answer and the one an author with forty
respondents cannot get by reading forty runs.

Three things make it different from the per-run summary, and each is a decision rather
than a detail.

**The model never writes a number.** Every count on this page comes from
``ResultsService.report``, which reads them out of the database. A finding names the
pattern and the question it draws on; the tally is attached to it afterwards, from the
report. So a figure cannot be wrong, because the model was never asked for one, and
``Finding`` refuses a statement containing digits rather than trusting it not to. That
rail exists because the invented denominator is the failure this codebase has already
seen: a run rated 5 on a scale of 1 to 5 was summarised as "5 out of 10", and the value
was real, only the scale was invented, so no checker could catch it.

**The cache can go wrong, unlike the run one.** A completed run never changes, so
``survey_runs.summary`` is a cache that is always right. A survey's responses keep
arriving. A recap generated from eight responses and served after twenty have landed is
not stale, it is wrong, and the prose gives no sign of it. So the stored document carries
the version and completed-run count it was made from, and anything else regenerates.

**A quote has to say who said it.** In one run the respondent is not in question. Across
a survey, "we still count stock on paper" means something different from one person and
from six, so a quote carries the question it answered and the person who gave it, and is
dropped unless it is a verbatim span of what that person actually said.
"""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError, NotFoundError
from app.llm import ledger
from app.llm.client import LLMError, LLMProtocol
from app.llm.decoding import decode_stringified
from app.llm.factory import get_llm
from app.llm.prompts import load_prompt
from app.runs.enums import AnswerKind, RunStatus
from app.runs.repository import ResultsRepository
from app.runs.schemas import SurveyReport
from app.runs.service import ResultsService, flatten_answer, respondent_label
from app.templates.models import SurveyTemplate
from app.templates.repository import TemplateRepository
from app.users.models import User

logger = logging.getLogger("app.runs.survey_summary")

MAX_FINDINGS = 6
MAX_QUOTES = 6
PROMPT_VERSION = "summarise_survey_v1"
VERIFY_PROMPT_VERSION = "verify_survey_summary_v1"

# A statement is the pattern in words. Digits in it are a number the model wrote, and
# every number on this page is supposed to come from the report instead.
_DIGITS = re.compile(r"\d")


class Finding(BaseModel):
    """One thing the survey found, and the question it comes from.

    ``statement`` is prose with no figures in it. ``question_position`` is how the tally
    gets attached: the model says which question it is reading, the service looks the
    counts up, and the page renders the two together. A finding that points at no
    question is not refused, because a real pattern can cross several ("the day shift
    reports worse on every question"), and forcing one would make the model pick
    arbitrarily.
    """

    statement: str = Field(min_length=1, max_length=400)
    question_position: int | None = None

    @field_validator("statement")
    @classmethod
    def _no_numbers(cls, value: str) -> str:
        statement = value.strip()
        if not statement:
            raise ValueError("a finding cannot be blank")
        if _DIGITS.search(statement):
            raise ValueError(
                "a finding must not contain figures: describe the pattern in words "
                "('most respondents', 'only one person') and the counts are attached "
                "from the results automatically"
            )
        return statement


class SurveyQuote(BaseModel):
    question: str = Field(min_length=1)
    respondent: str = Field(min_length=1)
    quote: str = Field(min_length=1)

    @field_validator("question", "respondent", "quote")
    @classmethod
    def _has_content(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("cannot be blank")
        return text


class SurveySummaryContent(BaseModel):
    """What the model returns. Only the headline is required, for the same reason the
    run summary requires only its own: a survey answered twice by two people who ticked
    three boxes has no findings worth listing, and padding it would be invention."""

    headline: str = Field(min_length=1, max_length=300)
    findings: list[Finding] = Field(default_factory=list, max_length=MAX_FINDINGS)
    notable_quotes: list[SurveyQuote] = Field(default_factory=list, max_length=MAX_QUOTES)

    @field_validator("headline")
    @classmethod
    def _headline_has_content(cls, value: str) -> str:
        headline = value.strip()
        if not headline:
            raise ValueError("headline cannot be blank")
        return headline


class FindingRead(Finding):
    """A finding as the author reads it: the model's words, the database's numbers."""

    question_text: str | None = None
    answered: int | None = None
    counts: list[dict[str, Any]] = Field(default_factory=list)
    average: float | None = None


class SurveySummaryRead(BaseModel):
    headline: str
    findings: list[FindingRead]
    notable_quotes: list[SurveyQuote]
    # What it was generated from, so the page can say so rather than implying the recap
    # covers whatever the report happens to show today.
    version: int
    runs_included: int
    generated_at: str
    # Provenance, already stored in the document and until now readable only by opening
    # the column. A recap that reads worse than it used to may be a prompt change or a
    # model change, and the author looking at it can see which without asking.
    prompt_version: str | None = None
    verify_prompt_version: str | None = None
    model: str | None = None


class SurveyRecapStatus(BaseModel):
    """The stored recap if it is still true of the results, else why there is none.

    An envelope rather than a 404, because neither absence is an error: a survey nobody
    has summarised yet is healthy, and a recap the results have moved past is a thing
    the page wants to say out loud ("written when 4 people had answered; 7 have now")
    rather than a missing resource.
    """

    recap: SurveySummaryRead | None = None
    absence: Literal["never_generated", "outdated"] | None = None


_TOOL: dict[str, Any] = {
    "name": "summarise_survey",
    "description": "Return what this survey found across every response, as structured data.",
    "input_schema": SurveySummaryContent.model_json_schema(),
}


class SurveyVerdict(BaseModel):
    """The checker's verdict, shaped so a wrong finding costs one finding.

    The run summary's verdict is all-or-nothing, and that is right there: a run summary
    is short and its claims stand together. A recap is six independent findings, and an
    all-or-nothing verdict means one bad one throws away five good ones.

    It also means a *mistaken* checker throws away everything, which is not theoretical.
    A live run refused a recap because "the tally for Q9 shows 7 said yes and 1 said no,
    which does not support a majority belief", and seven of eight is a majority. A gate
    whose false positives cost the whole feature is a gate that gets turned off; one
    whose false positives cost one line is a gate that survives contact.

    So the checker names which findings it will not stand behind, and those are dropped
    the way an unsupported quote is dropped. The headline is separate and is all or
    nothing: it is the one line an author reads if they read nothing else, and a recap
    whose headline is wrong has nothing worth keeping underneath it.
    """

    headline_supported: bool = True
    unsupported_findings: list[int] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("problems")
    @classmethod
    def _problems_are_readable(cls, values: list[str]) -> list[str]:
        return [v.strip().lstrip("-•* ").strip() for v in values if v.strip()]

    @property
    def clean(self) -> bool:
        return self.headline_supported and not self.unsupported_findings


_VERIFY_TOOL: dict[str, Any] = {
    "name": "report_verdict",
    "description": "Report which parts of the candidate recap the results do not support.",
    "input_schema": SurveyVerdict.model_json_schema(),
}


class SurveySummaryService:
    def __init__(
        self,
        session: AsyncSession,
        llm: LLMProtocol | None = None,
        verifier: LLMProtocol | None = None,
    ) -> None:
        self.session = session
        self._llm = llm
        self._verifier = verifier
        self.results = ResultsService(session)
        self.repo = ResultsRepository(session)
        self.templates = TemplateRepository(session)

    @property
    def llm(self) -> LLMProtocol:
        """Built on first use, so reading a stored recap needs no model."""
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    @property
    def verifier(self) -> LLMProtocol:
        if self._verifier is None:
            self._verifier = self.llm
        return self._verifier

    async def stored(self, template_id: UUID, author: User) -> SurveyRecapStatus:
        """The recap this survey already has, without writing a new one.

        The page needs this because generating is the only way it could read a recap
        before, so navigating away and back cost a model call to see prose that was
        already sitting in the column. Nothing here builds an LLM: the `llm` property
        is lazy precisely so a read costs no key.
        """
        # report() does the ownership check, so this inherits the numbers' boundary.
        report = await self.results.report(template_id, author)
        template = await self.templates.get(template_id)
        if template is None:  # pragma: no cover - report() would have raised first
            raise NotFoundError("Template not found.")

        recap = self._reusable(template, report)
        if recap is not None:
            return SurveyRecapStatus(recap=recap, absence=None)
        # Two different absences, and the page says different things about them: one
        # invites a first recap, the other says the results have moved past the one
        # that exists.
        absence = "never_generated" if template.summary is None else "outdated"
        return SurveyRecapStatus(recap=None, absence=absence)

    async def summarise(
        self, template_id: UUID, author: User, refresh: bool = False
    ) -> SurveySummaryRead:
        # report() does the ownership check and raises NotFoundError for someone else's
        # survey, so the recap inherits exactly the boundary the numbers have.
        report = await self.results.report(template_id, author)
        template = await self.templates.get(template_id)
        if template is None:  # pragma: no cover - report() would have raised first
            raise NotFoundError("Template not found.")

        if report.runs_completed == 0:
            raise ConflictError("No completed responses to summarise yet.")

        stored = self._reusable(template, report)
        if stored is not None and not refresh:
            return stored

        version = await self.templates.latest_version(template_id)
        if version is None:  # pragma: no cover - report() would have raised first
            raise ConflictError("This survey has no published version to summarise.")
        quotable = await self._quotable(template_id, version.id)
        with ledger.measuring(None) as spend:
            content = await self._generate(report, quotable, reviewer_notes=None)
            verdict = await self._verify(report, quotable, content)
            if not verdict.clean:
                notes = "; ".join(verdict.problems)
                logger.warning(
                    "survey recap sent back to the writer: template=%s problems=%r",
                    template_id,
                    verdict.problems,
                )
                content = await self._generate(
                    report,
                    quotable,
                    reviewer_notes=f"a reviewer compared it against the results and found: {notes}",
                )
                verdict = await self._verify(report, quotable, content)
        logger.info(
            "survey recap generated: template=%s calls=%s tokens=%s",
            template_id,
            spend.calls,
            spend.prompt_tokens + spend.completion_tokens,
        )
        if not verdict.headline_supported:
            # Nothing stored, for the reason the run summary stores nothing: an
            # unsupported recap sitting above the real numbers is worse than no recap.
            #
            # ConflictError, not LLMError. Every model call succeeded, and the recap was
            # refused on its merits by the checker. LLMError renders as 503 "the
            # assistant is briefly unavailable, try again in a moment", which tells the
            # author to retry something that will fail the same way and hides the one
            # thing worth reading, which is why it was refused. A live run produced
            # exactly that: two rounds of "says most stoppages are logged, but Q7 shows
            # 5 yes and 3 no", reported to the client as an outage. The run summary
            # refuses the same way now.
            logger.error(
                "survey recap failed verification twice: template=%s problems=%r",
                template_id,
                verdict.problems,
            )
            raise ConflictError(
                "The recap did not hold up against the numbers, so it was not saved: "
                + "; ".join(verdict.problems)
            )

        dropped = sorted(
            {i for i in verdict.unsupported_findings if 0 <= i < len(content.findings)}
        )
        if dropped:
            # Dropped, not refused, on the rule the quote gate already uses: the rest is
            # usually sound, `findings` has no floor, so losing one costs the author a
            # line while keeping an unsupported one costs them a decision. An index that
            # names no finding is ignored rather than trusted, so a checker counting badly
            # cannot take a real finding with it by landing on the wrong one.
            logger.warning(
                "dropped unsupported findings: template=%s indices=%r problems=%r",
                template_id,
                dropped,
                verdict.problems,
            )
            keep = set(dropped)
            content = content.model_copy(
                update={"findings": [f for i, f in enumerate(content.findings) if i not in keep]}
            )

        document = {
            **content.model_dump(),
            "version": report.version,
            "runs_included": report.runs_completed,
            "prompt_version": PROMPT_VERSION,
            "verify_prompt_version": VERIFY_PROMPT_VERSION,
            # The tier that wrote it, for the same reason the run summary records one: a
            # recap that reads worse than it used to may be a prompt change or a model
            # change, and without this only one of the two can be ruled out.
            "model": spend.last_model,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        template.summary = document
        await self.session.commit()
        return _with_numbers(content, report, document)

    def _reusable(self, template: SurveyTemplate, report: SurveyReport) -> SurveySummaryRead | None:
        """The stored recap, but only while it is still true of the results.

        Not merely a cache check. The per-run summary caches something immutable; this
        describes a moving set of responses, so reuse is conditional on the version and
        the completed-run count both being what they were. Anything else and the numbers
        beside the prose would have moved out from under it.
        """
        stored = template.summary
        if not isinstance(stored, dict):
            return None
        if stored.get("version") != report.version:
            return None
        if stored.get("runs_included") != report.runs_completed:
            return None
        try:
            content = SurveySummaryContent.model_validate(stored)
        except PydanticValidationError:
            logger.warning("stored recap no longer validates, regenerating: %s", template.id)
            return None
        return _with_numbers(content, report, stored)

    async def _quotable(self, template_id: UUID, version_id: UUID) -> list[dict[str, str]]:
        """Every answer a quote could legitimately come from, with who gave it.

        Read from the runs rather than the report, because the report's verbatim list has
        already dropped the attribution, and a quote with no name is the one thing this
        summary must not produce.

        Scoped to completed runs on the version the report counted, so the words and the
        numbers describe the same set of people. A quote from someone whose answers are
        excluded from every tally would be evidence for a finding the counts contradict.

        Whose words they are is carried as the survey's own pseudonym, not the person's
        name. The attribution mechanism is unchanged and needs no name to work: it needs
        one stable key per person, which is what the number gives it. What changes is that
        the provider is no longer sent a roster of who works here alongside what each of
        them said about their employer, and the recap the author reads attributes a
        complaint to Respondent 3 rather than naming a colleague.
        """
        numbers = await self.repo.respondent_numbers(template_id)
        out: list[dict[str, str]] = []
        for run, version, _ in await self.repo.list_for_template(template_id):
            if version.id != version_id or run.status is not RunStatus.completed:
                continue
            for answer in run.answers:
                text = flatten_answer(answer.value)
                if "unanswerable" in answer.value or not text.strip():
                    continue
                out.append(
                    {
                        "respondent": respondent_label(numbers[run.respondent_id]),
                        "question": answer.question_text,
                        "answer": text,
                        "kind": answer.kind.value,
                    }
                )
        return out

    async def _generate(
        self,
        report: SurveyReport,
        quotable: list[dict[str, str]],
        reviewer_notes: str | None,
    ) -> SurveySummaryContent:
        """One draft, with its own schema retry, on the pattern the run summary settled:
        the checker's notes and the schema retry are separate budgets, so a redraft is
        not born having already spent its nudge."""
        rejected: str | None = None
        for _ in range(2):
            messages = [{"role": "user", "content": _brief(report, quotable)}]
            feedback = "; ".join(filter(None, (reviewer_notes, rejected)))
            if feedback:
                messages.append(
                    {
                        "role": "user",
                        "content": f"Your previous recap was rejected: {feedback}\n"
                        "Return a corrected recap.",
                    }
                )
            with ledger.using_prompt(PROMPT_VERSION):
                turn = await self.llm.tool_turn(
                    system=load_prompt(PROMPT_VERSION),
                    messages=messages,
                    tools=[_TOOL],
                    max_tokens=2048,
                )
            raw = _decode_stringified_fields(turn.tool_input)
            raw = _without_invented_quotes(raw, quotable)
            raw = _without_unknown_questions(raw, report)
            try:
                return SurveySummaryContent.model_validate(raw)
            except PydanticValidationError as exc:
                if rejected is not None:
                    logger.error("survey recap failed after one retry: raw=%r error=%s", raw, exc)
                    raise LLMError(
                        f"Model returned an invalid recap after one retry: {exc}"
                    ) from exc
                rejected = str(exc)
                logger.warning("survey recap rejected, retrying: error=%s", exc)
        raise LLMError("unreachable")  # the loop either returns or raises

    async def _verify(
        self,
        report: SurveyReport,
        quotable: list[dict[str, str]],
        content: SurveySummaryContent,
    ) -> SurveyVerdict:
        """Fresh context, like the run checker: the results and the candidate, and
        nothing of how the draft was made."""
        with ledger.using_prompt(VERIFY_PROMPT_VERSION):
            turn = await self.verifier.tool_turn(
                system=load_prompt(VERIFY_PROMPT_VERSION),
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"{_brief(report, quotable)}\n\nCandidate recap:\n"
                            f"{json.dumps(content.model_dump(), ensure_ascii=False, indent=2)}"
                        ),
                    }
                ],
                tools=[_VERIFY_TOOL],
                max_tokens=1024,
            )
        raw = dict(turn.tool_input)
        for key in ("problems", "unsupported_findings"):
            if key in raw:
                raw[key] = decode_stringified(raw[key], list)
        try:
            return SurveyVerdict.model_validate(raw)
        except PydanticValidationError as exc:
            logger.error("recap checker returned an invalid verdict: raw=%r error=%s", raw, exc)
            raise LLMError(f"The recap checker returned an invalid verdict: {exc}") from exc


# ------------------------------------------------------------------------- helpers


def _decode_stringified_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Undo one JSON-encoding of the list fields, the small-model slip the generation
    path already handles. A right answer wrapped in a string is a serialization
    artifact, not a content problem, and burning the retry on it helps nobody."""
    out = dict(raw)
    for key in ("findings", "notable_quotes"):
        if key in out:
            out[key] = decode_stringified(out[key], list)
    return out


def _normalised(text: str) -> str:
    return " ".join(text.split()).casefold()


def _without_invented_quotes(raw: dict[str, Any], quotable: list[dict[str, str]]) -> dict[str, Any]:
    """Drop any quote that is not a verbatim span of what that named person said.

    Stricter than the per-run gate on purpose. There, the run fixes whose words they are;
    here the model supplies the name too, so a quote can be real and attributed to the
    wrong person, which is worse than an invented one: it is evidence, and it points at a
    colleague. Matched against that respondent's answers alone.
    """
    quotes = raw.get("notable_quotes")
    if not isinstance(quotes, list) or not quotes:
        return raw
    by_person: dict[str, str] = {}
    for row in quotable:
        key = _normalised(row["respondent"])
        by_person[key] = f"{by_person.get(key, '')}   {_normalised(row['answer'])}"

    kept: list[Any] = []
    for quote in quotes:
        if not isinstance(quote, dict):
            continue
        text = quote.get("quote")
        who = quote.get("respondent")
        said = by_person.get(_normalised(str(who))) if isinstance(who, str) else None
        if isinstance(text, str) and said and _normalised(text) and _normalised(text) in said:
            kept.append(quote)
        else:
            logger.warning("dropped an unsupported quote: respondent=%r quote=%r", who, text)
    return {**raw, "notable_quotes": kept}


def _without_unknown_questions(raw: dict[str, Any], report: SurveyReport) -> dict[str, Any]:
    """Unpoint any finding aimed at a question that does not exist.

    Unpointed rather than dropped: the statement may be a real pattern and only the
    reference wrong, and a finding with no tally beside it is still readable. Attaching
    the wrong question's counts to it would not be.
    """
    findings = raw.get("findings")
    if not isinstance(findings, list) or not findings:
        return raw
    positions = {q.position for q in report.questions}
    out: list[Any] = []
    for finding in findings:
        if isinstance(finding, dict) and finding.get("question_position") not in positions:
            if finding.get("question_position") is not None:
                logger.warning("finding pointed at no such question: %r", finding)
            finding = {**finding, "question_position": None}
        out.append(finding)
    return {**raw, "findings": out}


def _with_numbers(
    content: SurveySummaryContent, report: SurveyReport, document: dict[str, Any]
) -> SurveySummaryRead:
    """Attach the real tallies. This is the whole point of `question_position`: the model
    said what the pattern is, and the numbers beside it come from the database."""
    by_position = {q.position: q for q in report.questions}
    findings = []
    for finding in content.findings:
        # `is None`, not `or`: position 0 is the first question and it is falsy, so the
        # short form silently unpointed every finding about it.
        position = finding.question_position
        question = None if position is None else by_position.get(position)
        findings.append(
            FindingRead(
                statement=finding.statement,
                question_position=finding.question_position,
                question_text=question.text if question else None,
                answered=question.answered if question else None,
                counts=[c.model_dump() for c in question.counts] if question else [],
                average=question.average if question else None,
            )
        )
    return SurveySummaryRead(
        headline=content.headline,
        findings=findings,
        notable_quotes=content.notable_quotes,
        version=int(document["version"]),
        runs_included=int(document["runs_included"]),
        generated_at=str(document["generated_at"]),
        # Optional metadata, so `.get` is honest here rather than a shrug over required
        # data: a recap written before these were recorded has none, and that is a fact
        # about the document, not a failure to read it.
        prompt_version=_optional_str(document.get("prompt_version")),
        verify_prompt_version=_optional_str(document.get("verify_prompt_version")),
        model=_optional_str(document.get("model")),
    )


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _brief(report: SurveyReport, quotable: list[dict[str, str]]) -> str:
    """What the writer and the checker both see. One extract, for the reason the run
    summary keeps one: a checker judging against more would fail sound recaps, and one
    judging against less would pass unsupported ones."""
    lines = [
        f"Survey: {report.title}",
        f"Responses: {report.runs_completed} completed of {report.people_started} started, "
        f"from an audience of {report.reach}.",
        "",
        "RESULTS, question by question. These counts are the truth; do not restate them "
        "as figures in your findings.",
    ]
    for question in report.questions:
        lines.append("")
        lines.append(f"Q{question.position + 1}. {question.text}  [{question.answer_type.value}]")
        lines.append(f"  answered {question.answered}, declined {question.declined}")
        if question.average is not None:
            lines.append(f"  average {question.average:.2f}")
        for count in question.counts:
            mark = " (write-in)" if count.write_in else ""
            lines.append(f"  {count.label}: {count.count}{mark}")
        for text in question.verbatim:
            lines.append(f"  answer: {text}")
        for text in question.follow_ups:
            lines.append(f"  follow-up answer: {text}")

    lines.append("")
    lines.append(
        "WHO SAID WHAT. Quote only from here, word for word, and attribute to the name "
        "shown. A quote that is not a verbatim span of that person's answer is dropped."
    )
    for row in quotable:
        marker = " (follow-up)" if row["kind"] == AnswerKind.follow_up.value else ""
        lines.append(f"  {row['respondent']} on \"{row['question']}\"{marker}: {row['answer']}")
    return "\n".join(lines)
