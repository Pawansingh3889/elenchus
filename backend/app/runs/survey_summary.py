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

**The shape is fixed, and terse.** A headline of a few words, at most three findings of
one clause each, and a caveat line, chosen so every recap reads the same way and fits
on a screen. The caveat is
computed from the report rather than written by the model (who answered, who answered
an earlier version, what was mostly declined), because the one line that qualifies the
evidence must itself be beyond question. Quotes were dropped from this recap when the
shape was fixed: the per-run summary keeps its verbatim quotes, and the report's own
question cards carry every answer in full, so nothing became unreadable.
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

from app.access import is_admin_by_config, may_edit
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.llm import ledger
from app.llm.client import LLMError, LLMProtocol
from app.llm.decoding import decode_stringified
from app.llm.factory import get_llm
from app.llm.prompts import load_prompt
from app.runs.schemas import SurveyReport
from app.runs.service import ResultsService
from app.templates.models import SurveyTemplate
from app.templates.repository import TemplateRepository
from app.users.models import User

logger = logging.getLogger("app.runs.survey_summary")

MAX_FINDINGS = 3
PROMPT_VERSION = "summarise_survey_v3"
VERIFY_PROMPT_VERSION = "verify_survey_summary_v3"

# The caps the terse shape runs on: a punchy headline and one-clause findings. A longer
# candidate is refused at validation, on the rule that a recap past its size was already
# not going to be read.
_HEADLINE_MAX = 140
_FINDING_MAX = 160

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

    statement: str = Field(min_length=1, max_length=_FINDING_MAX)
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


