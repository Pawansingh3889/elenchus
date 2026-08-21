from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import require_admin
from app.seed import SEED_USERS, seed
from app.users.models import User

router = APIRouter(prefix="/api/v1/admin/seed", tags=["admin-seed"])


class SeedUserRead(BaseModel):
    id: str
    email: str
    display_name: str
    function: str
    band: str
    microsoft_id: str | None = None


class SeedRunRead(BaseModel):
    status: str
    users: int
    hats: int
    surveys: int
    runs: int = 0


@router.get("/users", response_model=list[SeedUserRead])
async def list_seed_users(_: User = Depends(require_admin)) -> list[SeedUserRead]:
    result = []
    for uid, email, name, function, band, microsoft_id in SEED_USERS:
        result.append(
            SeedUserRead(
                id=str(uid),
                email=email,
                display_name=name,
                function=function.value,
                band=band.value,
                microsoft_id=microsoft_id,
            )
        )
    return result


@router.post("/run", response_model=SeedRunRead)
async def run_seed(_: User = Depends(require_admin)) -> SeedRunRead:
    users, hats, surveys = await seed()
    return SeedRunRead(
        status="ok",
        users=users,
        hats=hats,
        surveys=surveys,
    )
