"""Invitation and approved employee-roster registry tests."""

import pytest

from app.errors import ConflictError
from app.users.models import Band, Function, User, WorkspaceRole
from app.workspaces.schemas import InvitationCreate, RosterCreate
from app.workspaces.service import WorkspaceAccessService


async def _owner(session) -> User:
    owner = User(
        email="owner@access.test",
        display_name="Access Owner",
        function=Function.hr,
        band=Band.manager,
        workspace_role=WorkspaceRole.owner,
    )
    session.add(owner)
    await session.flush()
    return owner


async def test_invitation_is_tokenized_and_audited(session):
    owner = await _owner(session)
    service = WorkspaceAccessService(session)
    created = await service.invite(
        InvitationCreate(
            email="invitee@example.test",
            display_name="Invited Analyst",
            workspace_role=WorkspaceRole.analyst,
            function=Function.hr,
            band=Band.manager,
        ),
        owner,
    )
    assert created.token is not None
    assert len(created.token) > 20

    listed = await service.invitations(owner)
    assert len(listed) == 1
    assert listed[0].token is None
    history = await service.access_history(owner)
    assert [(row.action, row.email) for row in history] == [("invited", "invitee@example.test")]

    await service.revoke_invitation(created.id, owner)
    history = await service.access_history(owner)
    assert [row.action for row in history] == ["revoked", "invited"]


async def test_roster_entry_requires_one_access_path_per_email(session):
    owner = await _owner(session)
    service = WorkspaceAccessService(session)
    entry = await service.approve_roster(
        RosterCreate(
            email="employee@example.test",
            display_name="Roster Employee",
            function=Function.production,
            band=Band.operative,
        ),
        owner,
    )
    assert entry.email == "employee@example.test"
    with pytest.raises(ConflictError):
        await service.approve_roster(
            RosterCreate(
                email="employee@example.test",
                display_name="Changed Employee",
                function=Function.quality,
                band=Band.supervisor,
            ),
            owner,
        )

    await service.revoke_roster(entry.id, owner)
    replaced = await service.approve_roster(
        RosterCreate(
            email="employee@example.test",
            display_name="Changed Employee",
            function=Function.quality,
            band=Band.supervisor,
        ),
        owner,
    )
    assert replaced.function is Function.quality
