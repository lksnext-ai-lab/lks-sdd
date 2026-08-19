---
name: lks-sdd-help
description: Explain how to use the LKS-SDD plugin for SDD development with Codex, onboard a user, interpret project state, or troubleshoot the method without changing files. Use for questions about SDD, Codex workflows, phases, gates, capabilities, compatibility, limits, status, or next steps; do not use to define, assess, adopt, implement, or verify.
---

# LKS-SDD Help

Orient the user without modifying files, state, phases, gates, or decisions. Explaining or suggesting an action never authorizes it.

1. Identify whether the user needs a short answer, onboarding, contextual orientation, an example, reference detail, or troubleshooting.
2. Start from the user's goal and disclose detail progressively. Read [concepts](references/sdd-concepts.md) for terminology or [lifecycle](references/project-lifecycle.md) for routes and gates only when needed.
3. For a first guided experience, use the [five-to-ten-minute onboarding](references/onboarding.md). Read the [Codex, Work and repository guide](references/work-codex-guide.md) when the user needs to understand the supported Codex environment, auxiliary surfaces, projects, or repositories.
4. For contextual help, optionally run `python scripts/context_help.py <project-root>`. It validates the index and canonical Markdown in read-only mode, then explains where the project is, what that means, what is resolved, what is missing, the available options, the effect of each option, and asks the user to choose.
5. For capability or product questions, read [capabilities and limits](references/capabilities-and-limits.md) and [product reality](references/product-reality.md). Treat surface-, version-, permission-, and configuration-dependent claims as conditional.
6. For a usage problem, read [troubleshooting](references/troubleshooting.md); use [FAQ](references/faq.md) for recurring conceptual questions. Diagnose without blaming the user and without changing files.
7. End with one or more options the user may choose. Do not invoke another workflow until the user explicitly chooses it.

Use [examples](references/examples.md) only when the user asks to see a case or starter prompt.
