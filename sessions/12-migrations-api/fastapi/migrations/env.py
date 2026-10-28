import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

from app.models import Base

load_dotenv()

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# autogenerate compares these models with the database.
target_metadata = Base.metadata
DATABASE_URL = os.environ["DATABASE_URL"]


def include_object(obj, name, type_, reflected, compare_to):
    """Ignore what exists in the database but not in the models.

    Pagila has about twenty tables and we map one, with only some of its columns.
    Without this filter, autogenerate would propose dropping every table, column
    and index it does not see in Base.metadata.
    """
    if reflected and compare_to is None:
        return False
    return True


def run_migrations_offline() -> None:
    """alembic upgrade head --sql: print the SQL instead of running it."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
