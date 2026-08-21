from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings
from app.db_models import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session, always closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
