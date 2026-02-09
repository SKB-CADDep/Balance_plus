import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = sqlalchemy.orm.declarative_base()


def init_db() -> None:
    # Tables are created with Alembic migrations
    pass

