"""Integration test fixtures. Skip when DATABASE_URL is unset or Postgres is unreachable."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _database_url() -> str | None:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    # Host-side default matching .env.example when Compose postgres is published.
    return "postgresql+psycopg://taxonomy:taxonomy@localhost:5432/taxonomy"


@pytest.fixture(scope="session")
def database_url() -> str:
    return _database_url()


@pytest.fixture(scope="session")
def engine(database_url: str) -> Generator[Engine, None, None]:
    # Ensure password is never stripped from env for later alembic/seed steps.
    os.environ["DATABASE_URL"] = database_url
    eng = create_engine(database_url, pool_pre_ping=True)
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — skip if postgres unavailable
        pytest.skip(f"Postgres unavailable at {database_url}: {exc}")
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def db_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def db_session(db_session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = db_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
