---
name: lks-sdd-adopt-existing
description: "Adopt an existing software system into LKS-SDD with GitHub Copilot by statically inspecting repositories and deployable boundaries, reconciling observed implementation with confirmed intent, detecting drift, and materializing an additive schema 1.5 baseline whose delivery, planning coverage, task-tracking and optional Jira-reporting choices and profile bindings remain proposed or pending human confirmation, without changing code or behavior."
---

# Copilot plugin entrypoint

You are using the Copilot adapter. Resolve the installed plugin root from this file's location (two parents), not the working directory or an invented environment variable.
If the project has .lks-sdd/distribution-lock.json, read it and run its exact runtime/scripts/lks_sdd.py runtime-doctor with the project path. Stop on invalid integrity; never substitute the newer installed core. Read .github/lks-sdd-host.md, then runtime/skills/lks-sdd-adopt-existing/SKILL.md and its references from that pinned runtime. Resolve <plugin-root> in that workflow to the pinned runtime.
If entrypoints is project (including a legacy lock without entrypoints), explain that the project adapters are already installed. Disable this plugin for that workspace or explicitly migrate using this plugin's setup; do not execute duplicate workflows.
Without a lock, help is read-only: use ../../core/skills/lks-sdd-help/SKILL.md and ../../core/docs/LEARNING-GUIDE.md relative to this file. For other workflows, first offer explicit project initialization using setup/install.py copilot <project-path> from the installed plugin. Show the preview and obtain approval for its exact changes before --apply --authorize HASH. Never initialize for help/status, never install globally, never upgrade a locked project merely because the plugin was updated.
In Copilot, image generation always uses the documented visual handoff to Codex; never call ImageGen or a paid image API here. Preserve all canonical gates, human approvals and no-commit/no-push boundaries. Read linked full workflows, not summaries.
