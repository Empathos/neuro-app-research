#!/usr/bin/env python3
"""Behavior tests for the research link checker."""

from __future__ import annotations

import http.server
import socketserver
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_links  # noqa: E402


class FixtureHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:  # noqa: N802 - stdlib handler API.
        self._respond()

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API.
        self._respond()

    def log_message(self, format: str, *args: object) -> None:
        return

    def _respond(self) -> None:
        if self.path == "/dead":
            self.send_response(404)
            self.end_headers()
            return
        if self.path == "/redirect-private":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()


class LinkCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def test_detects_ok_and_dead_links(self) -> None:
        ok = check_links.Link(f"{self.base_url}/ok", ("fixture.md",))
        dead = check_links.Link(f"{self.base_url}/dead", ("fixture.md",))

        self.assertEqual(
            check_links.check_link(ok, timeout=2, strict_network=False, allow_private=True).status,
            "ok",
        )
        dead_result = check_links.check_link(
            dead,
            timeout=2,
            strict_network=False,
            allow_private=True,
        )
        self.assertEqual(dead_result.status, "dead")
        self.assertEqual(dead_result.detail, "HTTP 404")

    def test_blocks_private_targets_by_default(self) -> None:
        link = check_links.Link(f"{self.base_url}/ok", ("fixture.md",))

        result = check_links.check_link(link, timeout=2, strict_network=False)

        self.assertEqual(result.status, "dead")
        self.assertIn("Blocked private/loopback", result.detail)

    def test_blocks_private_redirect_targets_by_default(self) -> None:
        link = check_links.Link("https://example.com/fixture", ("fixture.md",))

        with self.assertRaises(check_links.BlockedTargetError):
            check_links.PublicRedirectHandler(link, allow_private=False).redirect_request(
                check_links.build_request(link.url, "GET"),
                fp=None,
                code=302,
                msg="Found",
                headers={},
                newurl=f"{self.base_url}/ok",
            )

    def test_discovers_links_from_external_fixture_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir) / "fixture.md"
            fixture.write_text(f"- URL: {self.base_url}/ok\n", encoding="utf-8")

            links = check_links.discover_links([temp_dir])

        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].url, f"{self.base_url}/ok")
        self.assertIn("fixture.md", links[0].sources[0])


if __name__ == "__main__":
    unittest.main()
