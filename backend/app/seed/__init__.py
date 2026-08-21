"""Idempotent dev seed: one plant in miniature, every ladder represented.

Run with ``python -m app.seed``. Safe to run repeatedly (keyed on id).

Each person holds one job, which is the whole point of the job model: the seed used to
record a line leader who was also QA, and the org chart says that job does not exist.
The cast covers what the access rules need to be visible: a shift manager who authors
(Ava), the office functions (Arjun, Fatima), the quality ladder top to bottom (Tomas,
Quinn, Noor), a supervisor carrying the H&S hat (Rohan), and a dedicated H&S manager
(Hana).

**No executive.** There was one, on id a4, and she existed so that
`reads_all_surveys` could be seen from a real account. She is gone by request, and the
id goes with her rather than being handed to somebody else: ids are forever here, and
reusing one is what the check in `seed()` refuses. Nothing tests the executive rule
through the seed, so what is lost is a demonstration rather than coverage; add a fresh
c-block id if you want it back.

Nobody here is in IT, and so nobody here is an administrator. That is deliberate: IT
membership grants admin, and a committed seed that shipped an administrator would hand
one to every checkout. Admin locally is still ADMIN_EMAILS, or moving one of these
accounts into IT yourself.

Display names still carry the retired author/respondent wording ("Rina Respondent").
Ids are forever and names are cosmetic, so the names stay while the rights derive from
the band: Rina is a shift manager and may author, whatever her surname says.
"""

import asyncio
from uuid import UUID

from sqlalchemy import text

from app.db.session import SessionFactory
from app.sample_data.loader import load_sample_data
from app.users.models import Band, Function, Hat, User, UserHat

# (id, email, name, function, band, Entra object id). The id is a stand-in for the
# Microsoft login the authoring bands will hold; it decides nothing, and Rina is the
# deliberate counter-example: manager band, no Entra id, which the directory badges as
# somebody who authors today and cannot sign in when the header shim goes.
SEED_USERS: list[tuple[UUID, str, str, Function, Band, str | None]] = [
    (
        UUID("00000000-0000-0000-0000-0000000000a1"),
        "ava@elenchus.dev",
        "Ava Author",
        # A shift manager: the case the band model exists for. The walkthroughs and demo
        # script all run as Ava, and she authors from the floor, not from an office.
        Function.production,
        Band.manager,
        "entra-ava",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a2"),
        "arjun@elenchus.dev",
        "Arjun Author",
        # Head of HR. The office functions are one person deep here, so their lead sits
        # at head rather than manager, and under the seniority rule that is what lets
        # them survey the floor at all.
        Function.hr,
        Band.head,
        "entra-arjun",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a3"),
        "fatima@elenchus.dev",
        "Fatima Author",
        # Finance, alone and at director: the one function with a single person in it,
        # kept deliberately so the grid has a row that is one cell and the seniority
        # rule has somebody at the top of it.
        Function.finance,
        Band.director,
        "entra-fatima",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a5"),
        "tomas@elenchus.dev",
        "Tomas Author",
        # Head QA on the floor, straight from the org picture.
        Function.quality,
        Band.head,
        "entra-tomas",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a6"),
        "quinn@elenchus.dev",
        "Quinn Author",
        Function.quality,
        Band.manager,
        "entra-quinn",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b1"),
        "rosa@elenchus.dev",
        "Rosa Respondent",
        Function.production,
        Band.operative,
        None,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b2"),
        "ravi@elenchus.dev",
        "Ravi Respondent",
        # A line leader, and only that. The retired membership table recorded Ravi as
        # line leader and QA at once, which is the impossible job that led to the job
        # model; keep him single-jobbed so the fix stays demonstrated.
        Function.production,
        Band.line_leader,
        None,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b3"),
        "remy@elenchus.dev",
        "Remy Respondent",
        Function.production,
        Band.operative,
        None,
    ),
    # c-block ids, not the next b ones: b4 through b8 are already occupied in databases
    # seeded before 10 Aug, by respondent rows an older generation of this list created
    # and later dropped. Reusing an id does not fail; it silently decorates whoever holds
    # it, which is exactly what the email check in seed() refuses.
    (
        UUID("00000000-0000-0000-0000-0000000000c1"),
        "rina@elenchus.dev",
        "Rina Respondent",
        # A shift manager, so manager band: she authors, reads production colleagues'
        # results, and deliberately has no Entra id (see the note above SEED_USERS).
        Function.production,
        Band.manager,
        None,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000c2"),
        "rohan@elenchus.dev",
        "Rohan Respondent",
        # A supervisor with additional H&S responsibility: the case hats exist for.
        # The job stays production; the duty is in SEED_HATS below.
        Function.production,
        Band.supervisor,
        None,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000c3"),
        "hana@elenchus.dev",
        "Hana Author",
        # The H&S manager on the floor: the dedicated half of the health_safety
        # audience, beside Rohan's hatted half.
        Function.health_safety,
        Band.manager,
        "entra-hana",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000c4"),
        "noor@elenchus.dev",
        "Noor Respondent",
        # QA on the ground: the quality ladder's operative rung, so a survey aimed at
        # `qa` visibly spans floor to head.
        Function.quality,
        Band.operative,
        None,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000c5"),
        "sam@elenchus.dev",
        "Sam Author",
        # Supply chain, two deep: intake and dispatch are where a chill-chain problem
        # becomes somebody else's problem, so the function needs a ladder rather than a
        # single contact.
        Function.supply_chain,
        Band.manager,
        # An authoring band carries a sign-in, which the seed's own test pins: manager
        # and up build surveys, and one who cannot sign in is an account that will stop
        # working the day the shim goes.
        "entra-sam",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000c6"),
        "priya@elenchus.dev",
        "Priya Author",
        Function.supply_chain,
        Band.head,
        "entra-priya",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000c7"),
        "marta@elenchus.dev",
        "Marta Author",
        # The factory manager. Executive at head: she reads every survey and edits none,
        # and under the seniority rule she is the only person who can aim one at the
        # heads of the other functions.
        Function.executive,
        Band.head,
        "entra-marta",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000c8"),
        "pawankapkoti3889@gmail.com",
        "Pawan Kapkoti",
        # The demo's owner. Authoring band so the walkthrough's author side has a face
        # they can sign in with on a real address; administration comes from the
        # ADMIN_EMAILS allowlist in the deployment's environment, never from the seed.
        Function.production,
        Band.manager,
        "entra-pawan",
    ),
]


