from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_database_schema():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        rows = connection.execute(text("PRAGMA table_info(exhibitions)")).fetchall()
        columns = {row[1] for row in rows}
        additions = {
            "location_name": "VARCHAR",
            "duration_minutes": "INTEGER DEFAULT 15",
            "recommended_for": "VARCHAR",
            "cautions": "TEXT",
            "stage_start_time": "VARCHAR",
            "ticket_status": "VARCHAR",
            "capacity_status": "VARCHAR",
        }
        for name, ddl in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE exhibitions ADD COLUMN {name} {ddl}"))

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
