import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

DEFAULT_DATABASE_URL = (
    "sqlite:////data/recipes.db"
    if os.path.isdir("/data")
    else "sqlite:///./recipes.db"
)
DATABASE_URL = os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
