"""Safe IO, feed parsing, canonical JSON, and atomic state helpers."""

from __future__ import annotations

import hashlib
import html
import ipaddress
import json
import os
import re
import stat
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

from .models import (
    ARXIV_CATEGORY,
    MAX_CONFIG_BYTES,
    MAX_FEED_BYTES,
    MAX_TEXT_CHARS,
    MAX_TITLE_CHARS,
    MAX_URL_CHARS,
    MAX_XML_NODES,
    REPOSITORY,
    STATE_SCHEMA,
    ResearchWatchError,
    Source,
    State,
)

Fetcher = Callable[[str, float, int], bytes]
TOKEN = re.compile(r"[\w+#.-]+", re.UNICODE)


class _HTMLText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ResearchWatchError("JSON contains duplicate object keys")
        result[key] = value
    return result


def read_json(path: Path, max_bytes: int = MAX_CONFIG_BYTES) -> tuple[object, bytes]:
    raw = path.read_bytes()
    if not raw or len(raw) > max_bytes:
        raise ResearchWatchError("JSON file is empty or exceeds its size limit")
    try:
        value = json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchWatchError("JSON file is invalid") from exc
    return value, raw


def require_object(value: object, name: str) -> dict[str, object]:
    if type(value) is not dict:
        raise ResearchWatchError(f"{name} must be an object")
    return dict(value)


def require_list(value: object, name: str) -> list[object]:
    if type(value) is not list:
        raise ResearchWatchError(f"{name} must be a list")
    return list(value)


def require_string(value: object, name: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ResearchWatchError(f"{name} must be a non-empty trimmed string")
    return value


def optional_string(value: object, name: str) -> str | None:
    return None if value is None else require_string(value, name)


def require_int(value: object, name: str) -> int:
    if type(value) is not int:
        raise ResearchWatchError(f"{name} must be an integer")
    return value


def require_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ResearchWatchError(f"{name} must be boolean")
    return value


def validate_https_url(value: str) -> str:
    if len(value) > MAX_URL_CHARS:
        raise ResearchWatchError("source URL exceeds the length limit")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ResearchWatchError("source URL must use HTTPS with a hostname")
    if parsed.username or parsed.password or parsed.fragment:
        raise ResearchWatchError("source URL contains forbidden userinfo or fragment")
    try:
        literal = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        literal = None
    if literal and (
        literal.is_private
        or literal.is_loopback
        or literal.is_link_local
        or literal.is_reserved
        or literal.is_unspecified
        or literal.is_multicast
    ):
        raise ResearchWatchError("source URL targets a private or reserved IP")
    return value


def source_url(source: Source) -> str:
    if source.adapter == "rss":
        assert source.url
        return validate_https_url(source.url)
    if source.adapter == "github_releases":
        assert source.repository and REPOSITORY.fullmatch(source.repository)
        return f"https://github.com/{source.repository}/releases.atom"
    assert source.arxiv_category and ARXIV_CATEGORY.fullmatch(source.arxiv_category)
    return f"https://export.arxiv.org/rss/{source.arxiv_category}"


def default_fetch(url: str, timeout: float, max_bytes: int) -> bytes:
    request = urllib.request.Request(
        validate_https_url(url),
        headers={
            "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml",
            "User-Agent": "AI-Research-Watch/1.0 (+read-only; advisory-only)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final = validate_https_url(response.geturl())
        if urllib.parse.urlsplit(final).scheme != "https":
            raise ResearchWatchError("feed redirected away from HTTPS")
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            raise ResearchWatchError("feed exceeds the byte limit")
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ResearchWatchError("feed exceeds the byte limit")
    return data


def sanitize(value: str, maximum: int = MAX_TEXT_CHARS) -> str:
    parser = _HTMLText()
    try:
        parser.feed(html.unescape(value))
        parser.close()
        value = " ".join(parser.parts)
    except Exception:
        pass
    value = "".join(ch if ch >= " " or ch in "\n\t" else " " for ch in value)
    return re.sub(r"\s+", " ", value).strip()[:maximum]


def normalize(value: str) -> str:
    return " ".join(TOKEN.findall(value.casefold()))


def term_matches(term: str, text: str) -> bool:
    term = normalize(term)
    return bool(term) and (term in text if " " in term else term in text.split())


def parse_time(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    try:
        return ensure_utc(parsedate_to_datetime(value))
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        return ensure_utc(
            datetime.fromisoformat(
                value[:-1] + "+00:00" if value.endswith("Z") else value
            )
        )
    except ValueError:
        return None


def ensure_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def format_time(value: datetime | None) -> str | None:
    return (
        None
        if value is None
        else ensure_utc(value).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def _child_text(entry: ET.Element, names: set[str]) -> str:
    for node in entry.iter():
        if node is entry or _local(node.tag) not in names:
            continue
        text = "".join(node.itertext()).strip()
        if text:
            return text
    return ""


def _link(entry: ET.Element) -> str:
    preferred: list[str] = []
    fallback: list[str] = []
    for node in entry:
        if _local(node.tag) != "link":
            continue
        href = (node.attrib.get("href") or node.text or "").strip()
        if not href:
            continue
        (
            preferred
            if node.attrib.get("rel", "alternate") in {"alternate", ""}
            else fallback
        ).append(href)
    return (preferred or fallback or [""])[0][:MAX_URL_CHARS]


def parse_feed(data: bytes) -> list[dict[str, object]]:
    if not data or len(data) > MAX_FEED_BYTES:
        raise ResearchWatchError("feed is empty or exceeds the byte limit")
    upper = data[:4096].upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ResearchWatchError("DOCTYPE and ENTITY declarations are forbidden")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ResearchWatchError("feed XML is malformed") from exc
    if sum(1 for _ in root.iter()) > MAX_XML_NODES:
        raise ResearchWatchError("feed XML exceeds the node limit")
    entries = [node for node in root.iter() if _local(node.tag) in {"entry", "item"}]
    result: list[dict[str, object]] = []
    for entry in entries:
        title = sanitize(_child_text(entry, {"title"}), MAX_TITLE_CHARS)
        link = _link(entry)
        if not title or not link:
            continue
        result.append(
            {
                "title": title,
                "link": link,
                "summary": sanitize(
                    _child_text(entry, {"summary", "description", "content"})
                ),
                "published_at": parse_time(
                    _child_text(entry, {"published", "updated", "pubDate", "date"})
                ),
            }
        )
    return result


def item_id(source_id: str, link: str, title: str) -> str:
    digest = hashlib.sha256(f"{source_id}\0{link}\0{title}".encode()).hexdigest()
    return f"news_{digest[:24]}"


def load_state(path: Path | None) -> State:
    if path is None or not path.exists():
        return State()
    value, _ = read_json(path)
    raw = require_object(value, "state")
    if (
        set(raw) != {"schema_version", "seen_item_ids"}
        or raw["schema_version"] != STATE_SCHEMA
    ):
        raise ResearchWatchError("state schema is invalid")
    ids = [
        require_string(x, "seen_item_id")
        for x in require_list(raw["seen_item_ids"], "seen_item_ids")
    ]
    if len(ids) != len(set(ids)):
        raise ResearchWatchError("state contains duplicate item ids")
    return State(ids[-20_000:])


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            if not text.endswith("\n"):
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json_atomic(path: Path, value: object) -> None:
    write_text_atomic(path, canonical_json(value))
