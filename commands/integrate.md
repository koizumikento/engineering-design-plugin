---
description: 機械・回路の統合設計・整合性チェック
---

機械設計と回路設計の整合性をチェックします。

## 前提条件

- 統合仕様書（`specs/*-integrated-spec.md`）が存在すること
- 機械設計と回路設計が完了していること

## 手順

1. **仕様書の統合**
   - 機械設計仕様書と回路設計仕様書を読み込み
   - 基板-筐体インターフェース情報を抽出

2. **整合性チェック**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/integration_checker.py specs/integrated-spec.md
   ```
   - 基板外形と筐体内寸の適合性
   - コネクタ位置と開口部位置の一致
   - 取付穴位置の整合

3. **干渉検出**
   - 基板と筐体内壁のクリアランス
   - 部品高さと筐体高さの確認
   - コネクタ挿抜スペースの確認

4. **レポート出力**
   - `outputs/[project-name]-integration-report.md`

## 引数

`$ARGUMENTS` に統合仕様書のパスを指定できます。

## 使用例

```
/engineering-design:integrate specs/iot-device-integrated-spec.md
/engineering-design:integrate
```

## チェック項目

| 項目 | 基板側 | 筐体側 | チェック内容 |
|------|--------|--------|-------------|
| 基板サイズ | WxHmm | 内寸W+4xH+4mm | クリアランス確保 |
| 取付穴 | M2.5×4箇所 | ボス高5mm | 位置一致 |
| コネクタ | 側面配置 | 開口位置 | 位置・サイズ一致 |
| 部品高さ | 最大高 | 内部高さ | 干渉なし |
