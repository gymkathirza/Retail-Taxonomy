"""Integration: migrate + seed must yield PDF taxonomy counts and wrap names."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

WRAP_NAMES = (
    "Refrigerated English Muffins and Biscuits",
    "Refrigerated Sweet Breakfast Baked Goods",
)

def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "data" / "seed" / "taxonomy.csv").is_file():
            return parent
        if (parent / "apps" / "api" / "alembic.ini").is_file():
            return parent
        # Container layout: /app is apps/api; repo files mounted at /data and /app/scripts
        if (parent / "alembic.ini").is_file() and Path("/data/seed/taxonomy.csv").is_file():
            return Path("/")
    raise RuntimeError("Could not locate repository root from test file")


REPO_ROOT = _repo_root()
API_ROOT = REPO_ROOT / "apps" / "api"
if not (API_ROOT / "alembic.ini").is_file():
    # Running inside API container where WORKDIR is /app
    API_ROOT = Path("/app")


def _ensure_schema_and_seed(engine) -> None:
    """Apply migrations and run idempotent seed against the test database."""
    from alembic import command
    from alembic.config import Config

    alembic_ini = API_ROOT / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))
    command.upgrade(cfg, "head")

    seed_candidates = [
        REPO_ROOT / "scripts" / "seed.py",
        Path("/app/scripts/seed.py"),
        Path("/scripts/seed.py"),
    ]
    seed_script = next((p for p in seed_candidates if p.is_file()), None)
    assert seed_script is not None, "scripts/seed.py must exist"
    # Import and run seed in-process so DATABASE_URL matches the test engine.
    import importlib.util
    import os

    os.environ["DATABASE_URL"] = engine.url.render_as_string(hide_password=False)
    if Path("/data/seed/taxonomy.csv").is_file():
        os.environ["TAXONOMY_SEED_CSV"] = "/data/seed/taxonomy.csv"
    spec = importlib.util.spec_from_file_location("seed", seed_script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


@pytest.fixture(scope="module")
def seeded_engine(engine):
    _ensure_schema_and_seed(engine)
    return engine


@pytest.fixture
def seeded_session(seeded_engine, db_session_factory) -> Session:
    session = db_session_factory()
    try:
        yield session
    finally:
        session.close()


def test_seed_counts_match_pdf(seeded_session: Session) -> None:
    from app.models import Category, Department, Subcategory, Zone

    assert seeded_session.scalar(select(func.count()).select_from(Zone)) == 2
    assert seeded_session.scalar(select(func.count()).select_from(Department)) == 8
    assert seeded_session.scalar(select(func.count()).select_from(Category)) == 25
    assert seeded_session.scalar(select(func.count()).select_from(Subcategory)) == 61

    zones = {z.name for z in seeded_session.scalars(select(Zone)).all()}
    assert zones == {"Center", "Perimeter"}

    names = set(seeded_session.scalars(select(Subcategory.name)).all())
    for wrap in WRAP_NAMES:
        assert wrap in names

    active = seeded_session.scalar(
        select(func.count()).select_from(Subcategory).where(Subcategory.is_active.is_(True))
    )
    assert active == 61


def test_seed_is_idempotent(seeded_engine, seeded_session: Session) -> None:
    from app.models import Subcategory

    before = seeded_session.scalar(select(func.count()).select_from(Subcategory))
    _ensure_schema_and_seed(seeded_engine)
    seeded_session.expire_all()
    after = seeded_session.scalar(select(func.count()).select_from(Subcategory))
    assert before == after == 61
