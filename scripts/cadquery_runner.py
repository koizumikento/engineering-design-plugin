#!/usr/bin/env python3
"""
CadQuery Runner - CadQueryスクリプトを実行し、3Dモデルを出力

使用方法:
    python3 cadquery_runner.py input.py -o outputs/
    python3 cadquery_runner.py input.py -o outputs/ --format step,stl,png
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Optional


def load_script(script_path: Path) -> dict:
    """Pythonスクリプトを読み込み、結果を取得"""
    spec = importlib.util.spec_from_file_location("cadquery_script", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script: {script_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["cadquery_script"] = module

    # スクリプト実行
    spec.loader.exec_module(module)

    # 結果を探す（一般的な変数名）
    result = None
    for name in ['result', 'model', 'shape', 'part', 'assembly']:
        if hasattr(module, name):
            result = getattr(module, name)
            break

    if result is None:
        raise ValueError("スクリプトに 'result', 'model', 'shape', 'part', 'assembly' 変数が見つかりません")

    return result


def _shape_from_result(result):
    """CadQuery Workplane / Assembly / Shape から検査対象 shape を取り出す。"""
    import cadquery as cq

    if isinstance(result, cq.Workplane):
        return result.val()

    if hasattr(cq, "Assembly") and isinstance(result, cq.Assembly):
        return result.toCompound()

    if hasattr(result, "toCompound"):
        try:
            return result.toCompound()
        except Exception:
            pass

    return result


def _vector_to_dict(vector) -> dict:
    return {
        "x": float(getattr(vector, "x", 0.0)),
        "y": float(getattr(vector, "y", 0.0)),
        "z": float(getattr(vector, "z", 0.0)),
    }


def _topology_count(shape, method_name: str) -> int:
    method = getattr(shape, method_name, None)
    if method is None:
        return 0

    try:
        return len(method())
    except Exception:
        return 0


def _center_of_mass(shape) -> Optional[dict]:
    for method_name in ("CenterOfMass", "centerOfMass", "Center"):
        method = getattr(shape, method_name, None)
        if method is None:
            continue

        try:
            return _vector_to_dict(method())
        except Exception:
            continue

    return None


def validate_shape(result) -> dict:
    """形状の妥当性を検証"""
    info = {
        "valid": False,
        "volume": 0.0,
        "area": 0.0,
        "center_of_mass": None,
        "bounding_box": {},
        "topology": {
            "solids": 0,
            "faces": 0,
            "edges": 0,
            "vertices": 0,
        },
        "errors": []
    }

    try:
        shape = _shape_from_result(result)

        # 妥当性チェック
        info["valid"] = shape.isValid()
        if not info["valid"]:
            info["errors"].append("形状が無効です（自己交差または不正な形状）")

        # 体積・表面積
        info["volume"] = shape.Volume()
        info["area"] = shape.Area()
        info["center_of_mass"] = _center_of_mass(shape)

        # バウンディングボックス
        bb = shape.BoundingBox()
        info["bounding_box"] = {
            "x_len": bb.xlen,
            "y_len": bb.ylen,
            "z_len": bb.zlen,
            "x_min": bb.xmin,
            "x_max": bb.xmax,
            "y_min": bb.ymin,
            "y_max": bb.ymax,
            "z_min": bb.zmin,
            "z_max": bb.zmax,
        }
        info["topology"] = {
            "solids": _topology_count(shape, "Solids"),
            "faces": _topology_count(shape, "Faces"),
            "edges": _topology_count(shape, "Edges"),
            "vertices": _topology_count(shape, "Vertices"),
        }

    except Exception as e:
        info["errors"].append(str(e))

    return info


def write_report(result_data: dict, output_dir: Path, base_name: str) -> Path:
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{base_name}-cad-summary.json"
    result_data["report"] = str(report_path)
    report_path.write_text(
        json.dumps(result_data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return report_path


def export_model(result, output_dir: Path, base_name: str, formats: list) -> list:
    """モデルをエクスポート"""
    import cadquery as cq
    from cadquery import exporters

    exported_files = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for fmt in formats:
        fmt = fmt.lower().strip()
        output_path = output_dir / f"{base_name}.{fmt}"

        try:
            if fmt == "step":
                exporters.export(result, str(output_path))
                exported_files.append(str(output_path))

            elif fmt == "stl":
                exporters.export(result, str(output_path))
                exported_files.append(str(output_path))

            elif fmt == "dxf":
                exporters.exportDXF(result, str(output_path))
                exported_files.append(str(output_path))

            elif fmt == "svg":
                exporters.export(result, str(output_path))
                exported_files.append(str(output_path))

            elif fmt == "png":
                # PNGはpreview_generator.pyで処理
                pass

            else:
                print(f"Warning: Unknown format '{fmt}'", file=sys.stderr)

        except Exception as e:
            print(f"Error exporting {fmt}: {e}", file=sys.stderr)

    return exported_files


def generate_preview(result, output_path: Path, view: str = "iso") -> Optional[str]:
    """プレビュー画像を生成（OCC Viewerが利用可能な場合）"""
    try:
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
        from OCP.Graphic3d import Graphic3d_Camera
        import cadquery as cq

        # 簡易プレビュー（実際の実装ではcq-editorやvtkを使用）
        # ここではSTLを経由してmatplotlibで表示する代替実装

        from mpl_toolkits import mplot3d
        import matplotlib.pyplot as plt
        from stl import mesh
        import tempfile

        # 一時STLファイル作成
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            tmp_path = tmp.name

        from cadquery import exporters
        exporters.export(result, tmp_path)

        # STL読み込みとプロット
        figure = plt.figure(figsize=(10, 10))
        axes = figure.add_subplot(projection='3d')

        stl_mesh = mesh.Mesh.from_file(tmp_path)
        axes.add_collection3d(mplot3d.art3d.Poly3DCollection(
            stl_mesh.vectors,
            facecolors='lightblue',
            edgecolors='darkblue',
            linewidths=0.1,
            alpha=0.8
        ))

        # スケール調整
        scale = stl_mesh.points.flatten()
        axes.auto_scale_xyz(scale, scale, scale)

        # ビュー設定
        if view == "front":
            axes.view_init(elev=0, azim=0)
        elif view == "top":
            axes.view_init(elev=90, azim=0)
        elif view == "side":
            axes.view_init(elev=0, azim=90)
        else:  # iso
            axes.view_init(elev=30, azim=45)

        axes.set_xlabel('X')
        axes.set_ylabel('Y')
        axes.set_zlabel('Z')

        plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
        plt.close()

        # 一時ファイル削除
        Path(tmp_path).unlink()

        return str(output_path)

    except ImportError as e:
        print(f"Preview generation requires additional libraries: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error generating preview: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description='CadQueryスクリプトを実行し、3Dモデルを出力'
    )
    parser.add_argument('script', type=Path, help='入力スクリプト（.py）')
    parser.add_argument('-o', '--output', type=Path, default=Path('outputs'),
                        help='出力ディレクトリ（デフォルト: outputs/）')
    parser.add_argument('--format', type=str, default='step,stl',
                        help='出力形式（カンマ区切り: step,stl,dxf,svg,png）')
    parser.add_argument('--name', type=str, default=None,
                        help='出力ファイル名（デフォルト: スクリプト名）')
    parser.add_argument('--preview', action='store_true',
                        help='プレビュー画像を生成')
    parser.add_argument('--json', action='store_true',
                        help='結果をJSON形式で出力')
    parser.add_argument('--report', action='store_true',
                        help='検査結果を outputs/reports/[name]-cad-summary.json に保存')
    parser.add_argument('--fail-on-invalid', action='store_true',
                        help='isValid() が False の場合に非ゼロ終了する')

    args = parser.parse_args()

    # スクリプトパス確認
    if not args.script.exists():
        print(f"Error: Script not found: {args.script}", file=sys.stderr)
        sys.exit(1)

    # 基本名
    base_name = args.name or args.script.stem

    # 出力形式
    formats = [f.strip() for f in args.format.split(',')]

    result_data = {
        "script": str(args.script),
        "output_dir": str(args.output),
        "validation": {},
        "exported_files": [],
        "preview": None,
        "report": None,
        "errors": []
    }

    try:
        # CadQueryインポート確認
        try:
            import cadquery as cq
        except ImportError:
            print("Error: CadQuery is not installed. Run: uv sync", file=sys.stderr)
            sys.exit(1)

        # スクリプト実行
        print(f"Loading script: {args.script}")
        result = load_script(args.script)

        # 検証
        print("Validating shape...")
        validation = validate_shape(result)
        result_data["validation"] = validation

        if not validation["valid"]:
            print(f"Warning: Shape validation failed: {validation['errors']}", file=sys.stderr)

        # 情報出力
        bb = validation["bounding_box"]
        print(f"Size: {bb.get('x_len', 0):.2f} x {bb.get('y_len', 0):.2f} x {bb.get('z_len', 0):.2f} mm")
        print(f"Volume: {validation['volume']:.2f} mm^3")
        print(f"Surface Area: {validation['area']:.2f} mm^2")
        center = validation.get("center_of_mass")
        if center:
            print(f"Center of Mass: {center['x']:.2f}, {center['y']:.2f}, {center['z']:.2f} mm")
        topology = validation.get("topology", {})
        print(
            "Topology: "
            f"{topology.get('solids', 0)} solids, "
            f"{topology.get('faces', 0)} faces, "
            f"{topology.get('edges', 0)} edges, "
            f"{topology.get('vertices', 0)} vertices"
        )

        if args.fail_on_invalid and not validation["valid"]:
            if args.report:
                report_path = write_report(result_data, args.output, base_name)
                print(f"  Report: {report_path}")
            print("Error: Shape validation failed and --fail-on-invalid was set", file=sys.stderr)
            sys.exit(2)

        # エクスポート
        print(f"Exporting to: {args.output}")
        exported = export_model(result, args.output, base_name, formats)
        result_data["exported_files"] = exported

        for f in exported:
            print(f"  Created: {f}")

        # プレビュー生成
        if args.preview or 'png' in formats:
            preview_path = args.output / f"{base_name}-preview.png"
            preview = generate_preview(result, preview_path)
            if preview:
                result_data["preview"] = preview
                print(f"  Preview: {preview}")

        if args.report:
            report_path = write_report(result_data, args.output, base_name)
            print(f"  Report: {report_path}")

        # 成功
        print("\nDone!")

    except Exception as e:
        result_data["errors"].append(str(e))
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # JSON出力
    if args.json:
        print(json.dumps(result_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
