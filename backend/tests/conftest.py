"""Shared fixtures: an in-memory SQLite database and an API client.

The FastAPI dependency is overridden so tests never touch MySQL; the
TestClient is used without its context manager so the app lifespan
(which would create tables on the real engine) does not run.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Question


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def make_question(db):
    """Factory that inserts a question and returns it."""

    def _make(
        subgroup: str = "se_tc",
        level: int = 1,
        answer: tuple[int, ...] = (0,),
        n_choices: int = 5,
        group: str = "verbal",
        question_text: str = "question",
        explanation_ko: str = "한국어 해설입니다.",
        passage: str | None = None,
    ) -> Question:
        question = Question(
            group=group,
            subgroup=subgroup,
            level=level,
            question_type="multi" if len(answer) > 1 else "single",
            select_count=len(answer),
            passage=passage,
            question_text=question_text,
            choices=[f"choice {i}" for i in range(n_choices)],
            answer=list(answer),
            explanation_ko=explanation_ko,
        )
        db.add(question)
        db.commit()
        return question

    return _make
