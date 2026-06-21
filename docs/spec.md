# Spec: Neuro App Research

## Objective

Neuro App Research is a GitHub-native research loop for collecting public-source leads for apps, tools, directories, and repositories that may support neurodivergent people.

The system should keep discovery repeatable, reviewable, public-safe, and lightweight. It does not validate medical quality or app effectiveness. It verifies that published source URLs are currently reachable and preserves enough provenance for human review.

## Tech Stack

- Static site: Astro 6
- Language: TypeScript for site code, Python 3.12 for collection and link checking
- Automation: GitHub Actions
- Hosting: GitHub Pages
- External discovery: Perplexity Sonar when `PERPLEXITY_API_KEY` is available, GitHub repository search fallback otherwise

## Commands

```bash
npm run dev          # Start local Astro dev server
npm run build        # Build static site
npm run preview      # Preview built site
npm run typecheck    # TypeScript check
npm test             # Python unit tests
npm run check:links  # Verify published research URLs are reachable
npm run audit:high   # Dependency audit for high/critical vulnerabilities
npm run verify       # Local quality gate
```

## Project Structure

```text
.github/workflows/            GitHub Actions for CI, research collection, and Pages publish
docs/                         Specs, schema docs, process notes, and ADRs
prompts/                      Operator prompts and review guidance
public/                       Static public assets and CNAME
research/apps/                Durable public research leads rendered by the site
research/config/              Condition and support-category configuration
research/runs/                Human-readable and JSONL run records
research/state/               Duplicate tracking and condition state
scripts/                      Collector, link checker, and workflow dispatch helpers
src/                          Astro site source
tests/                        Python behavior tests
```

## Code Style

- Keep repo automation boring and explicit.
- Prefer deterministic file formats over hidden state.
- Treat `research/apps/**/*.md` as the durable review surface.
- Keep Python scripts standard-library first unless a dependency clearly earns its cost.
- Keep Astro pages static-first and derived from repository files.

Example research record:

```markdown
## Tool Name

- URL: https://example.com
- Source: perplexity
- Query: autism daily living app
- Date: 2026-06-21
- Description: Short public-source description for reviewer triage.
```

## Testing Strategy

- Unit/behavior tests cover script logic, especially link discovery and dead-link classification.
- `npm run typecheck` verifies TypeScript and Astro types.
- `npm run build` proves the static site renders all current research files.
- `npm run check:links` verifies rendered research URLs are currently reachable.
- The link checker blocks private, loopback, link-local, and reserved targets by default so untrusted research markdown cannot make CI probe internal network surfaces.
- The collector checks candidate URLs before writing research files. Dead links are excluded from `research/apps` and logged under `research/runs/rejected/`.
- GitHub Actions CI runs the same gates on pull requests and `main`.

## Boundaries

- Always:
  - Keep secrets out of the repository.
  - Run `npm run verify` before merging code or workflow changes when feasible.
  - Preserve source URLs, run logs, and state files for review.
  - Treat Perplexity and GitHub output as discovery leads, not medical validation.
- Ask first:
  - Adding new runtime services, paid APIs, or persistent infrastructure.
  - Changing the public/private boundary.
  - Changing GitHub Pages domain or deployment model.
  - Adding dependencies to production or automation paths.
- Never:
  - Commit API keys, tokens, credentials, or private operational schedules.
  - Present collected leads as clinical recommendations.
  - Silently remove research provenance to make output look cleaner.

## Success Criteria

- Each condition can be collected independently through GitHub Actions.
- Research output is stored in condition-scoped files and reviewed through pull requests.
- Published pages only render durable research leads from `research/apps`.
- Every rendered source URL is checked for current HTTP/HTTPS reachability before publish.
- Dead candidate URLs are rejected at link level without discarding the rest of the condition run.
- CI blocks regressions in type checking, unit tests, build, dependency audit, and link checking.
- Research review uses `docs/research-review-rubric.md` before merge.

## Open Questions

- Should transient link-check warnings remain accepted-for-review, or should some warning classes be quarantined too?
- Should the collector add a stricter public-source allowlist beyond the current private-network link-check guard?