# Cross-cutting responsibilities on top of the job. Small on purpose: a hat grants
# being asked (the health_safety audience) and nothing else.
SEED_HATS: list[tuple[UUID, tuple[Hat, ...]]] = [
    (UUID("00000000-0000-0000-0000-0000000000c2"), (Hat.health_safety,)),
]


async def seed() -> tuple[int, int, int]:
    async with SessionFactory() as session:
        for uid, email, name, function, band, microsoft_id in SEED_USERS:
            existing = await session.get(User, uid)
            if existing is None:
                session.add(
                    User(
                        id=uid,
                        email=email,
                        display_name=name,
                        function=function,
                        band=band,
                        microsoft_id=microsoft_id,
                    )
                )
            elif existing.email != email:
                raise RuntimeError(
                    f"seed id {uid} belongs to {existing.email}, not {email}; "
                    "this id was used by an earlier seed generation, so give the new "
                    "user a fresh one"
                )
        await session.commit()
        hats = 0
        for uid, wanted in SEED_HATS:
            for hat in wanted:
                if await session.get(UserHat, (uid, hat)) is None:
                    session.add(UserHat(user_id=uid, hat=hat))
                    hats += 1
        await session.commit()
        surveys_added, runs_added = await load_sample_data(session)
    print(
        f"Seeded {len(SEED_USERS)} users and {hats} new hats; "
        f"loaded {surveys_added} sample surveys and {runs_added} runs (idempotent)."
    )
    return len(SEED_USERS), hats, surveys_added


# The tables a full reset wipes, leaf to root for readability. TRUNCATE CASCADE would
# handle foreign keys in one statement; the order is for the reader, not the database.
RESET_TABLES: tuple[str, ...] = (
    "run_messages",
    "answers",
    "survey_runs",
    "survey_questions",
    "survey_templates",
    "account_changes",
    "user_hats",
    "users",
)


async def reset_demo() -> None:
    """Wipe every table and re-seed from scratch.

    The demo's whole promise is that its data is disposable: anyone who reaches the
    deployment can read, change or delete anything in it, and a visitor who answers a
    survey is replacing whatever a stranger wrote earlier. That promise is kept by
    starting every boot clean, because the only reset that ever ran was the one a human
    pressed. `reset()` leaves the ids that survive in databases seeded before 10 Aug
    alone, because they belong to the seed that planted them.
    """
    async with SessionFactory() as session:
        for table in RESET_TABLES:
            await session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
        await session.commit()
    await seed()


if __name__ == "__main__":
    asyncio.run(seed())
