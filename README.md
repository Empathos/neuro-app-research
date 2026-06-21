# Neuro App Research

Neuro App Research is a GitHub-native research loop for finding public apps, tools, directories, and repositories that may support neurodivergent people.

The goal is simple: run one script, collect condition-specific research through GitHub Actions, review the results through pull requests, and publish merged findings as a static research site.

## Why it exists

Research across neurodivergence support categories gets messy quickly. This repo keeps discovery structured enough to review without turning it into a heavyweight database.

It is designed for repeatable public-source discovery, not medical validation. Search results are leads. Human review decides what is useful.

## Core idea

```text
scripts/trigger_research_matrix.sh
  -> dispatches 8 GitHub Actions
  -> one action per condition
  -> each action queries Perplexity Sonar
  -> each action covers all support categories
  -> each action writes condition-scoped research files
  -> each action opens or updates one PR
  -> reviewed PRs merge into main
  -> Astro builds the merged research into GitHub Pages
```

The operating model is:

```text
8 conditions = 8 branches = 8 pull requests
```

## What it manages

- `autism`
- `adhd`
- `dyslexia`
- `dyspraxia`
- `tourette`
- `sensory-processing`
- `executive-function`
- `general`

## Support Categories

Each condition run covers every support category configured in `research/config/categories.json`, including communication/AAC, executive function, sensory regulation, education, emotional regulation, daily living, caregiver/clinician, and accessibility/assistive tech.

## Design principles

- Keep the operator surface simple: one script for all conditions, one script for a single condition.
- Use GitHub Actions as the executor, not as the clock.
- Keep one branch and one pull request per condition.
- Treat Perplexity output as discovery leads, not verified medical claims.
- Preserve durable source URLs, run logs, and state files for review.
- Keep secrets in GitHub Actions secrets, never in the repository.
- Keep the public site static-first: repository files are the database, commits are the audit trail, and GitHub Pages is the delivery surface.

## Repository layout

```text
.github/workflows/research-condition.yml   GitHub Action for one condition
.github/workflows/pages.yml                GitHub Pages build and deploy workflow
src/                                       Astro site source
public/CNAME                              Custom domain for GitHub Pages
scripts/trigger_research_matrix.sh         Dispatch all 8 condition runs
scripts/trigger_research_condition.sh      Dispatch one condition run
scripts/collect_neuro_apps.py              Deterministic collector
prompts/collect_neuro_apps.prompt.md       Operator prompt and review checklist
research/config/categories.json            Conditions, support categories, query terms
research/apps/<condition>/<category>.md    Durable app leads
research/state/conditions/<condition>.json Search state and duplicate memory
research/runs/conditions/<condition>.md    Latest human-readable run summary
research/runs/conditions/<condition>.jsonl Append-only run records
docs/schema.md                             Output format
```

## Operation

Run all conditions:

```bash
scripts/trigger_research_matrix.sh
```

Run one condition:

```bash
scripts/trigger_research_condition.sh autism
```

Build the static site locally:

```bash
npm install
npm run build
```

Run the local quality gate:

```bash
npm run verify
```

Optional knobs:

```bash
RESEARCH_MAX_RESULTS=4 RESEARCH_QUERY_COUNT=1 scripts/trigger_research_matrix.sh
```

## Current status

Prototype-ready. The collector uses Perplexity Sonar when `PERPLEXITY_API_KEY` is configured in GitHub Actions secrets. If the key is unavailable or the API call fails, it falls back to GitHub repository search.

The static site is configured for `research.empathos.ai` and publishes through GitHub Pages from the `main` branch build workflow.

The review gate is GitHub PRs. Merging a PR writes that condition's current research output to `main`.

## Public/private model

This repository should contain public-safe automation, schema, and research leads only. Runtime secrets live in GitHub Actions secrets. Private operational schedules or downstream deployment details should live outside this repo.

## Process

This repo uses a lightweight Agent Skills-inspired process:

- `docs/spec.md` is the living project spec.
- `docs/agent-skills-process.md` maps the repo workflow to the spec/plan/build/verify/review/ship lifecycle.
- `docs/research-review-rubric.md` defines the reviewer checklist for collected leads.
- `docs/recommendations/agent-skills-assessment.md` tracks the current process recommendations and their status.
- `docs/decisions/` records architecture decisions that future agents and reviewers need to understand.
- Pull requests are the review gate; CI runs type checking, tests, dependency audit, static build, and source URL reachability checks.
