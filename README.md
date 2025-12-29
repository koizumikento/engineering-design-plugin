# Engineering Design Plugin

機械製図・3Dモデリングと電子回路設計を統合したClaude Codeプラグイン。
自然言語要望から仕様書（Markdown）を生成し、CadQuery/SKiDLコードを自動生成します。

## 特徴

- **自然言語から設計**: 要望を伝えるだけで仕様書を自動生成
- **機械設計**: CadQueryによる3D CADモデル生成（STEP/STL）
- **回路設計**: SKiDLによる回路設計（ネットリスト/BOM）
- **統合設計**: 基板と筐体の整合性チェック
- **シミュレーション**: PySpiceによるSPICE回路シミュレーション

## インストール

### 前提条件

- Python 3.9以上
- Claude Code

### Python依存関係

```bash
pip install cadquery skidl PySpice schemdraw numpy matplotlib numpy-stl
```

### システム依存関係

```bash
# macOS
brew install openscad ngspice

# Ubuntu/Debian
sudo apt install openscad ngspice
```

### プラグインのインストール

#### 方法1: GitHubから直接インストール（推奨）

Claude Code内で以下のコマンドを実行します：

```
/plugin marketplace add https://github.com/koizumikento/engineering-design-plugin.git
```

マーケットプレースが追加されたら、プラグインをインストールします：

```
/plugin install engineering-design
```

#### 方法2: ローカルにクローンしてインストール

```bash
# リポジトリをクローン
git clone https://github.com/koizumikento/engineering-design-plugin.git

# Claude Codeでプラグインディレクトリを指定
cd engineering-design-plugin
```

Claude Code内でローカルマーケットプレースとして追加：

```
/plugin marketplace add ./engineering-design-plugin
/plugin install engineering-design
```

#### インストールの確認

```
/plugin list
```

インストール済みプラグインに `engineering-design` が表示されれば成功です。

## 使用方法

### コマンド一覧

| コマンド | 説明 |
|---------|------|
| `/engineering-design:spec` | 仕様書を生成 |
| `/engineering-design:cad` | CadQueryコードを生成・実行 |
| `/engineering-design:circuit` | SKiDLコードを生成・実行 |
| `/engineering-design:simulate` | SPICEシミュレーション |
| `/engineering-design:schematic` | 回路図を生成 |
| `/engineering-design:preview` | 3Dプレビューを生成 |
| `/engineering-design:integrate` | 統合設計チェック |

### ワークフロー

#### 機械設計

```
1. /engineering-design:spec 温度センサー用の防水筐体を設計して
2. (仕様書を確認・承認)
3. /engineering-design:cad specs/sensor-enclosure-spec.md
4. /engineering-design:preview outputs/sensor-enclosure.step
```

#### 回路設計

```
1. /engineering-design:spec 5VでLED3個を駆動する回路
2. (仕様書を確認・承認)
3. /engineering-design:circuit specs/led-driver-spec.md
4. /engineering-design:simulate src/led_driver.py --dc
5. /engineering-design:schematic src/led_driver.py
```

#### 統合設計（筐体+回路）

```
1. /engineering-design:spec ESP32を使った温湿度センサーデバイス
2. (統合仕様書を確認・承認)
3. /engineering-design:cad specs/iot-device-integrated-spec.md
4. /engineering-design:circuit specs/iot-device-integrated-spec.md
5. /engineering-design:integrate specs/iot-device-integrated-spec.md
```

## ディレクトリ構造

```
engineering-design-plugin/
├── .claude-plugin/
│   └── plugin.json          # プラグイン設定
├── commands/                 # スラッシュコマンド
├── skills/                   # スキル定義
│   ├── spec-writing/        # 仕様書作成
│   ├── mechanical-cad/      # 機械設計
│   ├── circuit-design/      # 回路設計
│   └── integration/         # 統合設計
├── hooks/                    # フック設定
├── scripts/                  # 実行スクリプト
├── templates/                # テンプレート
│   ├── spec/                # 仕様書テンプレート
│   ├── mechanical/          # 機械設計テンプレート
│   └── circuit/             # 回路テンプレート
└── examples/                 # サンプルプロジェクト
    ├── sensor-enclosure/    # センサー筐体
    ├── led-driver/          # LEDドライバ
    └── iot-device/          # IoTデバイス
```

## サンプルプロジェクト

### sensor-enclosure

温度センサー用の防水筐体（IP65相当）

```bash
cd examples/sensor-enclosure
python3 src/enclosure.py
```

### led-driver

5V入力でLED3個を並列駆動する回路

```bash
cd examples/led-driver
python3 src/led_driver.py
```

### iot-device

ESP32を使った温湿度センサーデバイス（筐体+回路の統合設計）

```bash
cd examples/iot-device
python3 src/enclosure.py
python3 src/circuit.py
```

## スキル

プラグインは以下のスキルを自動的に使用します：

- **spec-writing**: 自然言語から仕様書を生成
- **mechanical-cad**: CadQueryによる3Dモデル生成
- **circuit-design**: SKiDLによる回路設計
- **integration**: 基板-筐体の整合性チェック

## リファレンス

- `skills/mechanical-cad/refs/cadquery-api.md` - CadQuery APIリファレンス
- `skills/mechanical-cad/refs/jis-drawing.md` - JIS製図規格
- `skills/circuit-design/refs/skidl-api.md` - SKiDL APIリファレンス
- `skills/circuit-design/refs/circuit-patterns.md` - 回路パターン集
- `skills/circuit-design/refs/spice-guide.md` - SPICEシミュレーションガイド

## ライセンス

MIT License

## 作者

Koizumi
