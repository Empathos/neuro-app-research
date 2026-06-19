#!/usr/bin/env bash
set -euo pipefail

repo="${RESEARCH_REPO:-Empathos/neuro-app-research}"
workflow="${RESEARCH_WORKFLOW:-research-condition.yml}"
focus="${1:?usage: scripts/trigger_research_condition.sh <condition> [max_results] [query_count]}"
max_results="${2:-4}"
query_count="${3:-1}"

gh --repo "$repo" workflow run "$workflow" \
  --ref main \
  -f "focus=$focus" \
  -f "max_results=$max_results" \
  -f "query_count=$query_count"

echo "Dispatched $workflow: focus=$focus max_results=$max_results query_count=$query_count"
