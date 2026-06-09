"""Project path constants."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DIST = ROOT / "dist"
ANKI_ROOT = Path.home() / "projects" / "english-anki"
OBSCURA = Path.home() / ".local" / "bin" / "obscura"
CURSOR_AGENT = Path.home() / ".local" / "bin" / "cursor-agent"
CURSOR_ENV = Path.home() / ".config" / "cursor-agent" / "env"

RAW_FEED_DIR = DATA / "raw_feed"
BODIES_DIR = DATA / "bodies"
ANALYSES_DIR = DATA / "analyses" / "v2"
EDITIONS_DIR = DATA / "editions"
BUILD_LOGS_DIR = DATA / "build_logs"
LEGACY_DATA_DIR = DATA  # data/YYYY-MM-DD/*.json from prototype

DIST_ASSETS = DIST / "assets"
DIST_EDITIONS = DIST / "editions"
