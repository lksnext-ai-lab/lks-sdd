---
name: lks-sdd-verify
description: Verify one implemented LKS-SDD increment with Codex by running applicable locked-profile checks, linking acceptance criteria to tests and evidence, and classifying limitations without treating unexecuted checks as passed. Use after implementation; do not use to define, adopt, implement new scope, or authorize delivery.
---

# Verify an LKS-SDD Increment with Codex

Verification produces evidence, not approval. Never classify a check as passed unless it actually ran and its result is available.

1. Read the project index, selected profile lock, increment, acceptance criteria, test strategy, traceability, implementation diff, and repository instructions.
2. Read the [verification contract](references/verification-contract.md). Run `python scripts/run_verification.py <project-root> --increment <INC-###> --plan --json` and explain applicable checks, side effects, prerequisites, and omissions.
3. Execute only after explicit authorization with `--execute --authorize`. Add `--containers` only when starting the local PostgreSQL/Keycloak stack is authorized and safe. Do not substitute a different command because a required tool is missing.
4. Review semantic acceptance, security, accessibility, performance, deployment, and rollback according to applicability. The deterministic runner covers the H0 technical checks but cannot prove business behavior by itself.
5. Record evidence with a stable `EVID-###` using `--record-evidence`. Link it to requirements, acceptance criteria, the increment, and `TEST-###` rows; preserve raw sensitive logs outside canonical documentation and retain only the minimum safe result.
6. Classify the result as `verified`, `verified-with-reservations`, or `not-verified`. Report failed, blocked, not-run, and not-applicable checks separately, with limitations and the smallest corrective action.
7. Delivery remains a separate human decision. For a client view, follow [client-view rules](references/client-view-rules.md) and use the controlled renderer only with confirmed, client-authorized sources.
