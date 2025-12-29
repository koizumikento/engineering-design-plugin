#!/usr/bin/env python3
"""
Integration Checker - 基板-筐体の整合性チェック

使用方法:
    python3 integration_checker.py specs/integrated-spec.md -o outputs/
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PCBSpec:
    """基板仕様"""
    width: float = 0.0
    depth: float = 0.0
    thickness: float = 1.6
    mounting_holes: List[Tuple[float, float]] = None
    max_component_height: float = 0.0
    connectors: List[Dict] = None

    def __post_init__(self):
        if self.mounting_holes is None:
            self.mounting_holes = []
        if self.connectors is None:
            self.connectors = []


@dataclass
class EnclosureSpec:
    """筐体仕様"""
    internal_width: float = 0.0
    internal_depth: float = 0.0
    internal_height: float = 0.0
    wall_thickness: float = 2.0
    boss_positions: List[Tuple[float, float]] = None
    boss_height: float = 0.0
    openings: List[Dict] = None

    def __post_init__(self):
        if self.boss_positions is None:
            self.boss_positions = []
        if self.openings is None:
            self.openings = []


@dataclass
class CheckResult:
    """チェック結果"""
    name: str
    status: str  # "OK", "WARNING", "ERROR"
    message: str
    details: Dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


def parse_spec_file(spec_path: Path) -> Tuple[PCBSpec, EnclosureSpec]:
    """仕様書ファイルをパース"""
    content = spec_path.read_text(encoding='utf-8')

    pcb = PCBSpec()
    enclosure = EnclosureSpec()

    # 基板サイズ
    pcb_size_match = re.search(r'基板.*?(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)', content, re.IGNORECASE)
    if pcb_size_match:
        pcb.width = float(pcb_size_match.group(1))
        pcb.depth = float(pcb_size_match.group(2))

    # 基板厚
    pcb_thickness_match = re.search(r'基板厚.*?(\d+(?:\.\d+)?)\s*mm', content, re.IGNORECASE)
    if pcb_thickness_match:
        pcb.thickness = float(pcb_thickness_match.group(1))

    # 筐体内寸
    enc_size_match = re.search(r'内寸.*?(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)', content, re.IGNORECASE)
    if enc_size_match:
        enclosure.internal_width = float(enc_size_match.group(1))
        enclosure.internal_depth = float(enc_size_match.group(2))
        enclosure.internal_height = float(enc_size_match.group(3))

    # ボス高さ
    boss_height_match = re.search(r'ボス.*?高.*?(\d+(?:\.\d+)?)\s*mm', content, re.IGNORECASE)
    if boss_height_match:
        enclosure.boss_height = float(boss_height_match.group(1))

    # 最大部品高さ
    component_height_match = re.search(r'(?:最大)?部品高.*?(\d+(?:\.\d+)?)\s*mm', content, re.IGNORECASE)
    if component_height_match:
        pcb.max_component_height = float(component_height_match.group(1))

    # 取付穴位置（テーブル形式をパース）
    hole_pattern = re.compile(r'\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\)')
    holes_section = re.search(r'取付穴.*?位置[：:]?\s*(.*?)(?:\n\n|\Z)', content, re.DOTALL | re.IGNORECASE)
    if holes_section:
        for match in hole_pattern.finditer(holes_section.group(1)):
            pcb.mounting_holes.append((float(match.group(1)), float(match.group(2))))

    # コネクタ情報
    connector_pattern = re.compile(r'(USB-?[AC]|DC|RJ45|φ\d+(?:\.\d+)?)', re.IGNORECASE)
    for match in connector_pattern.finditer(content):
        pcb.connectors.append({"type": match.group(1)})

    return pcb, enclosure


def check_pcb_clearance(pcb: PCBSpec, enclosure: EnclosureSpec,
                        min_clearance: float = 2.0) -> CheckResult:
    """基板クリアランスチェック"""
    width_clearance = (enclosure.internal_width - pcb.width) / 2
    depth_clearance = (enclosure.internal_depth - pcb.depth) / 2

    if width_clearance < 0 or depth_clearance < 0:
        return CheckResult(
            name="基板クリアランス",
            status="ERROR",
            message=f"基板が筐体に収まりません",
            details={
                "pcb_size": f"{pcb.width} x {pcb.depth} mm",
                "internal_size": f"{enclosure.internal_width} x {enclosure.internal_depth} mm",
                "width_clearance": width_clearance,
                "depth_clearance": depth_clearance
            }
        )

    if width_clearance < min_clearance or depth_clearance < min_clearance:
        return CheckResult(
            name="基板クリアランス",
            status="WARNING",
            message=f"クリアランスが推奨値({min_clearance}mm)未満です",
            details={
                "width_clearance": width_clearance,
                "depth_clearance": depth_clearance,
                "min_recommended": min_clearance
            }
        )

    return CheckResult(
        name="基板クリアランス",
        status="OK",
        message=f"クリアランス: 幅{width_clearance:.1f}mm, 奥行{depth_clearance:.1f}mm",
        details={
            "width_clearance": width_clearance,
            "depth_clearance": depth_clearance
        }
    )


def check_height_clearance(pcb: PCBSpec, enclosure: EnclosureSpec,
                           min_clearance: float = 2.0) -> CheckResult:
    """高さクリアランスチェック"""
    required_height = enclosure.boss_height + pcb.thickness + pcb.max_component_height + min_clearance
    available_height = enclosure.internal_height

    clearance = available_height - (enclosure.boss_height + pcb.thickness + pcb.max_component_height)

    if clearance < 0:
        return CheckResult(
            name="高さクリアランス",
            status="ERROR",
            message=f"部品が筐体に干渉します",
            details={
                "required_height": required_height,
                "available_height": available_height,
                "clearance": clearance,
                "boss_height": enclosure.boss_height,
                "pcb_thickness": pcb.thickness,
                "max_component_height": pcb.max_component_height
            }
        )

    if clearance < min_clearance:
        return CheckResult(
            name="高さクリアランス",
            status="WARNING",
            message=f"高さクリアランスが推奨値({min_clearance}mm)未満です",
            details={
                "clearance": clearance,
                "min_recommended": min_clearance
            }
        )

    return CheckResult(
        name="高さクリアランス",
        status="OK",
        message=f"高さクリアランス: {clearance:.1f}mm",
        details={
            "clearance": clearance,
            "breakdown": {
                "boss_height": enclosure.boss_height,
                "pcb_thickness": pcb.thickness,
                "max_component_height": pcb.max_component_height,
                "internal_height": available_height
            }
        }
    )


def check_mounting_holes(pcb: PCBSpec, enclosure: EnclosureSpec,
                        tolerance: float = 0.5) -> CheckResult:
    """取付穴位置チェック"""
    if not pcb.mounting_holes:
        return CheckResult(
            name="取付穴",
            status="WARNING",
            message="基板の取付穴位置が指定されていません",
            details={}
        )

    if not enclosure.boss_positions:
        return CheckResult(
            name="取付穴",
            status="WARNING",
            message="筐体のボス位置が指定されていません",
            details={}
        )

    # 位置の照合
    mismatched = []
    for i, pcb_hole in enumerate(pcb.mounting_holes):
        matched = False
        for boss in enclosure.boss_positions:
            distance = ((pcb_hole[0] - boss[0])**2 + (pcb_hole[1] - boss[1])**2)**0.5
            if distance <= tolerance:
                matched = True
                break
        if not matched:
            mismatched.append(pcb_hole)

    if mismatched:
        return CheckResult(
            name="取付穴",
            status="ERROR",
            message=f"{len(mismatched)}箇所の取付穴が一致しません",
            details={
                "mismatched_holes": mismatched,
                "tolerance": tolerance
            }
        )

    return CheckResult(
        name="取付穴",
        status="OK",
        message=f"全{len(pcb.mounting_holes)}箇所の取付穴が一致",
        details={
            "hole_count": len(pcb.mounting_holes),
            "tolerance": tolerance
        }
    )


def generate_report(spec_path: Path, pcb: PCBSpec, enclosure: EnclosureSpec,
                   results: List[CheckResult], output_path: Path) -> str:
    """レポートを生成"""
    report_lines = [
        "# 統合設計 整合性チェックレポート",
        "",
        f"**仕様書**: {spec_path.name}",
        f"**生成日時**: {__import__('datetime').datetime.now().isoformat()}",
        "",
        "---",
        "",
        "## 仕様サマリー",
        "",
        "### 基板仕様",
        f"- 外形: {pcb.width} x {pcb.depth} mm",
        f"- 厚さ: {pcb.thickness} mm",
        f"- 最大部品高: {pcb.max_component_height} mm",
        f"- 取付穴: {len(pcb.mounting_holes)}箇所",
        "",
        "### 筐体仕様",
        f"- 内寸: {enclosure.internal_width} x {enclosure.internal_depth} x {enclosure.internal_height} mm",
        f"- 肉厚: {enclosure.wall_thickness} mm",
        f"- ボス高さ: {enclosure.boss_height} mm",
        "",
        "---",
        "",
        "## チェック結果",
        "",
    ]

    # 結果サマリー
    ok_count = sum(1 for r in results if r.status == "OK")
    warning_count = sum(1 for r in results if r.status == "WARNING")
    error_count = sum(1 for r in results if r.status == "ERROR")

    if error_count > 0:
        overall = "**不合格**"
    elif warning_count > 0:
        overall = "**条件付き合格（要確認）**"
    else:
        overall = "**合格**"

    report_lines.extend([
        f"### 総合判定: {overall}",
        "",
        f"- OK: {ok_count}",
        f"- WARNING: {warning_count}",
        f"- ERROR: {error_count}",
        "",
    ])

    # 詳細結果
    report_lines.append("### 詳細")
    report_lines.append("")

    status_emoji = {"OK": "[OK]", "WARNING": "[WARN]", "ERROR": "[NG]"}

    for result in results:
        emoji = status_emoji.get(result.status, "")
        report_lines.append(f"#### {emoji} {result.name}")
        report_lines.append("")
        report_lines.append(f"**結果**: {result.status}")
        report_lines.append(f"**メッセージ**: {result.message}")
        report_lines.append("")

        if result.details:
            report_lines.append("**詳細**:")
            for key, value in result.details.items():
                report_lines.append(f"- {key}: {value}")
            report_lines.append("")

    report_content = "\n".join(report_lines)

    # ファイル出力
    output_path.write_text(report_content, encoding='utf-8')

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='基板-筐体の整合性チェック'
    )
    parser.add_argument('spec', type=Path, help='統合仕様書（.md）')
    parser.add_argument('-o', '--output', type=Path, default=Path('outputs'),
                        help='出力ディレクトリ（デフォルト: outputs/）')
    parser.add_argument('--name', type=str, default=None,
                        help='出力ファイル名（デフォルト: スペック名）')
    parser.add_argument('--clearance', type=float, default=2.0,
                        help='推奨クリアランス（デフォルト: 2.0mm）')
    parser.add_argument('--tolerance', type=float, default=0.5,
                        help='位置公差（デフォルト: 0.5mm）')
    parser.add_argument('--json', action='store_true',
                        help='結果をJSON形式で出力')

    args = parser.parse_args()

    # 仕様書確認
    if not args.spec.exists():
        print(f"Error: Spec file not found: {args.spec}", file=sys.stderr)
        sys.exit(1)

    # 基本名
    base_name = args.name or args.spec.stem.replace('-spec', '')

    # 出力ディレクトリ作成
    args.output.mkdir(parents=True, exist_ok=True)

    result_data = {
        "spec": str(args.spec),
        "output_dir": str(args.output),
        "checks": [],
        "overall_status": "OK",
        "exported_files": [],
        "errors": []
    }

    try:
        # 仕様書パース
        print(f"Parsing spec: {args.spec}")
        pcb, enclosure = parse_spec_file(args.spec)

        print(f"PCB: {pcb.width} x {pcb.depth} mm")
        print(f"Enclosure internal: {enclosure.internal_width} x {enclosure.internal_depth} x {enclosure.internal_height} mm")

        # チェック実行
        print("\nRunning checks...")
        results = []

        # 基板クリアランス
        results.append(check_pcb_clearance(pcb, enclosure, args.clearance))

        # 高さクリアランス
        results.append(check_height_clearance(pcb, enclosure, args.clearance))

        # 取付穴
        results.append(check_mounting_holes(pcb, enclosure, args.tolerance))

        # 結果表示
        for result in results:
            status_str = f"[{result.status}]"
            print(f"  {status_str:8} {result.name}: {result.message}")
            result_data["checks"].append({
                "name": result.name,
                "status": result.status,
                "message": result.message,
                "details": result.details
            })

        # 総合判定
        if any(r.status == "ERROR" for r in results):
            result_data["overall_status"] = "ERROR"
        elif any(r.status == "WARNING" for r in results):
            result_data["overall_status"] = "WARNING"

        # レポート生成
        print("\nGenerating report...")
        report_path = args.output / f"{base_name}-integration-report.md"
        generate_report(args.spec, pcb, enclosure, results, report_path)
        result_data["exported_files"].append(str(report_path))
        print(f"  Created: {report_path}")

        print(f"\nOverall: {result_data['overall_status']}")

    except Exception as e:
        result_data["errors"].append(str(e))
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # JSON出力
    if args.json:
        print(json.dumps(result_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
