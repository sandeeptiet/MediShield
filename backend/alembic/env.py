"""Alembic migration environment.

Wires Alembic to the SQLAlchemy metadata and uses MYSQL_URL from settings.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# TODO (Phase 2): import Base from app.database and all model modules so
# autogenerate picks up table definitions.
# from app.database import Base
# from app.models import user, case, audit_log  # noqa: F401

target_metadata = None  # set to Base.metadata in Phase 2

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
