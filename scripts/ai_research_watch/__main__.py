"""Command-line entry point for the read-only research watcher."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .engine import load_config, render_markdown, run_watch
from .models import ResearchWatchError
from .util import load_state, sanitize, write_json_atomic, write_text_atomic


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Read-only AI research/news watcher")
    value.add_argument("--config", type=Path, required=True)
    value.add_argument("--output", type=Path, required=True)
    value.add_argument("--markdown-output", type=Path)
    value.add_argument("--state", type=Path)
    value.add_argument("--new-only", action="store_true")
    value.add_argument(
        "--strict", action="store_true", help="fail when every enabled source fails"
    )
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config, digest_sha = load_config(args.config)
        state = load_state(args.state)
        digest = run_watch(
            config, config_sha256=digest_sha, state=state, new_only=args.new_only
        )
        write_json_atomic(args.output, digest.to_dict())
        if args.markdown_output:
            write_text_atomic(args.markdown_output, render_markdown(digest))
        if args.state:
            write_json_atomic(args.state, state.to_dict())
        return (
            1
            if args.strict and digest.sources_attempted and not digest.sources_succeeded
            else 0
        )
    except (OSError, ResearchWatchError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": "ai.research-watch.error.v1",
                    "error_type": type(exc).__name__,
                    "message": sanitize(str(exc), 500),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
