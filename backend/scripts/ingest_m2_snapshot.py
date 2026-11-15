"""Explicitly ingest the bundled historical Bengaluru pilot into PostgreSQL."""

from app.database import SessionLocal
from app.services.data_ingestion_service import ingest_bengaluru_dataset


def main() -> None:
    with SessionLocal() as db:
        result = ingest_bengaluru_dataset(db)
    print(result)


if __name__ == "__main__":
    main()
