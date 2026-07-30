#!/usr/bin/env python3
"""Helpers for circuit-design artifact summaries."""

from __future__ import annotations

from pathlib import Path


ARTIFACT_SUFFIXES = (
    "-erc-summary.md",
    "-bom.csv",
    ".net",
)


def reports_dir(output_root: Path) -> Path:
    return output_root / "reports"


def kicad_project_dir(output_root: Path, base_name: str) -> Path:
    return output_root / "kicad" / base_name


def ensure_standard_output_dirs(output_root: Path, base_name: str) -> tuple[Path, Path]:
    reports = reports_dir(output_root)
    kicad = kicad_project_dir(output_root, base_name)
    reports.mkdir(parents=True, exist_ok=True)
    kicad.mkdir(parents=True, exist_ok=True)
    return reports, kicad


def find_related_spec(script_path: Path) -> Path | None:
    candidate_dirs = [
        script_path.parent.parent / "specs",
        script_path.parent / "specs",
    ]

    project_name = script_path.stem.replace("_", "-")
    candidate_names = [
        f"{project_name}-spec.md",
        f"{project_name}.md",
    ]

    for directory in candidate_dirs:
        if not directory.exists():
            continue
        for name in candidate_names:
            candidate = directory / name
            if candidate.exists():
                return candidate

        matches = sorted(directory.glob("*-spec.md"))
        if len(matches) == 1:
            return matches[0]

    return None


def write_erc_summary(output_path: Path, erc_result: dict) -> str:
    status = "PASSED" if erc_result.get("passed") else "FAILED"
    warnings = erc_result.get("warnings", [])
    errors = erc_result.get("errors", [])

    lines = [
        "# ERC Summary",
        "",
        f"- Status: `{status}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Errors: `{len(errors)}`",
        "",
    ]

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    if errors:
        lines.append("## Errors")
        lines.append("")
        for error in errors:
            lines.append(f"- {error}")
        lines.append("")

    if not warnings and not errors:
        lines.append("No ERC warnings or errors.")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return str(output_path)


def read_erc_summary(summary_path: Path) -> dict:
    result = {
        "passed": None,
        "warnings": [],
        "errors": [],
    }

    if not summary_path.exists():
        return result

    section = None
    for raw_line in summary_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- Status:"):
            result["passed"] = "`PASSED`" in line
        elif line == "## Warnings":
            section = "warnings"
        elif line == "## Errors":
            section = "errors"
        elif line.startswith("## "):
            section = None
        elif line.startswith("- ") and section in {"warnings", "errors"}:
            result[section].append(line[2:])

    return result


def collect_artifact_paths(output_root: Path, base_name: str) -> list[str]:
    summary_name = f"{base_name}-design-summary.md"
    ordered: list[str] = []

    report_dir = reports_dir(output_root)
    for suffix in ARTIFACT_SUFFIXES:
        candidate = report_dir / f"{base_name}{suffix}"
        if candidate.exists() and candidate.name != summary_name:
            ordered.append(str(candidate))

    project_dir = kicad_project_dir(output_root, base_name)
    for suffix in (".kicad_sch", ".kicad_pro"):
        candidate = project_dir / f"{base_name}{suffix}"
        if candidate.exists():
            ordered.append(str(candidate))

    sim_dir = output_root / "sim"
    for extra in sorted(sim_dir.glob(f"{base_name}-sim.*")):
        if extra.name != summary_name and str(extra) not in ordered:
            ordered.append(str(extra))

    return ordered


def write_design_summary(
    output_path: Path,
    script_path: Path,
    circuit_info: dict,
    erc_result: dict,
    exported_files: list[str],
) -> str:
    related_spec = find_related_spec(script_path)
    erc_state = erc_result.get("passed")
    if erc_state is True:
        erc_status = "PASSED"
    elif erc_state is False:
        erc_status = "FAILED"
    else:
        erc_status = "SKIPPED"

    lines = [
        "# Design Summary",
        "",
        f"- Project: `{circuit_info['name']}`",
        f"- Source script: `{script_path}`",
        f"- Parts: `{circuit_info['parts_count']}`",
        f"- Nets: `{circuit_info['nets_count']}`",
        f"- ERC status: `{erc_status}`",
    ]

    if related_spec:
        lines.append(f"- Related spec: `{related_spec}`")

    lines.extend([
        "",
        "## Artifacts",
        "",
    ])

    for file_path in exported_files:
        lines.append(f"- `{file_path}`")

    lines.extend([
        "",
        "## Notes",
        "",
        "- Standard circuit outputs are the BOM, ERC summary, design summary, and KiCad-native schematic/project files.",
        "- Netlist should be generated only when explicitly needed.",
        "",
    ])

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return str(output_path)
