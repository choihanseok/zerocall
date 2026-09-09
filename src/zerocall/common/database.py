from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from zerocall.common.config import Settings


class Base(DeclarativeBase):
    pass


def make_engine(settings: Settings) -> Engine:
    engine = create_engine(
        settings.database_url.get_secret_value(),
        echo=False,
        hide_parameters=True,
        connect_args={"check_same_thread": False, "timeout": 5},
    )

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
