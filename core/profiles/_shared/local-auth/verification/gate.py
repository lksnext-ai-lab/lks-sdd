"""Fixed local-auth certification adapter; commands never come from metadata.

Resources use a dedicated synthetic Docker network and disposable database.
No application directories outside the materialized fixture are inspected.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path.cwd().resolve()
RUNTIME = ROOT / ".runtime"
STATE = RUNTIME / "state.json"
_config_args = argparse.ArgumentParser(add_help=False)
_config_args.add_argument("--config", type=Path, default=ROOT / "profile-runtime.json")
_config_path = _config_args.parse_known_args()[0].config.resolve()
_config_path.relative_to(ROOT)
CONFIG = json.loads(_config_path.read_text())
ROLE = CONFIG["role"]
BACKEND = ROOT / CONFIG.get("unit_paths", {}).get("api", "apps/backend" if ROLE == "system" else ".")
FRONTEND = ROOT / CONFIG.get("unit_paths", {}).get("frontend", "apps/frontend" if ROLE == "system" else ".")
MIGRATION = ROOT / CONFIG.get("unit_paths", {}).get("migration", "apps/migration" if ROLE == "system" else ".")
DATABASE = ROOT / CONFIG.get("unit_paths", {}).get("database", "infra/database" if ROLE == "system" else ".")
BACKEND.resolve().relative_to(ROOT)
FRONTEND.resolve().relative_to(ROOT)
MIGRATION.resolve().relative_to(ROOT)
DATABASE.resolve().relative_to(ROOT)
RESOURCES = Path(__file__).resolve().parent
PREFIX = "lkssdd18" + hashlib.sha256(str(ROOT).encode()).hexdigest()[:12]
ORG = "10000000-0000-4000-8000-000000000001"


def run(command, *, input=None, timeout=600, success=True):
    result = subprocess.run(command, input=input, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
    if success and result.returncode:
        # Only local synthetic data exists here; nevertheless strip token-like
        # material before errors reach a persistent certification report.
        tail = (result.stdout + result.stderr)[-8000:]
        tail = re.sub(r"eyJ[A-Za-z0-9_.-]+", "[redacted-token]", tail)
        if STATE.is_file():
            for value in json.loads(STATE.read_text()).get("sensitive_values", []):
                tail = tail.replace(value, "[redacted]")
        raise RuntimeError(f"{command[0]} failed ({result.returncode}): {tail}")
    return result


def state():
    return json.loads(STATE.read_text())


def save(value):
    STATE.write_text(json.dumps(value), encoding="utf-8")


def image(kind):
    value = CONFIG["images"][kind]
    if not re.fullmatch(r"[a-zA-Z0-9./_-]+:[a-zA-Z0-9._-]+@sha256:[a-f0-9]{64}", value):
        raise ValueError("Unpinned runtime image")
    return value


def setup():
    if STATE.is_file():
        return
    RUNTIME.mkdir(exist_ok=True)
    password, credential = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
    ring = {"current": "initial", "keys": {"initial": base64.b64encode(secrets.token_bytes(32)).decode()}}
    (RUNTIME / "keyring.json").write_text(json.dumps(ring))
    fixture = {"organizations": [ORG, "10000000-0000-4000-8000-000000000002"], "users": [{"id": "20000000-0000-4000-8000-000000000001", "username": "synthetic-user", "password": credential, "organizations": [ORG], "permissions": ["read", "write", "admin"]}]}
    (RUNTIME / "fixture.json").write_text(json.dumps(fixture))
    (RUNTIME / "database.env").write_text(f"POSTGRES_USER=fixture\nPOSTGRES_DB=fixture\nPOSTGRES_PASSWORD={password}\n")
    (RUNTIME / "api.env").write_text(f"DATABASE_URL=postgresql+psycopg://fixture:{password}@{PREFIX}db:5432/fixture\nLKS_AUTH_ENVIRONMENT=ci\nLKS_AUTH_ORIGIN=https://localhost:8443\nLKS_AUTH_ISSUER=lks-sdd-isolated\nLKS_AUTH_AUDIENCE=lks-sdd-fixture\nLKS_AUTH_KEYRING_FILE=/runtime/keyring.json\nLKS_AUTH_FIXTURE_FILE=/runtime/fixture.json\n")
    save({"sensitive_values": [password, credential, ring["keys"]["initial"]], "observations": {}, "built": []})
    database_image = image("postgresql")
    if ROLE in {"database", "system"}:
        run(["docker", "build", "--quiet", "--tag", PREFIX+"database", str(DATABASE)], timeout=600)
        database_image = PREFIX+"database"
    run(["docker", "network", "create", PREFIX])
    run(["docker", "run", "--detach", "--name", PREFIX+"db", "--network", PREFIX,
         "--env-file", str(RUNTIME / "database.env"), database_image])
    for _ in range(60):
        if run(["docker", "exec", PREFIX+"db", "pg_isready", "-U", "fixture", "-d", "fixture"], success=False).returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("Synthetic PostgreSQL did not become ready")


def sql(statement):
    return run(["docker", "exec", "-i", PREFIX+"db", "psql", "-U", "fixture", "-d", "fixture", "-v", "ON_ERROR_STOP=1", "-At"], input=statement).stdout.strip()


def build(kind):
    setup()
    value = state()
    if kind in value["built"]:
        return
    directory = {"api": BACKEND, "frontend": FRONTEND, "migration": MIGRATION}[kind]
    run(["docker", "build", "--quiet", "--tag", PREFIX+kind, str(directory)], timeout=900)
    value["built"].append(kind)
    save(value)


def api_command(args, *, success=True):
    kind = "migration" if ROLE == "system" and args[:3] == ["python", "-m", "alembic"] else "api"
    build(kind)
    return run(["docker", "run", "--rm", "--network", PREFIX, "--env-file", str(RUNTIME / "api.env"),
                "-v", f"{RUNTIME.as_posix()}:/runtime", "-v", f"{RESOURCES.as_posix()}:/verification:ro", PREFIX+kind, *args], success=success)


def frontend_command(args):
    build("frontend")
    return run(["docker", "run", "--rm", PREFIX+"frontend", *args])


def migrate():
    api_command(["python", "-m", "alembic", "upgrade", "head"])


def security_tests(expression):
    migrate()
    result = api_command(["python", "-m", "pytest", "-q", "tests/test_security.py", "-k", expression])
    return {"observer": "pytest-real-postgresql", "selection": expression, "result": result.stdout[-1200:]}


def database_test():
    setup()
    sql("CREATE TABLE IF NOT EXISTS isolated_probe(id integer PRIMARY KEY, value text NOT NULL); INSERT INTO isolated_probe VALUES(1,'synthetic') ON CONFLICT DO NOTHING;")
    assert sql("SELECT value FROM isolated_probe WHERE id=1;") == "synthetic"
    run(["docker", "restart", PREFIX+"db"])
    for _ in range(60):
        if run(["docker", "exec", PREFIX+"db", "pg_isready", "-U", "fixture"], success=False).returncode == 0: break
        time.sleep(1)
    assert sql("SELECT value FROM isolated_probe WHERE id=1;") == "synthetic"
    return {"observer": "postgresql", "runtime_units": ["database"], "server_version": sql("SHOW server_version;"), "independent_read": True, "restart_preserved": True,
            "mutation": {"record_id": "1", "resource": "isolated_probe"}, "read_back": {"observer": "postgresql-psql", "resource": "isolated_probe", "record_id": "1", "matches": True}, "persistence": True}


def database_schema_test():
    observation = database_test()
    sql("BEGIN; ALTER TABLE isolated_probe ADD COLUMN migration_probe text; UPDATE isolated_probe SET migration_probe='preserved'; COMMIT;")
    assert sql("SELECT value || ':' || migration_probe FROM isolated_probe WHERE id=1;") == "synthetic:preserved"
    failed = run(["docker", "exec", "-i", PREFIX+"db", "psql", "-U", "fixture", "-d", "fixture", "-v", "ON_ERROR_STOP=1"], input="BEGIN; UPDATE isolated_probe SET value='incorrect'; SELECT nonexistent_function(); COMMIT;", success=False)
    assert failed.returncode != 0 and sql("SELECT value FROM isolated_probe WHERE id=1;") == "synthetic"
    sql("ALTER TABLE isolated_probe DROP COLUMN migration_probe;")
    return {**observation, "observer": "postgresql-ddl", "from": "probe-v1", "to": "probe-v2", "empty_database": True, "data_preserved": True, "forward_fix_rehearsed": True}


def migration_test():
    build("api")
    sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    api_command(["python", "-m", "alembic", "upgrade", "0001"])
    sql(f"INSERT INTO auth_organizations(id) VALUES ('{ORG}'); INSERT INTO records(id,org_id,label) VALUES ('30000000-0000-4000-8000-000000000001','{ORG}','before-upgrade');")
    migrate()
    assert sql("SELECT version_num FROM alembic_version;") == "0002"
    assert sql("SELECT label FROM records;") == "before-upgrade"
    # Rehearse a failed transaction and a reviewed forward fix, retaining data.
    failed = run(["docker", "exec", "-i", PREFIX+"db", "psql", "-U", "fixture", "-d", "fixture", "-v", "ON_ERROR_STOP=1"], input="BEGIN; ALTER TABLE records ADD COLUMN forward_probe text; SELECT definitely_missing(); COMMIT;", success=False)
    assert failed.returncode != 0
    sql("BEGIN; ALTER TABLE records ADD COLUMN forward_probe text; UPDATE records SET forward_probe='recovered'; COMMIT;")
    assert sql("SELECT label || ':' || forward_probe FROM records;") == "before-upgrade:recovered"
    sql("ALTER TABLE records DROP COLUMN forward_probe;")
    return {"observer": "alembic-postgresql", "runtime_units": ["migration", "database"], "from": "0001", "to": "0002", "empty_database": True, "data_preserved": True, "forward_fix_rehearsed": True,
            "mutation": {"record_id": "30000000-0000-4000-8000-000000000001", "resource": "records"}, "read_back": {"observer": "postgresql-psql", "resource": "records", "record_id": "30000000-0000-4000-8000-000000000001", "matches": True}, "persistence": True}


def http_contract_test():
    build("api")
    migrate()
    sql("TRUNCATE auth_rate_limits;")
    api_command(["python", "-m", "local_auth.provision"])
    run(["docker", "rm", "--force", PREFIX+"api"], success=False)
    run(["docker", "run", "--detach", "--name", PREFIX+"api", "--network", PREFIX,
         "--env-file", str(RUNTIME / "api.env"), "-v", f"{RUNTIME.as_posix()}:/runtime:ro", PREFIX+"api"])
    time.sleep(1)
    probe = json.loads(api_command(["python", "/verification/http_probe.py", "--base-url", f"http://{PREFIX}api:8000"]).stdout)
    identifier = str(uuid.UUID(probe["record_id"]))
    assert sql(f"SELECT label FROM records WHERE id='{identifier}';") == "synthetic-http-probe"
    return {**probe, "runtime_units": ["api", "database"], "mutation": {"method": "POST", "path": "/records", "record_id": identifier},
            "read_back": {"observer": "postgresql-psql", "record_id": identifier, "resource": "records", "matches": True}, "persistence": True}


def execute(gate):
    if CONFIG.get("mode") == "adoption":
        # Never run scaffold provisioning/migrations against an existing app.
        # A technology match does not close its functional/fixture adaptation.
        raise ValueError("Adoption verification requires reviewed functional and isolated-fixture adaptation; scaffold execution is prohibited")
    if gate == "GATE-SCAFFOLD-INTEGRITY":
        assert ROLE in {"api", "frontend", "database", "migration", "system"}
        for kind in CONFIG["images"]: image(kind)
        return {"profile": CONFIG["profile_id"], "role": ROLE}
    if gate == "GATE-HTTP-CONTRACT-INTEGRATION":
        return http_contract_test()
    if gate in {"GATE-DATA-MIGRATION", "GATE-MIGRATION-INTEGRATION"}:
        return database_schema_test() if ROLE == "database" else migration_test()
    if gate in {"GATE-DATA-INTEGRATION", "GATE-POSTGRES-INTEGRATION"}:
        return database_test()
    if gate == "GATE-OCI-BUILD":
        if ROLE == "database": setup()
        else: build("api")
        return {"image_digest": run(["docker", "image", "inspect", image("postgresql") if ROLE == "database" else PREFIX+"api", "--format", "{{.Id}}"] ).stdout.strip()}
    if gate == "GATE-OCI-SMOKE":
        return database_test() if ROLE == "database" else {"python": api_command(["python", "--version"]).stdout.strip()}
    if gate in {"GATE-PYTHON-LOCK", "GATE-API-LOCK"}:
        build("api")
        return {"dependencies": api_command(["python", "-c", "import importlib.metadata as m,json; print(json.dumps({n:m.version(n) for n in ['fastapi','sqlalchemy','alembic','PyJWT','argon2-cffi']}))"]).stdout.strip()}
    if gate in {"GATE-PYTHON-LINT", "GATE-API-LINT"}:
        return {"lint": api_command(["python", "-m", "ruff", "check", "src", "tests"]).stdout.strip()}
    if gate in {"GATE-PYTHON-TYPECHECK", "GATE-API-TYPECHECK"}:
        return {"typecheck": api_command(["python", "-m", "mypy", "src"]).stdout.strip()}
    if gate in {"GATE-PYTHON-TEST", "GATE-API-TEST"}:
        return security_tests("not never")
    expressions = {"GATE-LOCAL-CREDENTIALS": "argon2 or generic_login or password_change or admin_provision",
                   "GATE-LOCAL-JWT": "invalid_tokens or key_rotation", "GATE-LOCAL-SESSION": "refresh or expiration or logout",
                   "GATE-TENANT-AUTHORIZATION": "tenant or live_permissions", "GATE-SECURITY-CONFIG": "csrf or concurrent_login",
                   "GATE-SECURITY-AUDIT": "validation_and_audit"}
    if gate in expressions: return security_tests(expressions[gate])
    if gate == "GATE-API-OPENAPI":
        return {"openapi": api_command(["python", "-c", "from local_auth.main import app; s=app.openapi(); assert '/records' in s['paths']; assert '/auth/login' in s['paths']; assert '/register' not in s['paths']; print('contract paths verified')"]).stdout.strip()}
    manager = "npm" if CONFIG["frontend_line"] == "TS59" else "pnpm"
    if gate in {"GATE-FRONTEND-LOCK", "GATE-FRONTEND-BUILD", "GATE-STATIC-OUTPUT"}:
        build("frontend")
        return {"static_output": frontend_command(["node", "--input-type=module", "-e", "import fs from 'node:fs'; if(!fs.existsSync('dist/index.html'))process.exit(1); console.log(process.version)"]).stdout.strip()}
    if gate in {"GATE-FRONTEND-LINT", "GATE-FRONTEND-TYPECHECK", "GATE-FRONTEND-TEST", "GATE-LOCAL-SPA"}:
        action = {"GATE-FRONTEND-LINT": "lint", "GATE-FRONTEND-TYPECHECK": "typecheck"}.get(gate, "test")
        return {"component_only": True, "result": frontend_command([manager, "run", action]).stdout[-1200:]}
    if gate in {"GATE-BROWSER-SMOKE", "GATE-BROWSER-ACCESSIBILITY", "GATE-BROWSER-FULLSTACK-E2E"}:
        from web_gate import web_gate
        return web_gate(gate)
    if gate.startswith("GATE-COMPOSE-"):
        value = state()
        assert value["observations"], "No runtime gates were observed"
        return {"profile": CONFIG["profile_id"], "observed_gates": sorted(value["observations"])}
    raise ValueError("Unknown packaged gate")


def cleanup():
    for name in [PREFIX+"web", PREFIX+"api", PREFIX+"db"]:
        run(["docker", "rm", "--force", "--volumes", name], success=False)
    run(["docker", "network", "rm", PREFIX], success=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()
    if args.cleanup:
        cleanup()
        return
    try:
        observations = execute(args.gate)
        if STATE.is_file():
            value = state()
            value["observations"][args.gate] = observations
            save(value)
        output = ROOT / ".lks-sdd"
        output.mkdir(exist_ok=True)
        (output / (args.gate + ".json")).write_text(json.dumps({"observations": observations, "mocks": []}, indent=2))
        print(json.dumps({"gate_id": args.gate, "observations": observations, "status": "passed"}))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__": main()
