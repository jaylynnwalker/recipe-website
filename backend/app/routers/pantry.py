from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import Workspace, current_workspace
from ..models import PantryStaple
from ..schemas import PantryStapleCreate, PantryStapleRead


router = APIRouter(prefix='/pantry-staples', tags=['pantry staples'])


@router.get('', response_model=list[PantryStapleRead])
async def list_staples(workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    return db.scalars(select(PantryStaple).where(PantryStaple.household_id == workspace.household_id).order_by(PantryStaple.name)).all()


@router.post('', response_model=PantryStapleRead, status_code=status.HTTP_201_CREATED)
async def create_staple(payload: PantryStapleCreate, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    name = ' '.join(payload.name.split())
    staple = PantryStaple(household_id=workspace.household_id, name=name, normalized_name=name.casefold())
    db.add(staple)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Pantry staple already exists')
    db.refresh(staple)
    return staple


@router.delete('/{staple_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_staple(staple_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    staple = db.scalar(select(PantryStaple).where(PantryStaple.id == staple_id, PantryStaple.household_id == workspace.household_id))
    if not staple:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Pantry staple not found')
    db.delete(staple)
    db.commit()
