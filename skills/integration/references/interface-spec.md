# 基板-筐体インターフェース仕様

## 概要

基板（PCB）と筐体を統合する際のインターフェース設計ガイドです。

---

## 1. 基板外形と筐体内寸

### 基本ルール

```
筐体内寸 = 基板外形 + クリアランス × 2

例：
基板: 50 × 30mm
クリアランス: 2mm
筐体内寸: 54 × 34mm
```

### クリアランス設計

| 製造方法 | 最小クリアランス | 推奨クリアランス |
|---------|-----------------|-----------------|
| 3Dプリント（FDM） | 1.5mm | 2.0mm |
| 3Dプリント（SLA） | 1.0mm | 1.5mm |
| 射出成形 | 0.5mm | 1.0mm |
| 板金 | 1.0mm | 1.5mm |

### 基板の傾き考慮

```
対角線長 = √(W² + H²)
必要クリアランス ≥ (対角線長 - W) / 2

例：50×30mm基板
対角線 = √(50² + 30²) = 58.3mm
傾き考慮 = (58.3 - 50) / 2 = 4.15mm
```

---

## 2. 取付穴設計

### 基板側の穴配置

```
推奨位置：各コーナーから3〜5mm内側
穴径：M3 → φ3.2mm、M2.5 → φ2.7mm、M2 → φ2.2mm

例（50×30mm基板）：
穴位置：(3, 3), (47, 3), (3, 27), (47, 27)
```

### 筐体側のボス設計

| ねじ | ボス外径 | ボス内径（タップ下穴） | ボス高さ |
|------|---------|---------------------|---------|
| M2 | 4.0mm | 1.6mm | 4〜6mm |
| M2.5 | 5.0mm | 2.1mm | 5〜8mm |
| M3 | 6.0mm | 2.5mm | 6〜10mm |

### CadQueryでのボス実装

```python
import cadquery as cq

def add_pcb_bosses(body, pcb_width, pcb_depth, hole_offset, boss_height, boss_od, tap_hole):
    """基板取付ボスを追加"""
    positions = [
        (hole_offset - pcb_width/2, hole_offset - pcb_depth/2),
        (pcb_width/2 - hole_offset, hole_offset - pcb_depth/2),
        (hole_offset - pcb_width/2, pcb_depth/2 - hole_offset),
        (pcb_width/2 - hole_offset, pcb_depth/2 - hole_offset),
    ]

    for x, y in positions:
        boss = (
            cq.Workplane("XY")
            .workplane(offset=wall_thickness)
            .center(x, y)
            .circle(boss_od / 2)
            .extrude(boss_height)
            .faces(">Z").workplane()
            .hole(tap_hole)
        )
        body = body.union(boss)

    return body
```

---

## 3. コネクタ開口部

### コネクタ寸法と開口部

| コネクタ | コネクタ寸法 | 開口部寸法 | 備考 |
|---------|------------|-----------|------|
| USB-A | 12.0×4.5mm | 13.0×5.5mm | 上下左右0.5mm |
| USB-C | 8.9×3.2mm | 10.0×4.0mm | 挿抜考慮 |
| microUSB | 7.5×2.7mm | 8.5×3.5mm | |
| φ3.5ジャック | φ6.0mm | φ7.0mm | |
| DC端子φ5.5 | φ8.0mm | φ9.0mm | |
| RJ45 | 16.0×13.5mm | 17.0×14.5mm | |

### 開口部の位置合わせ

```
開口中心 = 基板原点 + コネクタオフセット

例：
基板原点（筐体中心から）: (-25, -15)
コネクタ位置（基板上）: (25, 0)  # 右端中央
開口中心: (0, -15)

高さ:
基板下面高さ = ボス高さ
コネクタ中心高さ = 基板下面高さ + 基板厚 + コネクタ高さ/2
```

### CadQueryでの開口部実装

