# 既製部品CAD・図面の扱い

## Source priority

1. メーカー公式CADと寸法図
2. メーカー公式datasheet/product page
3. 採用代理店がメーカー提供物として明示するCAD
4. 規格品の適用規格と購入仕様
5. 実測
6. 暫定envelope

型式なしの一般名だけで精密な開口、嵌合、穴、熱設計を確定しない。

## Provenance record

- manufacturer / exact MPN
- document or CAD title
- revision/date and retrieval date
- source URL or controlled file path
- units and coordinate convention
- license/use restriction if stated
- used dimensions and simplifications
- mismatch between CAD, drawing, and sample if found

## Model strategy

- 統合確認に必要な外形、datum、mounting、mating、keep-outを優先する。
- ネジ山、ロゴ、微細外観など解析不要のdetailを抑える。
- メーカーCADの原点・向きをそのまま信用せず、drawing datumと照合する。
- geometryを簡略化しても、最大包絡と機能面は縮めない。
- connectorはreceptacleだけでなくmating plug、latch、cable/service envelopeを持つ。

## Missing data

暫定モデルには `PROVISIONAL`、根拠、最大包絡、未確認項目を記載する。暫定値から規格適合、公差、強度、寿命を主張しない。
