#!/usr/bin/env python3
"""Check research lead URLs and write a small markdown report."""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
URL_PATTERN = re.compile(r"^- URL:\s*(https?://\S+)\s*$", re.MULTILINE)
PROTECTED_STATUSES = {401, 403, 405, 406, 407, 408, 409, 418, 423, 425, 429, 451}
HARD_DEAD_STATUSES = {404, 410}


@dataclasses.dataclass(frozen=True)
class Link:
    url: str
    sources: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class Result:
    url: str
    status: str
    detail: str
    sources: tuple[str, ...]


def discover_links(paths: list[str]) -> list[Link]:
    found: dict[str, set[str]] = {}
    for raw_path in paths:
        path = (ROOT / raw_path).resolve()
        candidates = sorted(path.rglob("*.md")) if path.is_dir() else [path]
        for candidate in candidates:
            if not candidate.exists() or candidate.suffix != ".md":
                continue
            rel = candidate.relative_to(ROOT).as_posix()
            text = candidate.read_text(encoding="utf-8")
            for match in URL_PATTERN.finditer(text):
                url = match.group(1).rstrip(".,)")
                found.setdefault(url, set()).add(rel)
    return [Link(url=url, sources=tuple(sorted(sources))) for url, sources in sorted(found.items())]


def build_request(url: str, method: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        method=method,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8",
            "User-Agent": (
                "Mozilla/5.0 (compatible; EmpathosResearchLinkCheck/0.1; "
                "+https://research.empathos.ai)"
            ),
        },
    )


def classify_http_error(exc: urllib.error.HTTPError, link: Link) -> Result:
    code = exc.code
    if code in HARD_DEAD_STATUSES:
        return Result(link.url, "dead", f"HTTP {code}", link.sources)
    if code in PROTECTED_STATUSES:
        return Result(link.url, "warning", f"HTTP {code} reachable/protected", link.sources)
    if 500 <= code <= 599:
        return Result(link.url, "warning", f"HTTP {code} server error", link.sources)
    return Result(link.url, "warning", f"HTTP {code}", link.sources)


def classify_url_error(exc: urllib.error.URLError, link: Link, strict_network: bool) -> Result:
    reason = exc.reason
    status = "dead" if strict_network else "warning"
    if isinstance(reason, ssl.SSLError):
        return Result(link.url, status, f"TLS error: {reason}", link.sources)
    return Result(link.url, status, f"Network error: {reason}", link.sources)


def check_link(link: Link, timeout: float, strict_network: bool) -> Result:
    parsed = urllib.parse.urlparse(link.url)
    if not parsed.scheme or not parsed.netloc:
        return Result(link.url, "dead", "Invalid URL", link.sources)

    for method in ("HEAD", "GET"):
        try:
            with urllib.request.urlopen(build_request(link.url, method), timeout=timeout) as response:
                code = response.status
                final_url = response.geturl()
            if 200 <= code <= 399:
                detail = f"HTTP {code}"
                if final_url != link.url:
                    detail = f"{detail} -> {final_url}"
                return Result(link.url, "ok", detail, link.sources)
            if code in HARD_DEAD_STATUSES:
                return Result(link.url, "dead", f"HTTP {code}", link.sources)
            if code in PROTECTED_STATUSES or 500 <= code <= 599:
                return Result(link.url, "warning", f"HTTP {code}", link.sources)
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in {405, 501}:
                continue
            return classify_http_error(exc, link)
        except urllib.error.URLError as exc:
            if method == "HEAD":
                continue
            return classify_url_error(exc, link, strict_network)
        except TimeoutError as exc:
            if method == "HEAD":
                continue
            status = "dead" if strict_network else "warning"
            return Result(link.url, status, f"Timeout: {exc}", link.sources)
        except Exception as exc:  # noqa: BLE001 - report unexpected checker/runtime failures.
            if method == "HEAD":
                continue
            return Result(link.url, "warning", f"{type(exc).__name__}: {exc}", link.sources)
    return Result(link.url, "warning", "No usable response", link.sources)


def write_report(results: list[Result], report_path: Path) -> None:
    counts = {
        "ok": sum(1 for result in results if result.status == "ok"),
        "warning": sum(1 for result in results if result.status == "warning"),
        "dead": sum(1 for result in results if result.status == "dead"),
    }
    lines = [
        "# Link Check Report",
        "",
        f"- Checked links: {len(results)}",
        f"- OK: {counts['ok']}",
        f"- Warnings: {counts['warning']}",
        f"- Dead: {counts['dead']}",
        "",
    ]
    for status in ("dead", "warning", "ok"):
        bucket = [result for result in results if result.status == status]
        if not bucket:
            continue
        lines.append(f"## {status.title()}")
        lines.append("")
        for result in bucket:
            source_list = ", ".join(result.sources[:4])
            if len(result.sources) > 4:
                source_list += f", +{len(result.sources) - 4} more"
            lines.append(f"- `{result.detail}` {result.url}")
            lines.append(f"  - Sources: {source_list}")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", default=["research/apps"])
    parser.add_argument("--report", default="link-check-report.md")
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument(
        "--strict-network",
        action="store_true",
        help="Treat transient network/TLS/timeouts as failures instead of warnings.",
    )
    args = parser.parse_args()

    links = discover_links(args.paths)
    if not links:
        print("No research links found.")
        write_report([], ROOT / args.report)
        return 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        results = list(
            executor.map(
                lambda link: check_link(link, args.timeout, args.strict_network),
                links,
            )
        )
    results = sorted(results, key=lambda result: (result.status, result.url))
    write_report(results, ROOT / args.report)

    dead = [result for result in results if result.status == "dead"]
    warnings = [result for result in results if result.status == "warning"]
    print(f"Checked {len(results)} links: {len(dead)} dead, {len(warnings)} warning(s).")
    if dead:
        for result in dead[:20]:
            print(f"DEAD {result.detail}: {result.url}", file=sys.stderr)
        if len(dead) > 20:
            print(f"... and {len(dead) - 20} more dead link(s)", file=sys.stderr)
        print(f"Full report: {args.report}", file=sys.stderr)
        return 1
    if warnings:
        print(f"Warnings recorded in {args.report}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
