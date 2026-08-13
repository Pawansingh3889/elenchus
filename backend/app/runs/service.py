"""Reading run results back for authors.

Deliberately separate from the conduct engine: conducting is respondent-owned and
refuses anyone else, while results are author-facing and cross-respondent.
"""

import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin_by_config, may_list, may_read_rows
from app.errors import NotFoundError
from app.runs.enums import AnswerKind, RunStatus
from app.runs.models import REPLY_PREFIX, SurveyRun
from app.runs.repository import ResultsRepository
from app.runs.schemas import (
    AnswerRead,
    AnswersMatrix,
    DashboardRow,
    MatrixQuestion,
    MatrixRun,
    MessageDetailRead,
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
from app.users.service import UserService

logger = logging.getLogger("app.runs.results")


class ResultsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ResultsRepository(session)
        self.templates = TemplateRepository(session)
        self.users = UserRepository(session)

    async def dashboard(self, author: User) -> list[DashboardRow]:
        """Every survey this author's department owns, with how each one is going.

        Scoped in the query to the author plus their department rather than filtered
        afterwards, so a survey from outside it is never loaded in the first place.
        """
        creators = {author.id} | await self.users.ids_in_department(author.department)
        rows = await self.repo.dashboard_rows(creators)
        admin = is_admin_by_config(author)
        reach = await self._reach_by_audience()
        departments = await self.users.departments_by_id()
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
                # A survey aimed at one person has a reach of one, and no shared count
                # can say so: `reach` is per audience, and every person-aimed survey
                # names a different person. Zero when it names nobody, which is a broken
                # row rather than a survey with an audience of none.
                reach=(
                    (1 if template.audience_user_id is not None else 0)
                    if template.audience is SurveyAudience.person
                    else reach.get(template.audience, 0)
                ),
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
            if may_list(
                author,
                template.audience,
                template.created_by,
                admin,
                target=template.audience_user_id,
                creator_department=departments.get(template.created_by),
            )
        ]

    async def _reach_by_audience(self) -> dict[SurveyAudience, int]:
        """One shared answer to "how many people is this audience": UserService's.

        Moved there when the publish dialog started asking too. Kept as a private
        delegating method rather than inlined at the call sites, so the dashboard and
        the report keep reading like they did and the one-answer property is a fact of
        UserService rather than of everyone remembering to call it.
        """
        return await UserService(self.session).reach_by_audience()

    async def list_runs(self, template_id: UUID, author: User) -> list[RunSummary]:
        await self._owned_or_404(template_id, author)
        rows = await self.repo.list_for_template(template_id)
        numbers = await self.repo.respondent_numbers(template_id)
        return [_summary(run, version, numbers) for run, version, _ in rows]

    async def get_run(self, template_id: UUID, run_id: UUID, author: User) -> RunDetail:
        await self._owned_or_404(template_id, author)
        row = await self.repo.get_detail(run_id)
        if row is None:
            raise NotFoundError("Run not found.")
        run, version, _ = row
        if version.template_id != template_id:
            raise NotFoundError("That run belongs to a different template.")
        # Numbered across the whole survey rather than within this row, which is why the
        # lookup is a second query rather than something the run carries: a respondent's
        # number is their position among everyone who answered, and one run cannot know it.
        numbers = await self.repo.respondent_numbers(template_id)
        return RunDetail(
            id=run.id,
            respondent_label=respondent_label(numbers[run.respondent_id]),
            status=run.status,
            version=version.version,
            started_at=run.started_at,
            completed_at=run.completed_at,
            messages=[MessageDetailRead.model_validate(m) for m in run.messages],
            answers=[AnswerRead.model_validate(a) for a in run.answers],
            follow_ups_asked=follow_ups_asked(run),
            summary=run.summary,
        )

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
        # The probes, kept beside the tallies rather than dropped. They were discarded
        # here until now, which left the elaboration an author most wants to read visible
        # only in the export and one run at a time: a survey that asked "have you reported
        # this?" could show four yeses and nothing about what happened next.
        probes: dict[str, list[dict[str, Any]]] = {q["id"]: [] for q in questions}
        probed_runs: dict[str, set[UUID]] = {q["id"]: set() for q in questions}
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
                key = str(answer.question_id)
                if key not in answers:
                    continue
                if answer.kind is AnswerKind.scripted:
                    answers[key].append(answer.value)
                else:
                    probes[key].append(answer.value)
                    probed_runs[key].add(run.id)

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
            questions=[
                _report_question(q, answers[q["id"]], probes[q["id"]], len(probed_runs[q["id"]]))
                for q in questions
            ],
        )

    async def answers_matrix(self, template_id: UUID, author: User) -> AnswersMatrix:
        """Every answer on the current version, by respondent, with nothing tallied.

        The report says what each question found; this says who said it, which is what
        an author needs to ask whether the people who picked one thing also picked
        another. That join was reachable only one run at a time, so correlating a survey
        of forty meant forty requests and doing the arithmetic by hand.

        Scoped to the latest published version on the same rule as the report: a run
        that answered different questions under different ids is excluded and counted,
        not folded in.
        """
        template = await self._owned_or_404(template_id, author)
        version = await self.templates.latest_version(template_id)
        if version is None:
            raise NotFoundError("This survey has no published version to report on.")

        questions = questions_of(version.definition)
        numbers = await self.repo.respondent_numbers(template_id)
        runs: list[MatrixRun] = []
        on_earlier = 0
        for run, run_version, _ in await self.repo.list_for_template(template_id):
            if run_version.id != version.id:
                on_earlier += 1
                continue
            runs.append(
                MatrixRun(
                    run_id=run.id,
                    respondent_label=respondent_label(numbers[run.respondent_id]),
                    status=run.status,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                    # Follow-ups included, carrying their kind. They can never join a
                    # tally, but they are what the respondent actually elaborated, and
                    # the client shows them beside the answer they came from.
                    answers=[AnswerRead.model_validate(a) for a in run.answers],
                )
            )

        return AnswersMatrix(
            template_id=template.id,
            title=template.title,
            version=version.version,
            questions=[
                MatrixQuestion(
                    id=UUID(q["id"]),
                    position=q["position"],
                    text=q["text"],
                    answer_type=q["answer_type"],
                    options=q.get("options") or [],
                )
                for q in questions
            ],
            runs=runs,
            runs_on_earlier_versions=on_earlier,
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


def _report_question(
    question: dict[str, Any],
    values: list[dict[str, Any]],
    probe_values: list[dict[str, Any]],
    probed: int,
) -> QuestionReport:
    """One question's tally, from the raw stored values.

    Shape by shape rather than through ``flatten_answer``, which exists to make one
    printable cell and would have "yes" and a write-in reading "yes" land in the same
    bucket. Counting is where that distinction matters most.

    ``probe_values`` are the follow-up answers, and they are printed rather than counted.
    Their shape is whatever the model's own question called for, so they belong to no
    option list and no scale, and every number below is computed without them.
    """
    answered = [v for v in values if "unanswerable" not in v]
    declined = len(values) - len(answered)
    answer_type = question["answer_type"]
    counts: list[OptionCount] = []
    verbatim: list[str] = []
    average: float | None = None
    low: float | None = None
    high: float | None = None

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
            low, high = min(numbers), max(numbers)
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
        low=low,
        high=high,
        verbatim=verbatim,
        # A declined probe is not words the respondent said, so it is left out on the
        # same rule the tallies use. `probed` still counts the run: the question was
        # asked, and "asked and declined" is a finding.
        follow_ups=[flatten_answer(v) for v in probe_values if "unanswerable" not in v],
        probed=probed,
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


def respondent_label(number: int) -> str:
    """How one respondent is named to the author, given their number in this survey.

    One function because the label has two jobs and they must agree. It is what the
    results list and the run detail show, and it is also the key the survey recap
    attributes quotes with: the model is given "Respondent 3 on ...", returns a quote
    against that name, and the verifier matches it back. Two spellings of the same
    respondent would silently drop every quote as unattributable.

    Left in English rather than translated for that second job. It is an identifier the
    model copies exactly, the way option values are, and a key that changed with the
    author's interface language would match nothing the moment they switched.
    """
    return f"Respondent {number}"


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


def _summary(
    run: SurveyRun, version: SurveyTemplateVersion, numbers: dict[UUID, int]
) -> RunSummary:
    questions = questions_of(version.definition)
    answers = {str(a.question_id): a.value for a in run.answers if a.kind is AnswerKind.scripted}
    return RunSummary(
        id=run.id,
        respondent_label=respondent_label(numbers[run.respondent_id]),
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
