---
name: lks-sdd-define
description: Start or continue the specification of a new web application in versioned LKS-SDD Markdown, separating facts, proposals, decisions, assumptions, and open points. Use to clarify scope, requirements, acceptance, architecture options, technology choices, risks, or increments; do not use for help-only questions, existing-repository adoption, readiness assessment, code generation, or verification.
---

# Define with LKS-SDD

The Markdown artifacts in the application repository are authoritative; `.lks-sdd/project.json` is only their operational index. Never turn a proposal, inference, or ambiguous answer into a decision.

1. Inspect the authorized root and current LKS-SDD state. If application code already exists and no materialized adoption baseline exists, stop definition changes and explain that `lks-sdd-adopt-existing` is required but not implemented in plugin `0.1.0`.
2. For a new project, read [method](references/method.md) and [document contract](references/document-contract.md). Initialize only after the user explicitly requests creation, using `python scripts/init_project.py <project-root> --project-id <id>`; use `--dry-run` first when files may already exist.
3. Classify each contribution as fact, objective, requirement, restriction, proposal, decision, assumption, open point, risk, or evidence. Preserve provenance, uncertainty, and human edits. Use the [definition coverage matrix](references/definition-coverage.md) to focus questions without turning maturity into an opaque percentage.
4. Update only affected Markdown. If the core does not cover an applicable concern, read [conditional annexes](references/conditional-annexes.md) and materialize only the justified annex; never create empty documents to imply coverage. Summarize changes, then ask one to three highest-impact questions and explain why they matter. The user may answer, defer, mark not applicable with a reason, or close the current detail level.
5. Compare technology only after requirements and constraints. Read [technology selection](references/technology-selection.md) when relevant. FastAPI, React, PostgreSQL, and Keycloak are preferred candidates, never automatic choices.
6. Recommend `lks-sdd-assess-readiness` only when a concrete increment and its critical decisions are documented.

Do not generate application code, infer authority, claim formal approval, or modify a repository merely because the user asked for an explanation.
