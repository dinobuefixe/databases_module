from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool

from alembic import context

from models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The URL comes from the environment, so no credentials live in alembic.ini.
database_url = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:change-me-postgres@localhost:5432/ex12",
)
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Keep autogenerate inside the tables mapped in ``models.py``.

    Pagila has around 30 tables and the exercise maps five. Without this filter,
    ``alembic revision --autogenerate`` would see every unmapped table as
    "removed from the model" and emit ``op.drop_table`` for each one. It would
    also try to drop every unmapped column and index of the mapped tables.
    """
    if type_ == "table":
        return name in Base.metadata.tables

    table = getattr(object, "table", None)
    if table is not None and table.name in Base.metadata.tables:
        mapped = Base.metadata.tables[table.name]
        if type_ == "column":
            return name in mapped.columns
        if type_ == "index":
            return name in {index.name for index in mapped.indexes}
        if type_ == "unique_constraint":
            return name in {
                constraint.name
                for constraint in mapped.constraints
                if constraint.name
            }
        return True

    # Anything attached to a table we did not map is ignored.
    return table is None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
