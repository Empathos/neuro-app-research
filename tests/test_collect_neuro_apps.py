#!/usr/bin/env python3
"""Behavior tests for research collection filtering."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_links  # noqa: E402
import collect_neuro_apps  # noqa: E402


class CollectNeuroAppsTests(unittest.TestCase):
    def test_validate_findings_rejects_dead_links_only(self) -> None:
        findings = [
            {
                "title": "Good Tool",
                "url": "https://example.com/good",
                "description": "Useful public lead.",
                "source": "fixture",
            },
            {
                "title": "Protected Tool",
                "url": "https://example.com/protected",
                "description": "Public lead with protected response.",
                "source": "fixture",
            },
            {
                "title": "Dead Tool",
                "url": "https://example.com/dead",
                "description": "Dead public lead.",
                "source": "fixture",
            },
        ]
        results = {
            "https://example.com/good": check_links.Result(
                "https://example.com/good",
                "ok",
                "HTTP 200",
                ("fixture.md",),
            ),
            "https://example.com/protected": check_links.Result(
                "https://example.com/protected",
                "warning",
                "HTTP 403 reachable/protected",
                ("fixture.md",),
            ),
            "https://example.com/dead": check_links.Result(
                "https://example.com/dead",
                "dead",
                "HTTP 404",
                ("fixture.md",),
            ),
        }

        with mock.patch.object(
            collect_neuro_apps.check_links,
            "check_link",
            side_effect=lambda link, timeout, strict_network: results[link.url],
        ):
            accepted, rejected = collect_neuro_apps.validate_findings(
                "autism",
                "daily-living",
                "autism daily living app",
                findings,
                timeout=1,
            )

        self.assertEqual([item["title"] for item in accepted], ["Good Tool", "Protected Tool"])
        self.assertEqual([item["link_status"] for item in accepted], ["ok", "warning"])
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["title"], "Dead Tool")
        self.assertEqual(rejected[0]["reason"], "HTTP 404")


if __name__ == "__main__":
    unittest.main()
