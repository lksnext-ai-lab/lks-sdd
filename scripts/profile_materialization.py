"""Materialize a profile driver into a local working directory."""

from __future__ import annotations

import shlex
from pathlib import Path

from profile_registry import PLUGIN_ROOT, load_profile_bundle, profile_source_files


PYTHON_IMAGE = (
    "python:3.14.7-slim@sha256:"
    "ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4"
)
NODE_IMAGE = (
    "node:24.19.0-bookworm-slim@sha256:"
    "3638d9a6fe4030bd716be989438248074489337ba3275657f93595428be4fc03"
)
PLAYWRIGHT_IMAGE = (
    "mcr.microsoft.com/playwright:v1.62.1-noble@sha256:"
    "dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e"
)


def materialize_profile(profile_id: str, work: Path) -> None:
    bundle = load_profile_bundle(profile_id)
    if bundle.root is None:
        raise ValueError(f"Perfil no encontrado: {profile_id}")
    written: dict[Path, bytes] = {}
    for source in bundle.driver["prepare"]["sources"]:
        origin = (PLUGIN_ROOT / source["from"]).resolve()
        target = Path(source["to"])
        if target.is_absolute() or ".." in target.parts:
            raise ValueError(f"Destino de perfil inseguro: {source['to']}")
        destination_root = work / target
        if origin.is_file():
            entries = [
                (
                    origin,
                    Path(origin.name) if destination_root.is_dir() else Path("."),
                )
            ]
            if source["to"] != "." and destination_root.suffix:
                entries = [(origin, Path("."))]
        else:
            entries = [
                (path, path.relative_to(origin)) for path in profile_source_files(origin)
            ]
        for path, relative in entries:
            destination = (
                destination_root if relative == Path(".") else destination_root / relative
            )
            content = path.read_bytes()
            prior = written.get(destination)
            if prior is not None and prior != content:
                raise ValueError(
                    f"Fuentes del perfil colisionan en {destination.relative_to(work)}"
                )
            if destination.exists() and destination.read_bytes() != content:
                raise ValueError(
                    f"Fuentes del perfil divergen en {destination.relative_to(work)}"
                )
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(content)
            written[destination] = content


def docker_command(
    command: list[str],
    work: Path,
    cwd: Path,
    check_name: str,
    dependency_volume: str | None = None,
) -> list[str]:
    relative = cwd.relative_to(work).as_posix()
    shell_cwd = "/work" if relative == "." else f"/work/{relative}"
    first = command[0] if command else ""
    if first in {"npm", "npx", "npm.cmd", "npx.cmd"}:
        browser = any(
            token in check_name for token in ("browser", "accessibility", "hydration")
        )
        image = PLAYWRIGHT_IMAGE if browser else NODE_IMAGE
        script = f"cd {shlex.quote(shell_cwd)} && {shlex.join(command)}"
    else:
        image = PYTHON_IMAGE
        uv_prefix = (
            "python -m pip install --disable-pip-version-check --quiet uv==0.12.5 && "
            if first in {"uv", "uv.exe"}
            else ""
        )
        script = f"{uv_prefix}cd {shlex.quote(shell_cwd)} && {shlex.join(command)}"
    mount_path = str(work.resolve()).replace("\\", "/")
    mounts = ["-v", f"{mount_path}:/work"]
    if dependency_volume and first in {
        "npm",
        "npx",
        "npm.cmd",
        "npx.cmd",
        "pnpm",
        "pnpm.cmd",
    }:
        mounts.extend(["-v", f"{dependency_volume}:{shell_cwd}/node_modules"])
    elif dependency_volume and first in {"uv", "uv.exe"}:
        mounts.extend(["-v", f"{dependency_volume}:{shell_cwd}/.venv"])
    return ["docker", "run", "--rm", *mounts, image, "sh", "-lc", script]
