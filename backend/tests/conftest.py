from pathlib import Path

import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.models import Household


@pytest.fixture()
def db_session(tmp_path: Path):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    with TestingSession() as session:
        household = Household(name='Our Kitchen')
        session.add(household)
        session.commit()
        yield session


@pytest.fixture()
def anyio_backend():
    return 'asyncio'


@pytest.fixture()
async def client(db_session, tmp_path: Path):
    async def override_db():
        yield db_session
    app.dependency_overrides[get_db] = override_db
    settings = get_settings()
    old_media_root = settings.media_root
    old_auth_mode = settings.auth_mode
    old_team_domain = settings.cloudflare_access_team_domain
    old_audience = settings.cloudflare_access_audience
    settings.auth_mode = 'local'
    settings.media_root = tmp_path / 'media'
    settings.media_root.mkdir()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as test_client:
        yield test_client
    settings.media_root = old_media_root
    settings.auth_mode = old_auth_mode
    settings.cloudflare_access_team_domain = old_team_domain
    settings.cloudflare_access_audience = old_audience
    app.dependency_overrides.clear()


@pytest.fixture()
async def authenticated(client: httpx.AsyncClient):
    return client


@pytest.fixture()
def recipe_payload():
    return {
        'title': 'Test Supper', 'description': 'A persisted recipe.', 'status': 'Our Rotation', 'cuisine': 'American', 'protein': 'Vegetarian',
        'tags': ['Quick'], 'categories': ['Dinner'], 'prep_minutes': 10, 'cook_minutes': 20, 'base_servings': 4,
        'ingredients': [{'name': 'Carrots', 'quantity': 2, 'unit': None, 'note': 'sliced', 'optional': False}],
        'steps': [{'instruction': 'Cook until tender.', 'tip': 'Use a wide pan.'}], 'notes': 'Household note',
        'source': {'type': 'family', 'label': 'Recipe card', 'url': None, 'page': None},
    }
