# GitHub Copilot host contract

This adapter is for GitHub Copilot Agent mode in VS Code. It is not a VSIX and
does not configure MCP, hooks, agents, providers or personal settings.
`<plugin-root>` is `{{RUNTIME}}`, relative to the consumer project root.
Read the exact shared workflow from that runtime, including its linked references.
Resolve its `scripts/`, `profiles/`, `schemas/`, `assets/` against that runtime.

Before LKS-SDD work run `python {{RUNTIME}}/scripts/lks_sdd.py runtime-doctor . --json`.
Failure blocks affected work. Never download or choose a different runtime silently.
Use natural discovery or `/lks-sdd:lks-sdd-define` etc. for plugin entrypoints;
the project-only alternative uses `/lks-sdd-define`. Follow the lock's entrypoints
mode and do not enable both. `$skill` names in the shared method
identify those same workflows, not a required Copilot syntax.

## Visual work (takes precedence over shared Codex rendering instructions)

Do not call ImageGen or any image API, install a generator, ask for a provider key,
or replace required raster proposals with SVG, HTML screenshots or placeholders.
For a sufficient brief and `new`/`material-change`, preserve the canonical visual
pending state, prepare the durable handoff described in
`{{RUNTIME}}/docs/VISUAL-HANDOFF.md`, and invite the user once to Codex desktop.
Use the CLI preview/hash/apply protocol; the invitation refers to the real request.md.
Generation/review happens there under that user's access and usage limits.
The person may remain in Codex afterwards; return here is optional.

For incomplete briefs, ask the missing decisions here first. For backend-only work
or reuse of a confirmed baseline, do not offer a handoff. A pending handoff blocks
only dependent visual closure/work, not unrelated authorized tasks.
On return/new conversation inspect shared requests, select the relevant ID, validate
its result, then recompute normal readiness. Do not repeat invitations every turn.
Missing images, approval or stale inputs stay pending. Never infer human approval.

## Other capabilities and authority

Use available terminal/file tools for the same Python CLI and gates. Use available
browser tools to test the actual application and capture evidence; generated
prototypes do not replace browser review, accessibility, integration or persistence.
If a required browser/tool capability is absent, report the precise gate as not-run;
do not fabricate success. Skill selection and tool permissions remain host-managed.

Atlassian Rovo remains an optional independently configured peer. Check its actual
availability and authorization before any read/write. Follow the shared preview,
receipt and reconciliation contracts verbatim. Do not add an alternative Jira client.
Repository-only remains complete and must not prompt for Atlassian access.

Preserve all six skill boundaries, exact profiles, plan/readiness, authorization,
tracking, checkpoints, verification and delivery gates. Sharing a repository grants
no additional authority. One writer per shared scope; transfer files via approved
Git workflow. Never synchronize account configuration, credentials or conversations.
