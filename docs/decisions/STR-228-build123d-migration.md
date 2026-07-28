# STR-228: CadQueryからbuild123dへの移行判断

- Status: Accepted — resolved by STR-231
- Date: 2026-07-28
- Decision: build123dの技術PoCは合格。生成精度差はなかったが、後続STR-229で管理単純化を優先して全面統一した
- Linear: [STR-228](https://linear.app/straydev/issue/STR-228/phase-1-build123d移行pocと採否判定を行う)
- Follow-up: [STR-231](https://linear.app/straydev/issue/STR-231/phase-1b-cadqueryとbuild123dのエージェント生成精度を比較する)
- Final benchmark: [STR-231 decision](STR-231-agent-generation-benchmark.md)
- Scoped adoption: [STR-232 decision](STR-232-assembly-routing.md)
- Final production decision: [STR-229 decision](STR-229-build123d-unification.md)

## Context

`engineering-design-plugin`の機械CAD基盤はCadQuery Pythonをパラメトリック定義、STEPを中立形状交換の一次成果物としている。build123dのBuilder/Algebra API、明示的なShape/Location、型情報が、エージェント生成コードの保守性と安定性を改善するかを確認した。

評価は`pocs/build123d-migration/`に隔離し、productionの依存とworkflowは変更していない。CadQueryとbuild123dは異なるOCP distributionを要求するため、それぞれroot環境とPoC専用環境で実行し、export後のSTEPをbuild123d 0.11.1 / OCP 7.9.3.1.1で同一条件検査した。

## Existing baseline

現在のlockで既存4モデルをそのまま再実行した結果:

| Model | Result | Observation |
|---|---|---|
| calibration block | PASS | valid STEPを生成 |
| bracket template | FAIL | `Fillets requires that edges be selected` |
| PCB enclosure template | PASS with defect | validだが5 solids。4本のbossがfloorから浮いている |
| sensor enclosure | FAIL | `Fillets requires that edges be selected` |

bracketとsensor enclosureの失敗は文字列/連鎖selectorが現在の形状topologyで対象edgeを返さないこと、PCB enclosureの複数solidはbossのZ datumがfloorと接続していないことが原因である。これは既存資産の修正対象だが、CAD engine移行を必須にする証拠ではない。

## PoC method

次の4モデルについて、同じ寸法とdatumを持つ修正版CadQueryモデルとbuild123dモデルを実装した。

1. calibration block
2. L-bracket
3. PCB enclosure
4. sensor enclosure body/lid

各engineでSTEP/STLを生成し、STEPを再importして次を比較した。

- BREP validity
- bounding box
- volume
- solids/faces/edges/vertices
- 仕様上重要な円筒面の軸、半径、位置
- source code metrics
- 同一入力2回のgeometry report一致
- iso/front/top/right preview

## Results

| Model | Geometry checks | Volume delta | CadQuery / build123d code lines |
|---|---|---:|---:|
| calibration block | PASS | 0.0000% | 32 / 34 |
| bracket | PASS | 0.0000% | 58 / 67 |
| PCB enclosure | PASS | 0.0000% | 75 / 75 |
| sensor enclosure | PASS | 0.0179% | 113 / 139 |

- 両engineの全モデルがexpected bbox、solid数、穴径・穴位置などの検査を通過した。
- face/edge/vertex数は全モデルで一致した。
- 2回の生成で両engineのbbox、volume、area、center、topology、cylinder factsが一致した。
- 4視点previewをレビューし、engine間の視覚的な意味差は確認されなかった。
- build123d版は比較モデルから文字列selectorを除去できた。
- build123d版はCadQuery版より6〜23%多いsource codeを必要とした。
- 同じcold-process方式の複数回実行では、build123dの平均生成時間がCadQueryより約22〜48%長かった。最終記録はCadQuery 1.89秒、build123d 2.79秒で約48%差だった。この値は4モデル、Apple Silicon、Python 3.11.11でのPoC値であり、一般benchmarkではない。
- build123d専用lockは49 packages、ローカル環境は約516 MBだった。root環境との容量比較は、rootが回路・preview依存も含むため判断材料にしない。
- build123d 0.11.1はPython 3.10以上を要求する。PoCは3.11.11へ固定したため、productionの`>=3.9,<3.14`より対応範囲が狭い。

Reproduce:

```bash
uv sync
uv sync --project pocs/build123d-migration
uv run python pocs/build123d-migration/scripts/run.py
uv run python -m unittest tests.test_build123d_migration_poc
```

Generated evidence:

- `outputs/build123d-migration-poc/comparison.json`
- `outputs/build123d-migration-poc/comparison.md`
- `outputs/build123d-migration-poc/repeatability.json`
- `outputs/build123d-migration-poc/timings.json`
- `outputs/build123d-migration-poc/legacy/summary.json`
- `outputs/build123d-migration-poc/previews/`

`outputs/`は生成物でありcommitしない。

## Decision

build123dは同等のSTEP geometryを生成でき、明示的なAPIで文字列selector依存を減らせる。これにより、build123dをproduction候補として扱える技術的な成立性は確認できた。

一方、このPoCで比較したのは人手で同等になるよう実装したモデルであり、自然言語仕様からエージェントがコードを生成する成功率は測定していない。source code量、cold-process時間、Python対応範囲だけでは、ユーザーが重視する生成精度の優劣を決定できない。したがって、CadQuery継続を最終決定とはせず、STR-231の生成精度benchmarkまでproduction engineの採否を保留する。

STR-231では、同一条件で各engine・各仕様を複数回生成し、first-runの仕様完全合格率、valid BREP、STEP再import、重要寸法、修復回数、失敗種別、試行間ばらつきを比較する。build123d移行の主なgateは次のとおりとする。

1. first-runの仕様完全合格率がCadQueryより10 percentage points以上高い、または平均修復回数が25%以上少ない。
2. critical dimension、valid BREP、STEP再importに重大なregressionがない。
3. 少なくとも3つの形状カテゴリで改善が再現する。
4. engineごとの追加ヒント、prompt leakage、事前の手修正なしで差が確認できる。
5. 速度、依存、Python対応範囲のtrade-offを含めてもproduction移行の便益が上回る。

STR-231では10仕様、各engine 3回、合計60件を独立生成した。修正版の最終runは両engineとも次の結果だった。

| Metric | CadQuery | build123d |
|---|---:|---:|
| first-run execution | 30/30 | 30/30 |
| valid BREP | 30/30 | 30/30 |
| STEP再import | 30/30 | 30/30 |
| first-run full specification | 30/30 | 30/30 |
| repair rounds | 0 | 0 |

生成精度差は0 percentage points、repair差も0で、3カテゴリ以上の改善もなかった。build123dの全面migration gateは未達である。したがって単一部品のproduction workflowはCadQueryを継続し、STR-229は実施しない。

そのほか、以下はengineの最終採否と独立して採用する。

1. build123d PoCは回帰比較と再評価のため隔離状態で保持する。
2. `text-to-cad`からはspec-driven inspection、snapshot gate、source hash、runtime/export metadataの考え方を採用候補とする。
3. 既存bracket/sensor selectorとPCB enclosure boss datumは、現行CadQuery資産の個別修正として扱う。
4. STR-232により、named datum、明示transform、jointを必要とするアセンブリだけはbuild123d production routeへ送る。

## Consequences

- STR-229はmigration gate未達としてキャンセルする。
- STR-228/STR-231時点では`skills/mechanical-cad/SKILL.md`、root `pyproject.toml`、root `uv.lock`を変更しない。後続STR-232はskillへ用途別routingを追加するが、root依存は変更しない。
- PoC環境はproduction runtimeへ暗黙に取り込まない。
- 検証・provenance改善はCAD engineに依存しない変更として別途扱える。
- sensor enclosure仕様の「IP65相当」はPoC形状から立証しておらず、production readinessの根拠にしない。

## Sources

- [build123d documentation](https://build123d.readthedocs.io/)
- [CadQuery documentation](https://cadquery.readthedocs.io/)
- [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad)
- [text-to-cad inspection and validation](https://github.com/earthtojake/text-to-cad/blob/main/skills/cad/references/inspection-and-validation.md)
- [text-to-cad snapshot review](https://github.com/earthtojake/text-to-cad/blob/main/skills/cad/references/snapshot-review.md)
