"""User business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.access import in_audience
from app.templates.enums import SurveyAudience
from app.users.repository import UserRepository


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)

    async def reach_by_audience(self) -> dict[SurveyAudience, int]:
        """How many people each audience is, right now.

        Moved here from the results service the day the publish dialog started asking
        the same question, because "how many people is this audience" is a question
        about users and there must be one answer to it: the dashboard, the report and
        the publish confirmation now all read this number from this method, so they
        cannot drift apart.

        Live on purpose, and that is a recorded decision rather than an oversight: the
        audience of a survey is whoever is in the group *today*, so somebody hired on
        Tuesday is asked Monday's survey, and every denominator moves when membership
        does. The guardrails around that are the admin edit preview and the account
        audit log, not a frozen snapshot.

        The rule is asked, not paraphrased: `in_audience` is `may_answer` with the
        author and admin escape hatches shut, so this cannot drift from the rule that
        decides who may actually answer. Writing the same thing in SQL would be a second
        copy with nothing to catch it diverging.

        Every user is loaded and the predicate run five times over them, which is one
        query and a few hundred comparisons for a plant's staff list, and the wrong
        shape at ten thousand users. The escape hatch when that day comes is one grouped
        query, asking the rule once per group instead of once per person. Author-side
        only, deliberately: nothing on the respondent path calls this, so the break-time
        burst never pays for it.
        """
        users = await self.repo.list_all()
        return {
            audience: sum(1 for user in users if in_audience(user, audience))
            # `person` is skipped: its reach is one by definition and depends on which
            # person, so a single entry here would be a number that is wrong for every
            # survey. The dashboard supplies it directly.
            for audience in SurveyAudience
            if audience is not SurveyAudience.person
        }
