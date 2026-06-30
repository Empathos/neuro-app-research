#!/usr/bin/env python3
"""Behavior tests for research collection filtering."""

from __future__ import annotations

import sys
import tempfile
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
                "general",
                "daily-living",
                "general daily living app",
                findings,
                timeout=1,
            )

        self.assertEqual([item["title"] for item in accepted], ["Good Tool", "Protected Tool"])
        self.assertEqual([item["link_status"] for item in accepted], ["ok", "warning"])
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["title"], "Dead Tool")
        self.assertEqual(rejected[0]["reason"], "HTTP 404")

    def test_validate_findings_rejects_dyslexia_lead_without_condition_evidence(self) -> None:
        findings = [
            {
                "title": "Accessibility Settings - iOS User Guide",
                "url": "https://support.apple.com/guide/iphone/accessibility-iph3e2e4367/ios",
                "description": "Guide to Speech, Voice Control, and text-to-speech tools.",
                "source": "fixture",
            },
            {
                "title": "Dyslexia Reading Assistant",
                "url": "https://example.com/dyslexia-reading",
                "description": "Text-to-speech support for dyslexic students and accessible reading.",
                "source": "fixture",
            },
        ]
        ok = check_links.Result(
            "https://example.com/dyslexia-reading",
            "ok",
            "HTTP 200",
            ("fixture.md",),
        )

        with mock.patch.object(
            collect_neuro_apps.check_links,
            "check_link",
            return_value=ok,
        ) as check_link:
            accepted, rejected = collect_neuro_apps.validate_findings(
                "dyslexia",
                "accessibility-assistive-tech",
                "text to speech assistive technology app",
                findings,
                timeout=1,
            )

        self.assertEqual([item["title"] for item in accepted], ["Dyslexia Reading Assistant"])
        self.assertEqual([item["title"] for item in rejected], ["Accessibility Settings - iOS User Guide"])
        self.assertEqual(rejected[0]["reason"], "missing condition-specific evidence")
        self.assertEqual(check_link.call_count, 1)

    def test_prune_condition_mismatches_removes_existing_dyslexia_false_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with unittest.mock.patch.object(collect_neuro_apps, "APP_DIR", Path(tmpdir)):
                path = collect_neuro_apps.APP_DIR / "dyslexia" / "accessibility-assistive-tech.md"
                path.parent.mkdir(parents=True)
                path.write_text(
                    "### Accessibility Settings - iOS User Guide\n\n"
                    "- URL: https://support.apple.com/accessibility\n"
                    "- Source: fixture\n"
                    "- Description: Guide to Speech and text-to-speech tools.\n\n"
                    "### Dyslexia Reading Assistant\n\n"
                    "- URL: https://example.com/dyslexia-reading\n"
                    "- Source: fixture\n"
                    "- Description: Support for dyslexic students and accessible reading.\n",
                    encoding="utf-8",
                )

                pruned = collect_neuro_apps.prune_condition_mismatches("dyslexia")

                self.assertEqual(
                    [item["title"] for item in pruned],
                    ["Accessibility Settings - iOS User Guide"],
                )
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("Accessibility Settings", text)
                self.assertIn("Dyslexia Reading Assistant", text)


if __name__ == "__main__":
    unittest.main()
