#!/usr/bin/env python3
"""Backward-compatible entrypoint — use `python3 -m english_news_digest` instead."""

from __future__ import annotations

import sys

from english_news_digest.cli import main

if __name__ == "__main__":
    # Map legacy flags to build-edition where possible.
    argv = ["build-edition"]
    for arg in sys.argv[1:]:
        if arg == "--refresh":
            argv.append("--refresh-analysis")
        elif arg == "--import-anki":
            argv.append("--import-anki")
        elif arg == "--deep" or arg == "--deep-only":
            print("Note: --deep is removed; unified article pages include chunk explanations.")
        elif arg.startswith("--limit"):
            print("Note: --limit is removed; editions always select exactly five articles.")
        else:
            argv.append(arg)
    raise SystemExit(main(argv))
