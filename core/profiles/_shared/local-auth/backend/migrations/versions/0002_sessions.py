"""Server-side sessions preserve records and users from revision 0001."""
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade():
    for statement in [
        "CREATE TABLE auth_sessions (id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES auth_users(id), org_id uuid NOT NULL REFERENCES auth_organizations(id), created_at timestamptz NOT NULL DEFAULT now(), last_seen timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL, revoked boolean NOT NULL DEFAULT false)",
        "CREATE INDEX auth_sessions_user ON auth_sessions(user_id)",
        "CREATE TABLE auth_refresh_tokens (token_hash char(64) PRIMARY KEY, session_id uuid NOT NULL REFERENCES auth_sessions(id), consumed boolean NOT NULL DEFAULT false)",
        "CREATE INDEX auth_refresh_session ON auth_refresh_tokens(session_id)",
        "CREATE TABLE auth_recovery (token_hash char(64) PRIMARY KEY, user_id uuid NOT NULL REFERENCES auth_users(id), expires_at timestamptz NOT NULL, consumed boolean NOT NULL DEFAULT false)",
        "CREATE TABLE auth_rate_limits (key text PRIMARY KEY, attempts integer NOT NULL, window_start timestamptz NOT NULL)",
        "CREATE TABLE security_audit (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, event text NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now())",
    ]:
        op.execute(statement)


def downgrade():
    raise RuntimeError("Session migration uses forward recovery; destructive downgrade is excluded")
