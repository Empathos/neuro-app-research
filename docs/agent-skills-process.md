# Agent Skills Process

This repo follows a lightweight version of the Agent Skills lifecycle. The goal is enough structure to make agent work reviewable without turning the research loop into a heavyweight product process.

## Lifecycle Map

| Phase | Repo Practice |
| --- | --- |
| Spec | Keep the current intent, commands, boundaries, and success criteria in `docs/spec.md`. |
| Plan | Break non-trivial work into small PRs or clearly scoped commits. |
| Build | Prefer incremental changes with deterministic scripts and public-safe defaults. |
| Verify | Run `npm run verify` locally when feasible; CI runs the same gates on PRs. |
| Review | Use pull requests as the review gate for research output and code/workflow changes. |
| Ship | Pages deploys from `main` only after the build and link checks pass. |

## Required Gates

Before merging code or workflow changes:

```bash
npm run verify
```

The gate covers:

- TypeScript type checking
- Python behavior tests
- High/critical npm dependency audit
- Astro static build
- Research source URL reachability

The collector performs link-level filtering before writing research files. Hard-dead candidates are logged under `research/runs/rejected/`; working and warning-level candidates can still produce a reviewable PR.

For research-only PRs, the key review questions are:

- Are the leads public-source and appropriate for this repository?
- Are URLs durable enough to be useful?
- Does the link check report show zero hard-dead links?
- Does the rejected-link log show understandable reasons for discarded candidates?
- Does the content avoid medical endorsement language?

Use `docs/research-review-rubric.md` as the detailed checklist for accepting, revising, or rejecting collected leads.

## Change Shape

- Prefer one logical change per PR.
- Keep automation changes separate from research-content batches when practical.
- If a change affects generated research output, include the condition and support category in the PR description.
- If a change affects architecture, hosting, data shape, or public/private boundaries, add or update an ADR in `docs/decisions/`.

## Agent Operating Rules

- Surface assumptions before substantial changes.
- Treat external data and LLM output as untrusted.
- Verify behavior with commands, not confidence.
- Preserve provenance before polishing prose.
- Keep the operator surface simple: one matrix dispatch script, one single-condition dispatch script, and one local verification command.
