---
name: lks-sdd-help
description: "Use with Codex. Explain LKS-SDD or answer questions about documented project behavior, requirements, features, tasks and history in clear, source-linked language, without changing canonical files; inspect code only for an explicit comparison or a bounded implementation gap."
---

# LKS-SDD Help

## Routing por contrato

Read [v2 common policy and workflows](../../docs/V2-WORKFLOWS.md) for contract
2.0 or a new v2 project. Responsibility: Consultar y explicar, sin escritura.
Use only the relevant section of that shared workflow and its linked references;
do not combine v2 syntax with the legacy workflow below. Existing projects remain
on their exact pinned runtime until explicitly migrated. Unknown schemas fail
closed; a question never initiates adoption, migration or implementation.

For a project reporting a 1.5→2.0 transition, use the read-only
`v2 migration-status` guard and, when a TASK is named,
`v2 migration-continuation`. Never treat `already-v2` as proof from the index
header alone; explain the conservation receipt, clean cutover and any
TASK-scoped reconciliation blockers.

## Workflow conservado para contrato 1.5

For questions about project content, read `<plugin-root>/docs/PROJECT-QUERY.md`
and use `python -B <plugin-root>/scripts/lks_sdd.py query <project-root> --json`
with the relevant topic/entity/document. This query path checks the pinned runtime
itself; it does not require project initialization or a readiness assessment.
Synthesize a human explanation with source links; consult code only after a
concrete implementation gap or an explicit request. Missing SDD documentation
does not mean missing functionality. Do not run the lifecycle/status steps below
unless the question actually concerns them.

For non-catalogued versions/compositions or project-approved observers, read
la declaración tecnológica local indexada. Explain the opt-in route and its
separate documented confirmation, approval, verification, TASK and delivery axes. Diagnosis
is static; an unknown combination is not automatically incompatible.

For a project with `.lks-sdd/distribution-lock.json`, use its exact pinned runtime
and this workflow from that runtime, not a different global version. Run
`<plugin-root>/scripts/lks_sdd.py runtime-doctor <project-root> --json` before work;
integrity failure blocks affected actions. The invoking host adapter governs tools,
not folder presence. Preserve all method gates below. On resumption, read applicable
visual handoffs and validate their results; no handoff grants implementation authority.
Help/status remain read-only. Native Codex work never creates or announces a handoff.

Orient the user without modifying files, state, phases, gates, or decisions. Explaining or suggesting an action never authorizes it.

For users unfamiliar with agents, SDD, VS Code or Codex, read the shared
[learning guide](../../docs/LEARNING-GUIDE.md) from the selected runtime. Teach from
their concrete goal; distinguish editor, model, agent, plugin and project. Define
each necessary term on first use, explain what a proposed command will change,
and separate expected behavior from observed acceptance. Do not dump the whole
manual or start initialization while answering help. For installation and testing,
read [installation](../../docs/INSTALLATION.md) and [guided pilot](../../docs/COPILOT-PILOT.md).
These are shared maintained sources, not separate Copilot/Codex copies. Use the
host's actual invocation syntax and never promise native Copilot image generation.

