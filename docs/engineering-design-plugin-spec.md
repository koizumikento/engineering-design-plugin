# Engineering Design Plugin 仕様書

## 概要

機械製図・3Dモデリングと電子回路設計を統合したClaude Codeプラグイン。
自然言語要望から仕様書（Markdown）を生成し、CadQuery/SKiDLコードを自動生成する。

## ワークフロー

### 単体設計フロー
```
[ユーザー要望] → [仕様書生成] → [コード生成] → [検証] → [出力ファイル]
                      ↑
                 人間がレビュー・承認
```

### 統合設計フロー
```
[ユーザー要望（筐体+回路）]
        ↓
[統合仕様書生成]
    ├── 機械設計仕様
    ├── 回路設計仕様
    └── 基板-筐体インターフェース定義
        ↓
[整合性チェック] ← /eng:integrate
        ↓
[並行してコード生成]
    ├── 筐体: CadQuery → STEP/STL
    └── 回路: SKiDL → ネットリスト/SVG
```

---

## ディレクトリ構造

```
engineering-design-plugin/
├── .claude-plugin/
│   └── plugin.json
│
├── commands/
│   ├── spec.md
│   ├── cad.md
│   ├── circuit.md
│   ├── simulate.md
│   ├── schematic.md
│   ├── preview.md
│   └── integrate.md
│
├── skills/
│   ├── spec-writing/
│   │   ├── SKILL.md
│   │   └── refs/
│   │       └── spec-templates.md
│   ├── mechanical-cad/
│   │   ├── SKILL.md
│   │   └── refs/
│   │       ├── cadquery-api.md
│   │       ├── jis-drawing.md
│   │       └── templates.md
│   ├── circuit-design/
│   │   ├── SKILL.md
│   │   └── refs/
│   │       ├── skidl-api.md
│   │       ├── circuit-patterns.md
│   │       └── spice-guide.md
│   └── integration/
│       ├── SKILL.md
│       └── refs/
│           └── interface-spec.md
│
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── validate-code.sh
│
├── scripts/
│   ├── cadquery_runner.py
│   ├── skidl_runner.py
│   ├── pyspice_sim.py
│   ├── schemdraw_render.py
│   ├── preview_generator.py
│   └── integration_checker.py
│
├── templates/
│   ├── spec/
│   │   ├── mechanical-spec.md
│   │   ├── circuit-spec.md
│   │   └── integrated-spec.md
│   ├── mechanical/
│   │   ├── box_with_holes.py
│   │   ├── enclosure_with_pcb.py
│   │   ├── shaft.py
│   │   └── bracket.py
│   └── circuit/
│       ├── voltage_divider.py
│       ├── rc_filter.py
│       └── opamp_amplifier.py
│
├── examples/
│   ├── sensor-enclosure/
│   ├── led-driver/
│   └── iot-device/
│
├── README.md
└── LICENSE
```

---

## plugin.json

```json
{
  "name": "engineering-design",
  "version": "1.0.0",
  "description": "機械製図・3Dモデリングと電子回路設計の統合プラグイン。自然言語から仕様書を生成し、CadQuery/SKiDLコードを自動生成。",
  "author": {
    "name": "Koizumi"
  },
  "repository": "https://github.com/koizumi/engineering-design-plugin",
  "license": "MIT",
  "keywords": [
    "cad", "cadquery", "3d-modeling", "mechanical-design",
    "circuit-design", "skidl", "electronics", "engineering"
  ]
}
```

---

## Skills

### skills/spec-writing/SKILL.md