class SurveySummaryContent(BaseModel):
    """What the model returns. Only the headline is required, for the same reason the
    run summary requires only its own: a survey answered twice by two people who ticked
    three boxes has no findings worth listing, and padding it would be invention."""

    headline: str = Field(min_length=1, max_length=_HEADLINE_MAX)
    findings: list[Finding] = Field(default_factory=list, max_length=MAX_FINDINGS)

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
    # The evidence line, computed from the report at generation time and stored with
    # the recap. Engine numbers only: the one line that qualifies everything above it
    # must not itself be a model's claim.
    caveat: str
    # What it was generated from, so the page can say so rather than implying the recap
    # covers whatever the report happens to show today. The version used to be half of
    # this and cannot be any more: with one definition per survey, an edit to the
    # questions moves no number a stored recap can notice, so a recap can now outlive
    # the wording it described. Recorded in CLAUDE.md as the sharpest edge of dropping
    # versions.
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
    is short and its claims stand together. A recap is independent findings, and an
    all-or-nothing verdict means one bad one throws away the good ones.

    It also means a *mistaken* checker throws away everything, which is not theoretical.
    A live run refused a recap because "the tally for Q9 shows 7 said yes and 1 said no,
    which does not support a majority belief", and seven of eight is a majority. A gate
    whose false positives cost the whole feature is a gate that gets turned off; one
    whose false positives cost one line is a gate that survives contact.

    So the checker names which findings it will not stand behind, and those are dropped
    the way an unsupported quote used to be dropped. The headline is separate and is all
    or nothing: it is the one line an author reads if they read nothing else, and a
    recap whose headline is wrong has nothing worth keeping underneath it.
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
        # report() decides who may read the numbers, and that boundary now includes a
        # function colleague. Summarising is not reading: it writes a recap onto the
        # survey and spends money on a model call to do it, so it asks the narrower
        # question as well. Inheriting the read boundary alone would have let a colleague
        # attach a summary to somebody else's survey.
        report = await self.results.report(template_id, author)
        template = await self.templates.get(template_id)
        if template is None:  # pragma: no cover - report() would have raised first
            raise NotFoundError("Template not found.")
        decision = may_edit(author, template.created_by, is_admin_by_config(author))
        if not decision:
            raise ForbiddenError(decision.reason)

        if report.runs_completed == 0:
            raise ConflictError("No completed responses to summarise yet.")

        stored = self._reusable(template, report)
        if stored is not None and not refresh:
            return stored

        with ledger.measuring(None) as spend:
            content = await self._generate(report, reviewer_notes=None)
            verdict = await self._verify(report, content)
            if not verdict.clean:
                notes = "; ".join(verdict.problems)
                logger.warning(
                    "survey recap sent back to the writer: template=%s problems=%r",
                    template_id,
                    verdict.problems,
                )
                content = await self._generate(
                    report,
                    reviewer_notes=f"a reviewer compared it against the results and found: {notes}",
                )
                verdict = await self._verify(report, content)
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
            # Dropped, not refused: the rest is usually sound, `findings` has no floor,
            # so losing one costs the author a line while keeping an unsupported one
            # costs them a decision. An index that names no finding is ignored rather
            # than trusted, so a checker counting badly cannot take a real finding with
            # it by landing on the wrong one.
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
            # Computed here and stored with the recap: the numbers it states cannot
            # move while the recap is servable, because reuse is conditional on the
            # same completed-run count. The version used to be part of this key and
            # cannot be any more: a survey has one definition now, so an edit to its
            # questions no longer moves a number the reuse check can see. A recap written
            # before an edit therefore survives it, which is the sharpest edge of dropping
            # versions and is recorded in CLAUDE.md rather than hidden here.
            "caveat": _caveat(report),
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

        The prompt version is part of the condition. A recap written under an older
        shape (longer, with quotes, without the caveat line) would otherwise be served
        into a page that renders today's, for as long as nobody else answered; treating
        it as outdated invites a fresh one instead of mis-rendering an old one.
        """
        stored = template.summary
        if not isinstance(stored, dict):
            return None
        if stored.get("runs_included") != report.runs_completed:
            return None
        if stored.get("prompt_version") != PROMPT_VERSION:
            logger.info(
                "stored recap predates %s, treating as outdated: %s", PROMPT_VERSION, template.id
            )
            return None
        try:
            content = SurveySummaryContent.model_validate(stored)
        except PydanticValidationError:
            logger.warning("stored recap no longer validates, regenerating: %s", template.id)
            return None
        return _with_numbers(content, report, stored)

    async def _generate(
        self,
        report: SurveyReport,
        reviewer_notes: str | None,
    ) -> SurveySummaryContent:
        """One draft, with its own schema retry, on the pattern the run summary settled:
        the checker's notes and the schema retry are separate budgets, so a redraft is
        not born having already spent its nudge."""
        rejected: str | None = None
        for _ in range(2):
            messages = [{"role": "user", "content": _brief(report)}]
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
                    max_tokens=1024,
                )
            raw = _decode_stringified_fields(turn.tool_input)
            raw = _without_unknown_questions(raw, report)
            raw = _within_caps(raw)
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
                            f"{_brief(report)}\n\nCandidate recap:\n"
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


def _caveat(report: SurveyReport) -> str:
    """The evidence line, from the report and nowhere else.

    One sentence, identical shape every recap: coverage first, then what a reader
    should hold the findings against. Computed rather than model-written by decision:
    the caveat is the line that qualifies everything above it, so it must be beyond
    question, and every part of it is a fact the database already holds.
    """
    parts = [f"{report.people_completed} of {report.reach} answered"]
    mostly_declined = [q for q in report.questions if q.declined > q.answered]
    if mostly_declined:
        worst = max(mostly_declined, key=lambda q: q.declined)
        parts.append(f"question {worst.position + 1} was mostly declined")
    return "; ".join(parts) + "."


def _decode_stringified_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Undo one JSON-encoding of the list field, the small-model slip the generation
    path already handles. A right answer wrapped in a string is a serialization
    artifact, not a content problem, and burning the retry on it helps nobody."""
    out = dict(raw)
    if "findings" in out:
        out["findings"] = decode_stringified(out["findings"], list)
    return out


def _within_caps(raw: dict[str, Any]) -> dict[str, Any]:
    """Trim an over-long findings list to its cap instead of losing the recap over it.

    A live run threw away a sound recap twice because the model returned one item more
    than a cap allowed, so the author was told the assistant was unavailable when
    nothing was unavailable. Dropping rather than refusing is the rule this file
    already follows for a finding the checker will not stand behind; an item past the
    cap is a weaker fault than that. Only the tail is cut, so the model's own ordering
    decides what survives, which is the same order the page would have shown.
    """
    items = raw.get("findings")
    if isinstance(items, list) and len(items) > MAX_FINDINGS:
        logger.warning("recap findings over cap, trimming %d to %d", len(items), MAX_FINDINGS)
        raw = {**raw, "findings": items[:MAX_FINDINGS]}
    return raw


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
        # Required, not defaulted: every document written under PROMPT_VERSION carries
        # one, and `_reusable` refuses older documents before they reach here.
        caveat=str(document["caveat"]),
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


def _brief(report: SurveyReport) -> str:
    """What the writer and the checker both see. One extract, for the reason the run
    summary keeps one: a checker judging against more would fail sound recaps, and one
    judging against less would pass unsupported ones.

    Verbatim answers appear under their questions, unattributed. The recap carries no
    quotes any more, so nothing here needs to say who said what, and the roster of who
    works here no longer travels to the provider at all.
    """
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
    return "\n".join(lines)
