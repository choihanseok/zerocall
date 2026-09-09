from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from zerocall.common.config import Settings
from zerocall.common.database import make_engine

ROOT = Path(__file__).resolve().parents[1]


def migrate(engine, revision="head"):
    config = Config(str(ROOT / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, revision)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        _env_file=None,
        environment="TEST",
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}",
    )


@pytest.fixture
def engine(settings):
    engine = make_engine(settings)
    migrate(engine)
    yield engine
    engine.dispose()
