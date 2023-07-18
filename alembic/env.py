import models
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import create_engine
from sqlalchemy.schema import MetaData
from sqlalchemy import text

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# Replace 'your_schema' with the schema you want to use.

custom_schema = 'public'
# config.set_main_option(
#     'sqlalchemy.url', f"{config.get_main_option('sqlalchemy.url')}?options=-csearch_path={custom_schema}")

print("Imported Models: ", models)
print("MetaData from improted Models: ", models.Base.metadata)
target_metadata = models.Base.metadata
target_metadata.schema = custom_schema

# The following line is needed to ensure the schema is used for alembic_version table

metadata = MetaData(schema=custom_schema)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

url = "postgresql://wizard_app:password@localhost:5432/wizards_database"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # url = config.get_main_option("sqlalchemy.url")
    print(config.get_main_option("sqlalchemy.url"))

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # ここがおかしい？
    # url = config.get_main_option("sqlalchemy.url")
    print("URL from alembic.ini: ", config.get_main_option("sqlalchemy.url"))
    print("URL in env.py: ", url)

    connectable = models.engine
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolcnannikalass=pool.NullPool,
    # )

    # Print out the engine's connection URL
    print(f"Engine URL: {models.engine.url}")

    print("connectable: ", connectable)

    with connectable.connect() as connection:
        with connection.begin():
            connection.execute(text("SET search_path TO public"))
        context.configure(
            url=url,
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=custom_schema,
            metadata=metadata
        )

        result = connection.execute(text("SHOW search_path"))
        for row in result:
            print(f"Current search path: {row}")

        print("Connection info: ", connection)
        print("Connection info: ", connection.__dict__)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
