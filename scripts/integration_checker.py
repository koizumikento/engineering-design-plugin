#!/usr/bin/env python3
"""Screen machine-readable PCB/enclosure dimensions from an integrated Markdown spec."""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


NUMBER = r"-?\d+(?:\.\d+)?"


@dataclass
class PCBSpec:
    width: Optional[float] = None
    depth: Optional[float] = None
    thickness: Optional[float] = None
    mounting_holes: List[Tuple[float, float]] = field(default_factory=list)
    max_component_height: Optional[float] = None
    bottom_component_height: Optional[float] = None
    connectors: List[str] = field(default_factory=list)


@dataclass
class EnclosureSpec:
    internal_width: Optional[float] = None
    internal_depth: Optional[float] = None
    internal_height: Optional[float] = None
    boss_positions: List[Tuple[float, float]] = field(default_factory=list)
    boss_height: Optional[float] = None


@dataclass
class AcceptanceCriteria:
    xy_clearance: Optional[float] = None
    top_clearance: Optional[float] = None
    bottom_clearance: Optional[float] = None
    mounting_tolerance: Optional[float] = None


@dataclass
class CheckResult:
    name: str
    status: str
    message: str
    details: Dict = field(default_factory=dict)


def extract_section(content: str, title: str) -> str:
    match = re.search(
        rf"^###\s+{re.escape(title)}\s*$\n(.*?)(?=^###\s+|\Z)",
        content,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return match.group(1) if match else ""


def extract_row_value(content: str, label: str) -> Optional[str]:
    match = re.search(
        rf"^\|\s*{re.escape(label)}\s*\|\s*([^|\n]+)",
        content,
        re.MULTILINE | re.IGNORECASE,
    )
    if not match:
        return None
    value = match.group(1).strip()
    if not value or "[" in value or re.search(r"\bW\b|\bD\b|\bH\b", value):
        return None
    return value


def parse_scalar(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    match = re.search(NUMBER, value)
    return float(match.group(0)) if match else None


def parse_dimensions(value: Optional[str], count: int) -> Tuple[Optional[float], ...]:
    if not value:
        return tuple([None] * count)
    values = [float(item) for item in re.findall(NUMBER, value)]
    if len(values) < count:
        return tuple([None] * count)
    return tuple(values[:count])


def parse_points(value: Optional[str]) -> List[Tuple[float, float]]:
    if not value:
        return []
    pattern = re.compile(rf"\(\s*({NUMBER})\s*,\s*({NUMBER})\s*\)")
    return [(float(x), float(y)) for x, y in pattern.findall(value)]


def parse_max_height_table(content: str) -> Optional[float]:
    section = extract_section(content, "部品高さ")
    if not section:
        return None
    heights = [
        float(value)
        for value in re.findall(
            rf"^\|[^|]+\|\s*({NUMBER})\s*mm\s*\|",
            section,
            re.MULTILINE | re.IGNORECASE,
        )
    ]
    return max(heights) if heights else None


def parse_connectors(content: str) -> List[str]:
    connector_section = extract_section(content, "コネクタ・開口部")
    if not connector_section:
        connector_section = extract_section(content, "Connectors, controls, and openings")
    names: List[str] = []
    for line in connector_section.splitlines():
        if not line.startswith("|") or re.match(r"^\|\s*(?:---|ID\b|コネクタ\b)", line, re.IGNORECASE):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and cells[0]:
            names.append(cells[0])
    return names


def parse_spec_file(spec_path: Path) -> Tuple[PCBSpec, EnclosureSpec, AcceptanceCriteria]:
    content = spec_path.read_text(encoding="utf-8")
    pcb_section = extract_section(content, "基板仕様") or content
    enclosure_section = extract_section(content, "筐体仕様") or content
    criteria_section = extract_section(content, "Acceptance thresholds") or content

    pcb_width, pcb_depth = parse_dimensions(extract_row_value(pcb_section, "基板サイズ"), 2)
    enc_width, enc_depth, enc_height = parse_dimensions(extract_row_value(enclosure_section, "内寸"), 3)

    max_component_height = parse_scalar(extract_row_value(pcb_section, "最大部品高"))
    if max_component_height is None:
        max_component_height = parse_max_height_table(content)

    pcb = PCBSpec(
        width=pcb_width,
        depth=pcb_depth,
        thickness=parse_scalar(extract_row_value(pcb_section, "基板厚")),
        mounting_holes=parse_points(extract_row_value(pcb_section, "取付穴位置")),
        max_component_height=max_component_height,
        bottom_component_height=parse_scalar(extract_row_value(pcb_section, "下面最大部品高")),
        connectors=parse_connectors(content),
    )
    enclosure = EnclosureSpec(
        internal_width=enc_width,
        internal_depth=enc_depth,
        internal_height=enc_height,
        boss_positions=parse_points(extract_row_value(enclosure_section, "ボス位置")),
        boss_height=parse_scalar(extract_row_value(enclosure_section, "ボス高さ")),
    )
    criteria = AcceptanceCriteria(
        xy_clearance=parse_scalar(extract_row_value(criteria_section, "基板外周最小クリアランス")),
        top_clearance=parse_scalar(extract_row_value(criteria_section, "上面最小クリアランス")),
        bottom_clearance=parse_scalar(extract_row_value(criteria_section, "下面最小クリアランス")),
        mounting_tolerance=parse_scalar(extract_row_value(criteria_section, "取付位置許容差")),
    )
    return pcb, enclosure, criteria


def check_required_inputs(pcb: PCBSpec, enclosure: EnclosureSpec) -> CheckResult:
    critical = {
        "基板幅": pcb.width,
        "基板奥行": pcb.depth,
        "筐体内幅": enclosure.internal_width,
        "筐体内奥行": enclosure.internal_depth,
        "筐体内高": enclosure.internal_height,
    }
    supporting = {
        "基板厚": pcb.thickness,
        "ボス高さ": enclosure.boss_height,
        "最大部品高": pcb.max_component_height,
    }
    missing_critical = [name for name, value in critical.items() if value is None]
    missing_supporting = [name for name, value in supporting.items() if value is None]
    if missing_critical:
        return CheckResult(
            "入力完全性",
            "ERROR",
            "必須寸法が不足しているため完全な適合判定はできません",
            {"missing_critical": missing_critical, "missing_supporting": missing_supporting},
        )
    if missing_supporting:
        return CheckResult(
            "入力完全性",
            "CONDITIONAL",
            "外形は評価できますが、高さまたは取付の評価データが不足しています",
            {"missing_supporting": missing_supporting},
        )
    return CheckResult("入力完全性", "PASS", "主要な数値入力を取得しました")


def check_pcb_clearance(
    pcb: PCBSpec, enclosure: EnclosureSpec, required: Optional[float]
) -> CheckResult:
    if None in (pcb.width, pcb.depth, enclosure.internal_width, enclosure.internal_depth):
        return CheckResult("基板外周クリアランス", "NOT_EVALUATED", "外形寸法が不足しています")

    width_gap = (enclosure.internal_width - pcb.width) / 2
    depth_gap = (enclosure.internal_depth - pcb.depth) / 2
    minimum_gap = min(width_gap, depth_gap)
    details = {"width_gap_mm": width_gap, "depth_gap_mm": depth_gap, "required_mm": required}

    if minimum_gap < 0:
        return CheckResult("基板外周クリアランス", "FAIL", "公称外形で基板が筐体に収まりません", details)
    if required is None:
        return CheckResult(
            "基板外周クリアランス",
            "CONDITIONAL",
            "公称外形では収まりますが、必要最小クリアランスが未定義です",
            details,
        )
    if minimum_gap < required:
        return CheckResult("基板外周クリアランス", "FAIL", "必要最小クリアランスを満たしません", details)
    return CheckResult("基板外周クリアランス", "PASS", "公称外形で必要最小クリアランスを満たします", details)


def check_height_clearance(
    pcb: PCBSpec, enclosure: EnclosureSpec, required: Optional[float]
) -> CheckResult:
    values = (pcb.thickness, pcb.max_component_height, enclosure.boss_height, enclosure.internal_height)
    if any(value is None for value in values):
        return CheckResult(
            "上面クリアランス",
            "NOT_EVALUATED",
            "基板厚、最大部品高、ボス高、または筐体内高が不足しています",
        )

    gap = enclosure.internal_height - (
        enclosure.boss_height + pcb.thickness + pcb.max_component_height
    )
    details = {
        "top_gap_mm": gap,
        "required_mm": required,
        "boss_height_mm": enclosure.boss_height,
        "pcb_thickness_mm": pcb.thickness,
        "max_component_height_mm": pcb.max_component_height,
    }
    if gap < 0:
        return CheckResult("上面クリアランス", "FAIL", "公称寸法で上面部品が筐体と干渉します", details)
    if required is None:
        return CheckResult(
            "上面クリアランス",
            "CONDITIONAL",
            "公称寸法では干渉しませんが、必要最小クリアランスが未定義です",
            details,
        )
    if gap < required:
        return CheckResult("上面クリアランス", "FAIL", "必要最小上面クリアランスを満たしません", details)
    return CheckResult("上面クリアランス", "PASS", "公称寸法で必要最小上面クリアランスを満たします", details)


def check_mounting_holes(
    pcb: PCBSpec, enclosure: EnclosureSpec, tolerance: Optional[float]
) -> CheckResult:
    if not pcb.mounting_holes or not enclosure.boss_positions:
        return CheckResult(
            "取付位置",
            "NOT_EVALUATED",
            "基板取付穴または筐体ボスの座標が不足しています",
            {"pcb_holes": pcb.mounting_holes, "bosses": enclosure.boss_positions},
        )
    if len(pcb.mounting_holes) != len(enclosure.boss_positions):
        return CheckResult(
            "取付位置",
            "FAIL",
            "基板取付穴と筐体ボスの個数が一致しません",
            {"pcb_hole_count": len(pcb.mounting_holes), "boss_count": len(enclosure.boss_positions)},
        )

    unmatched = list(enclosure.boss_positions)
    offsets: List[float] = []
    for hole in pcb.mounting_holes:
        nearest = min(unmatched, key=lambda boss: ((hole[0] - boss[0]) ** 2 + (hole[1] - boss[1]) ** 2) ** 0.5)
        offset = ((hole[0] - nearest[0]) ** 2 + (hole[1] - nearest[1]) ** 2) ** 0.5
        offsets.append(offset)
        unmatched.remove(nearest)

    max_offset = max(offsets)
    details = {"offsets_mm": offsets, "max_offset_mm": max_offset, "tolerance_mm": tolerance}
    if tolerance is None:
        return CheckResult(
            "取付位置",
            "CONDITIONAL",
            "最近傍の公称位置差を算出しましたが、許容差が未定義です",
            details,
        )
    if max_offset > tolerance:
        return CheckResult("取付位置", "FAIL", "公称位置差が取付位置許容差を超えます", details)
    details["assumption"] = "both coordinate lists are already transformed into the same frame"
    return CheckResult(
        "取付位置",
        "CONDITIONAL",
        "同一座標frameへ変換済みと仮定すれば、公称位置差は許容差以内です",
        details,
    )


def check_connector_scope(pcb: PCBSpec) -> CheckResult:
    return CheckResult(
        "コネクタ・開口・挿抜",
        "NOT_EVALUATED",
        "このtext checkerは3D開口、plug、latch、工具、ケーブルのエンベロープを評価しません",
        {"declared_rows": pcb.connectors},
    )


def overall_status(results: List[CheckResult]) -> str:
    statuses = {result.status for result in results}
    if "ERROR" in statuses or "FAIL" in statuses:
        return "FAIL"
    if statuses & {"CONDITIONAL", "NOT_EVALUATED"}:
        return "CONDITIONAL"
    return "PASS"


def generate_report(
    spec_path: Path,
    pcb: PCBSpec,
    enclosure: EnclosureSpec,
    criteria: AcceptanceCriteria,
    results: List[CheckResult],
    output_path: Path,
) -> str:
    lines = [
        "# 統合設計スクリーニングレポート",
        "",
        f"- 仕様書: `{spec_path}`",
        "- 範囲: Markdownから抽出した公称寸法のscreening。3D干渉、最悪公差、熱、EMC、IP試験は含まない。",
        f"- 総合判定: **{overall_status(results)}**",
        "",
        "## Parsed inputs",
        "",
        "```json",
        json.dumps(
            {"pcb": asdict(pcb), "enclosure": asdict(enclosure), "criteria": asdict(criteria)},
            indent=2,
            ensure_ascii=False,
        ),
        "```",
        "",
        "## Checks",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"### {result.status}: {result.name}",
                "",
                result.message,
                "",
                "```json",
                json.dumps(result.details, indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return str(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="統合仕様書の公称寸法をscreeningする")
    parser.add_argument("spec", type=Path, help="統合仕様書（.md）")
    parser.add_argument("-o", "--output", type=Path, default=Path("outputs"))
    parser.add_argument("--name", type=str, default=None)
    parser.add_argument(
        "--clearance",
        type=float,
        default=None,
        help="基板外周の必要最小clearance [mm]。未指定時は仕様書の値を使用",
    )
    parser.add_argument(
        "--z-clearance",
        type=float,
        default=None,
        help="上面の必要最小clearance [mm]。未指定時は仕様書の値を使用",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=None,
        help="取付位置許容差 [mm]。未指定時は仕様書の値を使用",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-fail", action="store_true", help="FAIL判定時に終了コード2を返す")
    args = parser.parse_args()

    if not args.spec.exists():
        print(f"Error: Spec file not found: {args.spec}", file=sys.stderr)
        sys.exit(1)

    args.output.mkdir(parents=True, exist_ok=True)
    base_name = args.name or args.spec.stem.replace("-spec", "")

    try:
        pcb, enclosure, criteria = parse_spec_file(args.spec)
        if args.clearance is not None:
            criteria.xy_clearance = args.clearance
        if args.z_clearance is not None:
            criteria.top_clearance = args.z_clearance
        if args.tolerance is not None:
            criteria.mounting_tolerance = args.tolerance

        results = [
            check_required_inputs(pcb, enclosure),
            check_pcb_clearance(pcb, enclosure, criteria.xy_clearance),
            check_height_clearance(pcb, enclosure, criteria.top_clearance),
            check_mounting_holes(pcb, enclosure, criteria.mounting_tolerance),
            check_connector_scope(pcb),
        ]
        status = overall_status(results)
        report_path = args.output / f"{base_name}-integration-report.md"
        generate_report(args.spec, pcb, enclosure, criteria, results, report_path)

        result_data = {
            "spec": str(args.spec),
            "output_dir": str(args.output),
            "parsed": {
                "pcb": asdict(pcb),
                "enclosure": asdict(enclosure),
                "criteria": asdict(criteria),
            },
            "checks": [asdict(result) for result in results],
            "overall_status": status,
            "exported_files": [str(report_path)],
            "errors": [],
        }

        for result in results:
            print(f"[{result.status}] {result.name}: {result.message}")
        print(f"Report: {report_path}")
        print(f"Overall: {status}")
        if args.json:
            print(json.dumps(result_data, indent=2, ensure_ascii=False))
        if args.fail_on_fail and status == "FAIL":
            sys.exit(2)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if args.json:
            print(json.dumps({"errors": [str(exc)]}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
