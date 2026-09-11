"""Synthetic tenant data and identity; upgrade is transactional in PostgreSQL."""
from alembic import op

revision = "0001"
down_revision = None


def upgrade():
    for statement in [
        "CREATE TABLE auth_organizations (id uuid PRIMARY KEY, active boolean NOT NULL DEFAULT true)",
        "CREATE TABLE auth_users (id uuid PRIMARY KEY, username varchar(120) UNIQUE NOT NULL, password_hash text NOT NULL, hash_policy text NOT NULL, active boolean NOT NULL DEFAULT true)",
        "CREATE UNIQUE INDEX auth_users_casefold ON auth_users(lower(username))",
        "CREATE TABLE auth_memberships (user_id uuid REFERENCES auth_users(id), org_id uuid REFERENCES auth_organizations(id), active boolean NOT NULL DEFAULT true, permissions jsonb NOT NULL DEFAULT '[]', PRIMARY KEY(user_id,org_id))",
        "CREATE TABLE records (id uuid PRIMARY KEY, org_id uuid NOT NULL REFERENCES auth_organizations(id), label varchar(160) NOT NULL, parent_id uuid, UNIQUE(id,org_id), FOREIGN KEY(parent_id,org_id) REFERENCES records(id,org_id))",
    ]:
        op.execute(statement)


def downgrade():
    raise RuntimeError("Destructive downgrade is excluded; restore a reviewed backup or apply a forward fix")
