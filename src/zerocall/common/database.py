from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from zerocall.common.config import Settings


class Base(DeclarativeBase):
    pass


def make_engine(settings: Settings) -> Engine:
    url = make_url(settings.database_url.get_secret_value())
    sqlite = url.drivername == "sqlite+pysqlite"
    engine = create_engine(
        url,
        echo=False,
        hide_parameters=True,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False, "timeout": 5} if sqlite else {
            "connect_timeout": 5,
            "options": "-c statement_timeout=15000 -c lock_timeout=5000",
        },
    )

    if sqlite:
        @event.listens_for(engine, "connect")
        def configure_connection(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def make_sessions(engine: Engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


def check_database(engine: Engine) -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
