#!/usr/bin/env python3
"""Validate plugin release metadata, skill structure, and local references."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import unquote


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PLUGIN_VERSION = "2.1.1"
EXPECTED_PROJECT_VERSION = "0.3.0"
EXPECTED_SKILLS = {
    "circuit-design",
    "integration",
    "mechanical-cad",
    "spec-writing",
}
ACTION_PATTERN = re.compile(
    r"^\s*uses:\s*[^@\s]+@([0-9a-f]{40})(?:\s+#.*)?$",
    re.MULTILINE,
)
MARKDOWN_LINK_PATTERN = re.compile(r"\]\(([^)]+)\)")
REFERENCE_PATH_PATTERN = re.compile(r"`(references/[^`\s]+)`")
PACKAGED_RUNTIME_SCRIPTS = {
    "cad_inspect.py",
    "cad_runner.py",
    "integration_checker.py",
    "preview_generator.py",
}


class ValidationError(RuntimeError):
    """Raised when release validation finds one or more errors."""


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path.relative_to(REPO_ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(
            f"{path.relative_to(REPO_ROOT)}: expected a JSON object"
        )
    return value


def validate_synced_tree(
    source: Path,
    target: Path,
    label: str,
    errors: list[str],
) -> None:
    source_files = {
        path.relative_to(source)
        for path in source.rglob("*")
        if path.is_file()
    }
    target_files = {
        path.relative_to(target)
        for path in target.rglob("*")
        if path.is_file()
    }
    if source_files != target_files:
        missing = sorted(str(path) for path in source_files - target_files)
        extra = sorted(str(path) for path in target_files - source_files)
        errors.append(f"{label}: file set mismatch; missing={missing}, extra={extra}")
    for relative_path in sorted(source_files & target_files):
        if (source / relative_path).read_bytes() != (
            target / relative_path
        ).read_bytes():
            errors.append(f"{label}: stale packaged file {relative_path}")


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValidationError(
            f"{path.relative_to(REPO_ROOT)}: missing opening frontmatter delimiter"
        )
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValidationError(
            f"{path.relative_to(REPO_ROOT)}: missing closing frontmatter delimiter"
        ) from exc

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.fullmatch(r"([a-z_]+):\s*(.+)", line)
        if match:
            fields[match.group(1)] = match.group(2).strip().strip("\"'")
    return fields


def validate_skills(errors: list[str]) -> None:
    skills_root = REPO_ROOT / "skills"
    actual_skills = {
        path.name for path in skills_root.iterdir() if path.is_dir()
    }
    if actual_skills != EXPECTED_SKILLS:
        errors.append(
            "skills/: expected "
            f"{sorted(EXPECTED_SKILLS)}, found {sorted(actual_skills)}"
        )

    for skill_name in sorted(actual_skills):
        skill_dir = skills_root / skill_name
        skill_file = skill_dir / "SKILL.md"
        agent_file = skill_dir / "agents" / "openai.yaml"
        if not skill_file.is_file():
            errors.append(f"skills/{skill_name}: missing SKILL.md")
            continue
        if not agent_file.is_file():
            errors.append(f"skills/{skill_name}: missing agents/openai.yaml")
            continue

        try:
            fields = parse_frontmatter(skill_file)
        except ValidationError as exc:
            errors.append(str(exc))
            continue
        if fields.get("name") != skill_name:
            errors.append(
                f"skills/{skill_name}/SKILL.md: frontmatter name must be "
                f"{skill_name!r}"
            )
        if not fields.get("description"):
            errors.append(
                f"skills/{skill_name}/SKILL.md: description must not be empty"
            )

        skill_text = skill_file.read_text(encoding="utf-8")
        for reference in REFERENCE_PATH_PATTERN.findall(skill_text):
            reference_path = skill_dir / reference.rstrip(".,:;")
            if not reference_path.exists():
                errors.append(
                    f"skills/{skill_name}/SKILL.md: missing {reference}"
                )

        agent_text = agent_file.read_text(encoding="utf-8")
        for field in ("display_name", "short_description", "default_prompt"):
            if not re.search(rf"^\s{{2}}{field}:\s*\S", agent_text, re.MULTILINE):
                errors.append(
                    f"skills/{skill_name}/agents/openai.yaml: missing {field}"
                )
        if f"${skill_name}" not in agent_text:
            errors.append(
                f"skills/{skill_name}/agents/openai.yaml: default prompt must "
                f"invoke ${skill_name}"
            )


def validate_markdown_links(errors: list[str]) -> None:
    markdown_paths = [REPO_ROOT / "README.md"]
    markdown_paths.extend((REPO_ROOT / "docs").rglob("*.md"))
    markdown_paths.extend((REPO_ROOT / "skills").rglob("*.md"))

    for path in markdown_paths:
        text = path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_PATTERN.findall(text):
            target = raw_target.strip().strip("<>")
            if (
                not target
                or target.startswith(("#", "http://", "https://", "mailto:"))
            ):
                continue
            target = unquote(target.split("#", 1)[0])
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: broken relative link "
                    f"{raw_target!r}"
                )


def validate_manifests(errors: list[str]) -> None:
    root_manifest = load_json(REPO_ROOT / "plugin.json")
    package_manifest = load_json(
        REPO_ROOT / "plugins" / "engineering-design" / "plugin.json"
    )
    codex_manifest = load_json(
        REPO_ROOT
        / "plugins"
        / "engineering-design"
        / ".codex-plugin"
        / "plugin.json"
    )
    claude_manifest = load_json(
        REPO_ROOT / ".claude-plugin" / "plugin.json"
    )
    agents_marketplace = load_json(
        REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
    )
    claude_marketplace = load_json(
        REPO_ROOT / ".claude-plugin" / "marketplace.json"
    )

    if package_manifest != codex_manifest:
        errors.append(
            "plugins/engineering-design manifests must be byte-equivalent JSON"
        )

    common_fields = (
        "name",
        "version",
        "description",
        "author",
        "repository",
        "license",
        "interface",
    )
    for field in common_fields:
        if root_manifest.get(field) != package_manifest.get(field):
            errors.append(
                f"plugin.json: {field} differs from packaged manifest"
            )

    if root_manifest.get("skills") != "./skills/":
        errors.append("plugin.json: skills must point to ./skills/")
    if package_manifest.get("skills") != "./skills/":
        errors.append(
            "plugins/engineering-design/plugin.json: skills must point to "
            "./skills/"
        )

    for label, manifest in (
        ("plugin.json", root_manifest),
        ("packaged plugin", package_manifest),
        ("Claude plugin", claude_manifest),
    ):
        if manifest.get("name") != "engineering-design":
            errors.append(f"{label}: unexpected plugin name")
        if manifest.get("version") != EXPECTED_PLUGIN_VERSION:
            errors.append(
                f"{label}: expected version {EXPECTED_PLUGIN_VERSION}"
            )
        if manifest.get("repository") != (
            "https://github.com/koizumikento/engineering-design-plugin"
        ):
            errors.append(f"{label}: unexpected repository URL")

    claude_text = json.dumps(
        {
            "manifest": claude_manifest,
            "marketplace": claude_marketplace,
        }
    ).lower()
    if "cadquery" in claude_text:
        errors.append(".claude-plugin metadata still exposes CadQuery")

    try:
        agents_entry = agents_marketplace["plugins"][0]
        source = agents_entry["source"]
        source_path = REPO_ROOT / source["path"].removeprefix("./")
    except (KeyError, IndexError, TypeError) as exc:
        errors.append(f".agents/plugins/marketplace.json: {exc}")
    else:
        if agents_entry.get("name") != "engineering-design":
            errors.append(".agents marketplace: unexpected plugin name")
        if source.get("source") != "local" or not source_path.is_dir():
            errors.append(".agents marketplace: invalid local plugin source")

    try:
        claude_entry = claude_marketplace["plugins"][0]
    except (KeyError, IndexError, TypeError) as exc:
        errors.append(f".claude-plugin/marketplace.json: {exc}")
    else:
        if claude_entry.get("name") != "engineering-design":
            errors.append(".claude-plugin marketplace: unexpected plugin name")
        if claude_entry.get("source") != "./":
            errors.append(".claude-plugin marketplace: source must be ./")

    plugin_root = REPO_ROOT / "plugins" / "engineering-design"
    skills_target = (plugin_root / package_manifest["skills"]).resolve()
    if skills_target != (plugin_root / "skills").resolve():
        errors.append("packaged plugin does not resolve to packaged skills/")

    validate_synced_tree(
        REPO_ROOT / "skills",
        plugin_root / "skills",
        "plugins/engineering-design/skills",
        errors,
    )
    validate_synced_tree(
        REPO_ROOT / "templates",
        plugin_root / "templates",
        "plugins/engineering-design/templates",
        errors,
    )
    packaged_scripts = {
        path.name
        for path in (plugin_root / "scripts").glob("*.py")
        if path.is_file()
    }
    if packaged_scripts != PACKAGED_RUNTIME_SCRIPTS:
        errors.append(
            "plugins/engineering-design/scripts: expected "
            f"{sorted(PACKAGED_RUNTIME_SCRIPTS)}, found "
            f"{sorted(packaged_scripts)}"
        )
    for name in sorted(PACKAGED_RUNTIME_SCRIPTS):
        if (REPO_ROOT / "scripts" / name).read_bytes() != (
            plugin_root / "scripts" / name
        ).read_bytes():
            errors.append(
                f"plugins/engineering-design/scripts/{name}: stale packaged file"
            )
    for name in (".python-version", "pyproject.toml", "uv.lock"):
        if (REPO_ROOT / name).read_bytes() != (plugin_root / name).read_bytes():
            errors.append(
                f"plugins/engineering-design/{name}: stale packaged file"
            )

    project = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    if project.get("version") != EXPECTED_PROJECT_VERSION:
        errors.append(
            f"pyproject.toml: expected version {EXPECTED_PROJECT_VERSION}"
        )


def validate_ci(errors: list[str]) -> None:
    workflow = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    if not workflow.is_file():
        errors.append(".github/workflows/ci.yml: missing")
        return
    text = workflow.read_text(encoding="utf-8")
    for required in (
        "pull_request:",
        "push:",
        "contents: read",
        "uv sync --frozen",
        "scripts/sync_codex_plugin_package.py",
        "git diff --exit-code",
        "scripts/validate_release.py",
        "python -m unittest discover -s tests",
    ):
        if required not in text:
            errors.append(f".github/workflows/ci.yml: missing {required!r}")
    if re.search(r"^\s+\w[\w-]*:\s*write\s*$", text, re.MULTILINE):
        errors.append(".github/workflows/ci.yml: write permission is not allowed")

    uses_lines = [
        line for line in text.splitlines() if line.lstrip().startswith("uses:")
    ]
    if len(ACTION_PATTERN.findall(text)) != len(uses_lines):
        errors.append(
            ".github/workflows/ci.yml: every action must be pinned to a "
            "full commit SHA"
        )


def main() -> int:
    errors: list[str] = []
    for validator in (
        validate_skills,
        validate_markdown_links,
        validate_manifests,
        validate_ci,
    ):
        try:
            validator(errors)
        except (
            OSError,
            KeyError,
            TypeError,
            ValidationError,
            tomllib.TOMLDecodeError,
        ) as exc:
            errors.append(f"{validator.__name__}: {exc}")

    if errors:
        print("Release validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "Release validation passed: "
        f"{len(EXPECTED_SKILLS)} skills, plugin {EXPECTED_PLUGIN_VERSION}, "
        f"project {EXPECTED_PROJECT_VERSION}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
