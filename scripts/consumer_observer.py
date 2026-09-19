"""Run reviewed observers in a bounded Linux container, never in the host project."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from evidence_safety import evidence_safety_errors, sanitize
from observation_contract import gate_observation_errors, persistence_errors


class ObserverError(ValueError):
    """Invalid explicit local observer input or output."""


def checked_path(root: Path, relative: str) -> Path:
    path = root / relative
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ObserverError("Observer path escapes its root") from exc
    return path


def validate_schema(value: dict, name: str) -> None:
    import jsonschema
    schema = json.loads((Path(__file__).resolve().parents[1] / "schemas" / name).read_text(encoding="utf-8"))
    try:
        jsonschema.validate(value, schema)
    except jsonschema.ValidationError as exc:
        raise ObserverError("Observer schema validation failed: " + exc.message) from exc


def validate_output(output: dict, gate: dict, nonce: str, output_root: Path) -> dict:
    validate_schema(output, "consumer-observation.schema.json")
    if output["run_nonce"] != nonce or output["gate_id"] != gate["id"]:
        raise ObserverError("Observer output is not from this invocation")
    if set(output["scopes"]) != set(gate["scopes"]) or set(output["interfaces"]) != set(
        gate["interfaces"]
    ):
        raise ObserverError(
            "Observer scopes/interfaces differ from the approved contract"
        )
    if evidence_safety_errors(output):
        raise ObserverError("Observer output contains sensitive evidence")
    check = {
        "name": "visual-browser-review"
        if gate["id"] == "GATE-VISUAL-BROWSER-REVIEW"
        else gate["id"],
        "gate_id": gate["id"],
        "status": output["status"],
        "evidence_scopes": output["scopes"],
        "interface_ids": output["interfaces"],
        "observations": output["observations"],
        "mocks": [],
    }
    if output["status"] == "passed":
        errors = gate_observation_errors(check)
        if "persistence" in gate["scopes"]:
            errors.extend(persistence_errors(output["observations"]))
        if any(
            x in gate["scopes"] for x in ("composition", "user-flow", "persistence")
        ):
            if output["observations"].get("domain_mocks") is not False:
                errors.append(
                    "Integration requires an explicit absence of domain mocks"
                )
        if errors:
            raise ObserverError(
                "Insufficient runtime observations: " + "; ".join(errors)
            )
    artifacts = []
    paths = set()
    total = 0
    for artifact in output["artifacts"]:
        path = checked_path(output_root, artifact["path"])
        if (
            not path.is_file()
            or path.stat().st_size > 16 * 1024 * 1024
            or artifact["path"] in paths
        ):
            raise ObserverError("Invalid or duplicate observer artifact")
        paths.add(artifact["path"])
        data = path.read_bytes()
        total += len(data)
        if total > 32 * 1024 * 1024:
            raise ObserverError("Observer artifacts exceed 32 MB")
        if hashlib.sha256(data).hexdigest() != artifact["sha256"]:
            raise ObserverError("Observer artifact hash mismatch")
        artifacts.append({**artifact, "size": len(data)})
    return {**check, "artifacts": artifacts}


def execute(root: Path, gate: dict, hashes: dict[str, str]) -> tuple[dict, dict[str, bytes]]:
    """No shell, network, canonical mounts, host environment or unpinned images."""
    if gate["source"] != "approved-consumer":
        raise ObserverError("Only an explicit approved consumer observer is executable")
    nonce = uuid.uuid4().hex
    name = "lkssdd-observer-" + nonce
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="lks-observer-") as directory:
        temp = Path(directory)
        inputs, outputs = temp / "input", temp / "output"
        inputs.mkdir()
        outputs.mkdir()
        for relative, expected in hashes.items():
            source = checked_path(root, relative)
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ObserverError("Inputs changed before isolated execution")
            destination = inputs / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        command = list(gate["observer"]["command"])
        if not command or any("\x00" in x for x in command):
            raise ObserverError("Invalid observer command")
        docker = [
            "docker",
            "run",
            "--pull=never",
            "--name",
            name,
            "--network=none",
            "--read-only",
            "--user=65534:65534",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=128",
            "--memory=512m",
            "--cpus=1",
            "--ulimit=fsize=16777216:16777216",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=128m",
            "--workdir=/input",
            "--mount",
            f"type=bind,source={inputs},target=/input,readonly",
            "--mount",
            f"type=bind,source={outputs},target=/output",
            "--env",
            "LKS_RUN_NONCE=" + nonce,
            "--env",
            "LKS_GATE_ID=" + gate["id"],
            "--env",
            "LKS_OUTPUT=/output",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            "--env",
            "HOME=/tmp",
            "--entrypoint",
            command[0],
            gate["image"],
            *command[1:],
        ]
        # Bind directories are writable by the unprivileged container on Linux too.
        outputs.chmod(0o777)
        stdout_path, stderr_path = temp / "stdout", temp / "stderr"
        process = None
        failure = None
        returncode = None
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                process = subprocess.Popen(
                    docker, stdout=stdout, stderr=stderr, shell=False
                )
                deadline = time.monotonic() + gate["timeout_seconds"]
                while process.poll() is None:
                    if time.monotonic() > deadline:
                        failure = "Observer timed out"
                        break
                    if (
                        stdout_path.stat().st_size + stderr_path.stat().st_size
                        > 2 * 1024 * 1024
                    ):
                        failure = "Observer output exceeded 2 MB"
                        break
                    output_files = list(outputs.rglob("*"))
                    if (
                        len(output_files) > 128
                        or sum(p.lstat().st_size for p in output_files)
                        > 32 * 1024 * 1024
                    ):
                        failure = "Observer artifacts exceeded bounded output limits"
                        break
                    time.sleep(0.05)
                if failure:
                    process.kill()
                returncode = process.wait(timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            failure = "Observer process unavailable: " + type(exc).__name__
        finally:
            try:
                cleanup = subprocess.run(
                    ["docker", "rm", "-f", name], capture_output=True, timeout=20
                )
                if cleanup.returncode and b"No such container" not in cleanup.stderr:
                    failure = "Isolated container cleanup not confirmed"
            except (OSError, subprocess.SubprocessError):
                failure = "Isolated container cleanup not confirmed"
            if process and process.poll() is None:
                process.kill()
                process.wait(timeout=10)
        stdout = stdout_path.read_bytes() if stdout_path.exists() else b""
        stderr = stderr_path.read_bytes() if stderr_path.exists() else b""
        if len(stdout) + len(stderr) > 2 * 1024 * 1024:
            failure = "Observer output exceeded 2 MB"
        artifacts: dict[str, bytes] = {}
        try:
            if failure:
                raise ObserverError(failure)
            if returncode != 0:
                raise ObserverError(f"Observer exited with code {returncode}")
            if gate["source"] == "approved-consumer":
                output = json.loads(stdout.decode("utf-8"))
                check = validate_output(output, gate, nonce, outputs)
                for artifact in check["artifacts"]:
                    artifacts[artifact["sha256"]] = checked_path(
                        outputs, artifact["path"]
                    ).read_bytes()
            else:
                # Packaged commands retain their process-exit contract; raw logs are artifacts.
                if evidence_safety_errors(
                    {
                        "stdout": stdout.decode("utf-8", "replace"),
                        "stderr": stderr.decode("utf-8", "replace"),
                    }
                ):
                    raise ObserverError("Sensitive command output")
                sha = hashlib.sha256(stdout + stderr).hexdigest()
                artifacts[sha] = stdout + stderr
                check = {
                    "name": gate["id"],
                    "gate_id": gate["id"],
                    "status": "passed",
                    "evidence_scopes": gate["scopes"],
                    "interface_ids": gate["interfaces"],
                    "observations": {"exit_code": returncode},
                    "mocks": [],
                    "artifacts": [
                        {
                            "path": "process.log",
                            "sha256": sha,
                            "size": len(stdout + stderr),
                        }
                    ],
                }
                if set(gate["scopes"]) != {"component"}:
                    raise ObserverError(
                        "Structured scopes need an approved observer output"
                    )
        except (ObserverError, ValueError, UnicodeError, TypeError) as exc:
            safe, _ = sanitize(str(exc))
            check = {
                "name": gate["id"],
                "gate_id": gate["id"],
                "status": "blocked" if returncode in {None, 0, 125} else "failed",
                "evidence_scopes": gate["scopes"],
                "interface_ids": gate["interfaces"],
                "reason": safe,
                "artifacts": [],
            }
            artifacts = {}
        check.update(
            source=gate["source"],
            command=command,
            image=gate["image"],
            run_nonce=nonce,
            isolation="docker-linux-readonly-no-network",
            duration_seconds=round(time.monotonic() - started, 3),
            stdout_sha256=hashlib.sha256(stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr).hexdigest(),
        )
        return check, artifacts
