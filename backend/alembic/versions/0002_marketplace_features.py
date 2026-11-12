"""Create additional marketplace feature tables."""
from alembic import op
from app.db import Base
from app import models, models_extra  # noqa: F401

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(op.get_bind())

def downgrade():
    for name in ['password_reset_tokens','email_tokens','payments','notifications','messages','reviews','favorites','refresh_sessions']:
        op.drop_table(name)
