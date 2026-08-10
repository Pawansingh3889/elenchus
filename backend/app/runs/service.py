"""Reading run results back for authors.

Deliberately separate from the conduct engine: conducting is respondent-owned and
refuses anyone else, while results are author-facing and cross-respondent.
"""

import csv
import io
import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access import in_audience, is_admin_by_config, may_list, may_read_rows
from app.errors import NotFoundError
from app.runs.enums import AnswerKind, RunStatus
from app.runs.models import REPLY_PREFIX, SurveyRun
from app.runs.repository import ResultsRepository
from app.runs.schemas import (
    AnswerRead,
    DashboardRow,
    MessageRead,
    OptionCount,
    QuestionReport,
    RunDetail,
    RunSummary,
    SurveyReport,
)
from app.templates.enums import SurveyAudience
from app.templates.models import SurveyTemplate, SurveyTemplateVersion
from app.templates.repository import TemplateRepository
from app.templates.snapshot import questions_of
from app.templates.visibility import remaining_possible
from app.users.models import User
from app.users.repository import UserRepository

logger = logging.getLogger("app.runs.results")

EXPORT_COLUMNS = [
    "run_id",
    "respondent",
    "run_status",
    "version",
    "question",
    "kind",
    "answer",
    "answered_at",
]


class ResultsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ResultsRepository(session)
        self.templates = TemplateRepository(session)
        self.users = UserRepository(session)

    async def dashboard(self, author: User) -> list[DashboardRow]:
        """Every survey this author owns, with how each one is going.

        Author-scoped in the query rather than filtered afterwards, so another author's
        survey is never loaded in the first place.
        """
        rows = await self.repo.dashboard_rows(author.id)
        admin = is_admin_by_config(author)
        reach = await self._reach_by_audience()
        return [
            DashboardRow(
                id=template.id,
                title=template.title,
                status=template.status,
                updated_at=template.updated_at,
                closed_at=template.closed_at,
                started=started,
                completed=completed,
                in_progress=in_progress,
                abandoned=abandoned,
                reach=reach.get(template.audience, 0),
                people_started=people_started,
                people_completed=people_completed,
                last_started_at=last_started_at,
                last_completed_at=last_completed_at,
            )
            for (
                template,
                started,
                completed,
                in_progress,
                abandoned,
                people_started,
                people_completed,
                last_started_at,
                last_completed_at,
            ) in rows
            if may_list(author, template.audience, template.created_by, admin)
        ]

    async def _reach_by_audience(self) -> dict[SurveyAudience, int]:
        """How many people each audience is, counted once for the whole page.

        The rule is asked, not paraphrased: `in_audience` is `may_answer` with the author
        and admin escape hatches shut, so this cannot drift from the rule that decides who
        may actually answer. Writing the same thing in SQL would be a second copy with
        nothing to catch it diverging.

        Every user is loaded and the predicate run five times over them, which is one
        query and a few hundred comparisons for a plant's staff list, and the wrong shape
        at ten thousand users. The escape hatch when that day comes is one grouped query,
        `SELECT role, department, count(*) GROUP BY 1, 2`, asking the rule once per group
        instead of once per person.
        """
        users = await self.users.list_all()
        return {
            audience: sum(1 for user in users if in_audience(user, audience))
            for audience in SurveyAudience
        }

    async def list_runs(self, template_id: UUID, author: User) -> list[RunSummary]:
        await self._owned_or_404(template_id, author)
        rows = await self.repo.list_for_template(template_id)
        return [_summary(run, version, user) for run, version, user in rows]

    async def get_run(self, template_id: UUID, run_id: UUID, author: User) -> RunDetail:
        await self._owned_or_404(template_id, author)
        row = await self.repo.get_detail(run_id)
        if row is None:
            raise NotFoundError("Run not found.")
        run, version, user = row
        if version.template_id != template_id:
            raise NotFoundError("That run belongs to a different template.")
        return RunDetail(
            id=run.id,
            respondent_name=user.display_name,
            status=run.status,
            version=version.version,
            started_at=run.started_at,
            completed_at=run.completed_at,
            messages=[MessageRead.model_validate(m) for m in run.messages],
            answers=[AnswerRead.model_validate(a) for a in run.answers],
            follow_ups_asked=follow_ups_asked(run),
            summary=run.summary,
        )

    async def export(self, template_id: UUID, author: User) -> tuple[str, list[dict[str, Any]]]:
        """Every answer across every run, flattened to one row each, for download."""
        template = await self._owned_or_404(template_id, author)
        rows: list[dict[str, Any]] = []
        for run, version, user in await self.repo.list_for_template(template_id):
            for answer in run.answers:
                rows.append(
                    {
                        "run_id": str(run.id),
                        "respondent": user.display_name,
                        "run_status": run.status.value,
                        "version": version.version,
                        "question": answer.question_text,
                        "kind": answer.kind.value,
                        "answer": flatten_answer(answer.value),
                        "answered_at": answer.answered_at.isoformat(),
                    }
                )
        return template.title, rows

    async def export_structured(self, template_id: UUID, author: User) -> dict[str, Any]:
        """The whole survey per run: every question, its answer, and its follow-ups.

        The flat export exists for spreadsheets and cannot say more than one row per
        answer, which loses three things an analyst needs. A question nobody answered has
        no row at all, so a skipped question and an unasked one look identical to a
        question that was never in the survey. A follow-up sits beside its parent as a
        peer, with the model's invented wording in the question column and nothing
        joining them. And every value arrives pre-flattened to a string, so a rating and
        the text "4" are indistinguishable once exported.

        Here the question list comes from the frozen version rather than from the answers,
        so unanswered questions are present and explicitly unanswered; follow-ups nest
        under the question they were asked about; and each value appears twice, once in
        the shape it was stored in and once flattened, so a reader can take either
        without re-deriving the other and getting it subtly different.
        """
        template = await self._owned_or_404(template_id, author)
        runs: list[dict[str, Any]] = []
        for run, version, user in await self.repo.list_for_template(template_id):
            by_question: dict[str, list[Any]] = {}
            for answer in run.answers:
                by_question.setdefault(str(answer.question_id), []).append(answer)

            questions: list[dict[str, Any]] = []
            for question in questions_of(version.definition):
                found = by_question.get(question["id"], [])
                scripted = next((a for a in found if a.kind is AnswerKind.scripted), None)
                questions.append(
                    {
                        "position": question["position"],
                        "id": question["id"],
                        "text": question["text"],
                        "answer_type": question["answer_type"],
                        "options": question["options"],
                        "required": question["required"],
                        # False covers both "hidden by a condition" and "never reached",
                        # which the flat export could not distinguish from absent.
                        "answered": scripted is not None,
                        "answer": scripted.value if scripted else None,
                        "answer_display": flatten_answer(scripted.value) if scripted else None,
                        "answered_at": scripted.answered_at.isoformat() if scripted else None,
                        # The model wrote these questions, so their text lives on the
                        # answer rather than in the frozen definition.
                        "follow_ups": [
                            {
                                "question": a.question_text,
                                "answer": a.value,
                                "answer_display": flatten_answer(a.value),
                                "answered_at": a.answered_at.isoformat(),
                            }
                            for a in found
                            if a.kind is AnswerKind.follow_up
                        ],
                    }
                )

            runs.append(
                {
                    "run_id": str(run.id),
                    "respondent": user.display_name,
                    "status": run.status.value,
                    "language": run.language,
                    "version": version.version,
                    "started_at": run.started_at.isoformat(),
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                    "llm_spend": {
                        "calls": run.llm_calls,
                        "prompt_tokens": run.llm_prompt_tokens,
                        "completion_tokens": run.llm_completion_tokens,
                        # Kept beside the cost rather than folded into it: a total that
                        # hid the unmeasured calls would read as complete when it is not.
                        "unmetered_calls": run.llm_unmetered_calls,
                        "cost_usd": str(run.llm_cost_usd),
                    },
                    "questions": questions,
                }
            )
        return {"template": {"id": str(template.id), "title": template.title}, "runs": runs}

    async def report(self, template_id: UUID, author: User) -> SurveyReport:
        """What the survey found, question by question, across every run that answered it.

        Everything else here is per run: the dashboard counts how a survey is going and
        the results page shows one person at a time. Neither answers "what did people
        say", which is the question a survey is run to answer, and an author with forty
        respondents was opening forty runs or exporting a spreadsheet to find out.

        Counted against the latest published version. A run started before a republish
        answered different questions under different ids, and folding those answers in
        would quietly change what a number means; they are excluded and counted so the
        omission is on the page rather than in the code.
        """
        template = await self._owned_or_404(template_id, author)
        version = await self.templates.latest_version(template_id)
        if version is None:
            raise NotFoundError("This survey has no published version to report on.")

        questions = questions_of(version.definition)
        # Scripted answers only. A follow-up answers a question the model wrote, not the
        # author's, so counting them here would tally answers to questions nobody chose.
        answers: dict[str, list[dict[str, Any]]] = {q["id"]: [] for q in questions}
        runs_total = runs_completed = on_earlier = 0
        # People as well as runs, from rows already loaded. A run count answers "how much
        # material is there"; a person count answers "how many of the people this was for
        # have answered", and before the one-answer-per-person guard those differed by a
        # factor of four on a real survey.
        people_started: set[UUID] = set()
        people_completed: set[UUID] = set()
        for run, run_version, _ in await self.repo.list_for_template(template_id):
            runs_total += 1
            people_started.add(run.respondent_id)
            if run.status is RunStatus.completed:
                runs_completed += 1
                people_completed.add(run.respondent_id)
            if run_version.id != version.id:
                on_earlier += 1
                continue
            for answer in run.answers:
                if answer.kind is not AnswerKind.scripted:
                    continue
                key = str(answer.question_id)
                if key in answers:
                    answers[key].append(answer.value)

        return SurveyReport(
            template_id=template.id,
            title=template.title,
            version=version.version,
            runs_total=runs_total,
            runs_completed=runs_completed,
            reach=(await self._reach_by_audience()).get(template.audience, 0),
            people_started=len(people_started),
            people_completed=len(people_completed),
            runs_on_earlier_versions=on_earlier,
            questions=[_report_question(q, answers[q["id"]]) for q in questions],
        )

    async def _owned_or_404(self, template_id: UUID, author: User) -> SurveyTemplate:
        """Responses carry respondent names and verbatim transcripts, so they are readable
        only by the author and an admin. Being in a survey's audience means you were asked,
        not that you may read what your colleagues said. Someone else's template reads as
        absent rather than forbidden."""
        template = await self.templates.get(template_id)
        if template is None:
            raise NotFoundError("Template not found.")
        decision = may_read_rows(author, template.created_by, is_admin_by_config(author))
        if not decision:
            logger.info(
                "responses hidden: template=%s user=%s reason=%s",
                template_id,
                author.id,
                decision.reason,
            )
            raise NotFoundError("Template not found.")
        return template


