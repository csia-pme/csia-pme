from functools import lru_cache
from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from config import Settings, get_settings


def initialize_db(settings: Settings = Depends(get_settings)):
    """Initialize the database connection."""
    engine = create_engine(
        settings.database_url, connect_args=settings.database_connect_args
    )

    SQLModel.metadata.create_all(engine)

    return engine


def get_session(engine=Depends(initialize_db)):
    """Get a database session."""
    with Session(engine) as session:
        yield session