1. Identify whether the user needs a short answer, onboarding, contextual orientation, an example, reference detail, or troubleshooting.
2. Start from the user's goal and disclose detail progressively. Read [concepts](references/sdd-concepts.md) for terminology, including the Spec-first/Spec-anchored/Spec-as-source distinction, or [lifecycle](references/project-lifecycle.md) for routes and gates only when needed.
3. For a first guided experience, use the [five-to-ten-minute onboarding](references/onboarding.md). Read the [Codex, Work and repository guide](references/work-codex-guide.md) when the user needs to understand the supported Codex environment, auxiliary surfaces, projects, or repositories.
4. For contextual help, optionally resolve `<plugin-root>` as the directory containing `.codex-plugin/plugin.json`, then run `python "<plugin-root>/scripts/lks_sdd.py" help "<project-root>"`. It validates read-only state and exposes preflight separately from readiness. Readiness is derived on demand, never persisted as approval. For the supported schema 1.5 explain specification, strict `automation_support`, diagnostic `automation_coverage`, full-plan completeness, selected-task readiness, implementation, verification, delivery, task-tracking mode, projection state, reporting scope, coordination gate and local reporting status as separate facts. `automation_coverage` may show exact project documentation fit, preparation, local gates, external interoperability and delivery evidence, but never means partially supported or authorizes implementation. Show concrete uncovered IDs and executable next tasks instead of a global percentage. If schema/método differ from 1.5/1.5.0, explain the incompatibility without proposing a silent migration.
5. For capability or product questions, read [capabilities and limits](references/capabilities-and-limits.md) and [product reality](references/product-reality.md). Explain that capabilities are granular reusable contracts, while only an exact closed active local technology declaration is selectable and certifiable. The two simulated OIDC local technology declaration packaged in 0.13 are supported only for explicitly non-production environments, have external interoperability `not-applicable` and fail closed in production. The Entra local technology declaration remain candidates: do not present local implementation files/gate coverage as real-tenant interoperability and never substitute Entra with simulated OIDC or Keycloak. When the question concerns Markdown-only planning, the optional Jira Cloud projection/reporting, or Atlassian Rovo availability and limits, read [Jira companion guidance](references/jira-companion.md). Explain projection receipts separately from milestone comment/transition receipts, the one-confirmation-per-preview experience, exact marker checks, canonical-first ordering and append-only reconciliation; never imply that a receipt changes the canonical TASK or that 0.13 can detach/rebind a durable Jira binding. Help may explain installation, connection, permissions and recovery choices, but it never inspects an Atlassian account or Jira data. For a handoff, planning completion, task start/block/pause/resume, release completion or promotion summary, use [transition summaries](references/transition-summaries.md). Treat surface-, version-, permission-, and configuration-dependent claims as conditional.
6. For a usage problem, read [troubleshooting](references/troubleshooting.md); use [FAQ](references/faq.md) for recurring conceptual questions. Diagnose without blaming the user and without changing files.
7. If an execution exists, use the read-only contextual view or `python "<plugin-root>/scripts/lks_sdd.py" continuity "<project-root>" resume --json` to explain whether continuing, reconciling or replanning is safe. A checkpoint reports observed work; it is not a commit or verification result.
8. End with one or more options the user may choose. When specification is closed but planning is partial, offer full planning first, explicit incremental planning second, and pause third. A status-only request remains in `lks-sdd-help`; route to `lks-sdd-define` only when the user explicitly chooses to continue or change the definition. Do not invoke another workflow until the user explicitly chooses it.

Use [examples](references/examples.md) only when the user asks to see a case or starter prompt.

## Default status and narration in 0.18

For current project state, prefer `python "<plugin-root>/scripts/lks_sdd.py" status "<project-root>"` and its default `management` view. Use `--view developer` for actionable implementation detail and `--view audit --json` only on request or when a conflict requires full traceability. If no task is active, report `current_task: null` instead of selecting the first task. Separate code, tests, historical verification, current health and delivery. Do not expose hashes, fingerprints, locks, bindings, gates, authorizations, executions, checkpoints, evidence or receipts in the normal summary except for one compact technical-reference line.

Narrate outcome before mechanics: once before starting or resuming, after a material milestone, at a blocker, after implementation and after verification. Separate observed fact, checked result, pending work, active blocker and required human decision. Do not report every preview, hash or receipt.

For multiunit status, explain the typed evidence scopes separately: `component`, `contract`, `composition`, `user-flow`, `persistence` and `visual`. A passed component or visual check never means that units communicate or that data persists. Only a confirmed web-flow `INT-###` owned by the selected TASK slice makes the browser full-stack gate applicable; HTTP, PostgreSQL and migration interfaces use their appropriate observers; otherwise report its deterministic `not-applicable` reason. Historical component evidence remains valid for that scope, while an old joint claim without cross-binding proof is `reconciliation-required` and is never rewritten.

For version compatibility, local authentication or adoption questions, distinguish architectural contract, exact documented scope, reference implementation files and observed consumer resolution; updating the plugin never changes consumer dependencies or bindings.
