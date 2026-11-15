from sqlalchemy import select

from .config import get_settings
from .database import SessionLocal
from .models import Household, PantryStaple


def main():
    settings = get_settings()
    with SessionLocal() as db:
        household = db.scalar(select(Household).limit(1))
        if not household:
            household = Household(name=settings.household_name)
            db.add(household)
            db.flush()
        if not db.scalar(select(PantryStaple).where(PantryStaple.household_id == household.id)):
            for name in ['Olive oil', 'Garlic', 'Salt', 'Black pepper', 'Dried oregano', 'Rice', 'Flour']:
                db.add(PantryStaple(household_id=household.id, name=name, normalized_name=name.casefold()))
        db.commit()
    print('Shared household workspace and pantry staples are ready.')


if __name__ == '__main__':
    main()
