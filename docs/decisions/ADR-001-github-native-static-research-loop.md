# ADR-001: Use a GitHub-Native Static Research Loop

## Status

Accepted

## Date

2026-06-21

## Context

The project needs to collect and review public-source leads for neurodivergence-support apps and tools without introducing a database, backend service, or private operational dependency.

The current operating model is:

- GitHub Actions collects condition-specific research.
- Research output is committed to condition branches.
- Pull requests are the review gate.
- Astro renders merged research files into a static GitHub Pages site.

## Decision

Use repository files as the durable data store, GitHub Actions as the executor, pull requests as the review surface, and GitHub Pages as the publishing surface.

## Alternatives Considered

### Database-backed application

- Pros: richer querying, admin UI, structured validation.
- Cons: adds hosting, migrations, auth, monitoring, and private operational burden too early.
- Rejected for now because the project is still discovery-oriented and benefits from a simple public audit trail.

### Spreadsheet or Notion tracker

- Pros: easy manual editing and review.
- Cons: weaker automation, weaker public provenance, less suitable for static publishing and PR review.
- Rejected because this project needs GitHub-native automation and public-safe reproducibility.

### Static files generated manually

- Pros: simplest possible publishing path.
- Cons: not repeatable enough for condition/category matrix collection.
- Rejected because automated collection and link verification are core requirements.

## Consequences

- Git history becomes the audit trail.
- CI can enforce link reachability and build health before publish.
- Reviewers can inspect research changes as normal diffs.
- Querying and editorial tooling remain intentionally limited until the data model proves it needs more.
- Future work should preserve this simplicity unless a concrete pain point justifies heavier infrastructure.
