# Research Schema

## App Lead Markdown

Collector output is written to:

```text
research/apps/<condition>/<support-category>.md
```

Each lead uses this shape:

```markdown
### Lead Title

- URL: https://example.com
- Source: perplexity-sonar
- Condition: autism
- Support category: communication-aac
- Query: autism AAC app
- Found: 2026-06-19
- Description: Short source-derived description.
```

## Condition State

Condition state is written to:

```text
research/state/conditions/<condition>.json
```

State tracks:

- `seen_queries`
- `seen_urls`
- `condition_cursor`
- `modifier_cursor`
- `updated_at`

The state file prevents obvious duplicate URLs and varies future queries.

## Run Records

Latest human-readable run summary:

```text
research/runs/conditions/<condition>.md
```

Append-only machine-readable run log:

```text
research/runs/conditions/<condition>.jsonl
```

Each JSONL record contains:

- `timestamp`
- `condition`
- `categories`
- `new_findings`

`categories` maps support category IDs to the queries used and the number of accepted findings per query.

## Branch And PR Model

Each condition uses one branch:

```text
research/<condition>
```

Each branch opens or updates one pull request against `main`.

This keeps review at 8 PRs per full research pass instead of one PR per support-category lane.
