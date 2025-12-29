#!/usr/bin/env python3
"""
SKiDL Runner - SKiDLスクリプトを実行し、ネットリストとBOMを出力

使用方法:
    python3 skidl_runner.py input.py -o outputs/
    python3 skidl_runner.py input.py -o outputs/ --bom
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Optional
import csv


def load_script(script_path: Path) -> None:
    """SKiDLスクリプトを実行"""
    spec = importlib.util.spec_from_file_location("skidl_script", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script: {script_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["skidl_script"] = module

    # スクリプト実行
    spec.loader.exec_module(module)


def run_erc() -> dict:
    """ERCを実行して結果を取得"""
    from skidl import ERC, erc_logger
    import io
    from contextlib import redirect_stderr

    result = {
        "passed": True,
        "warnings": [],
        "errors": []
    }

    # ERCの出力をキャプチャ
    stderr_capture = io.StringIO()
    try:
        with redirect_stderr(stderr_capture):
            ERC()
        result["passed"] = True
    except Exception as e:
        result["passed"] = False
        result["errors"].append(str(e))

    # 警告/エラーを解析
    erc_output = stderr_capture.getvalue()
    for line in erc_output.split('\n'):
        line = line.strip()
        if not line:
            continue
        if 'WARNING' in line.upper():
            result["warnings"].append(line)
        elif 'ERROR' in line.upper():
            result["errors"].append(line)
            result["passed"] = False

    return result


def generate_netlist(output_path: Path, format: str = "kicad") -> str:
    """ネットリストを生成"""
    from skidl import generate_netlist as skidl_generate_netlist, KICAD

    netlist_path = str(output_path)

    if format == "kicad":
        skidl_generate_netlist(file_=netlist_path)
    else:
        skidl_generate_netlist(file_=netlist_path)

    return netlist_path


def generate_bom(output_path: Path) -> str:
    """BOM（部品表）を生成"""
    from skidl import default_circuit

    circuit = default_circuit

    # 部品情報を収集
    parts_dict = {}
    for part in circuit.parts:
        # キー: 部品タイプ + 値
        key = (part.name, part.value, getattr(part, 'footprint', ''))

        if key not in parts_dict:
            parts_dict[key] = {
                "name": part.name,
                "value": part.value,
                "footprint": getattr(part, 'footprint', ''),
                "quantity": 0,
                "references": []
            }

        parts_dict[key]["quantity"] += 1
        parts_dict[key]["references"].append(part.ref)

    # CSV出力
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Reference', 'Name', 'Value', 'Footprint', 'Quantity'])

        for part_info in sorted(parts_dict.values(), key=lambda x: x["references"][0]):
            refs = ', '.join(sorted(part_info["references"]))
            writer.writerow([
                refs,
                part_info["name"],
                part_info["value"],
                part_info["footprint"],
                part_info["quantity"]
            ])

    return str(output_path)


def get_circuit_info() -> dict:
    """回路情報を取得"""
    from skidl import default_circuit

    circuit = default_circuit

    info = {
        "name": circuit.name,
        "parts_count": len(circuit.parts),
        "nets_count": len(circuit.nets),
        "parts": [],
        "nets": []
    }

    # 部品一覧
    for part in circuit.parts:
        info["parts"].append({
            "ref": part.ref,
            "name": part.name,
            "value": part.value,
            "footprint": getattr(part, 'footprint', ''),
            "pins_count": len(part.pins)
        })

    # ネット一覧
    for net in circuit.nets:
        if net.name and not net.name.startswith('N$'):  # 自動命名以外
            info["nets"].append({
                "name": net.name,
                "pins_count": len(net.pins)
            })

    return info


def main():
    parser = argparse.ArgumentParser(
        description='SKiDLスクリプトを実行し、ネットリストとBOMを出力'
    )
    parser.add_argument('script', type=Path, help='入力スクリプト（.py）')
    parser.add_argument('-o', '--output', type=Path, default=Path('outputs'),
                        help='出力ディレクトリ（デフォルト: outputs/）')
    parser.add_argument('--name', type=str, default=None,
                        help='出力ファイル名（デフォルト: スクリプト名）')
    parser.add_argument('--bom', action='store_true',
                        help='BOM（部品表）を生成')
    parser.add_argument('--no-erc', action='store_true',
                        help='ERCをスキップ')
    parser.add_argument('--json', action='store_true',
                        help='結果をJSON形式で出力')

    args = parser.parse_args()

    # スクリプトパス確認
    if not args.script.exists():
        print(f"Error: Script not found: {args.script}", file=sys.stderr)
        sys.exit(1)

    # 基本名
    base_name = args.name or args.script.stem

    # 出力ディレクトリ作成
    args.output.mkdir(parents=True, exist_ok=True)

    result_data = {
        "script": str(args.script),
        "output_dir": str(args.output),
        "erc": {},
        "circuit_info": {},
        "exported_files": [],
        "errors": []
    }

    try:
        # SKiDLインポート確認
        try:
            from skidl import set_default_tool, KICAD
            set_default_tool(KICAD)
        except ImportError:
            print("Error: SKiDL is not installed. Run: pip install skidl", file=sys.stderr)
            sys.exit(1)

        # スクリプト実行
        print(f"Loading script: {args.script}")
        load_script(args.script)

        # 回路情報取得
        circuit_info = get_circuit_info()
        result_data["circuit_info"] = circuit_info
        print(f"Circuit: {circuit_info['name']}")
        print(f"  Parts: {circuit_info['parts_count']}")
        print(f"  Nets: {circuit_info['nets_count']}")

        # ERC実行
        if not args.no_erc:
            print("Running ERC...")
            erc_result = run_erc()
            result_data["erc"] = erc_result

            if erc_result["passed"]:
                print("  ERC: PASSED")
            else:
                print("  ERC: FAILED")
                for error in erc_result["errors"]:
                    print(f"    ERROR: {error}")

            for warning in erc_result["warnings"]:
                print(f"    WARNING: {warning}")

        # ネットリスト生成
        print(f"Generating netlist...")
        netlist_path = args.output / f"{base_name}.net"
        generate_netlist(netlist_path)
        result_data["exported_files"].append(str(netlist_path))
        print(f"  Created: {netlist_path}")

        # BOM生成
        if args.bom:
            print("Generating BOM...")
            bom_path = args.output / f"{base_name}-bom.csv"
            generate_bom(bom_path)
            result_data["exported_files"].append(str(bom_path))
            print(f"  Created: {bom_path}")

        # 成功
        print("\nDone!")

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
