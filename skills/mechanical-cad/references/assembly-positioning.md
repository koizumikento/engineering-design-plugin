# 組立・位置決め・データム

## 基本方針

複数部品、基板収納、コネクタ開口、嵌合部を扱う場合は、個々の形状を作る前に基準を決める。寸法を直接散らさず、part-local datum、mating plane、clearance envelope、mounting pattern を名前付きパラメータにする。

## 定義する基準

- assembly origin: 組立全体の原点
- part origin: 各部品の原点
- datum plane: XY / YZ / XZ のどの面を基準にするか
- mating plane: 蓋、底板、ブラケット、基板などの合わせ面
- mounting pattern: 取付穴の中心座標、穴径、ざぐり/皿穴の有無
- clearance envelope: 部品外形、可動範囲、ケーブル余長、工具アクセス範囲

## PCB収納の確認項目

- PCB外形と筐体内寸
- PCB取付穴とボス位置
- コネクタ位置と筐体開口
- 部品高さと蓋/壁のクリアランス
- ケーブルやスイッチ操作に必要な空間

## CadQueryでの書き方

```python
pcb_width = 50.0
pcb_depth = 30.0
pcb_clearance = 2.0
wall = 2.0

inner_width = pcb_width + 2 * pcb_clearance
inner_depth = pcb_depth + 2 * pcb_clearance
outer_width = inner_width + 2 * wall
outer_depth = inner_depth + 2 * wall

pcb_mount_offset_x = pcb_width / 2 - 3.0
pcb_mount_offset_y = pcb_depth / 2 - 3.0
mount_points = [
    (pcb_mount_offset_x, pcb_mount_offset_y),
    (-pcb_mount_offset_x, pcb_mount_offset_y),
    (pcb_mount_offset_x, -pcb_mount_offset_y),
    (-pcb_mount_offset_x, -pcb_mount_offset_y),
]
```

## 統合設計との接続

`integration` スキルに渡す可能性がある寸法は、変数名やコメントで追跡できるようにする。特にPCB外形、取付穴、コネクタ開口、部品高さ、蓋とのクリアランスは、仕様書の項目名と対応させる。
