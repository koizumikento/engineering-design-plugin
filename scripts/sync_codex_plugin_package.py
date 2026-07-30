from __future__ import annotations

import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "plugins" / "engineering-design"

PACKAGE_DIRECTORIES = ("skills", "templates")
RUNTIME_SCRIPTS = (
    "cad_inspect.py",
    "cad_runner.py",
    "integration_checker.py",
    "preview_generator.py",
)
ROOT_FILES = (".python-version", "pyproject.toml", "uv.lock")


def replace_directory(name: str) -> None:
    source = REPO_ROOT / name
    target = PACKAGE_ROOT / name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def sync_runtime_scripts() -> None:
    target = PACKAGE_ROOT / "scripts"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for name in RUNTIME_SCRIPTS:
        shutil.copy2(REPO_ROOT / "scripts" / name, target / name)


def main() -> None:
    for directory in PACKAGE_DIRECTORIES:
        replace_directory(directory)
    sync_runtime_scripts()
    for name in ROOT_FILES:
        shutil.copy2(REPO_ROOT / name, PACKAGE_ROOT / name)
    print(f"Synced Codex plugin package: {PACKAGE_ROOT}")


if __name__ == "__main__":
    main()
