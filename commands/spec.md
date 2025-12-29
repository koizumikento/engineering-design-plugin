---
description: ユーザー要望から設計仕様書を生成
---

ユーザーの自然言語要望から設計仕様書を作成します。

## 手順

1. **要望分析**
   - 設計対象の種類を判定（機械/回路/統合）
   - 明示的要件と暗黙的要件を抽出
   - 不明点をリストアップ

2. **対話による明確化**
   不明な場合は質問:
   - 寸法・公差の詳細
   - 材質・部品の選定基準
   - インターフェース仕様
   - 希望する出力形式

3. **仕様書生成**
   - `${CLAUDE_PLUGIN_ROOT}/templates/spec/`のテンプレートを使用
   - 機械設計: `mechanical-spec.md`
   - 回路設計: `circuit-spec.md`
   - 統合設計: `integrated-spec.md`

4. **ファイル出力**
   - `specs/[project-name]-spec.md`に保存
   - ユーザーに確認・承認を依頼

## 仕様書の品質基準

- すべての要件が検証可能（数値化・具体化）
- 曖昧な表現がない（「適切な」「十分な」等を排除）
- 設計制約が明記されている
- 出力形式が指定されている

## 引数

`$ARGUMENTS` にプロジェクト名または要望を指定できます。

## 使用例

```
/engineering-design:spec センサー用防水筐体
/engineering-design:spec LEDドライバ回路
/engineering-design:spec IoTデバイス（筐体+回路）
```
