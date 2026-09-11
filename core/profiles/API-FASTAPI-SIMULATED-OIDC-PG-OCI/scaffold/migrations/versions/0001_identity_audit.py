"""Create a minimal identity audit boundary."""

import sqlalchemy as sa
from alembic import op

revision = "0001_identity_audit"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "identity_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("subject_id", sa.String(length=255), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("identity_audit")
