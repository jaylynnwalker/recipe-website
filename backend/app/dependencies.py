from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import Household


@dataclass(frozen=True)
class Workspace:
    household_id: str
    email: str | None = None


async def current_workspace(cf_access_jwt_assertion: str | None = Header(default=None), db: Session = Depends(get_db)) -> Workspace:
    settings = get_settings()
    household = db.scalar(select(Household).order_by(Household.created_at).limit(1))
    if settings.auth_mode == 'local':
        if not household:
            household = Household(name=settings.household_name)
            db.add(household); db.commit(); db.refresh(household)
        return Workspace(household_id=household.id)
    if settings.auth_mode != 'cloudflare':
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Invalid authentication configuration')
    if not settings.cloudflare_access_team_domain or not settings.cloudflare_access_audience or not cf_access_jwt_assertion:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Verified Cloudflare Access identity required')
    issuer = f"https://{settings.cloudflare_access_team_domain.rstrip('/')}"
    try:
        signing_key = PyJWKClient(f'{issuer}/cdn-cgi/access/certs').get_signing_key_from_jwt(cf_access_jwt_assertion)
        claims = jwt.decode(cf_access_jwt_assertion, signing_key.key, algorithms=['RS256'], audience=settings.cloudflare_access_audience, issuer=issuer)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid Cloudflare Access identity')
    if not household:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Household workspace is not initialized')
    return Workspace(household_id=household.id, email=claims.get('email'))
