---
artifact_id: "ART-TRACKING"
artifact_type: "task-tracking"
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.13.0"
project_id: "{{PROJECT_ID}}"
baseline_id: "{{BASELINE_ID}}"
status: proposed
classification: internal
audience:
  - product
  - engineering
owners:
  - product
  - engineering
source_of_truth: true
last_updated: "{{DATE}}"
---

# Gestión operativa de tareas

Markdown conserva la autoridad sobre PLAN, REL, TASK, AUTH, EXEC y CKPT. Este artefacto registra la decisión de tracking y, si se confirma Jira, sus mapeos y recibos saneados; nunca contiene credenciales.

## Binding

| Binding | State | Mode | Provider | Site | Project | Issue type | Sync policy | Write policy | Decision | Last reviewed |
|---|---|---|---|---|---|---|---|---|---|---|
| TRK-001 | proposed | pending | pending | pending | pending | pending | pending | pending | pending: tracking mode not selected | {{DATE}} |

## Reporting policy

| Reporting | State | Scope | Coordination gate | Comment policy | Decision | Last reviewed |
|---|---|---|---|---|---|---|
| RPT-001 | proposed | pending | pending | pending | pending: reporting scope not selected | {{DATE}} |

## Workflow mapping

| Local state | State | Jira status ID | Jira status name | Decision | Last reviewed |
|---|---|---|---|---|---|

## Mapping

| Task | State | External ID | External key | URL | Projection fingerprint | Remote status | Last synced | Last operation | Notes |
|---|---|---|---|---|---|---|---|---|---|

## Operations

| ID | State | Task | Action | Preview hash | Projection fingerprint | Duplicate check | Authorized by role | Authorized on | External ID | External key | Recorded on | Result | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Milestone operations

| ID | State | Task | Source ref | Event kind | Action | Event hash | Preview hash | Duplicate check | Authorized by role | Authorized on | External ID | External key | Recorded on | Result | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
