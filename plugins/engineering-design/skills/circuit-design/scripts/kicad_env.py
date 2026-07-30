#!/usr/bin/env python3
"""Helpers for locating a local KiCad installation and exporting its paths."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def find_kicad_shared_support() -> Path | None:
    candidates = [
        Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport"),
        Path("/opt/homebrew/Caskroom/kicad/9.0.7/KiCad/KiCad.app/Contents/SharedSupport"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    cask_root = Path("/opt/homebrew/Caskroom/kicad")
    if cask_root.exists():
        versions = sorted(cask_root.iterdir(), reverse=True)
        for version_dir in versions:
            candidate = version_dir / "KiCad" / "KiCad.app" / "Contents" / "SharedSupport"
            if candidate.exists():
                return candidate

    return None


def configure_kicad_env() -> Path | None:
    shared_support = find_kicad_shared_support()
    if shared_support is None:
        return None

    symbols = str(shared_support / "symbols")
    footprints = str(shared_support / "footprints")

    for version in ("", "6", "7", "8", "9"):
        symbol_key = f"KICAD{version}_SYMBOL_DIR" if version else "KICAD_SYMBOL_DIR"
        footprint_key = f"KICAD{version}_FOOTPRINT_DIR" if version else "KICAD_FOOTPRINT_DIR"
        os.environ.setdefault(symbol_key, symbols)
        os.environ.setdefault(footprint_key, footprints)

    ensure_kicad_global_tables(shared_support)
    return shared_support


def ensure_kicad_global_tables(shared_support: Path) -> Path:
    root_config_dir = Path.home() / ".config" / "kicad"
    root_config_dir.mkdir(parents=True, exist_ok=True)

    for version in ("6.0", "7.0", "8.0", "9.0", ""):
        config_dir = root_config_dir / version if version else root_config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        for table_name in ("fp-lib-table", "sym-lib-table"):
            destination = config_dir / table_name
            if destination.exists():
                continue

            template = shared_support / "template" / table_name
            if template.exists():
                shutil.copyfile(template, destination)

    return root_config_dir / "9.0"
