"""Real HTTPS browser/HTTP observer. System mode never intercepts business API."""
import json
import time

import gate as runtime


def web_gate(gate_id):
    if runtime.ROLE != "system":
        # SPA-only smoke/a11y exercise its login surface, not a mocked business
        # composition. No joint persistence claim is made here.
        runtime.build("frontend")
    else:
        runtime.build("api")
        runtime.migrate()
        runtime.sql("TRUNCATE auth_rate_limits;")
        runtime.api_command(["python", "-m", "local_auth.provision"])
        runtime.build("frontend")
    image = runtime.image
    run = runtime.run
    run(["docker", "run", "--rm", "-v", f"{runtime.RUNTIME.as_posix()}:/certs", image("python"),
         "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2", "-subj", "/CN=localhost",
         "-addext", "subjectAltName=DNS:localhost", "-keyout", "/certs/tls.key", "-out", "/certs/tls.crt"])
    static = runtime.RUNTIME / "static"
    static.mkdir(exist_ok=True)
    run(["docker", "create", "--name", runtime.PREFIX+"assets", runtime.PREFIX+"frontend"])
    try:
        run(["docker", "cp", runtime.PREFIX+"assets:/app/dist/.", str(static)])
    finally:
        run(["docker", "rm", runtime.PREFIX+"assets"])
    run(["docker", "rm", "--force", runtime.PREFIX+"web", runtime.PREFIX+"api"], success=False)
    if runtime.ROLE == "system":
        run(["docker", "run", "--detach", "--name", runtime.PREFIX+"api", "--network", runtime.PREFIX,
             "--env-file", str(runtime.RUNTIME / "api.env"), "-v", f"{runtime.RUNTIME.as_posix()}:/runtime:ro", runtime.PREFIX+"api"])
    proxy = f"location ~ ^/(auth|admin|records|health|ready)(/|$) {{ proxy_pass http://{runtime.PREFIX}api:8000; proxy_set_header Host $host; }}" if runtime.ROLE == "system" else "location /auth/ { return 401; }"
    config = f"events {{}} http {{ include /etc/nginx/mime.types; access_log off; server {{ listen 8443 ssl; ssl_certificate /runtime/tls.crt; ssl_certificate_key /runtime/tls.key; root /static; {proxy} location / {{ try_files $uri /index.html; }} }} }}"
    (runtime.RUNTIME / "nginx.conf").write_text(config)
    run(["docker", "run", "--detach", "--name", runtime.PREFIX+"web", "--network", runtime.PREFIX,
         "-v", f"{runtime.RUNTIME.as_posix()}:/runtime:ro", "-v", f"{static.as_posix()}:/static:ro",
         image("nginx"), "nginx", "-c", "/runtime/nginx.conf", "-g", "daemon off;"])
    # Browser shares the HTTPS proxy network namespace: real https://localhost,
    # while no host ports, production hostnames or external application are used.
    test_root = runtime.RESOURCES / "browser"
    command = ["docker", "run", "--rm", "--network", "container:"+runtime.PREFIX+"web",
               "-e", "LKS_WEB_MODE="+runtime.ROLE, "-e", "LKS_WEB_GATE="+gate_id,
               "-v", f"{runtime.RUNTIME.as_posix()}:/runtime", "-v", f"{test_root.as_posix()}:/tests:ro", image("playwright"),
               "sh", "-c", "mkdir -p /work && cp /tests/* /work/ && cd /work && npm ci --ignore-scripts --no-audit --no-fund && npx playwright test --reporter=line"]
    run(command, timeout=600)
    value = json.loads((runtime.RUNTIME / "browser-evidence.json").read_text())
    if runtime.ROLE == "system":
        identifier = value["mutation"]["record_id"]
        # Validate identifier before any interpolation into the fixed SQL probe.
        import uuid
        uuid.UUID(identifier)
        label = runtime.sql(f"SELECT label FROM records WHERE id='{identifier}' AND org_id='{runtime.ORG}';")
        assert label == value["mutation"]["label"]
        run(["docker", "restart", runtime.PREFIX+"api"])
        time.sleep(1)
        assert runtime.sql(f"SELECT label FROM records WHERE id='{identifier}';") == label
        http = runtime.api_command(["python", "/verification/http_probe.py", "--base-url", f"http://{runtime.PREFIX}api:8000", "--record-id", identifier])
        value["read_after_restart"] = json.loads(http.stdout)
        value["read_back"] = {"observer": "postgresql-psql", "record_id": identifier, "resource": "records", "matches": True}
        value["persistence"] = True
        value["api_restart"] = True
        value["runtime_units"] = ["frontend", "api", "database", "migration"]
        value["participant_images"] = {role: run(["docker", "image", "inspect", runtime.PREFIX+role, "--format", "{{.Id}}"] ).stdout.strip() for role in value["runtime_units"]}
        try:
            run(["docker", "pause", runtime.PREFIX+"db"])
            fault = runtime.api_command(["python", "/verification/http_probe.py", "--base-url", f"http://{runtime.PREFIX}api:8000", "--database-unavailable"])
            value["database_unavailable"] = json.loads(fault.stdout)
        finally:
            run(["docker", "unpause", runtime.PREFIX+"db"], success=False)
        runtime.api_command(["python", "/verification/http_probe.py", "--base-url", f"http://{runtime.PREFIX}api:8000", "--record-id", identifier])
    return value