def _report_question(question: dict[str, Any], values: list[dict[str, Any]]) -> QuestionReport:
    """One question's tally, from the raw stored values.

    Shape by shape rather than through ``flatten_answer``, which exists to make one
    printable cell and would have "yes" and a write-in reading "yes" land in the same
    bucket. Counting is where that distinction matters most.
    """
    answered = [v for v in values if "unanswerable" not in v]
    declined = len(values) - len(answered)
    answer_type = question["answer_type"]
    counts: list[OptionCount] = []
    verbatim: list[str] = []
    average: float | None = None

    if answer_type in ("single_select", "multi_select"):
        # The author's order, so a scale reads as a scale rather than sorted by
        # popularity, and every option appears even when nobody picked it: a zero is a
        # finding and a missing row looks like the option was never offered.
        tally = {option: 0 for option in question["options"]}
        write_ins: list[str] = []
        for value in answered:
            chosen = value.get("options", [])
            if "option" in value:
                chosen = [value["option"]]
            for choice in chosen:
                if choice in tally:
                    tally[choice] += 1
            other = value.get("other")
            write_ins.extend(other if isinstance(other, list) else [other] if other else [])
        counts = [OptionCount(label=o, count=n) for o, n in tally.items()]
        counts += [
            OptionCount(label=w, count=write_ins.count(w), write_in=True)
            for w in dict.fromkeys(write_ins)
        ]
        verbatim = write_ins
    elif answer_type == "yes_no":
        yes = sum(1 for v in answered if v.get("yes_no") is True)
        counts = [
            OptionCount(label="yes", count=yes),
            OptionCount(label="no", count=len(answered) - yes),
        ]
    elif answer_type in ("rating", "number"):
        numbers = [v[answer_type] for v in answered if isinstance(v.get(answer_type), int | float)]
        if numbers:
            average = sum(numbers) / len(numbers)
        if answer_type == "rating":
            # The whole 1-5 scale, so an unused end of it is visible rather than absent.
            counts = [
                OptionCount(label=str(n), count=sum(1 for x in numbers if x == n))
                for n in range(1, 6)
            ]
    else:
        # Free text and dates: nothing to add up, so the values themselves, in full.
        verbatim = [str(next(iter(v.values()))) for v in answered if v]

    return QuestionReport(
        id=UUID(question["id"]),
        position=question["position"],
        text=question["text"],
        answer_type=answer_type,
        answered=len(answered),
        declined=declined,
        counts=counts,
        average=average,
        verbatim=verbatim,
    )


