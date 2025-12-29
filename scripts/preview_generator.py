#!/usr/bin/env python3
"""
Preview Generator - 3Dモデルのプレビュー画像を生成

使用方法:
    python3 preview_generator.py input.step -o outputs/
    python3 preview_generator.py input.py -o outputs/ --view iso
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Tuple
import tempfile


def load_step_file(step_path: Path):
    """STEPファイルを読み込み"""
    import cadquery as cq

    result = cq.importers.importStep(str(step_path))
    return result


def load_stl_file(stl_path: Path):
    """STLファイルを読み込み"""
    import cadquery as cq

    result = cq.importers.importStl(str(stl_path))
    return result


def load_cadquery_script(script_path: Path):
    """CadQueryスクリプトを実行して結果を取得"""
    import importlib.util

    spec = importlib.util.spec_from_file_location("cq_script", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script: {script_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["cq_script"] = module

    spec.loader.exec_module(module)

    # 結果を探す
    for name in ['result', 'model', 'shape', 'part', 'assembly']:
        if hasattr(module, name):
            return getattr(module, name)

    raise ValueError("Script does not contain 'result', 'model', 'shape', 'part', or 'assembly'")


def get_view_parameters(view: str) -> Tuple[float, float]:
    """ビュー名から視点パラメータを取得"""
    views = {
        "iso": (30, 45),      # 等角図
        "front": (0, 0),      # 正面図
        "back": (0, 180),     # 背面図
        "top": (90, 0),       # 上面図
        "bottom": (-90, 0),   # 底面図
        "left": (0, -90),     # 左側面図
        "right": (0, 90),     # 右側面図
    }
    return views.get(view, (30, 45))


def render_with_matplotlib(result, output_path: Path, view: str = "iso",
                          width: int = 1024, height: int = 768) -> str:
    """matplotlibを使用してレンダリング"""
    import cadquery as cq
    from cadquery import exporters
    import numpy as np
    import matplotlib.pyplot as plt
    from mpl_toolkits import mplot3d

    # 一時STLファイル作成
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
        tmp_path = tmp.name

    exporters.export(result, tmp_path)

    try:
        from stl import mesh

        # STL読み込み
        stl_mesh = mesh.Mesh.from_file(tmp_path)

        # プロット作成
        fig = plt.figure(figsize=(width/100, height/100), dpi=100)
        ax = fig.add_subplot(projection='3d')

        # メッシュ描画
        collection = mplot3d.art3d.Poly3DCollection(
            stl_mesh.vectors,
            facecolors='#4a90d9',
            edgecolors='#2d5a87',
            linewidths=0.1,
            alpha=0.9
        )
        ax.add_collection3d(collection)

        # スケール設定
        scale = stl_mesh.points.flatten()
        ax.auto_scale_xyz(scale, scale, scale)

        # ビュー設定
        elev, azim = get_view_parameters(view)
        ax.view_init(elev=elev, azim=azim)

        # 軸ラベル
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_zlabel('Z (mm)')

        # 背景色
        ax.set_facecolor('#f0f0f0')
        fig.patch.set_facecolor('#ffffff')

        # グリッド
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(str(output_path), dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()

        return str(output_path)

    finally:
        # 一時ファイル削除
        Path(tmp_path).unlink()


def render_with_vtk(result, output_path: Path, view: str = "iso",
                   width: int = 1024, height: int = 768) -> str:
    """VTKを使用してレンダリング（より高品質）"""
    try:
        import vtk
        from vtkmodules.util import numpy_support
        import cadquery as cq
        from cadquery import exporters
        import numpy as np

        # 一時STLファイル作成
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            tmp_path = tmp.name

        exporters.export(result, tmp_path)

        try:
            # STL読み込み
            reader = vtk.vtkSTLReader()
            reader.SetFileName(tmp_path)
            reader.Update()

            # マッパー
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())

            # アクター
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.29, 0.56, 0.85)  # 青色
            actor.GetProperty().SetSpecular(0.3)
            actor.GetProperty().SetSpecularPower(20)

            # レンダラー
            renderer = vtk.vtkRenderer()
            renderer.AddActor(actor)
            renderer.SetBackground(1, 1, 1)  # 白背景

            # ライト設定
            light = vtk.vtkLight()
            light.SetPosition(1, 1, 1)
            renderer.AddLight(light)

            # カメラ設定
            camera = renderer.GetActiveCamera()
            elev, azim = get_view_parameters(view)
            camera.SetPosition(
                np.cos(np.radians(azim)) * np.cos(np.radians(elev)),
                np.sin(np.radians(azim)) * np.cos(np.radians(elev)),
                np.sin(np.radians(elev))
            )
            camera.SetViewUp(0, 0, 1)
            renderer.ResetCamera()

            # オフスクリーンレンダリング
            render_window = vtk.vtkRenderWindow()
            render_window.SetOffScreenRendering(1)
            render_window.AddRenderer(renderer)
            render_window.SetSize(width, height)
            render_window.Render()

            # 画像出力
            window_to_image = vtk.vtkWindowToImageFilter()
            window_to_image.SetInput(render_window)
            window_to_image.Update()

            writer = vtk.vtkPNGWriter()
            writer.SetFileName(str(output_path))
            writer.SetInputConnection(window_to_image.GetOutputPort())
            writer.Write()

            return str(output_path)

        finally:
            Path(tmp_path).unlink()

    except ImportError:
        raise ImportError("VTK is not installed. Use matplotlib fallback.")


def render_preview(result, output_path: Path, view: str = "iso",
                  width: int = 1024, height: int = 768) -> str:
    """プレビュー画像を生成"""
    # VTKを試す
    try:
        return render_with_vtk(result, output_path, view, width, height)
    except ImportError:
        pass

    # matplotlibにフォールバック
    return render_with_matplotlib(result, output_path, view, width, height)


def main():
    parser = argparse.ArgumentParser(
        description='3Dモデルのプレビュー画像を生成'
    )
    parser.add_argument('input', type=Path, help='入力ファイル（.step, .stl, .py）')
    parser.add_argument('-o', '--output', type=Path, default=Path('outputs'),
                        help='出力ディレクトリ（デフォルト: outputs/）')
    parser.add_argument('--name', type=str, default=None,
                        help='出力ファイル名（デフォルト: 入力ファイル名）')
    parser.add_argument('--view', type=str, default='iso',
                        choices=['iso', 'front', 'back', 'top', 'bottom', 'left', 'right'],
                        help='ビュー（デフォルト: iso）')
    parser.add_argument('--all-views', action='store_true',
                        help='全ビューを生成')
    parser.add_argument('--width', type=int, default=1024, help='画像幅（px）')
    parser.add_argument('--height', type=int, default=768, help='画像高さ（px）')
    parser.add_argument('--json', action='store_true',
                        help='結果をJSON形式で出力')

    args = parser.parse_args()

    # 入力ファイル確認
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 基本名
    base_name = args.name or args.input.stem

    # 出力ディレクトリ作成
    args.output.mkdir(parents=True, exist_ok=True)

    result_data = {
        "input": str(args.input),
        "output_dir": str(args.output),
        "exported_files": [],
        "errors": []
    }

    try:
        # CadQueryインポート確認
        try:
            import cadquery as cq
        except ImportError:
            print("Error: CadQuery is not installed. Run: pip install cadquery", file=sys.stderr)
            sys.exit(1)

        # ファイル読み込み
        print(f"Loading: {args.input}")
        suffix = args.input.suffix.lower()

        if suffix == '.step' or suffix == '.stp':
            result = load_step_file(args.input)
        elif suffix == '.stl':
            result = load_stl_file(args.input)
        elif suffix == '.py':
            result = load_cadquery_script(args.input)
        else:
            print(f"Error: Unsupported file format: {suffix}", file=sys.stderr)
            sys.exit(1)

        # ビュー一覧
        if args.all_views:
            views = ['iso', 'front', 'top', 'right']
        else:
            views = [args.view]

        # レンダリング
        print("Generating preview...")
        for view in views:
            if len(views) > 1:
                output_file = args.output / f"{base_name}-{view}.png"
            else:
                output_file = args.output / f"{base_name}-preview.png"

            preview_path = render_preview(
                result, output_file, view,
                args.width, args.height
            )
            result_data["exported_files"].append(preview_path)
            print(f"  Created: {preview_path}")

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