```markdown
---
name: spec-writing
description: |
  設計仕様書の作成。以下の場合に使用:
  (1) 「仕様書を作成」「設計要件をまとめて」などのリクエスト
  (2) 機械設計・回路設計の要件整理
  (3) 統合設計の仕様策定
  入力: 自然言語要望
  出力: Markdown仕様書
---

# 仕様書作成スキル

## ワークフロー

1. **要望分析**
   - [ ] 設計対象の種類を判定（機械/回路/統合）
   - [ ] 明示的要件と暗黙的要件を抽出
   - [ ] 不明点をリストアップ

2. **対話による明確化**
   不明な場合は質問:
   - 寸法・公差の詳細
   - 材質・部品の選定基準
   - インターフェース仕様
   - 希望する出力形式

3. **仕様書生成**
   - `${CLAUDE_PLUGIN_ROOT}/templates/spec/`のテンプレートを使用
   - 要件をチェックリスト形式で記載
   - 数値仕様は表形式で整理

4. **ファイル出力**
   - `specs/[project-name]-spec.md`に保存
   - ユーザーに確認・承認を依頼

## 仕様書の品質基準

- [ ] すべての要件が検証可能（数値化・具体化）
- [ ] 曖昧な表現がない（「適切な」「十分な」等を排除）
- [ ] 設計制約が明記されている
- [ ] 出力形式が指定されている

## 詳細

`refs/spec-templates.md`を参照
```

### skills/mechanical-cad/SKILL.md

```markdown
---
name: mechanical-cad
description: |
  CadQueryを使用した3D CADモデルの生成。以下の場合に使用:
  (1) 「3Dモデルを作成」「筐体を設計」「ボックスを作って」などの機械設計リクエスト
  (2) STEP/STLファイルの生成が必要な場合
  (3) パラメトリック設計や穴・フィレット加工の指定
  入力: 仕様書または自然言語要望
  出力: Pythonスクリプト、STEP、STL、PNG
---

# Mechanical CAD Skill

## ワークフロー

1. **仕様確認**
   - [ ] 仕様書（specs/*.md）が存在するか確認
   - [ ] 承認チェックボックスがオンか確認
   - [ ] 必須項目（寸法、材質、出力形式）が揃っているか

2. **コード生成**
   - [ ] `refs/cadquery-api.md`を参照
   - [ ] パラメトリック設計を優先
   - [ ] 仕様書との対応をコメントで明記

3. **実行・検証**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cadquery_runner.py input.py -o outputs/
   ```
   - [ ] isValid()で形状の妥当性確認
   - [ ] 体積・表面積を算出して報告

4. **出力ファイル生成**
   - STEP: `outputs/[project-name].step`
   - STL: `outputs/[project-name].stl`
   - PNG: `outputs/[project-name]-preview.png`

## 基本パターン

```python
import cadquery as cq

# パラメータ
width, depth, height = 100, 60, 40
wall_thickness = 2.0
hole_diameter = 5.0

result = (
    cq.Workplane("XY")
    .box(width, depth, height)
    .faces(">Z").shell(-wall_thickness)
    .faces(">Z").workplane()
    .hole(hole_diameter)
)

assert result.val().isValid(), "形状が無効です"
cq.exporters.export(result, "output.step")
cq.exporters.export(result, "output.stl")
```

## エラー対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `isValid() = False` | 自己交差 | フィレット半径を小さく |
| `BOPAlgo_AlertSelfIntersection` | 形状重複 | 操作順序を見直し |

## 詳細

- `refs/cadquery-api.md` - CadQuery APIリファレンス
- `refs/jis-drawing.md` - JIS製図規格
- `refs/templates.md` - テンプレート集
```

### skills/circuit-design/SKILL.md

```markdown
---
name: circuit-design
description: |
  SKiDLを使用した回路設計。以下の場合に使用:
  (1) 「回路を設計」「分圧回路」「フィルタ回路」などの電子回路リクエスト
  (2) ネットリスト・回路図（SVG）の生成
  (3) SPICEシミュレーション
  入力: 仕様書または自然言語要望
  出力: Pythonスクリプト、ネットリスト、SVG、シミュレーション結果
---

# Circuit Design Skill

## ワークフロー

