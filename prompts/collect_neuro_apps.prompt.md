# collect_neuro_apps.py Operator Prompt

## Intent

Collect public URLs and short descriptions for apps, tools, directories, or repositories that may assist neurodivergent people. Split durable findings by condition, with each condition run covering every configured support category.

## Inputs

- Required/expected `--focus` condition in GitHub Actions
- Optional `--max-results`
- Optional `--query-count`, applied per support category
- Category definitions in `research/config/categories.json`
- Existing files under `research/apps/`
- Existing condition state under `research/state/conditions/`

## Boundaries

- Do not collect private personal data.
- Do not make medical efficacy claims.
- Do not claim an app is clinically validated unless the source explicitly says so.
- Treat search snippets as leads, not proof.
- Prefer URL, source, date, and description over polished prose.

## Verification

After running:

1. Confirm `research/runs/conditions/<condition>.jsonl` received a new line.
2. Confirm `research/state/conditions/<condition>.json` updated.
3. Confirm `research/runs/conditions/<condition>.md` reflects the current pass.
4. Review added markdown entries for obvious duplicates or irrelevant pages.
5. Let the GitHub pull request be the human review gate.

## Future LLM Step

An optional LLM pass may later classify condition, summarize app purpose, and score relevance. It should run only after URL discovery and must preserve source URLs.
