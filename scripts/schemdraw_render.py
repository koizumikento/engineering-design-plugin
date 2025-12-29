#!/usr/bin/env python3
"""
Schemdraw Renderer - SKiDL回路から回路図を生成

使用方法:
    python3 schemdraw_render.py input.py -o outputs/
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def load_skidl_circuit(script_path: Path):
    """SKiDLスクリプトを読み込み回路情報を取得"""
    spec = importlib.util.spec_from_file_location("skidl_script", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script: {script_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["skidl_script"] = module

    # スクリプト実行
    spec.loader.exec_module(module)

    # SKiDLのデフォルト回路を取得
    from skidl import default_circuit
    return default_circuit


def analyze_circuit(circuit) -> Dict:
    """回路構造を解析"""
    info = {
        "parts": [],
        "nets": [],
        "connections": []
    }

    # 部品情報
    for part in circuit.parts:
        part_info = {
            "ref": part.ref,
            "name": part.name,
            "value": part.value,
            "pins": []
        }
        for pin in part.pins:
            pin_info = {
                "num": pin.num,
                "name": pin.name,
                "net": pin.net.name if pin.net else None
            }
            part_info["pins"].append(pin_info)
        info["parts"].append(part_info)

    # ネット情報
    for net in circuit.nets:
        net_info = {
            "name": net.name,
            "pins": []
        }
        for pin in net.pins:
            net_info["pins"].append({
                "part_ref": pin.part.ref,
                "pin_num": pin.num
            })
        info["nets"].append(net_info)

    return info


def create_schematic(circuit_info: Dict, output_path: Path, format: str = "svg") -> str:
    """schemdrawを使用して回路図を生成"""
    import schemdraw
    import schemdraw.elements as elm

    d = schemdraw.Drawing()

    # 部品タイプに応じた要素マッピング
    element_map = {
        'R': elm.Resistor,
        'C': elm.Capacitor,
        'L': elm.Inductor,
        'D': elm.Diode,
        'LED': elm.LED,
        'Q_NPN': lambda: elm.BjtNpn(circle=True),
        'Q_PNP': lambda: elm.BjtPnp(circle=True),
        'Q_NMOS': elm.NFet,
        'Q_PMOS': elm.PFet,
    }

    # 部品位置の追跡
    part_elements = {}
    x_pos = 0
    y_pos = 0

    # 特殊ネット（電源、GND）の識別
    power_nets = set()
    gnd_nets = set()

    for net in circuit_info["nets"]:
        name = net["name"].upper()
        if name in ['VCC', 'VDD', 'V+', 'VIN', '5V', '3V3', '12V']:
            power_nets.add(net["name"])
        elif name in ['GND', 'VSS', 'V-', '0']:
            gnd_nets.add(net["name"])

    # 簡易レイアウト：水平に部品を配置
    for i, part in enumerate(circuit_info["parts"]):
        ref = part["ref"]
        name = part["name"]
        value = part["value"]

        # 要素を選択
        elem_class = None
        for key, cls in element_map.items():
            if key in name.upper():
                elem_class = cls
                break

        if elem_class is None:
            # デフォルト：抵抗として表示
            elem_class = elm.Resistor

        # 要素を配置
        if callable(elem_class) and not isinstance(elem_class, type):
            elem = elem_class()
        else:
            elem = elem_class()

        # ラベル設定
        label = f"{ref}\n{value}" if value else ref
        elem.label(label)

        # 位置設定（簡易グリッド配置）
        elem.at((x_pos, y_pos))

        d.add(elem)
        part_elements[ref] = {
            "element": elem,
            "pos": (x_pos, y_pos)
        }

        # 次の位置
        x_pos += 3
        if (i + 1) % 4 == 0:
            x_pos = 0
            y_pos -= 3

    # 電源とGNDシンボルを追加
    d.add(elm.Vdd().at((0, 2)).label('VCC'))
    d.add(elm.Ground().at((0, y_pos - 2)))

    # 保存
    output_file = str(output_path)
    if format == "svg":
        d.save(output_file)
    elif format == "png":
        d.save(output_file)
    else:
        d.save(output_file)

    return output_file


def create_simple_schematic(circuit_info: Dict, output_path: Path) -> str:
    """シンプルな回路図を生成（接続関係ベース）"""
    import schemdraw
    import schemdraw.elements as elm

    d = schemdraw.Drawing()

    # 回路パターンを検出して適切にレイアウト
    parts = circuit_info["parts"]
    nets = circuit_info["nets"]

    # 簡易実装：直列接続として描画
    current_pos = d.here

    for i, part in enumerate(parts):
        name = part["name"].upper()
        value = part["value"]
        ref = part["ref"]

        # 部品タイプに応じた要素選択
        if 'R' in name or 'RESISTOR' in name:
            elem = elm.Resistor()
        elif 'C' in name or 'CAPACITOR' in name:
            elem = elm.Capacitor()
        elif 'L' in name or 'INDUCTOR' in name:
            elem = elm.Inductor()
        elif 'D' in name or 'DIODE' in name:
            if 'LED' in name:
                elem = elm.LED()
            elif 'ZENER' in name:
                elem = elm.Zener()
            else:
                elem = elm.Diode()
        elif 'Q' in name:
            if 'NPN' in name:
                elem = elm.BjtNpn(circle=True)
            elif 'PNP' in name:
                elem = elm.BjtPnp(circle=True)
            elif 'NMOS' in name or 'NFET' in name:
                elem = elm.NFet()
            else:
                elem = elm.PFet()
        else:
            elem = elm.Resistor()  # デフォルト

        # ラベル
        label = f"{ref}: {value}" if value else ref
        d.add(elem.label(label))

    # 保存
    d.save(str(output_path))
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='SKiDL回路から回路図を生成'
    )
    parser.add_argument('script', type=Path, help='入力SKiDLスクリプト（.py）')
    parser.add_argument('-o', '--output', type=Path, default=Path('outputs'),
                        help='出力ディレクトリ（デフォルト: outputs/）')
    parser.add_argument('--name', type=str, default=None,
                        help='出力ファイル名（デフォルト: スクリプト名）')
    parser.add_argument('--format', type=str, default='svg', choices=['svg', 'png'],
                        help='出力形式（デフォルト: svg）')
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
        "circuit_info": {},
        "exported_files": [],
        "errors": []
    }

    try:
        # 依存ライブラリ確認
        try:
            import schemdraw
            import schemdraw.elements as elm
        except ImportError:
            print("Error: schemdraw is not installed. Run: pip install schemdraw", file=sys.stderr)
            sys.exit(1)

        try:
            from skidl import set_default_tool, KICAD
            set_default_tool(KICAD)
        except ImportError:
            print("Error: SKiDL is not installed. Run: pip install skidl", file=sys.stderr)
            sys.exit(1)

        # 回路読み込み
        print(f"Loading circuit: {args.script}")
        circuit = load_skidl_circuit(args.script)

        # 回路解析
        print("Analyzing circuit...")
        circuit_info = analyze_circuit(circuit)
        result_data["circuit_info"] = {
            "parts_count": len(circuit_info["parts"]),
            "nets_count": len(circuit_info["nets"])
        }
        print(f"  Parts: {len(circuit_info['parts'])}")
        print(f"  Nets: {len(circuit_info['nets'])}")

        # 回路図生成
        print(f"Generating schematic...")
        output_file = args.output / f"{base_name}-schematic.{args.format}"

        try:
            schematic_path = create_schematic(circuit_info, output_file, args.format)
        except Exception as e:
            print(f"  Falling back to simple schematic: {e}")
            schematic_path = create_simple_schematic(circuit_info, output_file)

        result_data["exported_files"].append(schematic_path)
        print(f"  Created: {schematic_path}")

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
