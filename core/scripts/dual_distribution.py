"""Deterministic, offline adapters; the runtime bytes are identical for both hosts."""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import zipfile
from pathlib import Path, PurePosixPath

from path_utils import filesystem_root

SKILLS = ("help", "define", "adopt-existing", "assess-readiness", "implement", "verify")
BEGIN = "<!-- LKS-SDD:BEGIN -->"
END = "<!-- LKS-SDD:END -->"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def safe_name(name: str) -> str:
    path = PurePosixPath(name)
    if not name or "\\" in name or ":" in name or path.is_absolute() or any(
        part in {"", ".", ".."} for part in name.split("/")
    ):
        raise ValueError(f"Unsafe relative path: {name}")
    return name


def inventory(files: dict[str, bytes]) -> dict[str, str]:
    return {safe_name(name): digest(data) for name, data in sorted(files.items())}


def runtime_identity(files: dict[str, bytes]) -> str:
    return digest(json_bytes(inventory(files)))


def zip_bytes(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(
                safe_name(name), date_time=(2026, 1, 1, 0, 0, 0)
            )
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    return output.getvalue()


def compact_distribution_core(core: dict[str, bytes]) -> dict[str, bytes]:
    """Return an isolated copy of the active source tree for distribution."""
    return dict(core)

def project_files(core: dict[str, bytes], source: str, channel: str, *, plugin_entrypoints: bool = False) -> dict[str, bytes]:
    core = compact_distribution_core(core)
    version = json.loads(core[".codex-plugin/plugin.json"])["version"]
    identity = runtime_identity(core)
    runtime = f".lks-sdd/runtime/{version}-{identity[:12]}"
    output = {f"{runtime}/{name}": data for name, data in core.items()}
    host = core["distribution/host-copilot.md"].decode("utf-8").replace("{{RUNTIME}}", runtime)
    output[".github/lks-sdd-host.md"] = host.encode("utf-8")
    output[".lks-sdd/.gitattributes"] = b"/.gitattributes -text\nruntime/** -text\ndistribution-lock.json -text\ninstallation.json -text\n"
    output[".github/.gitattributes"] = b"/.gitattributes -text\n/skills/lks-sdd-*/** -text\n/lks-sdd-host.md -text\n"
    for suffix in (() if plugin_entrypoints else SKILLS):
        name = f"lks-sdd-{suffix}"
        workflow = core[f"skills/{name}/SKILL.md"].decode("utf-8")
        description = re.search(r"^description:\s*(.+)$", workflow, re.MULTILINE)
        if description is None:
            raise ValueError(f"Missing description: {name}")
        text = description.group(1).replace("Codex plugin", "plugin").replace("with Codex", "with GitHub Copilot")
        output[f".github/skills/{name}/SKILL.md"] = (
            f"---\nname: {name}\ndescription: {text}\n---\n\n"
            f"# {name}\n\n"
            "This is the GitHub Copilot adapter, not the Codex adapter.\n"
            "Read the [host contract](../../lks-sdd-host.md) first, then the "
            f"[complete shared workflow](../../../{runtime}/skills/{name}/SKILL.md).\n"
            f"Resolve `<plugin-root>` to `{runtime}` relative to the project root, "
            "never to this wrapper. The host contract overrides only tool routing, "
            "image generation and host-specific invocation syntax; all method gates remain.\n"
            "Load linked workflow references relative to their actual runtime file. "
            "Do not copy or improvise a shorter workflow.\n"
        ).encode("utf-8")
    common = (
        "# Shared LKS-SDD project contract\n\n"
        "Markdown under docs/lks-sdd is authoritative; .lks-sdd/project.json is an index.\n"
        "Read .lks-sdd/distribution-lock.json. Both hosts use its exact runtime and workflows.\n"
        "For every requested application change, including changes to existing features or TASKs, "
        "reconcile the request with the current SPEC and complete PLAN/TASK coverage before editing code. "
        "Read docs/V2-SPEC-PLAN-TASK.md in the pinned runtime. If coverage is missing, use define; "
        "readiness and help remain read-only. Reuse valid decisions and tasks.\n"
        f"Runtime: `{runtime}`. Before work run "
        f"`python {runtime}/scripts/lks_sdd.py runtime-doctor . --json`.\n"
        "If integrity fails, stop affected work; do not fall back to a global plugin.\n"
        "The active host comes from the current tool/adapter, never from folder presence.\n"
        "In Codex read the pinned skills/<skill>/SKILL.md from this runtime. "
        "Native Codex image work proceeds normally without handoff announcements or files.\n"
        "In Copilot load .github/lks-sdd-host.md and use the installed plugin skills "
        "or project skills according to distribution-lock.json entrypoints. Never load both.\n"
        "At resumption inspect `.lks-sdd/handoffs/visual/` if present; select the requested "
        "scope explicitly. Read/status/help must not write. Validate any received result.\n"
        "One writer per shared scope; transfer changes and assets through your approved Git "
        "workflow before another developer resumes. Never share credentials or chat sessions.\n"
        "Prototype approval is not implementation authorization. Preserve human decisions, "
        "AUTH, EXEC, CKPT, EVID and all existing gates. No automatic commit, push or remote write.\n"
    )
    for path, content in (("AGENTS.md", common), (".github/copilot-instructions.md",
                           "# LKS-SDD in Copilot\n\nRead `.github/lks-sdd-host.md` for LKS-SDD work.\n"
                           "For every application change, including an existing feature, reconcile the request "
                           "with SPEC and complete PLAN/TASK before code. Follow the pinned runtime's "
                           "docs/V2-SPEC-PLAN-TASK.md and report missing coverage.\n"
                           "Use the six skills and the pinned runtime; the installed plugin must respect the project lock.\n")):
        output[path] = f"{BEGIN}\n{content}{END}\n".encode("utf-8")
    # Lock covers adapters as well as the runtime; it has no absolute paths or user identity.
    output[".lks-sdd/distribution-lock.json"] = json_bytes({
        "schema_version": "1.0", "version": version, "runtime": runtime,
        "runtime_digest": identity, "runtime_files": inventory(core),
        "managed_files": inventory({k: v for k, v in output.items() if not k.startswith(runtime + "/")}),
        "source": source, "channel": channel, "hosts": ["codex", "copilot"],
        "project_schema": json.loads(core["distribution/dual.json"])["project_schema"],
        "method_version": json.loads(core["distribution/dual.json"])["method_version"],
        "readable_method_versions": ["2.0.0", "2.1.0"],
        "collaboration": "sequential",
        "entrypoints": "plugin" if plugin_entrypoints else "project",
    })
    return output


def copilot_plugin_files(core: dict[str, bytes], source: str, channel: str) -> dict[str, bytes]:
    """Native Agent Plugins package, with an explicit, offline project bootstrap.

    Installing the personal plugin does not initialize or upgrade any project.
    The bootstrap has no discoverable project skills, avoiding double invocation.
    """
    core = compact_distribution_core(core)
    version = json.loads(core[".codex-plugin/plugin.json"])["version"]
    output = {f"core/{name}": data for name, data in core.items()}
    # Native plugins are also distributed as Git repositories. Preserve setup
    # manifest bytes when a teammate clones with core.autocrlf=true on Windows.
    output[".gitattributes"] = b"* -text\n"
    output["plugin.json"] = json_bytes({
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "lks-sdd", "version": version,
        "description": "Desarrollo guiado por especificaciones, decisiones humanas y evidencia; imágenes mediante relevo a Codex.",
    })
    output["README.md"] = (
        f"# LKS-SDD para Copilot {version}\n\n"
        "Plugin de agente: registre esta carpeta (la que contiene plugin.json), "
        "no core/ ni setup/. No es una extensión VSIX.\n\n"
        "Empiece por la [guía desde cero](core/docs/LEARNING-GUIDE.md), "
        "siga [instalación](core/docs/INSTALLATION.md) y el "
        "[piloto guiado](core/docs/COPILOT-PILOT.md).\n\n"
        "Las seis skills usan el núcleo fijado por proyecto. setup/ prepara ese "
        "proyecto solo después de revisar y autorizar los cambios. Actualizar este "
        "plugin no actualiza los proyectos. No instale también las skills de proyecto.\n\n"
        f"Canal: {channel}. Matriz detallada de aceptación de Copilot: not-run. "
        "Generación de imágenes mediante relevo a Codex, sin API añadida.\n"
    ).encode("utf-8")
    setup = {
        "install.py": core["distribution/install.py"],
        "install.ps1": core["distribution/install.ps1"],
        "INSTALLATION.md": (
            "# Preparación del proyecto desde el plugin Copilot\n\n"
            "Lea la [guía completa](../core/docs/INSTALLATION.md) y el "
            "[itinerario desde cero](../core/docs/LEARNING-GUIDE.md).\n\n"
            "Desde esta carpeta ejecute `python install.py copilot RUTA_DEL_PROYECTO` "
            "para obtener una vista previa. Solo tras aprobarla, repita con "
            "`--apply --authorize HASH_DE_LA_VISTA_PREVIA`. El consumidor debe existir.\n"
        ).encode("utf-8"),
        "payload/copilot.zip": zip_bytes(project_files(core, source, channel, plugin_entrypoints=True)),
    }
    setup["payload-manifest.json"] = json_bytes({
        "schema_version": "1.0", "version": version, "source": source, "channel": channel,
        "files": inventory(setup), "runtime_digest": runtime_identity(core),
    })
    output.update({f"setup/{name}": data for name, data in setup.items()})
    for suffix in SKILLS:
        name = f"lks-sdd-{suffix}"
        workflow = core[f"skills/{name}/SKILL.md"].decode("utf-8")
        description = re.search(r"^description:\s*(.+)$", workflow, re.MULTILINE).group(1)
        description = description.replace("Codex plugin", "plugin").replace("with Codex", "with GitHub Copilot")
        output[f"skills/{name}/SKILL.md"] = (
            f"---\nname: {name}\ndescription: {description}\n---\n\n"
            "# Copilot plugin entrypoint\n\n"
            "You are using the Copilot adapter. Resolve the installed plugin root from this "
            "file's location (two parents), not the working directory or an invented environment variable.\n"
            "If the project has .lks-sdd/distribution-lock.json, read it and run its exact "
            "runtime/scripts/lks_sdd.py runtime-doctor with the project path. Stop on invalid integrity; "
            "never substitute the newer installed core. Read .github/lks-sdd-host.md, then "
            f"runtime/skills/{name}/SKILL.md and its references from that pinned runtime. "
            "Resolve <plugin-root> in that workflow to the pinned runtime.\n"
            "If entrypoints is project (including a legacy lock without entrypoints), explain that "
            "the project adapters are already installed. Disable this plugin for that workspace "
            "or explicitly migrate using this plugin's setup; do not execute duplicate workflows.\n"
            "Without a lock, help is read-only: use ../../core/skills/lks-sdd-help/SKILL.md "
            "and ../../core/docs/LEARNING-GUIDE.md relative to this file. For other workflows, "
            "first offer explicit project initialization using setup/install.py copilot <project-path> "
            "from the installed plugin. Show the preview and obtain approval for its exact changes "
            "before --apply --authorize HASH. Never initialize for help/status, never install globally, "
            "never upgrade a locked project merely because the plugin was updated.\n"
            "In Copilot, image generation always uses the documented visual handoff to Codex; "
            "never call ImageGen or a paid image API here. Preserve all canonical gates, human "
            "approvals and no-commit/no-push boundaries. Read linked full workflows, not summaries.\n"
        ).encode("utf-8")
    return output


def artifacts(core: dict[str, bytes], source: str, channel: str) -> dict[str, bytes]:
    core = compact_distribution_core(core)
    version = json.loads(core[".codex-plugin/plugin.json"])["version"]
    marketplace = core["distribution/marketplace.template.json"]
    plugin = {f"lks-sdd/{name}": data for name, data in core.items()}
    codex = {f"plugins/lks-sdd/{name}": data for name, data in core.items()}
    codex[".agents/plugins/marketplace.json"] = marketplace
    copilot = project_files(core, source, channel)
    # Keep setup extraction shallow on Windows; only the installer expands payloads.
    setup = {"payload/codex.zip": zip_bytes(codex), "payload/copilot.zip": zip_bytes(copilot)}
    setup.update({"install.py": core["distribution/install.py"],
                  "install.ps1": core["distribution/install.ps1"],
                  "INSTALLATION.md": core["docs/INSTALLATION.md"]})
    setup["payload-manifest.json"] = json_bytes({
        "schema_version": "1.0", "version": version, "source": source, "channel": channel,
        "files": inventory(setup), "runtime_digest": runtime_identity(core),
    })
    result = {
        f"lks-sdd-plugin-v{version}.zip": zip_bytes(plugin),
        f"lks-sdd-marketplace-v{version}.zip": zip_bytes(codex),
        f"lks-sdd-copilot-v{version}.zip": zip_bytes(copilot),
        f"lks-sdd-setup-v{version}.zip": zip_bytes(setup),
        f"lks-sdd-copilot-plugin-v{version}.zip": zip_bytes({
            f"lks-sdd/{name}": data for name, data in copilot_plugin_files(core, source, channel).items()
        }),
    }
    result["distribution-manifest.json"] = json_bytes({
        "schema_version": "1.0", "version": version, "source": source,
        "channel": channel, "runtime_digest": runtime_identity(core),
        "hosts": ["codex", "copilot"], "artifacts": inventory(result),
        "host_acceptance": "not-run", "collaboration": "sequential",
    })
    result["SHA256SUMS"] = ("".join(f"{digest(data)}  {name}\n" for name, data in sorted(result.items()))).encode()
    return result