def follow_ups_asked(run: SurveyRun) -> dict[UUID, int]:
    """The follow-up probes the engine issued, per question id.

    ``probes_asked`` is the engine's own ledger and holds two things: follow-up counts
    keyed by question id, and reply counts under a ``reply:`` prefix sharing the same
    JSONB. That prefix is a storage detail, so only the probes cross the API boundary.
    """
    counts: dict[UUID, int] = {}
    for key, count in run.probes_asked.items():
        if key.startswith(REPLY_PREFIX):
            continue
        try:
            counts[UUID(key)] = count
        except ValueError:
            # Only the engine writes this column, so a key that is neither a question id
            # nor a reply marker means an engine bug — worth a line in the log, but not
            # worth failing an author's whole results view over.
            logger.warning("skipping unrecognised probes_asked key: run=%s key=%r", run.id, key)
    return counts


def flatten_answer(value: dict[str, Any]) -> str:
    """One human-readable cell per stored answer value, whatever its shape."""
    if "text" in value:
        return str(value["text"])
    if "rating" in value:
        return str(value["rating"])
    if "number" in value:
        return str(value["number"])
    if "yes_no" in value:
        return "yes" if value["yes_no"] else "no"
    if "date" in value:
        return str(value["date"])
    if "option" in value:
        return str(value["option"])
    if "options" in value:  # before "other": a multi_select may carry both keys
        parts = [str(v) for v in value["options"]]
        parts += [f"(other) {v}" for v in value.get("other", [])]
        return "; ".join(parts)
    if "other" in value:
        return f"(other) {value['other']}"
    if "unanswerable" in value:
        return f"(declined) {value['unanswerable']}"
    return json.dumps(value)  # future shapes export verbatim rather than crash a download


def to_csv(rows: list[dict[str, Any]]) -> str:
    """RFC-4180 CSV with a UTF-8 BOM so Excel opens it with the right encoding."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return "\ufeff" + buffer.getvalue()


def _summary(run: SurveyRun, version: SurveyTemplateVersion, user: User) -> RunSummary:
    questions = questions_of(version.definition)
    answers = {str(a.question_id): a.value for a in run.answers if a.kind is AnswerKind.scripted}
    return RunSummary(
        id=run.id,
        respondent_name=user.display_name,
        status=run.status,
        version=version.version,
        answered=len(answers),
        # Same denominator the respondent sees: questions a condition ruled out were
        # never asked, so counting them would leave every conditional run looking
        # abandoned at "2 of 4".
        total=len(answers) + remaining_possible(run.current_question_index, questions, answers),
        started_at=run.started_at,
        completed_at=run.completed_at,
    )
