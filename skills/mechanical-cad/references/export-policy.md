# CAD出力ポリシー

| 形式 | 主用途 | 正本性 | 検証上の注意 |
|---|---|---|---|
| CadQuery `.py` | パラメトリック定義、再生成 | 設計ロジックの正本 | 依存版、入力、乱数/外部ファイルを固定 |
| STEP/STP | CAD交換、統合、計測 | 中立形状の一次成果物 | parametric historyは保持しない。再import確認を検討 |
| BREP/XBF/XML | OCCT/XCAF系の中間・詳細交換 | 用途限定 | 受け手の対応を確認 |
| STL/3MF | 3Dプリント、mesh処理 | 派生成果物 | linear/angular tessellation、単位、watertightを確認 |
| DXF | 2D断面、レーザー/板金輪郭 | 指定輪郭の派生成果物 | 平面、layer、単位、curve近似を記録 |
| SVG | 説明・簡易2D表示 | 製造正本にしない | 尺度と投影を明示 |
| PNG | 人による形状レビュー | 証拠補助 | iso/front/top/right、透視/正投影を明示 |

## Naming and metadata

- ファイル名にproject/part名を含める。
- reportへ生成元script、commit/revision、CadQuery version、単位、export設定を記録する。
- assemblyと単体partを混同しない。
- 重要な派生成果物は再importまたは別viewerで開き、寸法とsolid数を確認する。

## Mesh

STL/3MFのtoleranceは「小さいほど常によい」ではない。過密meshは計算量を増やし、粗いmeshは曲面・小穴を損なう。部品スケールと最小曲率に合わせ、代表断面を確認する。

CadQueryが現在対応する形式と引数は[公式Import/Export資料](https://cadquery.readthedocs.io/en/latest/importexport.html)で確認する。runnerが未対応の形式をSKILL.mdで生成済みと主張しない。
