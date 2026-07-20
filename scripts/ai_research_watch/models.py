"""Typed contracts and safety invariants for the read-only research watcher."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

CONFIG_SCHEMA: Final = "ai.research-watch.config.v1"
DIGEST_SCHEMA: Final = "ai.research-watch.digest.v1"
STATE_SCHEMA: Final = "ai.research-watch.state.v1"
MAX_CONFIG_BYTES: Final = 512 * 1024
MAX_FEED_BYTES: Final = 2 * 1024 * 1024
MAX_XML_NODES: Final = 20_000
MAX_SEEN_ITEMS: Final = 20_000
MAX_TEXT_CHARS: Final = 4_000
MAX_TITLE_CHARS: Final = 300
MAX_URL_CHARS: Final = 2_048
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ARXIV_CATEGORY = re.compile(r"^[A-Za-z][A-Za-z0-9.-]{0,31}$")
CATEGORIES = frozenset(
    {
        "market",
        "research",
        "software",
        "security",
        "regulatory",
        "management",
        "marketing",
        "infrastructure",
    }
)
SIDE_EFFECTS = frozenset({"none", "sandbox", "draft_only"})


class ResearchWatchError(ValueError):
    """Fail-closed configuration, parsing, state, or output error."""


def identifier(value: str, name: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise ResearchWatchError(f"{name} contains unsupported characters")
    return value


def normalized_terms(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    terms = tuple(" ".join(value.casefold().split()) for value in values)
    if any(not value or len(value) > 160 for value in terms):
        raise ResearchWatchError(f"{name} contains an invalid term")
    if len(terms) != len(set(terms)) or len(terms) > 256:
        raise ResearchWatchError(f"{name} contains duplicates or is too large")
    return terms


@dataclass(frozen=True)
class Source:
    source_id: str
    adapter: str
    category: str
    language: str
    trust_weight: int
    enabled: bool = True
    url: str | None = None
    repository: str | None = None
    arxiv_category: str | None = None
    include_terms: tuple[str, ...] = ()
    exclude_terms: tuple[str, ...] = ()
    priority_terms: tuple[str, ...] = ()
    max_items: int = 25

    def __post_init__(self) -> None:
        identifier(self.source_id, "source.id")
        identifier(self.language, "source.language")
        if self.adapter not in {"rss", "github_releases", "arxiv"}:
            raise ResearchWatchError("unsupported source adapter")
        if self.category not in CATEGORIES:
            raise ResearchWatchError("unsupported source category")
        if type(self.enabled) is not bool:
            raise ResearchWatchError("source.enabled must be boolean")
        if type(self.trust_weight) is not int or not 0 <= self.trust_weight <= 40:
            raise ResearchWatchError("source.trust_weight must be in [0, 40]")
        if type(self.max_items) is not int or not 1 <= self.max_items <= 200:
            raise ResearchWatchError("source.max_items must be in [1, 200]")
        object.__setattr__(
            self, "include_terms", normalized_terms(self.include_terms, "include_terms")
        )
        object.__setattr__(
            self, "exclude_terms", normalized_terms(self.exclude_terms, "exclude_terms")
        )
        object.__setattr__(
            self,
            "priority_terms",
            normalized_terms(self.priority_terms, "priority_terms"),
        )
        if self.adapter == "rss" and not self.url:
            raise ResearchWatchError("rss source requires url")
        if self.adapter == "github_releases" and (
            not self.repository or not REPOSITORY.fullmatch(self.repository)
        ):
            raise ResearchWatchError("github release source requires owner/repository")
        if self.adapter == "arxiv" and (
            not self.arxiv_category or not ARXIV_CATEGORY.fullmatch(self.arxiv_category)
        ):
            raise ResearchWatchError("arxiv source requires a valid category")


@dataclass(frozen=True)
class Rule:
    rule_id: str
    categories: tuple[str, ...]
    action: str
    target: str
    priority: str
    min_score: int
    side_effect: str
    max_evidence: int
    requires_human_approval: bool

    def __post_init__(self) -> None:
        identifier(self.rule_id, "recommendation_rule.id")
        identifier(self.action, "recommendation_rule.action")
        identifier(self.target, "recommendation_rule.target")
        if not self.categories or any(x not in CATEGORIES for x in self.categories):
            raise ResearchWatchError("recommendation rule categories are invalid")
        if len(self.categories) != len(set(self.categories)):
            raise ResearchWatchError("recommendation rule categories must be unique")
        if self.priority not in {"low", "medium", "high", "critical"}:
            raise ResearchWatchError("recommendation rule priority is invalid")
        if type(self.min_score) is not int or not 0 <= self.min_score <= 100:
            raise ResearchWatchError(
                "recommendation rule min_score must be in [0, 100]"
            )
        if self.side_effect not in SIDE_EFFECTS:
            raise ResearchWatchError("recommendation rule side_effect is invalid")
        if type(self.max_evidence) is not int or not 1 <= self.max_evidence <= 20:
            raise ResearchWatchError(
                "recommendation rule max_evidence must be in [1, 20]"
            )
        if self.requires_human_approval is not True:
            raise ResearchWatchError("v1 recommendations must require human approval")


@dataclass(frozen=True)
class Config:
    project: str
    max_age_hours: int
    min_score: int
    output_limit: int
    timeout_seconds: float
    keyword_weights: dict[str, dict[str, int]]
    sources: tuple[Source, ...]
    rules: tuple[Rule, ...]

    def __post_init__(self) -> None:
        identifier(self.project, "project")
        if type(self.max_age_hours) is not int or not 1 <= self.max_age_hours <= 8760:
            raise ResearchWatchError("max_age_hours must be in [1, 8760]")
        if type(self.min_score) is not int or not 0 <= self.min_score <= 100:
            raise ResearchWatchError("min_score must be in [0, 100]")
        if type(self.output_limit) is not int or not 1 <= self.output_limit <= 1000:
            raise ResearchWatchError("output_limit must be in [1, 1000]")
        if not 0.5 <= self.timeout_seconds <= 60:
            raise ResearchWatchError("timeout_seconds must be in [0.5, 60]")
        if not self.sources or len(self.sources) > 128:
            raise ResearchWatchError("sources must contain 1..128 entries")
        if len({x.source_id for x in self.sources}) != len(self.sources):
            raise ResearchWatchError("source ids must be unique")
        if len({x.rule_id for x in self.rules}) != len(self.rules):
            raise ResearchWatchError("recommendation rule ids must be unique")
        for category, weights in self.keyword_weights.items():
            if category not in CATEGORIES or not weights or len(weights) > 256:
                raise ResearchWatchError("keyword_weights group is invalid")
            for term, weight in weights.items():
                if not term.strip() or type(weight) is not int or not 1 <= weight <= 40:
                    raise ResearchWatchError(
                        "keyword weight must be an integer in [1, 40]"
                    )


@dataclass(frozen=True)
class Item:
    item_id: str
    source_id: str
    category: str
    language: str
    title: str
    summary: str
    link: str
    published_at: datetime | None
    observed_at: datetime
    score: int
    matched_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        from .util import format_time

        return {
            "item_id": self.item_id,
            "source_id": self.source_id,
            "category": self.category,
            "language": self.language,
            "title": self.title,
            "summary": self.summary,
            "link": self.link,
            "published_at": format_time(self.published_at),
            "observed_at": format_time(self.observed_at),
            "score": self.score,
            "matched_terms": list(self.matched_terms),
        }


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    rule_id: str
    action: str
    target: str
    priority: str
    side_effect: str
    evidence_item_ids: tuple[str, ...]
    requires_human_approval: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "recommendation_id": self.recommendation_id,
            "rule_id": self.rule_id,
            "action": self.action,
            "target": self.target,
            "priority": self.priority,
            "side_effect": self.side_effect,
            "requires_human_approval": self.requires_human_approval,
            "execution_authority": "none",
            "evidence_item_ids": list(self.evidence_item_ids),
        }


@dataclass
class State:
    seen_ids: list[str] = field(default_factory=list)

    def add(self, values: list[str]) -> None:
        merged = list(dict.fromkeys([*self.seen_ids, *values]))
        self.seen_ids = merged[-MAX_SEEN_ITEMS:]

    def to_dict(self) -> dict[str, object]:
        return {"schema_version": STATE_SCHEMA, "seen_item_ids": self.seen_ids}


@dataclass(frozen=True)
class Digest:
    project: str
    config_sha256: str
    generated_at: datetime
    sources_attempted: int
    sources_succeeded: int
    source_errors: tuple[dict[str, str], ...]
    items: tuple[Item, ...]
    recommendations: tuple[Recommendation, ...]

    def to_dict(self) -> dict[str, object]:
        from .util import format_time

        return {
            "schema_version": DIGEST_SCHEMA,
            "project": self.project,
            "config_sha256": self.config_sha256,
            "generated_at": format_time(self.generated_at),
            "authority": {
                "mode": "advisory_only",
                "execution_authority": "none",
                "requires_human_approval": True,
            },
            "sources": {
                "attempted": self.sources_attempted,
                "succeeded": self.sources_succeeded,
                "failed": self.sources_attempted - self.sources_succeeded,
                "errors": list(self.source_errors),
            },
            "items": [item.to_dict() for item in self.items],
            "recommendations": [item.to_dict() for item in self.recommendations],
        }
