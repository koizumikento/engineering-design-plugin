#!/usr/bin/env python3
"""Helpers for locating a local KiCad installation and exporting its paths."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def find_kicad_shared_support(version: int = 9) -> Path | None:
    symbol_dir = os.environ.get(f"KICAD{version}_SYMBOL_DIR") or os.environ.get("KICAD_SYMBOL_DIR")
    if symbol_dir and Path(symbol_dir).is_dir():
        return Path(symbol_dir).parent
    candidates = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "KiCad" / f"{version}.0" / "share" / "kicad",
        Path("/usr/share/kicad"),
        Path("/usr/local/share/kicad"),
        Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport"),
    ]

    for candidate in candidates:
        if (candidate / "symbols").is_dir():
            return candidate

    cask_root = Path("/opt/homebrew/Caskroom/kicad")
    if cask_root.exists():
        versions = sorted(cask_root.iterdir(), reverse=True)
        for version_dir in versions:
            if not version_dir.name.startswith(f"{version}."):
                continue
            candidate = version_dir / "KiCad" / "KiCad.app" / "Contents" / "SharedSupport"
            if candidate.exists():
                return candidate

    return None


def configure_kicad_env(version: int = 9) -> Path | None:
    if version not in (9, 10):
        raise ValueError("supported KiCad targets are 9 and 10")
    shared_support = find_kicad_shared_support(version)
    if shared_support is None:
        return None

    symbols = str(shared_support / "symbols")
    footprints = str(shared_support / "footprints")

    for suffix in ("", str(version)):
        symbol_key = f"KICAD{suffix}_SYMBOL_DIR" if suffix else "KICAD_SYMBOL_DIR"
        footprint_key = f"KICAD{suffix}_FOOTPRINT_DIR" if suffix else "KICAD_FOOTPRINT_DIR"
        os.environ.setdefault(symbol_key, symbols)
        os.environ.setdefault(footprint_key, footprints)

    ensure_kicad_global_tables(shared_support, version)
    return shared_support


def ensure_kicad_global_tables(shared_support: Path, version: int = 9) -> Path:
    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library/Preferences"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_dir = root / "kicad" / f"{version}.0"
    for table_name in ("fp-lib-table", "sym-lib-table"):
        destination = config_dir / table_name
        template = shared_support / "template" / table_name
        if not destination.exists() and template.is_file():
            config_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(template, destination)
    return config_dir
