# Agent Skills Assessment Recommendations

Date: 2026-06-21

This document records the follow-up recommendations from the Agent Skills process assessment. It is intentionally small: the repo should gain enough structure for repeatable agent work without becoming a heavyweight product process.

## Implemented

- Add a living spec in `docs/spec.md`.
- Add a lightweight Agent Skills lifecycle map in `docs/agent-skills-process.md`.
- Add an ADR home in `docs/decisions/` with ADR-001 for the GitHub-native static research loop.
- Add local quality scripts in `package.json`, including `npm run verify`.
- Add PR/push CI in `.github/workflows/ci.yml`.
- Add a research review rubric in `docs/research-review-rubric.md`.
- Block private, loopback, link-local, reserved, and internal-DNS link targets in `scripts/check_links.py` by default.

## Recommended Next

1. Decide whether link-check warnings should remain report-only or block publish in stricter release modes.
2. Add a simple lint/format gate once the repo has enough TypeScript/CSS surface area to justify the dependency.
3. Add a collector-side public-source guard if future collection paths fetch or enrich URLs before they reach `research/apps`.
4. Add a PR template that points reviewers to `docs/research-review-rubric.md` and asks for the condition/category scope.
5. Keep workflow and research-content changes in separate PRs when practical so reviewers can reason about automation and data independently.

## Operating Guidance

- Treat LLM and search-provider output as candidate leads only.
- Verify claims with commands, source files, or public URLs before merging.
- Use ADRs for hosting, data shape, security boundary, or workflow decisions.
- Keep `npm run verify` as the shared local and CI quality gate.
