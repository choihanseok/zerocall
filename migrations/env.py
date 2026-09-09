from alembic import context

from zerocall.account.persistence import AccountRow  # noqa: F401
from zerocall.common.config import load_settings
from zerocall.common.database import Base, make_engine

target_metadata = Base.metadata

if context.is_offline_mode():
    raise RuntimeError("Offline migrations are not enabled; use a configured local database")

provided = context.config.attributes.get("connection")
if provided is not None:
    context.configure(connection=provided, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(load_settings())
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()
