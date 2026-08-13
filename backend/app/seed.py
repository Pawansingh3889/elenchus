"""Idempotent dev seed: one plant in miniature, every ladder represented.

Run with ``python -m app.seed``. Safe to run repeatedly (keyed on id).

Each person holds one job, which is the whole point of the job model: the seed used to
record a line leader who was also QA, and the org chart says that job does not exist.
The cast covers what the access rules need to be visible: a shift manager who authors
(Ava), the office functions (Arjun, Fatima), an executive who reads everything without
owning anything (Adaeze), the quality ladder top to bottom (Tomas, Quinn, Noor), a
supervisor carrying the H&S hat (Rohan), and a dedicated H&S manager (Hana).

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
        Function.hr,
        Band.manager,
        "entra-arjun",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a3"),
        "fatima@elenchus.dev",
        "Fatima Author",
        Function.finance,
        Band.manager,
        "entra-fatima",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a4"),
        "adaeze@elenchus.dev",
        "Adaeze Author",
        # The factory manager: executive reads every survey and edits none of them,
        # which needs one seeded account to be seen from. Not IT, so still not admin.
        Function.executive,
        Band.head,
        "entra-adaeze",
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
]


# Cross-cutting responsibilities on top of the job. Small on purpose: a hat grants
# being asked (the health_safety audience) and nothing else.
SEED_HATS: list[tuple[UUID, tuple[Hat, ...]]] = [
    (UUID("00000000-0000-0000-0000-0000000000c2"), (Hat.health_safety,)),
]


async def seed() -> None:
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
                # The id is taken by somebody else. Refusing beats the alternative,
                # which actually happened: an id reused from a retired generation of
                # this list silently skipped the insert and then handed the impostor
                # every group membership below, and the only symptom was two strangers
                # gaining a group. Ids are forever; pick a fresh one.
                raise RuntimeError(
                    f"seed id {uid} belongs to {existing.email}, not {email}; "
                    "this id was used by an earlier seed generation, so give the new "
                    "user a fresh one"
                )
        await session.commit()
        hats = 0
        for uid, wanted in SEED_HATS:
            for hat in wanted:
                # Keyed on the pair, so re-running adds nothing and the seed stays safe to
                # run over a database somebody has already been using.
                if await session.get(UserHat, (uid, hat)) is None:
                    session.add(UserHat(user_id=uid, hat=hat))
                    hats += 1
        await session.commit()
        surveys_added, runs_added = await load_sample_data(session)
    print(
        f"Seeded {len(SEED_USERS)} users and {hats} new hats; "
        f"loaded {surveys_added} sample surveys and {runs_added} runs (idempotent)."
    )


if __name__ == "__main__":
    asyncio.run(seed())
