"""Create a company's workspace and its owner, which is how a production database starts.

Production has no seed and no sign-up: an account exists before anybody signs in with it,
and after that the owner makes everybody else from the admin screen. This makes the one
account nobody can make from a screen. Run it in the deployment's shell, once per company:

    python -m app.provision "Acme Foods" owner@acme.test "Ada Owner" \\
        --function executive --band director [--microsoft-id <Entra object id>]

Safe to repeat: an address that already has an account is reported and left alone. The
owner's audit row has no actor, because nobody in the system created them.
"""

import argparse
import asyncio
from uuid import uuid4

from app.db.session import SessionFactory
from app.users.models import AccountChange, Band, Function, User, UserHat, WorkspaceRole
from app.users.repository import UserRepository
from app.users.schemas import AccountCreate, AccountSnapshot
from app.workspaces.models import Workspace
from app.workspaces.repository import WorkspaceRepository


async def provision(workspace_name: str, data: AccountCreate) -> tuple[User, bool]:
    """Return the owner and whether this call created them."""
    async with SessionFactory() as session:
        if await WorkspaceRepository(session).resolve_identity(email=data.email):
            existing = await UserRepository(session).get_by_email(data.email)
            assert existing is not None, "the identity just resolved"
            return existing, False

    workspace_id = uuid4()
    # Bound before the first statement, so the row policies admit exactly this workspace.
    async with SessionFactory(info={"workspace_id": workspace_id}) as session:
        session.add(Workspace(id=workspace_id, name=workspace_name))
        await session.flush()
        users = UserRepository(session)
        owner = User(
            email=data.email,
            display_name=data.display_name,
            function=data.function,
            band=data.band,
            microsoft_id=data.microsoft_id,
            workspace_role=WorkspaceRole.owner,
            hat_rows=[UserHat(hat=h) for h in data.hats],
        )
        users.add(owner)
        await session.flush()
        users.add_change(
            AccountChange(
                user_id=owner.id,
                changed_by=None,
                change={
                    "kind": "created",
                    "before": None,
                    "after": AccountSnapshot.of(owner).model_dump(mode="json"),
                },
            )
        )
        await session.commit()
        return owner, True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workspace")
    parser.add_argument("email")
    parser.add_argument("display_name")
    parser.add_argument("--function", required=True, choices=[f.value for f in Function])
    parser.add_argument("--band", required=True, choices=[b.value for b in Band])
    parser.add_argument("--microsoft-id")
    args = parser.parse_args()
    data = AccountCreate(
        email=args.email,
        display_name=args.display_name,
        function=Function(args.function),
        band=Band(args.band),
        microsoft_id=args.microsoft_id,
        workspace_role=WorkspaceRole.owner,
    )
    owner, created = asyncio.run(provision(args.workspace, data))
    verb = "created" if created else "already exists, left alone:"
    print(f"owner {verb} {owner.email} ({owner.id}) in workspace {owner.workspace_id}")


if __name__ == "__main__":
    main()
