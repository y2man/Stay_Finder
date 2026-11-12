"""initial schema incl. btree_gist exclusion constraint"""
from alembic import op
from app.db import Base
from app import models  # noqa
from app import models_extra  # noqa

revision = "0001"; down_revision = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    Base.metadata.create_all(op.get_bind())

def downgrade():
    Base.metadata.drop_all(op.get_bind())
