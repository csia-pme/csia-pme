from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends
import config

Base = declarative_base()


def initialize_db(settings: config.Settings = Depends(config.get_settings)):
    engine = create_engine(
        settings.database_url, connect_args=settings.database_connect_args
    )

    Base.metadata.create_all(bind=engine)

    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# TODO: Correct linting errors below
def get_db(SessionLocal: Session = Depends(initialize_db)):
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
