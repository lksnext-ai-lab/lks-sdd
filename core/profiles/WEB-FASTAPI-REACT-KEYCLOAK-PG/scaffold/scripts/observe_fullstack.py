"""Observe the browser mutation independently in this disposable PostgreSQL."""
import json
import subprocess
import uuid
from pathlib import Path

compose = ["docker", "compose", "--env-file", "infra/compose/gate.env", "-f", "infra/compose/compose.yaml"]
subprocess.run([*compose, "run", "--rm", "e2e"], check=True)
path = Path(".lks-sdd/fullstack-evidence.json")
value = json.loads(path.read_text())
mutation = value["observations"]["mutation"]
identifier = str(uuid.UUID(mutation["record_id"]))
query = f"SELECT label FROM reference_items WHERE id='{identifier}';"
# Compose expands only its packaged environment, never an untrusted command.
result = subprocess.run([*compose, "exec", "-T", "postgres", "sh", "-c",
                         'psql -U "$POSTGRES_USER" -d app -v ON_ERROR_STOP=1 -At'],
                        input=query, text=True, capture_output=True, check=True)
if result.stdout.strip() != mutation["label"]:
    raise ValueError("Independent PostgreSQL observation differs from UI mutation")
value["observations"]["read_back"] = {"observer": "postgresql-psql", "record_id": identifier,
                                       "resource": "reference_items", "matches": True}
value["observations"]["persistence"] = True
path.write_text(json.dumps(value, indent=2) + "\n")
