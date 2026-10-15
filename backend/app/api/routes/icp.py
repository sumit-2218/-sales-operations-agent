from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.models import IcpProfile, User
from ...schemas.schemas import IcpIn, IcpOut, IcpPatch
from ...services.activity_service import log_activity
from ...services.icp_service import DEFAULT_ICP_CONFIG, explain_icp
from ...services.qualification_service import rescore_all
from ..deps import get_current_user

router = APIRouter(prefix="/icp", tags=["icp"])


def _out(i: IcpProfile) -> IcpOut:
    return IcpOut(id=i.id, name=i.name, owner_id=i.owner_id, is_active=i.is_active, config=i.config,
                  explanations=explain_icp(i.config), created_at=i.created_at, updated_at=i.updated_at)


def _own(db: Session, icp_id: int, user: User) -> IcpProfile:
    icp = db.get(IcpProfile, icp_id)
    if not icp or icp.owner_id != user.id:
        raise HTTPException(404, "ICP not found")
    return icp


def _activate(db: Session, user: User, icp: IcpProfile):
    db.execute(update(IcpProfile).where(IcpProfile.owner_id == user.id, IcpProfile.id != icp.id).values(is_active=False))
    icp.is_active = True


@router.get("", response_model=list[IcpOut])
def list_icps(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(IcpProfile).where(IcpProfile.owner_id == user.id).order_by(IcpProfile.id)).all()
    return [_out(i) for i in rows]


@router.get("/default-config")
def default_config(user: User = Depends(get_current_user)):
    return {"config": DEFAULT_ICP_CONFIG, "explanations": explain_icp(DEFAULT_ICP_CONFIG)}


@router.post("", response_model=IcpOut, status_code=201)
def create_icp(body: IcpIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    icp = IcpProfile(name=body.name.strip(), owner_id=user.id, config=body.config.model_dump(), is_active=False)
    db.add(icp)
    db.flush()
    if body.is_active or not db.scalar(select(IcpProfile.id).where(IcpProfile.owner_id == user.id, IcpProfile.is_active.is_(True))):
        _activate(db, user, icp)
        db.flush()
        rescore_all(db, user)
    log_activity(db, user, "icp.created", "icp", icp.id, meta={"name": icp.name})
    db.commit()
    return _out(icp)


@router.get("/{icp_id}", response_model=IcpOut)
def get_icp(icp_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _out(_own(db, icp_id, user))


@router.patch("/{icp_id}", response_model=IcpOut)
def update_icp(icp_id: int, body: IcpPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    icp = _own(db, icp_id, user)
    if body.name:
        icp.name = body.name.strip()
    if body.config:
        icp.config = body.config.model_dump()
    if body.is_active:
        _activate(db, user, icp)
    elif body.is_active is False:
        icp.is_active = False
    db.flush()
    rescore_all(db, user)  # scores depend on the active ICP
    log_activity(db, user, "icp.updated", "icp", icp.id, meta={"name": icp.name})
    db.commit()
    return _out(icp)


@router.delete("/{icp_id}", status_code=204)
def delete_icp(icp_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    icp = _own(db, icp_id, user)
    log_activity(db, user, "icp.deleted", "icp", icp.id, meta={"name": icp.name})
    db.delete(icp)
    db.flush()
    rescore_all(db, user)
    db.commit()
    return Response(status_code=204)