```python
import cadquery as cq

def add_connector_opening(body, face_selector, position, width, height, fillet=1.0):
    """コネクタ開口部を追加"""
    opening = (
        body
        .faces(face_selector).workplane(centerOption="CenterOfMass")
        .center(position[0], position[1])
        .rect(width, height)
        .cutThruAll()
    )

    if fillet > 0:
        # 開口部エッジにフィレット
        pass  # 選択が複雑なため省略

    return opening
```

---

## 4. 部品高さと内部空間

### 高さ計算

```
必要内部高さ = ボス高さ + 基板厚 + 最大部品高 + クリアランス

例：
ボス高さ: 5mm
基板厚: 1.6mm
最大部品高: 12mm（電解コンデンサ）
クリアランス: 2mm
必要内部高さ: 20.6mm → 21mm
```

### よくある部品高さ

| 部品 | 高さ | 備考 |
|------|------|------|
| 0603チップ部品 | 0.5mm | |
| 0805チップ部品 | 0.7mm | |
| SOICパッケージ | 1.75mm | |
| DIP-8 | 4.0mm | |
| 電解コンデンサφ6.3 | 11mm | |
| USB-Cコネクタ | 3.2mm | |
| タクトスイッチ | 3.5〜5.0mm | |

---

## 5. 放熱設計

### 通気口

```python
def add_ventilation_slots(body, face, slot_width=2, slot_length=15, spacing=4, count=5):
    """通気スリットを追加"""
    result = body
    for i in range(count):
        offset = (i - (count-1)/2) * spacing
        result = (
            result
            .faces(face).workplane()
            .center(0, offset)
            .slot2D(slot_length, slot_width)
            .cutThruAll()
        )
    return result
```

### ヒートシンク取付

| 発熱量 | 対策 |
|--------|------|
| < 0.5W | 自然対流（通気口） |
| 0.5〜2W | ヒートシンク + 通気口 |
| > 2W | 強制空冷（ファン） |

---

## 6. 防水設計

### パッキン溝

```
Oリング溝寸法（JIS B 2401）:
溝幅 = 線径 × 1.3〜1.4
溝深さ = 線径 × 0.7〜0.8

例（P10 Oリング、線径2.4mm）:
溝幅: 3.1〜3.4mm
溝深さ: 1.7〜1.9mm
```

### ケーブルグランド

| 規格 | ケーブル径 | 取付穴径 |
|------|-----------|---------|
| PG7 | 3〜6.5mm | 12.5mm |
| PG9 | 4〜8mm | 15.2mm |
| PG11 | 5〜10mm | 18.6mm |
| M12 | 3〜6.5mm | 12.0mm |
| M16 | 5〜10mm | 16.0mm |

---

## 7. チェックリスト

### 設計完了チェック

- [ ] 基板サイズ + クリアランス ≤ 筐体内寸
- [ ] 取付穴位置が一致（±0.5mm）
- [ ] コネクタ開口部の位置・サイズが適切
- [ ] 部品高さ + クリアランス ≤ 内部高さ
- [ ] 放熱経路が確保されている
- [ ] ケーブル引き出し部が考慮されている

### 製造チェック

- [ ] 最小肉厚を満たしている
- [ ] アンダーカットがない（または分割可能）
- [ ] 抜き勾配がある（射出成形の場合）
- [ ] 組立手順が明確

---

## 8. 統合仕様書テンプレート

```markdown
## 基板-筐体インターフェース

### 基板情報
- 外形: W × H mm
- 厚さ: mm
- 取付穴: Mx × N箇所
- 穴位置: (x1, y1), (x2, y2), ...

### 筐体情報
- 内寸: W × H × D mm
- ボス位置: (x1, y1), (x2, y2), ...
- ボス高さ: mm

### コネクタ
| 名称 | 基板位置 | 開口位置 | サイズ |
|------|---------|---------|--------|
| USB-C | | | |

### 部品高さ
- 最大部品高: mm
- 部品名: xxx
- 位置: (x, y)

### チェック結果
- [ ] クリアランス: OK / NG
- [ ] 取付穴: OK / NG
- [ ] コネクタ開口: OK / NG
- [ ] 高さ: OK / NG
```