1. **仕様確認**
   - [ ] 仕様書（specs/*.md）が存在するか確認
   - [ ] 電気的仕様（入出力電圧、電流）が明確か
   - [ ] シミュレーション要件を確認

2. **コード生成**
   - [ ] `refs/skidl-api.md`を参照
   - [ ] 部品値の計算（必要に応じて）
   - [ ] 仕様書との対応をコメントで明記

3. **ERC実行**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skidl_runner.py input.py -o outputs/
   ```
   - [ ] 未接続ピンの検出
   - [ ] 電源接続の確認

4. **出力ファイル生成**
   - ネットリスト: `outputs/[project-name].net`
   - BOM: `outputs/[project-name]-bom.csv`

## 基本パターン

```python
from skidl import *

# 分圧回路
vin, vout, gnd = Net('VIN'), Net('VOUT'), Net('GND')
r1 = Part("Device", 'R', value='10K')
r2 = Part("Device", 'R', value='10K')

vin & r1 & vout & r2 & gnd

ERC()
generate_netlist()
```

## 詳細

- `refs/skidl-api.md` - SKiDL APIリファレンス
- `refs/circuit-patterns.md` - 回路パターン集
- `refs/spice-guide.md` - SPICEシミュレーションガイド
```

### skills/integration/SKILL.md

```markdown
---
name: integration
description: |
  機械-電子統合設計。以下の場合に使用:
  (1) 「筐体と回路を一緒に設計」「基板を収める筐体」などの統合設計リクエスト
  (2) 基板-筐体の整合性チェック
  (3) コネクタ位置と開口部の照合
  入力: 統合仕様書
  出力: 整合性レポート
---

# Integration Skill

## ワークフロー

1. **仕様書の統合**
   - [ ] 機械設計仕様書と回路設計仕様書を読み込み
   - [ ] 基板-筐体インターフェース情報を抽出

2. **整合性チェック**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/integration_checker.py specs/integrated-spec.md
   ```
   - [ ] 基板外形と筐体内寸の適合性
   - [ ] コネクタ位置と開口部位置の一致
   - [ ] 取付穴位置の整合

3. **干渉検出**
   - [ ] 基板と筐体内壁のクリアランス
   - [ ] 部品高さと筐体高さの確認

4. **レポート出力**
   - `outputs/[project-name]-integration-report.md`

## 基板-筐体インターフェース定義

| 項目 | 基板側 | 筐体側 |
|------|--------|--------|
| 基板サイズ | WxHmm | 内寸W+4xH+4mm |
| 取付穴 | M2.5×4箇所 | ボス高5mm |
| コネクタ | 側面配置 | 開口位置 |

## 詳細

`refs/interface-spec.md`を参照
```

---

## Commands

### commands/spec.md

```markdown
---
description: ユーザー要望から設計仕様書を生成
---

ユーザーの自然言語要望から設計仕様書を作成します。

## 手順

1. 要望を分析し、設計対象（機械/回路/統合）を判定
2. 不明点があれば質問
3. `${CLAUDE_PLUGIN_ROOT}/templates/spec/`のテンプレートを使用
4. `specs/[project-name]-spec.md`に保存
5. ユーザーに確認・承認を依頼
```

### commands/cad.md

```markdown
---
description: 承認済み仕様書からCadQueryコードを生成・実行
---

仕様書に基づいてCadQueryコードを生成します。

## 前提条件

- 仕様書が存在すること
- 承認チェックボックスがオンであること

## 手順

1. 仕様書の読込・検証
2. `skills/mechanical-cad/`を参照してコード生成
3. `${CLAUDE_PLUGIN_ROOT}/scripts/cadquery_runner.py`で実行
4. STEP/STL/PNGを出力
```

### commands/circuit.md

```markdown
---
description: 承認済み仕様書からSKiDLコードを生成・実行
---

仕様書に基づいてSKiDLコードを生成します。

## 前提条件

- 仕様書が存在すること
- 承認チェックボックスがオンであること

## 手順

1. 仕様書の読込・検証
2. `skills/circuit-design/`を参照してコード生成
3. `${CLAUDE_PLUGIN_ROOT}/scripts/skidl_runner.py`で実行
4. ネットリスト/BOMを出力
```

### commands/simulate.md

```markdown
---
description: 回路のSPICEシミュレーションを実行
---

SKiDLコードに基づいてSPICEシミュレーションを実行します。

## 手順

1. シミュレーション設定の確認（DC/AC/過渡解析）
2. `${CLAUDE_PLUGIN_ROOT}/scripts/pyspice_sim.py`で実行
3. グラフとデータを出力
```

### commands/schematic.md

```markdown
---
description: 回路図（SVG）を生成
---

SKiDLコードから回路図を生成します。

## 手順

1. SKiDLスクリプトを読み込み
2. `${CLAUDE_PLUGIN_ROOT}/scripts/schemdraw_render.py`で実行
3. `outputs/[project-name]-schematic.svg`を出力
```

### commands/preview.md

```markdown
---
description: 3Dモデルのプレビュー画像を生成
---

CadQueryモデルのプレビュー画像を生成します。

## 手順

1. STEP/STLファイルを読み込み
2. `${CLAUDE_PLUGIN_ROOT}/scripts/preview_generator.py`で実行
3. `outputs/[project-name]-preview.png`を出力
```

### commands/integrate.md

```markdown
---
description: 機械・回路の統合設計・整合性チェック
---

機械設計と回路設計の整合性をチェックします。

## 手順

1. 統合仕様書を読み込み
2. `${CLAUDE_PLUGIN_ROOT}/scripts/integration_checker.py`で実行
3. 整合性レポートを出力
```

---

## Hooks

### hooks/hooks.json

```json
{
  "description": "Engineering Design Plugin validation hooks",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate-code.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "CadQueryまたはSKiDLスクリプトの実行結果を確認。エラーがあれば原因を分析し、修正案を提示。"
          }
        ]
      }
    ]
  }
}
```

### hooks/scripts/validate-code.sh

```bash
#!/bin/bash
read -r INPUT
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *.py ]]; then
  python3 -m py_compile "$FILE_PATH" 2>&1
  if [ $? -ne 0 ]; then
    echo '{"decision": "block", "reason": "Python構文エラー"}'
    exit 0
  fi
  
  if grep -qE "import (os|subprocess|shutil)" "$FILE_PATH"; then
    echo '{"decision": "ask", "reason": "システム操作を含むコード"}'
    exit 0
  fi
fi

echo '{"decision": "allow"}'
exit 0
```

---

## 仕様書テンプレート

### templates/spec/mechanical-spec.md

```markdown
# 機械設計仕様書

## 基本情報
- **プロジェクト名**: [名称]
- **バージョン**: 1.0
- **作成日**: YYYY-MM-DD
- **ステータス**: Draft | Review | Approved

## 要求仕様

### 機能要件
- [ ] [要件1]
- [ ] [要件2]

### 寸法・形状
| 項目 | 値 | 公差 | 備考 |
|------|-----|------|------|
| 全長 | mm | ±mm | |
| 全幅 | mm | ±mm | |
| 全高 | mm | ±mm | |

### 材質・表面処理
- **想定材質**: 
- **表面処理**: 
- **色**: 

### 接続・取付
- **取付穴**: 
- **ねじ規格**: 

## 設計制約
- [ ] [制約1]

## 出力形式
- [ ] STEP
- [ ] STL
- [ ] PNG

## 承認
- [ ] **仕様承認済み** - 承認後に `/eng:cad` でコード生成を実行
```

### templates/spec/circuit-spec.md

```markdown
# 回路設計仕様書

## 基本情報
- **プロジェクト名**: [名称]
- **バージョン**: 1.0
- **作成日**: YYYY-MM-DD
- **ステータス**: Draft | Review | Approved

## 要求仕様

### 機能要件
- [ ] [要件1]

### 電気的仕様
| 項目 | 最小 | 標準 | 最大 | 単位 |
|------|------|------|------|------|
| 入力電圧 | | | | V |
| 出力電圧 | | | | V |
| 消費電流 | | | | mA |

### 部品選定方針
- **抵抗**: サイズ、精度
- **コンデンサ**: 種類、耐圧
- **半導体**: 型番指定 or 汎用

### インターフェース
- **入力**: 
- **出力**: 
- **電源**: 

## シミュレーション要件
- [ ] DC動作点解析
- [ ] AC周波数特性
- [ ] 過渡応答解析

## 出力形式
- [ ] ネットリスト
- [ ] 回路図（SVG）
- [ ] BOM

## 承認
- [ ] **仕様承認済み** - 承認後に `/eng:circuit` でコード生成を実行
```

### templates/spec/integrated-spec.md

```markdown
# 統合設計仕様書

## 基本情報
- **プロジェクト名**: [名称]
- **バージョン**: 1.0
- **作成日**: YYYY-MM-DD

## 機械設計仕様
[mechanical-spec.mdの内容]

## 回路設計仕様
[circuit-spec.mdの内容]

## 基板-筐体インターフェース

| 項目 | 基板側 | 筐体側 | 備考 |
|------|--------|--------|------|
| 基板サイズ | | 内寸 | |
| 取付穴位置 | | ボス | |
| コネクタ | | 開口部 | |

## 干渉チェック
- [ ] 基板と筐体内壁のクリアランス確認
- [ ] コネクタ挿抜スペースの確認
- [ ] 放熱経路の確保

## 承認
- [ ] **仕様承認済み**
```

---

## 依存関係

### Python パッケージ
```
cadquery>=2.4
skidl>=1.2
PySpice>=1.5
schemdraw>=0.22
numpy
matplotlib
```

### システムパッケージ
```bash
# Ubuntu/Debian
sudo apt install openscad ngspice

# macOS
brew install openscad ngspice
```

---

## 使用例

### センサー筐体の設計

```
ユーザー: /eng:spec 温度センサー用の防水筐体を設計して。
         外形は50x30x20mm程度、M3ねじで蓋を固定、ケーブルグランド用の穴が必要

Claude: いくつか確認させてください：
1. 防水等級の目標は？（IP65、IP67など）
2. 蓋固定ねじの本数は？
3. ケーブルグランドの規格は？
4. 3Dプリント用ですか、それとも切削加工用ですか？

ユーザー: IP65相当、ねじ4本、ケーブルグランドPG7、3Dプリント用

Claude: 仕様書を生成しました。
📄 specs/sensor-enclosure-spec.md
承認後、`/eng:cad specs/sensor-enclosure-spec.md` で3Dモデルを生成します。
```

### LEDドライバ回路

```
ユーザー: /eng:spec 5V入力で白色LED（Vf=3.2V、20mA）を3個並列駆動する回路

Claude: 確認事項：
1. LEDは個別に電流制限しますか？
2. シミュレーションは必要ですか？

ユーザー: 個別に電流制限、DC動作点解析だけお願い

Claude: 仕様書を生成しました。
📄 specs/led-driver-spec.md
電流制限抵抗値: (5V - 3.2V) / 20mA = 90Ω → 100Ω（E24系列）
承認後、`/eng:circuit specs/led-driver-spec.md` で回路を生成します。
```

### IoTデバイス統合設計

```
ユーザー: /eng:spec ESP32を使った温湿度センサーデバイスを設計して。
         筐体と回路の両方が必要。USB-C給電、DHT22センサー使用

Claude: 統合設計の仕様を作成します。確認事項：

【筐体関連】
1. 設置方法は？（壁掛け、卓上など）
2. センサー部の露出方法は？

【回路関連】
3. ステータスLEDは必要ですか？
4. リセットボタンは必要ですか？

ユーザー: 壁掛け、通気スリットでセンサー露出、LED1個とリセットボタン

Claude: 統合仕様書を生成しました。
📄 specs/iot-sensor-integrated-spec.md

承認後、以下のコマンドで設計を進めます：
1. `/eng:cad specs/iot-sensor-integrated-spec.md` - 筐体生成
2. `/eng:circuit specs/iot-sensor-integrated-spec.md` - 回路生成
3. `/eng:integrate specs/iot-sensor-integrated-spec.md` - 整合性チェック
```
