"""Configuration loading, deterministic scoring, recommendations, and digest rendering."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from .models import (
    Config,
    Digest,
    Item,
    Recommendation,
    ResearchWatchError,
    Rule,
    Source,
    State,
)
from .util import (
    Fetcher,
    canonical_json,
    default_fetch,
    ensure_utc,
    item_id,
    normalize,
    parse_feed,
    read_json,
    require_bool,
    require_int,
    require_list,
    require_object,
    require_string,
    sanitize,
    source_url,
    term_matches,
)

TOP_LEVEL = {
    "schema_version",
    "project",
    "max_age_hours",
    "min_score",
    "output_limit",
    "timeout_seconds",
    "keyword_weights",
    "sources",
    "recommendation_rules",
}
SOURCE_FIELDS = {
    "id",
    "adapter",
    "category",
    "language",
    "trust_weight",
    "enabled",
    "url",
    "repository",
    "arxiv_category",
    "include_terms",
    "exclude_terms",
    "priority_terms",
    "max_items",
}
RULE_FIELDS = {
    "id",
    "categories",
    "action",
    "target",
    "priority",
    "min_score",
    "side_effect",
    "max_evidence",
    "requires_human_approval",
}


def _strings(value: object, name: str) -> tuple[str, ...]:
    return tuple(require_string(x, name) for x in require_list(value, name))


def load_config(path: Path) -> tuple[Config, str]:
    value, raw_bytes = read_json(path)
    raw = require_object(value, "config")
    if set(raw) != TOP_LEVEL or raw["schema_version"] != "ai.research-watch.config.v1":
        raise ResearchWatchError("configuration fields or schema version are invalid")
    sources: list[Source] = []
    for value in require_list(raw["sources"], "sources"):
        source = require_object(value, "source")
        if set(source) != SOURCE_FIELDS:
            raise ResearchWatchError("source fields do not match the schema")
        sources.append(
            Source(
                source_id=require_string(source["id"], "source.id"),
                adapter=require_string(source["adapter"], "source.adapter"),
                category=require_string(source["category"], "source.category"),
                language=require_string(source["language"], "source.language"),
                trust_weight=require_int(source["trust_weight"], "source.trust_weight"),
                enabled=require_bool(source["enabled"], "source.enabled"),
                url=None
                if source["url"] is None
                else require_string(source["url"], "source.url"),
                repository=None
                if source["repository"] is None
                else require_string(source["repository"], "source.repository"),
                arxiv_category=None
                if source["arxiv_category"] is None
                else require_string(source["arxiv_category"], "source.arxiv_category"),
                include_terms=_strings(source["include_terms"], "source.include_terms"),
                exclude_terms=_strings(source["exclude_terms"], "source.exclude_terms"),
                priority_terms=_strings(
                    source["priority_terms"], "source.priority_terms"
                ),
                max_items=require_int(source["max_items"], "source.max_items"),
            )
        )
    rules: list[Rule] = []
    for value in require_list(raw["recommendation_rules"], "recommendation_rules"):
        rule = require_object(value, "recommendation_rule")
        if set(rule) != RULE_FIELDS:
            raise ResearchWatchError(
                "recommendation rule fields do not match the schema"
            )
        rules.append(
            Rule(
                rule_id=require_string(rule["id"], "recommendation_rule.id"),
                categories=_strings(
                    rule["categories"], "recommendation_rule.categories"
                ),
                action=require_string(rule["action"], "recommendation_rule.action"),
                target=require_string(rule["target"], "recommendation_rule.target"),
                priority=require_string(
                    rule["priority"], "recommendation_rule.priority"
                ),
                min_score=require_int(
                    rule["min_score"], "recommendation_rule.min_score"
                ),
                side_effect=require_string(
                    rule["side_effect"], "recommendation_rule.side_effect"
                ),
                max_evidence=require_int(
                    rule["max_evidence"], "recommendation_rule.max_evidence"
                ),
                requires_human_approval=require_bool(
                    rule["requires_human_approval"],
                    "recommendation_rule.requires_human_approval",
                ),
            )
        )
    weights_raw = require_object(raw["keyword_weights"], "keyword_weights")
    weights: dict[str, dict[str, int]] = {}
    for category, value in weights_raw.items():
        group = require_object(value, f"keyword_weights.{category}")
        weights[category] = {
            require_string(term, "keyword term").casefold(): require_int(
                weight, "keyword weight"
            )
            for term, weight in group.items()
        }
    config = Config(
        project=require_string(raw["project"], "project"),
        max_age_hours=require_int(raw["max_age_hours"], "max_age_hours"),
        min_score=require_int(raw["min_score"], "min_score"),
        output_limit=require_int(raw["output_limit"], "output_limit"),
        timeout_seconds=float(cast(int | float, raw["timeout_seconds"])),
        keyword_weights=weights,
        sources=tuple(sources),
        rules=tuple(rules),
    )
    return config, hashlib.sha256(raw_bytes).hexdigest()


def _score(
    config: Config, source: Source, raw: dict[str, object], now: datetime
) -> Item | None:
    title = sanitize(str(raw["title"]), 300)
    summary = sanitize(str(raw.get("summary", "")))
    link = str(raw["link"])
    text = normalize(f"{title} {summary}")
    if source.include_terms and not any(
        term_matches(term, text) for term in source.include_terms
    ):
        return None
    if any(term_matches(term, text) for term in source.exclude_terms):
        return None
    published = raw.get("published_at")
    published_at = ensure_utc(published) if isinstance(published, datetime) else None
    if published_at and (
        published_at > now + timedelta(hours=6)
        or now - published_at > timedelta(hours=config.max_age_hours)
    ):
        return None
    matches: list[str] = []
    score = source.trust_weight
    for category, terms in config.keyword_weights.items():
        for term, weight in terms.items():
            if term_matches(term, text):
                score += weight
                matches.append(f"{category}:{term}")
    for term in source.priority_terms:
        if term_matches(term, text):
            score += 10
            matches.append(f"priority:{term}")
    if published_at:
        age = max(0.0, (now - published_at).total_seconds() / 3600)
        score += 12 if age <= 24 else 8 if age <= 72 else 4
    score = min(100, score)
    if score < config.min_score:
        return None
    return Item(
        item_id=item_id(source.source_id, link, title),
        source_id=source.source_id,
        category=source.category,
        language=source.language,
        title=title,
        summary=summary,
        link=link,
        published_at=published_at,
        observed_at=now,
        score=score,
        matched_terms=tuple(sorted(set(matches))),
    )


def _recommendations(
    config: Config, items: tuple[Item, ...]
) -> tuple[Recommendation, ...]:
    result: list[Recommendation] = []
    for rule in config.rules:
        evidence = tuple(
            item.item_id
            for item in items
            if item.category in rule.categories and item.score >= rule.min_score
        )[: rule.max_evidence]
        if not evidence:
            continue
        payload = {
            "project": config.project,
            "rule": rule.rule_id,
            "evidence": evidence,
        }
        digest = hashlib.sha256(canonical_json(payload).encode()).hexdigest()
        result.append(
            Recommendation(
                recommendation_id=f"rec_{digest[:24]}",
                rule_id=rule.rule_id,
                action=rule.action,
                target=rule.target,
                priority=rule.priority,
                side_effect=rule.side_effect,
                evidence_item_ids=evidence,
            )
        )
    return tuple(result)


def run_watch(
    config: Config,
    *,
    config_sha256: str,
    state: State,
    new_only: bool = False,
    fetcher: Fetcher = default_fetch,
    now: datetime | None = None,
) -> Digest:
    now = ensure_utc(now or datetime.now(UTC))
    previous = set(state.seen_ids)
    attempted = succeeded = 0
    errors: list[dict[str, str]] = []
    found: dict[str, Item] = {}
    for source in config.sources:
        if not source.enabled:
            continue
        attempted += 1
        try:
            data = fetcher(source_url(source), config.timeout_seconds, 2 * 1024 * 1024)
            entries = parse_feed(data)[: source.max_items]
            succeeded += 1
            for raw in entries:
                item = _score(config, source, raw, now)
                if item and (not new_only or item.item_id not in previous):
                    current = found.get(item.item_id)
                    if current is None or item.score > current.score:
                        found[item.item_id] = item
        except Exception as exc:
            errors.append(
                {
                    "source_id": source.source_id,
                    "error": sanitize(f"{type(exc).__name__}: {exc}", 300),
                }
            )
    items = tuple(
        sorted(
            found.values(),
            key=lambda item: (
                -item.score,
                -(item.published_at or datetime.min.replace(tzinfo=UTC)).timestamp(),
                item.item_id,
            ),
        )[: config.output_limit]
    )
    state.add([item.item_id for item in items])
    return Digest(
        project=config.project,
        config_sha256=config_sha256,
        generated_at=now,
        sources_attempted=attempted,
        sources_succeeded=succeeded,
        source_errors=tuple(errors),
        items=items,
        recommendations=_recommendations(config, items),
    )


def render_markdown(digest: Digest) -> str:
    lines = [
        f"# AI research/news digest — {digest.project}",
        "",
        "> Advisory only. This output cannot trade, publish, deploy, merge, install dependencies or mutate production state.",
        "",
        f"- Sources: {digest.sources_succeeded}/{digest.sources_attempted} succeeded",
        f"- Relevant items: {len(digest.items)}",
        f"- Human-gated recommendations: {len(digest.recommendations)}",
        "",
        "## Recommendations",
    ]
    if not digest.recommendations:
        lines.append("- No recommendation crossed its evidence threshold.")
    for rec in digest.recommendations:
        lines.append(
            f"- **{rec.priority.upper()}** `{rec.action}` → `{rec.target}`; approval required; authority: none"
        )
    lines.extend(["", "## Evidence"])
    if not digest.items:
        lines.append("- No new relevant item.")
    for item in digest.items:
        title = item.title.replace("[", "\\[").replace("]", "\\]")
        lines.append(
            f"- [{title}]({item.link}) — score {item.score}, `{item.category}`, `{item.source_id}`"
        )
    if digest.source_errors:
        lines.extend(["", "## Source failures"])
        for error in digest.source_errors:
            lines.append(f"- `{error['source_id']}`: {error['error']}")
    return "\n".join(lines) + "\n"
