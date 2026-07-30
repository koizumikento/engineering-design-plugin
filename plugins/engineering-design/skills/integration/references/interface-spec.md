# PCB・筐体インターフェース設計

## 目次

1. チェックの限界
2. 座標系とデータム
3. Interface Control Table
4. 許容差とマージン
5. 形状・取付・開口
6. 動的・組立・保守エンベロープ
7. 熱・EMC・防塵防水
8. 検証とレポート
9. 公式資料

## 1. チェックの限界

`scripts/integration_checker.py` はMarkdownに記載された外形、厚さ、ボス、最大部品高などを比較するスクリーニングツールである。次は単独では証明できない。

- 任意形状同士の最小距離または干渉
- コネクタの挿抜軌跡、ラッチ、指・工具アクセス
- ケーブル曲げ、可動部、組立経路
- PCB反り、筐体変形、熱膨張を含む最悪公差
- 放熱、EMC/ESD、耐振動、防塵防水性能

不足データや未対応項目を `PASS` に変換しない。STEP/BREP/PCB 3Dデータがある場合は共通座標系に配置して追加確認する。

## 2. 座標系とデータム

統合前に次を固定する。

- assembly frame: 原点、+X/+Y/+Z、単位
- PCB frame: 基板原点、上面/下面、部品面、厚さ方向
- enclosure frame: 底面、中心面、合わせ面、開口基準面
- transform: PCB frameからassembly frameへの平行移動・回転
- handedness: 右手系/左手系
- revision: 各モデル・図面の版

座標値はフレーム名と組で記載する。

```markdown
assembly frame: enclosure bottom inner face center; +Z toward lid; mm
PCB transform: translation (0, 0, 6.6), rotation (0, 0, 0 deg)
PCB mounting holes in PCB frame: (-22, -12), (22, -12), (-22, 12), (22, 12)
```

## 3. Interface Control Table

```markdown
| ID | interface | owner A | owner B | source/rev | frame/datum | nominal | tolerance | required margin | verification |
|---|---|---|---|---|---|---|---|---|---|
| IF-MNT-001 | PCB hole to boss | EE | ME | PCB-A/r3, ENC-A/r2 | assembly/A | coordinates | hole/boss position tolerances | radial clearance | CAD + inspection |
```

所有者を分けることで、PCB変更か筐体変更か、どちらが追従すべきかを明確にする。

## 4. 許容差とマージン

クリアランスは単一の経験値ではなく、最悪条件で評価する。

```text
available gap = enclosure boundary - transformed component envelope
worst-case margin = nominal gap - enclosure tolerance - PCB tolerance
                    - placement tolerance - component envelope tolerance
                    - deformation/thermal allowance
```

RSSなどの統計合成を使う場合は、分布と独立性の根拠を記録する。安全、干渉、シールなど境界超過を許容できない項目は、根拠なく統計合成へ置き換えない。

基準値の優先順位:

1. 承認済みインターフェース要求
2. 相手部品のメーカー図面/3Dモデル
3. 採用製造工程の能力・設計ガイド
4. 適用規格
5. 明記した暫定仮定

## 5. 形状・取付・開口

### PCB外形

- 直交外形だけでなく切欠き、面取り、タブ、レール挿入経路を確認する。
- PCB厚は公称値だけでなく許容差、銅/実装、局所突起を確認する。
- エッジコネクタやアンテナ領域は専用keep-outとして扱う。

### 取付

- 穴径、めっき有無、ボス外径、座面、ねじ頭、ワッシャ、インサートを含める。
- PCB穴とボス中心の単純一致だけでなく、穴径差と位置公差から組立可能性を評価する。
- ねじ長、かかり代、底付き、基板圧縮、絶縁距離、締付工具アクセスを確認する。
- 位置決め機能と締結機能を区別する。全締結点を過拘束にしない。

### コネクタ開口

型式名だけで開口を決めない。採用コネクタと相手プラグの図面から次を取る。

- receptacle datumと基板位置
- shell/latch最大包絡
- プラグ挿抜方向とストローク
- 開口の板厚方向形状、面取り、R
- 指、工具、ケーブル、ストレインリリーフのエンベロープ
- PCB/部品/筐体の累積公差

USB-Cなどの規格上のインターフェース形状と、特定コネクタの実装高さ・外形・推奨開口は同一ではない。必ず採用部品のメーカー資料を使う。

### 高さ

上面と下面を別に確認する。`最大部品高` 1値だけでは、局所的な蓋リブ、ボス、ねじ、ヒートシンクとの干渉を見落とす。

```text
component top Z = PCB seating Z + PCB thickness + placed component top envelope
component bottom Z = PCB seating Z - bottom-side component envelope
```

## 6. 動的・組立・保守エンベロープ

- プラグ挿抜、スイッチ/ボタン操作、表示視野
- ケーブル最小曲げ半径、引張、ストレインリリーフ
- アンテナkeep-out、センサー露出、通気流路
- 蓋の開閉、スナップ変形、ガスケット圧縮
- ドライバー、レンチ、ピック&プレース、はんだごてアクセス
- 部品交換、再作業、清掃、点検

静止状態で非干渉でも、組立不能なら不合格である。

## 7. 熱・EMC・防塵防水

### 熱

発熱量だけで対策を固定しない。損失、許容接合温度、周囲温度、熱抵抗、接触、放射/対流、姿勢、通気阻害をモデルまたは試験条件として定義する。

### EMC/ESD

コネクタ入口、シールド/シャーシ接続、リターン経路、筐体継目、ケーブル、保護部品配置を回路・PCB・筐体の共同インターフェースとして扱う。形状確認だけで適合を主張しない。

### 防塵防水

シール面、ガスケット/Oリング、締結間隔、圧縮、表面状態、ベント、コネクタ、ケーブルグランド、排水を一つの封止系として追跡する。IPコードは設計特徴ではなく、規定条件の試験で確認する保護等級である。

2026年1月にJIS C 0920:2003は廃止され、移行先はJIS C 60529:2026となった。要求には適用版と試験条件を明記する。

## 8. 検証とレポート

結果の状態:

- PASS: 根拠と合格基準を満たす
- FAIL: 基準を満たさない
- CONDITIONAL: 仮定または暫定データの下で満たす
- NOT EVALUATED: データ、ツール、方法が不足

レポートには次を含める。

- 入力ファイル、出典、revision
- 座標系とtransform
- 各要求ID、判定、最小マージン
- 使用した公差・仮定
- スクリーニングと3D/試験の区別
- 未評価項目と必要な次の証拠
- 修正候補と所有者

## 9. 公式資料

- [NASA Systems Engineering Handbook Rev. 2](https://ntrs.nasa.gov/api/citations/20170001761/downloads/20170001761.pdf) — interface management、interface requirements document、verification matrix。
- [JIS C 60529:2026（日本規格協会）](https://webdesk.jsa.or.jp/books/W11M0090/?bunsyo_id=JIS+C+60529%3A2026) — 現行のIPコードJIS。
- [JIS C 0920:2003（廃止・移行先表示）](https://webdesk.jsa.or.jp/books/W11M0090/index/?bunsyo_id=JIS+C+0920%3A2003) — 2026年廃止とJIS C 60529への移行記録。
- [IEC 60529 consolidated edition 2.2](https://webstore.iec.ch/en/publication/2452) — 国際規格の公式カタログ情報。
