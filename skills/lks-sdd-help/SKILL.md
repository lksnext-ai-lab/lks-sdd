---
name: lks-sdd-help
description: "Explain how to use the LKS-SDD plugin for professional SDD development with Codex, including delivery models, Git/versioning, environments, plans/releases/tasks, multi-profile architecture, gates, evidence, migration, status, and troubleshooting without changing files. Do not define, assess, adopt, implement, verify, deploy, or mutate project state."
---

# LKS-SDD Help

Orient the user without modifying files, state, phases, gates, or decisions. Explaining or suggesting an action never authorizes it.

1. Identify whether the user needs a short answer, onboarding, contextual orientation, an example, reference detail, or troubleshooting.
2. Start from the user's goal and disclose detail progressively. Read [concepts](references/sdd-concepts.md) for terminology or [lifecycle](references/project-lifecycle.md) for routes and gates only when needed.
3. For a first guided experience, use the [five-to-ten-minute onboarding](references/onboarding.md). Read the [Codex, Work and repository guide](references/work-codex-guide.md) when the user needs to understand the supported Codex environment, auxiliary surfaces, projects, or repositories.
4. For contextual help, optionally resolve `<plugin-root>` as the directory containing `.codex-plugin/plugin.json`, then run `python "<plugin-root>/scripts/lks_sdd.py" help "<project-root>"`. It validates read-only state and exposes preflight separately from readiness. Readiness is derived on demand, never persisted as approval. For schema 1.2 explain the current delivery model, `PLAN/REL/TASK` board, deployable-unit bindings, certification/support state, and task blockers as separate facts. Show the compact accessible definition groups and never calculate a global percentage.
5. For capability or product questions, read [capabilities and limits](references/capabilities-and-limits.md) and [product reality](references/product-reality.md). Treat surface-, version-, permission-, and configuration-dependent claims as conditional.
6. For a usage problem, read [troubleshooting](references/troubleshooting.md); use [FAQ](references/faq.md) for recurring conceptual questions. Diagnose without blaming the user and without changing files.
7. End with one or more options the user may choose. A status-only request remains in `lks-sdd-help`; route to `lks-sdd-define` only when the user explicitly chooses to continue or change the definition. Do not invoke another workflow until the user explicitly chooses it.

Use [examples](references/examples.md) only when the user asks to see a case or starter prompt.
