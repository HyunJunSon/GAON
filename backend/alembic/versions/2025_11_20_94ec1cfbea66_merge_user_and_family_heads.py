"""merge user and family heads

Revision ID: 94ec1cfbea66
Revises: 2687d42f5bc6, 740afd11abfe
Create Date: 2025-11-20 15:31:26.203123

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94ec1cfbea66'
down_revision = ('2687d42f5bc6', '740afd11abfe')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass