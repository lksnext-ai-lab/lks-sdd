"""Explicit isolated-fixture provisioning; no public registration endpoint."""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from sqlalchemy import create_engine, text

from .security import HASH_POLICY, Settings, password_hash


def main() -> None:
    settings = Settings.load()
    fixture = json.loads(Path(os.environ["LKS_AUTH_FIXTURE_FILE"]).read_text())
    engine = create_engine(settings.database_url, hide_parameters=True)
    with engine.begin() as conn:
        for org in fixture["organizations"]:
            conn.execute(text("INSERT INTO auth_organizations (id) VALUES (:id) ON CONFLICT DO NOTHING"), {"id": uuid.UUID(org)})
        for user in fixture["users"]:
            conn.execute(text("INSERT INTO auth_users (id,username,password_hash,hash_policy) VALUES (:id,:name,:hash,:policy) ON CONFLICT(id) DO UPDATE SET password_hash=EXCLUDED.password_hash,active=true"),
                         {"id": uuid.UUID(user["id"]), "name": user["username"], "hash": password_hash(user["password"]), "policy": HASH_POLICY})
            for org in user["organizations"]:
                conn.execute(text("INSERT INTO auth_memberships (user_id,org_id,permissions) VALUES (:id,:org,CAST(:permissions AS jsonb)) ON CONFLICT DO NOTHING"),
                             {"id": user["id"], "org": org, "permissions": json.dumps(user["permissions"])})


if __name__ == "__main__":
    main()
