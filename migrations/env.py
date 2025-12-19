from logging.config import fileConfig
import os
from sqlalchemy import create_engine
from alembic import context
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import your Base from the new location
from app.db.base_class import Base 

# Import all your models so Alembic can see them
from app.models import user, blacklist, story 

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get the database URL from the environment variable
db_url = os.getenv("DATABASE_URL")
if not db_url:
    # Fallback to the .ini file if the environment variable is not set
    db_url = config.get_main_option("sqlalchemy.url")
    if not db_url or db_url == '${DATABASE_URL}':
        raise ValueError("Database URL not found in environment variable or alembic.ini")

# Set the URL in the config for other parts of Alembic that might need it
config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=db_url, # Use the db_url we fetched
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Create the engine manually from the db_url
    connectable = create_engine(db_url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
