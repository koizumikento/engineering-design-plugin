# 組立・位置決め・エンベロープ

## 基準を先に定義する

- assembly originと軸方向
- 各part origin
- primary/secondary/tertiary datum
- mating/seating plane
- locating featureとfastening feature
- transformとrevision

部品を固定する機能と位置決めする機能を分ける。複数の剛体拘束で過拘束にすると、公差内でも組み立たない場合がある。

## 座標変換

インターフェース座標は部品ローカル値のまま比較しない。

```text
point_assembly = transform_part_to_assembly(point_part)
```

回転、反転、基板上下面、ミラーを含めて確認する。build123dではpart-local datumを `Location` / `Axis` とnamed jointで表し、fixed/root側のjointからmoving側へ `connect_to()` する。単純な静的配置では明示的な`Location`を一箇所で構成し、穴・開口・component envelopeへ同じ変換を適用する。

## 許容差スタック

nominal clearanceだけでなく、境界を縮める寄与を列挙する。

```text
worst_case_margin = nominal_gap
                  - part_A_size_tolerance
                  - part_B_size_tolerance
                  - locating_tolerance
                  - assembly_shift
                  - deformation_or_thermal_allowance
```

統計合成は分布・独立性・許容不良率の根拠がある場合だけ使う。干渉、シール、安全境界は根拠なくRSSへ変更しない。

## エンベロープ

- static envelope: 最大外形
- keep-out: 接触禁止領域
- swept envelope: 可動・挿抜軌跡
- service envelope: 指、工具、測定プローブ、交換作業
- cable envelope: 曲げ半径、strain relief、引き抜き
- thermal envelope: 熱膨張、断熱/放熱空間

単純なbounding boxは初期スクリーニングに使えるが、非直交形状や挿入経路の最終判定には不足する。

## PCB収納

- PCB outline、切欠き、厚さ、反り
- 取付穴と座面、ねじ頭、ワッシャ、インサート
- top/bottom component envelopes
- connector receptacle、mating plug、latch、cable
- antenna/sensor/vent keep-out
- lid ribs、boss、fastener、seamとの局所干渉
- assembly orderとrework access

統合仕様の要求IDをbuild123dのパラメータ名・コメントに結び、後でレポートへ追跡できるようにする。

## Verification

- transformとdatumを表でレビュー
- CAD内のcontainment/overlap/minimum-distance確認
- 重要寸法の独立計測
- 最悪公差計算
- 組立順序のdemonstration
- 初品または治具によるtest/inspection

build123dのsource-level jointは[Joints](https://build123d.readthedocs.io/en/latest/joints.html)を参照する。実装と実行方法は`references/build123d-api.md`に従う。
