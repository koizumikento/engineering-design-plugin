#!/usr/bin/env python3
"""
PySpice Simulator - SPICEシミュレーションを実行

使用方法:
    python3 pyspice_sim.py input.py --dc -o outputs/
    python3 pyspice_sim.py input.py --ac -o outputs/
    python3 pyspice_sim.py input.py --tran -o outputs/
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Optional
import csv


def load_circuit(script_path: Path):
    """回路定義を読み込み"""
    spec = importlib.util.spec_from_file_location("circuit_script", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script: {script_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["circuit_script"] = module

    # スクリプト実行
    spec.loader.exec_module(module)

    # 回路オブジェクトを探す
    circuit = None
    for name in ['circuit', 'cir', 'netlist']:
        if hasattr(module, name):
            circuit = getattr(module, name)
            break

    if circuit is None:
        raise ValueError("スクリプトに 'circuit', 'cir', 'netlist' 変数が見つかりません")

    return circuit


def run_dc_analysis(circuit, output_dir: Path, base_name: str, source: str = None,
                    start: float = 0, stop: float = 5, step: float = 0.1) -> dict:
    """DC解析を実行"""
    import numpy as np
    import matplotlib.pyplot as plt

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)

    result = {
        "type": "dc",
        "files": []
    }

    if source:
        # DCスイープ
        analysis = simulator.dc(**{source: slice(start, stop, step)})

        # データ保存
        csv_path = output_dir / f"{base_name}-dc.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)

            # ヘッダー
            nodes = [str(n) for n in analysis.nodes.keys()]
            writer.writerow(['sweep'] + nodes)

            # データ
            sweep_data = np.array(analysis[source.lower()])
            for i, sweep_val in enumerate(sweep_data):
                row = [sweep_val]
                for node in nodes:
                    row.append(float(analysis[node][i]))
                writer.writerow(row)

        result["files"].append(str(csv_path))

        # プロット
        plt.figure(figsize=(10, 6))
        for node in analysis.nodes.keys():
            if str(node) not in ['0', 'gnd']:
                plt.plot(sweep_data, analysis[node], label=str(node))

        plt.xlabel(f'{source} (V)')
        plt.ylabel('Voltage (V)')
        plt.title('DC Sweep Analysis')
        plt.legend()
        plt.grid(True)

        plot_path = output_dir / f"{base_name}-dc.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        result["files"].append(str(plot_path))

    else:
        # 動作点解析
        analysis = simulator.operating_point()

        csv_path = output_dir / f"{base_name}-dc-op.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Node', 'Voltage (V)'])
            for node in analysis.nodes.keys():
                writer.writerow([str(node), float(analysis[node])])

        result["files"].append(str(csv_path))

        print("\nOperating Point:")
        for node in analysis.nodes.keys():
            print(f"  {node}: {float(analysis[node]):.4f} V")

    return result


def run_ac_analysis(circuit, output_dir: Path, base_name: str,
                    start_freq: float = 10, stop_freq: float = 1e6,
                    points_per_decade: int = 10) -> dict:
    """AC解析を実行"""
    import numpy as np
    import matplotlib.pyplot as plt
    from PySpice.Unit import u_Hz

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)

    analysis = simulator.ac(
        start_frequency=start_freq@u_Hz,
        stop_frequency=stop_freq@u_Hz,
        number_of_points=points_per_decade,
        variation='dec'
    )

    result = {
        "type": "ac",
        "files": []
    }

    frequency = np.array(analysis.frequency)

    # データ保存
    csv_path = output_dir / f"{base_name}-ac.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)

        nodes = [str(n) for n in analysis.nodes.keys() if str(n) not in ['0', 'gnd']]
        header = ['Frequency (Hz)']
        for node in nodes:
            header.extend([f'{node}_mag (dB)', f'{node}_phase (deg)'])
        writer.writerow(header)

        for i, freq in enumerate(frequency):
            row = [freq]
            for node in nodes:
                mag = 20 * np.log10(np.abs(analysis[node][i]))
                phase = np.angle(analysis[node][i], deg=True)
                row.extend([mag, phase])
            writer.writerow(row)

    result["files"].append(str(csv_path))

    # ボード線図
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 8))

    for node in analysis.nodes.keys():
        if str(node) not in ['0', 'gnd']:
            node_data = np.array(analysis[node])
            gain_db = 20 * np.log10(np.abs(node_data))
            phase_deg = np.angle(node_data, deg=True)

            ax1.semilogx(frequency, gain_db, label=str(node))
            ax2.semilogx(frequency, phase_deg, label=str(node))

    ax1.set_ylabel('Gain (dB)')
    ax1.set_title('Bode Plot')
    ax1.legend()
    ax1.grid(True)

    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Phase (deg)')
    ax2.legend()
    ax2.grid(True)

    plot_path = output_dir / f"{base_name}-ac-bode.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    result["files"].append(str(plot_path))

    return result


def run_transient_analysis(circuit, output_dir: Path, base_name: str,
                           step_time: float = 1e-6, end_time: float = 1e-3) -> dict:
    """過渡解析を実行"""
    import numpy as np
    import matplotlib.pyplot as plt
    from PySpice.Unit import u_s

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)

    analysis = simulator.transient(
        step_time=step_time@u_s,
        end_time=end_time@u_s
    )

    result = {
        "type": "transient",
        "files": []
    }

    time = np.array(analysis.time)

    # データ保存
    csv_path = output_dir / f"{base_name}-tran.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)

        nodes = [str(n) for n in analysis.nodes.keys() if str(n) not in ['0', 'gnd']]
        writer.writerow(['Time (s)'] + nodes)

        for i, t in enumerate(time):
            row = [t]
            for node in nodes:
                row.append(float(analysis[node][i]))
            writer.writerow(row)

    result["files"].append(str(csv_path))

    # プロット
    plt.figure(figsize=(10, 6))

    for node in analysis.nodes.keys():
        if str(node) not in ['0', 'gnd']:
            plt.plot(time * 1e6, analysis[node], label=str(node))

    plt.xlabel('Time (us)')
    plt.ylabel('Voltage (V)')
    plt.title('Transient Analysis')
    plt.legend()
    plt.grid(True)

    plot_path = output_dir / f"{base_name}-tran.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    result["files"].append(str(plot_path))

    return result


def main():
    parser = argparse.ArgumentParser(
        description='SPICEシミュレーションを実行'
    )
    parser.add_argument('script', type=Path, help='入力スクリプト（.py）')
    parser.add_argument('-o', '--output', type=Path, default=Path('outputs'),
                        help='出力ディレクトリ（デフォルト: outputs/）')
    parser.add_argument('--name', type=str, default=None,
                        help='出力ファイル名（デフォルト: スクリプト名）')

    # 解析タイプ
    analysis_group = parser.add_mutually_exclusive_group(required=True)
    analysis_group.add_argument('--dc', action='store_true', help='DC解析')
    analysis_group.add_argument('--ac', action='store_true', help='AC解析')
    analysis_group.add_argument('--tran', action='store_true', help='過渡解析')

    # DC解析オプション
    parser.add_argument('--dc-source', type=str, help='DCスイープ電源名')
    parser.add_argument('--dc-start', type=float, default=0, help='DCスイープ開始値')
    parser.add_argument('--dc-stop', type=float, default=5, help='DCスイープ終了値')
    parser.add_argument('--dc-step', type=float, default=0.1, help='DCスイープステップ')

    # AC解析オプション
    parser.add_argument('--ac-start', type=float, default=10, help='開始周波数（Hz）')
    parser.add_argument('--ac-stop', type=float, default=1e6, help='終了周波数（Hz）')
    parser.add_argument('--ac-points', type=int, default=10, help='decade当たりのポイント数')

    # 過渡解析オプション
    parser.add_argument('--tran-step', type=float, default=1e-6, help='ステップ時間（s）')
    parser.add_argument('--tran-end', type=float, default=1e-3, help='終了時間（s）')

    parser.add_argument('--json', action='store_true', help='結果をJSON形式で出力')

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
        "analysis": {},
        "errors": []
    }

    try:
        # PySpiceインポート確認
        try:
            from PySpice.Spice.Netlist import Circuit
            from PySpice.Unit import u_V, u_Ohm, u_F
        except ImportError:
            print("Error: PySpice is not installed. Run: pip install PySpice", file=sys.stderr)
            sys.exit(1)

        # 回路読み込み
        print(f"Loading circuit: {args.script}")
        circuit = load_circuit(args.script)
        print(f"Circuit: {circuit.name if hasattr(circuit, 'name') else 'unnamed'}")

        # 解析実行
        if args.dc:
            print("Running DC analysis...")
            result_data["analysis"] = run_dc_analysis(
                circuit, args.output, base_name,
                source=args.dc_source,
                start=args.dc_start,
                stop=args.dc_stop,
                step=args.dc_step
            )
        elif args.ac:
            print("Running AC analysis...")
            result_data["analysis"] = run_ac_analysis(
                circuit, args.output, base_name,
                start_freq=args.ac_start,
                stop_freq=args.ac_stop,
                points_per_decade=args.ac_points
            )
        elif args.tran:
            print("Running transient analysis...")
            result_data["analysis"] = run_transient_analysis(
                circuit, args.output, base_name,
                step_time=args.tran_step,
                end_time=args.tran_end
            )

        for f in result_data["analysis"].get("files", []):
            print(f"  Created: {f}")

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
