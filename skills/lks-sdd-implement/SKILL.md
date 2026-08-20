---
name: lks-sdd-implement
description: Implement one confirmed LKS-SDD increment with Codex after its readiness gate passes, using the selected and locked technology profile, bounded code changes, tests, and traceability. Use only when the user explicitly requests implementation; do not use to define requirements, adopt a repository, assess readiness only, or claim verification.
---

# Implement an LKS-SDD Increment with Codex

Implement only the requested increment. A `ready` result is necessary but does not replace the user's explicit authorization to change code.

1. Read `.lks-sdd/project.json` and the indexed Markdown. Confirm the active increment, included and excluded scope, requirements, acceptance criteria, decisions, tests, blockers, interface applicability, and any confirmed `UX-###`/`VIS-###` contract.
2. Read the [implementation contract](references/implementation-contract.md). Run `python scripts/prepare_increment.py <project-root> --increment <INC-###> --dry-run --json` before creating the H0 scaffold. Stop if readiness, the selected profile, its confirmed ADR, or an adopted baseline is invalid.
3. Present planned files and collisions. Apply the scaffold only after explicit authorization, using the returned preview hash with `--apply --authorize --preview-hash <hash>`. The preview is bound to the readiness `input_fingerprint`; a change to any checked Markdown or prototype image requires a new assessment and preview. Preserve existing files; integrate an existing `.gitignore`, README, AGENTS instructions, pipeline, or application structure as a separate reviewed change.
4. Implement the smallest vertical slice that satisfies the linked acceptance criteria. When the interface is applicable, treat the confirmed screens, flows, direction and prototype assets as implementation inputs, not optional inspiration. Do not silently reinterpret or replace a validated visual baseline. Keep business rules out of transport boundaries, avoid speculative infrastructure, and do not expand the increment to unrelated cleanup.
5. Add or update tests linked to the documented `TEST-###` identifiers. Inspect repository commands before executing them; obtain separate authorization for commands with material side effects not already implied by the implementation request.
6. Update affected Markdown and the operational index without turning observed behavior into a new requirement. Record changed scope, deviations, tests actually run, and evidence identifiers. Leave unexecuted verification as `not-run`.
7. Hand off to `$lks-sdd-verify`. Do not classify the increment as verified from implementation tests alone.

For a non-H0 stack, implement only when a separately packaged profile declares the required capability and has a validated lock. Otherwise explain that the project remains documentable but implementation is not guaranteed.
