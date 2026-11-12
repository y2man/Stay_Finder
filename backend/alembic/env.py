
import sys
from pathlib import Path

# Add the backend directory to Python's import path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import context
from sqlalchemy import create_engine
from app.config import settings
from app.db import Base
from app import models  # noqa
from app import models_extra  # noqa


def run():
    eng = create_engine(settings.DATABASE_URL)
    with eng.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


run()
