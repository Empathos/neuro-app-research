#!/usr/bin/env bash
set -euo pipefail

repo="${RESEARCH_REPO:-Empathos/neuro-app-research}"
workflow="${RESEARCH_WORKFLOW:-research-condition.yml}"
config_path="${RESEARCH_CONFIG:-research/config/categories.json}"
max_results="${RESEARCH_MAX_RESULTS:-${1:-4}}"
query_count="${RESEARCH_QUERY_COUNT:-${2:-1}}"
sleep_seconds="${RESEARCH_DISPATCH_SLEEP_SECONDS:-1}"
dry_run="${RESEARCH_DRY_RUN:-0}"

python3 - "$config_path" <<'PY' | while IFS= read -r focus; do
import json
import sys
from pathlib import Path

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for condition in config["conditions"]:
    print(condition["id"])
PY
  if [[ "$dry_run" == "1" || "$dry_run" == "true" ]]; then
    echo "DRY RUN $workflow: focus=$focus max_results=$max_results query_count=$query_count"
  else
    gh --repo "$repo" workflow run "$workflow" \
      --ref main \
      -f "focus=$focus" \
      -f "max_results=$max_results" \
      -f "query_count=$query_count"
    echo "Dispatched $workflow: focus=$focus max_results=$max_results query_count=$query_count"
    sleep "$sleep_seconds"
  fi
done
