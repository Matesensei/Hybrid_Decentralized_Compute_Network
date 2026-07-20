from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from scripts.ai_research_watch.engine import load_config, render_markdown, run_watch
from scripts.ai_research_watch.models import ResearchWatchError, State
from scripts.ai_research_watch.util import parse_feed, source_url, write_json_atomic

RSS = b"""<?xml version="1.0"?><rss><channel><item><title>Online learning &amp; drift</title><link>https://example.org/a</link><description><![CDATA[<b>continual learning</b> and rollback]]></description><pubDate>Sun, 19 Jul 2026 08:00:00 GMT</pubDate></item></channel></rss>"""
ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Release</title><link rel="alternate" href="https://example.org/release"/><updated>2026-07-19T08:00:00Z</updated><summary>security patch</summary></entry></feed>"""


def config_dict() -> dict[str, object]:
    return {
        "schema_version": "ai.research-watch.config.v1",
        "project": "test_project",
        "max_age_hours": 168,
        "min_score": 20,
        "output_limit": 20,
        "timeout_seconds": 2,
        "keyword_weights": {
            "research": {"online learning": 20, "continual learning": 15},
            "management": {"rollback": 10},
            "security": {"security patch": 20},
        },
        "sources": [
            {
                "id": "test_feed",
                "adapter": "rss",
                "category": "research",
                "language": "en",
                "trust_weight": 20,
                "enabled": True,
                "url": "https://example.org/feed.xml",
                "repository": None,
                "arxiv_category": None,
                "include_terms": [],
                "exclude_terms": [],
                "priority_terms": ["online learning"],
                "max_items": 10,
            }
        ],
        "recommendation_rules": [
            {
                "id": "research_review",
                "categories": ["research"],
                "action": "reproduce_in_sandbox",
                "target": "research:sandbox",
                "priority": "high",
                "min_score": 30,
                "side_effect": "sandbox",
                "max_evidence": 5,
                "requires_human_approval": True,
            }
        ],
    }


class ResearchWatchTests(unittest.TestCase):
    def _config(self, directory: Path):
        path = directory / "config.json"
        path.write_text(json.dumps(config_dict()), encoding="utf-8")
        return load_config(path)

    def test_parse_rss_sanitizes_html(self):
        item = parse_feed(RSS)[0]
        self.assertEqual(item["title"], "Online learning & drift")
        self.assertEqual(item["summary"], "continual learning and rollback")

    def test_parse_atom_uses_alternate_link(self):
        self.assertEqual(parse_feed(ATOM)[0]["link"], "https://example.org/release")

    def test_xml_doctype_and_entities_are_rejected(self):
        with self.assertRaises(ResearchWatchError):
            parse_feed(b'<!DOCTYPE x [<!ENTITY y "boom">]><rss/>')

    def test_non_web_item_links_are_skipped(self):
        feed = b"""<?xml version="1.0"?><rss><channel><item><title>Bad</title><link>javascript:alert(1)</link></item><item><title>Good</title><link>https://example.org/good#section</link></item></channel></rss>"""
        items = parse_feed(feed)
        self.assertEqual([item["title"] for item in items], ["Good"])

    def test_boolean_timeout_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = config_dict()
            raw["timeout_seconds"] = True
            path = Path(tmp) / "bad-timeout.json"
            path.write_text(json.dumps(raw))
            with self.assertRaises(ResearchWatchError):
                load_config(path)

    def test_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"schema_version":"x","schema_version":"y"}')
            with self.assertRaises(ResearchWatchError):
                load_config(path)

    def test_source_adapters_resolve_reviewed_https_feeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, _ = self._config(Path(tmp))
            self.assertEqual(
                source_url(config.sources[0]), "https://example.org/feed.xml"
            )

    def test_run_watch_emits_human_gated_recommendation(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, sha = self._config(Path(tmp))
            digest = run_watch(
                config,
                config_sha256=sha,
                state=State(),
                fetcher=lambda _url, _timeout, _limit: RSS,
                now=datetime(2026, 7, 19, 12, tzinfo=UTC),
            )
            self.assertEqual(len(digest.items), 1)
            recommendation = digest.to_dict()["recommendations"][0]
            self.assertTrue(recommendation["requires_human_approval"])
            self.assertEqual(recommendation["execution_authority"], "none")

    def test_new_only_uses_state_before_current_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, sha = self._config(Path(tmp))
            state = State()
            first = run_watch(
                config,
                config_sha256=sha,
                state=state,
                new_only=True,
                fetcher=lambda *_: RSS,
                now=datetime(2026, 7, 19, 12, tzinfo=UTC),
            )
            second = run_watch(
                config,
                config_sha256=sha,
                state=state,
                new_only=True,
                fetcher=lambda *_: RSS,
                now=datetime(2026, 7, 19, 13, tzinfo=UTC),
            )
            self.assertEqual(len(first.items), 1)
            self.assertEqual(len(second.items), 0)

    def test_partial_source_failure_is_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = config_dict()
            raw["sources"] = [
                *raw["sources"],
                {
                    **raw["sources"][0],
                    "id": "broken",
                    "url": "https://example.org/broken.xml",
                },
            ]
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps(raw))
            config, sha = load_config(path)
            digest = run_watch(
                config,
                config_sha256=sha,
                state=State(),
                fetcher=lambda url, *_: (
                    (_ for _ in ()).throw(OSError("down")) if "broken" in url else RSS
                ),
                now=datetime(2026, 7, 19, 12, tzinfo=UTC),
            )
            self.assertEqual(digest.sources_succeeded, 1)
            self.assertEqual(len(digest.source_errors), 1)

    def test_atomic_output_is_canonical_and_owner_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.json"
            write_json_atomic(path, {"b": 2, "a": 1})
            self.assertEqual(path.read_text().strip(), '{"a":1,"b":2}')
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)

    def test_markdown_keeps_advisory_boundary_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, sha = self._config(Path(tmp))
            digest = run_watch(
                config,
                config_sha256=sha,
                state=State(),
                fetcher=lambda *_: RSS,
                now=datetime(2026, 7, 19, 12, tzinfo=UTC),
            )
            self.assertIn(
                "cannot trade, publish, deploy, merge", render_markdown(digest)
            )

    def test_repository_config_is_strict_and_human_gated(self):
        path_text = os.environ.get(
            "RESEARCH_WATCH_CONFIG", "config/ai/research_sources.json"
        )
        if not path_text:
            self.skipTest("repository config path not supplied")
        config, _ = load_config(Path(path_text))
        self.assertTrue(config.sources)
        self.assertTrue(config.rules)
        self.assertTrue(all(rule.requires_human_approval for rule in config.rules))
        self.assertTrue(
            all(
                rule.side_effect in {"none", "sandbox", "draft_only"}
                for rule in config.rules
            )
        )


if __name__ == "__main__":
    unittest.main()
