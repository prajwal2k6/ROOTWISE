"""Create only the established ROOTWISE Farmer and Farm tables if absent."""

from app.database import Base, engine
from app.models.farm import Farm
from app.models.farmer import Farmer


def main() -> None:
    Base.metadata.create_all(
        bind=engine,
        tables=[Farmer.__table__, Farm.__table__],
    )


if __name__ == "__main__":
    main()
