#!/usr/bin/env python3
"""Collect neurodivergence app leads and write standardized research output."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

import check_links


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "research" / "apps"
CONFIG_PATH = ROOT / "research" / "config" / "categories.json"
RUN_DIR = ROOT / "research" / "runs"
STATE_DIR = ROOT / "research" / "state"
CONDITION_STATE_DIR = STATE_DIR / "conditions"
CONDITION_RUN_DIR = RUN_DIR / "conditions"
REJECTED_RUN_DIR = RUN_DIR / "rejected"

CONDITIONS = [
    "autism",
    "adhd",
    "dyslexia",
    "dyspraxia",
    "tourette",
    "sensory-processing",
    "executive-function",
    "general",
]

CONDITION_TERMS = {
    "autism": ["autism", "autistic", "AAC", "social story"],
    "adhd": ["ADHD", "executive function", "focus"],
    "dyslexia": ["dyslexia", "reading support", "text to speech"],
    "dyspraxia": ["dyspraxia", "motor planning", "coordination"],
    "tourette": ["Tourette", "tic tracking", "habit awareness"],
    "sensory-processing": ["sensory processing", "sensory regulation", "overload"],
    "executive-function": ["executive function", "routine", "task initiation"],
    "general": ["neurodivergent", "neurodiversity", "accessibility"],
}

RELEVANCE_TERMS = {
    "app",
    "mobile",
    "tool",
    "assistive",
    "accessibility",
    "support",
    "communication",
    "routine",
    "sensory",
    "focus",
    "reading",
    "regulation",
    "caregiver",
    "student",
    "neurodivergent",
    "neurodiversity",
    "autism",
    "autistic",
    "adhd",
    "dyslexia",
    "dyspraxia",
    "tourette",
}

CONDITION_EVIDENCE_TERMS = {
    "dyslexia": [
        "dyslexia",
        "dyslexic",
        "reading disorder",
        "reading disability",
        "specific learning disability",
        "specific learning difference",
        "decoding",
        "phonological",
        "structured literacy",
        "orton-gillingham",
        "print disability",
        "accessible reading",
    ],
}


def slug(value: str) -> str:
    return value.strip().lower().replace("_", "-").replace(" ", "-")


def condition_branch_id(condition: str) -> str:
    return slug(condition)


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "conditions": [
            {"id": condition, "label": condition.title(), "terms": terms}
            for condition, terms in CONDITION_TERMS.items()
        ],
        "support_categories": [
            {"id": "general", "label": "General", "terms": ["app", "tool"]}
        ],
        "modifiers": ["app", "mobile app", "tool"],
    }


def config_ids(config: dict, key: str) -> list[str]:
    return [item["id"] for item in config[key]]


def config_item(config: dict, key: str, item_id: str) -> dict:
    items = {item["id"]: item for item in config[key]}
    return items.get(item_id) or items[next(iter(items))]


def condition_state_path(condition: str) -> Path:
    return CONDITION_STATE_DIR / f"{condition_branch_id(condition)}.json"


def condition_runs_path(condition: str) -> Path:
    return CONDITION_RUN_DIR / f"{condition_branch_id(condition)}.jsonl"


def condition_latest_path(condition: str) -> Path:
    return CONDITION_RUN_DIR / f"{condition_branch_id(condition)}.md"


def condition_rejected_path(condition: str) -> Path:
    return REJECTED_RUN_DIR / f"{condition_branch_id(condition)}.jsonl"


def load_state(path: Path) -> dict:
    if not path.exists():
        return {
            "seen_queries": [],
            "seen_urls": [],
            "condition_cursor": 0,
            "category_cursor": 0,
            "modifier_cursor": 0,
            "updated_at": None,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def request_text(url: str, headers: dict[str, str] | None = None) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "neuro-app-research-agent/0.1 (+https://github.com/Empathos)",
            **(headers or {}),
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return value[:500]


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(html.unescape(url))
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    filtered = [(k, v) for k, v in query if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
    return urllib.parse.urlunparse(
        parsed._replace(query=urllib.parse.urlencode(filtered), fragment="")
    )


def extract_json_array(value: str) -> list[dict]:
    value = value.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value)
        value = re.sub(r"\s*```$", "", value)
    start = value.find("[")
    end = value.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        payload = json.loads(value[start : end + 1])
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def perplexity_search(query: str, max_results: int) -> list[dict]:
    api_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if not api_key:
        print("PERPLEXITY_API_KEY is not set; falling back to github-search.", file=sys.stderr)
        return []

    prompt = (
        "Find current public app, tool, or repository leads for this neurodivergence support "
        f"research query: {query!r}. Return only a JSON array with up to "
        f"{max_results} objects. Each object must have title, url, and description. "
        "Use source-backed public URLs. Prefer official product, app-store, documentation, "
        "or repository pages. Do not include commentary outside the JSON."
    )
    body = json.dumps(
        {
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 900,
        }
    ).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.perplexity.ai/v1/sonar",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "neuro-app-research-agent/0.1 (+https://github.com/Empathos)",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read().decode("utf-8", errors="replace")
        payload = json.loads(raw)
    except Exception as exc:
        print(f"perplexity-search failed for {query!r}: {exc}", file=sys.stderr)
        return []

    content = (
        payload.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    candidate_items = extract_json_array(content)
    if not candidate_items:
        candidate_items = payload.get("search_results") or payload.get("citations") or []

    results = []
    for item in candidate_items:
        if isinstance(item, str):
            title = item
            url = item
            description = ""
        elif isinstance(item, dict):
            title = item.get("title") or item.get("name") or "Untitled lead"
            url = item.get("url") or item.get("link") or ""
            description = item.get("description") or item.get("snippet") or item.get("summary") or ""
        else:
            continue
        url = normalize_url(str(url))
        if not url.startswith(("http://", "https://")):
            continue
        results.append(
            {
                "title": clean_text(str(title)),
                "url": url,
                "description": clean_text(str(description)),
                "source": "perplexity-sonar",
            }
        )
        if len(results) >= max_results:
            break
    return results


def github_search(query: str, max_results: int) -> list[dict]:
    search = f"{query} app neurodivergent in:name,description,readme"
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": search, "sort": "updated", "order": "desc", "per_page": max_results}
    )
    try:
        payload = json.loads(
            request_text(
                url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
        )
    except Exception as exc:
        print(f"github-search failed for {query!r}: {exc}", file=sys.stderr)
        return []

    results = []
    for item in payload.get("items", []):
        title = item.get("full_name") or item.get("name") or "GitHub repository"
        description = clean_text(item.get("description") or "")
        if not relevant_enough(title, description, query):
            continue
        results.append(
            {
                "title": title,
                "url": normalize_url(item.get("html_url", "")),
                "description": description,
                "source": "github-search",
            }
        )
    return [item for item in results if item["url"]][:max_results]


def relevant_enough(title: str, description: str, query: str) -> bool:
    haystack = f"{title} {description}".lower()
    if not description.strip():
        return False
    query_terms = {
        term
        for term in re.findall(r"[a-z0-9]+", query.lower())
        if len(term) >= 4 and term not in {"support", "mobile", "source", "open"}
    }
    has_query_match = any(term in haystack for term in query_terms)
    has_domain_match = any(term in haystack for term in RELEVANCE_TERMS)
    return has_query_match and has_domain_match


def condition_evidence_text(finding: dict) -> str:
    return " ".join(
        str(finding.get(key, ""))
        for key in ("title", "description", "url")
    ).lower()


def has_condition_evidence(condition: str, finding: dict) -> bool:
    evidence_terms = CONDITION_EVIDENCE_TERMS.get(condition, [])
    if not evidence_terms:
        return True
    haystack = condition_evidence_text(finding)
    return any(term in haystack for term in evidence_terms)


def compose_query(condition_term: str, category_term: str, modifier: str) -> str:
    category_words = set(re.findall(r"[a-z0-9]+", category_term.lower()))
    modifier_words = set(re.findall(r"[a-z0-9]+", modifier.lower()))
    if modifier_words and modifier_words.issubset(category_words):
        return f"{condition_term} {category_term}"
    return f"{condition_term} {category_term} {modifier}"


def choose_condition(config: dict, state: dict, focus: str | None) -> str:
    conditions = config_ids(config, "conditions")
    if focus:
        normalized = slug(focus)
        return normalized if normalized in conditions else "general"
    cursor = int(state.get("condition_cursor", 0))
    return conditions[cursor % len(conditions)]


def build_queries(config: dict, state: dict, condition: str, category: str, count: int) -> list[str]:
    seen = set(state.get("seen_queries", []))
    condition_terms = config_item(config, "conditions", condition).get("terms", [])
    category_terms = config_item(config, "support_categories", category).get("terms", [])
    modifiers = config.get("modifiers") or ["app", "mobile app", "tool"]
    modifier_cursor = int(state.get("modifier_cursor", 0))
    queries = []

    pairs = [(a, b) for a in condition_terms for b in category_terms]
    if not pairs:
        pairs = [(condition, category)]

    for offset in range(len(modifiers) * len(pairs)):
        condition_term, category_term = pairs[offset % len(pairs)]
        modifier = modifiers[(modifier_cursor + offset) % len(modifiers)]
        query = compose_query(condition_term, category_term, modifier)
        if query not in seen:
            queries.append(query)
        if len(queries) >= count:
            break

    while len(queries) < count:
        query = (
            f"{condition} {category} neurodivergent app research "
            f"pass {len(seen) + len(queries) + 1}"
        )
        queries.append(query)

    return queries


def entry_exists(url: str) -> bool:
    for path in APP_DIR.rglob("*.md"):
        if url in path.read_text(encoding="utf-8"):
            return True
    return False


def append_entries(
    condition: str,
    category: str,
    query: str,
    findings: list[dict],
    seen_urls: set[str],
) -> list[dict]:
    today = dt.datetime.now(dt.UTC).date().isoformat()
    path = APP_DIR / condition / f"{category}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    accepted = []

    with path.open("a", encoding="utf-8") as handle:
        for finding in findings:
            url = finding["url"]
            if url in seen_urls or entry_exists(url):
                continue
            seen_urls.add(url)
            accepted.append(finding)
            title = finding["title"] or "Untitled lead"
            description = finding["description"] or "No description captured from source."
            handle.write(
                "\n"
                f"### {title}\n\n"
                f"- URL: {url}\n"
                f"- Source: {finding['source']}\n"
                f"- Condition: {condition}\n"
                f"- Support category: {category}\n"
                f"- Query: {query}\n"
                f"- Found: {today}\n"
                f"- Description: {description}\n"
            )
    return accepted


def rejected_finding(
    finding: dict,
    condition: str,
    category: str,
    query: str,
    reason: str,
) -> dict:
    return {
        **finding,
        "condition": condition,
        "support_category": category,
        "query": query,
        "rejected_at": dt.datetime.now(dt.UTC).isoformat(),
        "reason": reason,
    }


def validate_findings(
    condition: str,
    category: str,
    query: str,
    findings: list[dict],
    timeout: float,
) -> tuple[list[dict], list[dict]]:
    accepted = []
    rejected = []
    for finding in findings:
        if not has_condition_evidence(condition, finding):
            rejected.append(
                rejected_finding(
                    finding,
                    condition,
                    category,
                    query,
                    "missing condition-specific evidence",
                )
            )
            continue
        url = finding.get("url", "")
        result = check_links.check_link(
            check_links.Link(url, (f"collector:{condition}/{category}",)),
            timeout=timeout,
            strict_network=False,
        )
        finding_with_status = {
            **finding,
            "link_status": result.status,
            "link_detail": result.detail,
        }
        if result.status == "dead":
            rejected.append(
                rejected_finding(finding_with_status, condition, category, query, result.detail)
            )
            continue
        accepted.append(finding_with_status)
    return accepted, rejected


def parse_entry_blocks(markdown: str) -> list[tuple[str, dict]]:
    pattern = re.compile(r"(?ms)^### .+?(?=^### |\Z)")
    blocks = []
    for match in pattern.finditer(markdown):
        block = match.group(0)
        title = block.splitlines()[0].removeprefix("### ").strip()
        fields = {
            key.lower().replace(" ", "_"): value.strip()
            for key, value in re.findall(r"^- ([^:]+):\s*(.*)$", block, flags=re.MULTILINE)
        }
        blocks.append(
            (
                block,
                {
                    "title": title,
                    "url": fields.get("url", ""),
                    "description": fields.get("description", ""),
                    "source": fields.get("source", ""),
                },
            )
        )
    return blocks


def prune_condition_mismatches(condition: str, dry_run: bool = False) -> list[dict]:
    pruned = []
    condition_dir = APP_DIR / condition
    if not condition_dir.exists():
        return pruned
    for path in sorted(condition_dir.glob("*.md")):
        markdown = path.read_text(encoding="utf-8")
        updated = markdown
        try:
            display_path = str(path.relative_to(ROOT))
        except ValueError:
            display_path = str(path)
        for block, finding in parse_entry_blocks(markdown):
            if has_condition_evidence(condition, finding):
                continue
            pruned.append(
                {
                    **finding,
                    "condition": condition,
                    "support_category": path.stem,
                    "path": display_path,
                    "reason": "missing condition-specific evidence",
                }
            )
            updated = updated.replace(block, "")
        if updated != markdown and not dry_run:
            path.write_text(re.sub(r"\n{3,}", "\n\n", updated).lstrip(), encoding="utf-8")
    return pruned


def prune_all_condition_mismatches(dry_run: bool = False) -> list[dict]:
    pruned = []
    for condition in sorted(CONDITION_EVIDENCE_TERMS):
        pruned.extend(prune_condition_mismatches(condition, dry_run=dry_run))
    return pruned


def write_run_summary(record: dict) -> None:
    path = condition_latest_path(record["condition"])
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Latest Research Run",
        "",
        f"- Condition: {record['condition']}",
        f"- UTC timestamp: {record['timestamp']}",
        f"- New findings: {record['new_findings']}",
        f"- Rejected dead links: {record['rejected_findings']}",
        "",
        "## Support Categories",
        "",
    ]
    for category, category_record in record["categories"].items():
        lines.append(f"### {category}")
        lines.append("")
        for query in category_record["queries"]:
            count = category_record["accepted_by_query"].get(query, 0)
            rejected = category_record["rejected_by_query"].get(query, 0)
            lines.append(f"- `{query}`: {count} new finding(s), {rejected} rejected dead link(s)")
        lines.append("")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def append_run_log(record: dict) -> None:
    path = condition_runs_path(record["condition"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def append_rejected_log(condition: str, rejected: list[dict]) -> None:
    if not rejected:
        return
    path = condition_rejected_path(condition)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for item in rejected:
            handle.write(json.dumps(item, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--focus", help="Condition focus. Defaults to rotating condition state.")
    parser.add_argument("--max-results", type=int, default=8)
    parser.add_argument("--query-count", type=int, default=3)
    parser.add_argument("--link-timeout", type=float, default=8.0)
    parser.add_argument(
        "--prune-condition-mismatches",
        action="store_true",
        help="Remove existing leads that lack condition-specific evidence.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report prune candidates without changing files.",
    )
    parser.add_argument(
        "--all-conditions",
        action="store_true",
        help="Apply prune mode to every condition with condition-specific evidence rules.",
    )
    args = parser.parse_args()

    config = load_config()
    bootstrap_state = {
        "condition_cursor": 0,
        "category_cursor": 0,
        "modifier_cursor": 0,
        "seen_queries": [],
        "seen_urls": [],
    }
    condition = choose_condition(config, bootstrap_state, args.focus)
    if args.prune_condition_mismatches:
        pruned = (
            prune_all_condition_mismatches(dry_run=args.dry_run)
            if args.all_conditions
            else prune_condition_mismatches(condition, dry_run=args.dry_run)
        )
        scope = "all" if args.all_conditions else condition
        print(json.dumps({"condition": scope, "pruned": pruned}, indent=2, sort_keys=True))
        return 1 if args.dry_run and pruned else 0

    state_path = condition_state_path(condition)
    state = load_state(state_path)
    seen_urls = set(state.get("seen_urls", []))

    total_found = 0
    total_rejected = 0
    rejected_findings = []
    categories_record = {}
    all_queries = []
    for category in config_ids(config, "support_categories"):
        queries = build_queries(config, state, condition, category, max(1, args.query_count))
        all_queries.extend(queries)
        accepted_by_query = {}
        rejected_by_query = {}
        category_found = 0
        for query in queries:
            findings = perplexity_search(query, args.max_results)
            if not findings:
                findings = github_search(query, args.max_results)
            valid_findings, rejected = validate_findings(
                condition,
                category,
                query,
                findings,
                args.link_timeout,
            )
            rejected_findings.extend(rejected)
            total_rejected += len(rejected)
            accepted = append_entries(condition, category, query, valid_findings, seen_urls)
            accepted_by_query[query] = len(accepted)
            rejected_by_query[query] = len(rejected)
            category_found += len(accepted)
            total_found += len(accepted)
        categories_record[category] = {
            "queries": queries,
            "accepted_by_query": accepted_by_query,
            "rejected_by_query": rejected_by_query,
            "new_findings": category_found,
            "rejected_findings": sum(rejected_by_query.values()),
        }

    seen_queries = list(dict.fromkeys([*state.get("seen_queries", []), *all_queries]))
    state["seen_queries"] = seen_queries[-500:]
    state["seen_urls"] = list(dict.fromkeys([*state.get("seen_urls", []), *sorted(seen_urls)]))[-5000:]
    conditions = config_ids(config, "conditions")
    modifiers = config.get("modifiers") or ["app", "mobile app", "tool"]
    state["condition_cursor"] = (conditions.index(condition) + 1) % len(conditions)
    state["modifier_cursor"] = (int(state.get("modifier_cursor", 0)) + len(all_queries)) % len(modifiers)
    state["updated_at"] = dt.datetime.now(dt.UTC).isoformat()
    save_state(state, state_path)

    record = {
        "timestamp": state["updated_at"],
        "condition": condition,
        "categories": categories_record,
        "new_findings": total_found,
        "rejected_findings": total_rejected,
    }
    append_run_log(record)
    append_rejected_log(condition, rejected_findings)
    write_run_summary(record)
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
