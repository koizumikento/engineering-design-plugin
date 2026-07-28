# STR-231: CadQueryとbuild123dのエージェント生成精度

- Status: Accepted
- Date: 2026-07-28
- Decision: benchmark単体では優位差なし。後続STR-229で管理単純化を根拠にbuild123dへ統一した
- Linear: [STR-231](https://linear.app/straydev/issue/STR-231/phase-1b-cadqueryとbuild123dのエージェント生成精度を比較する)

## Question

STR-228は、人手で同等モデルを実装した場合にCadQueryとbuild123dが同等のSTEP geometryを生成できることを確認した。STR-231では、同じエージェントが自然言語仕様から生成する場合にbuild123dの成功率が高いかを比較した。

## Method

10仕様を用意し、CadQueryとbuild123dで各3回、合計60件を独立した新規サブエージェントへ割り当てた。

- calibration block: fillet、穴pattern、blind pocket
- bracket: 直交穴、internal fillet、rib
- PCB enclosure: cavity、boss、through hole
- sensor enclosure: body/lid、side port、slot、counterbore
- flange: bolt circle、bore、chamfer
- stepped shaft: coaxial steps、bore、keyway、chamfer
- clevis: parallel arms、cross hole、symmetry
- open enclosure: cavity、standoff、blind hole
- three-part assembly: separate solids、explicit transforms
- modification task: 既存feature保持、hole移動、boss追加

各試行は共通contract、割り当て仕様、同じ構成のengine guide、engine名だけを入力とした。既存実装、他試行、生成結果の参照を禁止し、最初のsource提出前には実行・修正を行わなかった。

評価は生成engineから独立したbuild123d/OCP環境でSTEPを再importし、次を機械判定した。

- valid closed BREPとsolid数
- overall/per-solid bounding boxとvolume
- cylindrical faceのinternal/external、axis、radius、anchor、axial span
- 穴、cavity、slot、keyway、chamfer、rib、standoff、assembly gapのpoint probes
- requirement IDとcheckのcoverage

source、prompt input、rendered taskはSHA-256を記録した。

## Rejected pilot

最初のpilotは採否判断から除外した。

1. build123d guideが`Cylinder(..., align=Align.MIN)`を例示していた。このscalar指定はX/Y/ZすべてをMIN整列し、全円柱軸をX/Yへ半径分ずらした。これはengineの生成精度ではなく共通入力の欠陥だった。
2. clevisはarm幅8 mmにØ8 holeを要求しており、正しく生成しても上端が分離して1 solidにならない仕様だった。
3. rectangularly trimmed cylindrical surfaceで`Face.radius`が`None`になる検査器の欠陥があった。

guideを`align=(Align.CENTER, Align.CENTER, Align.MIN)`へ修正し、clevisを10 mm arm/Ø8 holeへ変更し、trimmed surfaceのbasis cylinderからradiusを取得するよう検査器を修正した。build123d 30件とclevis両engine 6件は、pilot sourceを見ない新規エージェントで再生成した。

pilotの生成物は`outputs/str231-agent-benchmark-pilot/`へ退避し、最終集計へ混入させていない。

## Final results

| Metric | CadQuery | build123d |
|---|---:|---:|
| Trials | 30 | 30 |
| First-run execution | 100% | 100% |
| STEP reimport | 100% | 100% |
| Valid BREP | 100% | 100% |
| Feature checks | 100% | 100% |
| Critical dimensions | 100% | 100% |
| Full specification | 100% | 100% |
| Repair rounds | 0 | 0 |
| Unique source hashes | 30 | 30 |
| Nonblank source lines, total | 1,815 | 1,751 |
| Mean evaluation time | 4.214 s | 4.495 s |

全10仕様で両engineのfull-spec pass rateは100%だった。失敗taxonomyは両engineとも空である。

## Migration gate

事前に定義したbuild123d移行条件は、次のいずれかだった。

- first-run full-spec pass rateがCadQueryより10 percentage points以上高い
- full passまでのrepair roundsが25%以上少ない

加えて、critical dimension等のregressionがなく、少なくとも3カテゴリで改善する必要があった。

実測差はfull-spec 0 points、repair 0%、改善カテゴリ0だったため、gateは未達である。

## Decision

build123dはCadQueryと同等の生成精度を示し、production候補として技術的に成立する。しかし、移行コスト、Python対応範囲、依存分離、既存assetの書換えを正当化する生成精度の改善は確認できなかった。

したがって、単一部品のproduction workflow、root dependency、CadQuery runnerは継続する。STR-229の全面移行はキャンセルする。build123d PoCとbenchmarkは、将来のengine regressionや新しい生成modelで再評価するため保持する。

## Subsequent scoped adoption

STR-232では生成精度ではなく、native label、明示的な`Location`/`Axis`、source-level jointというアセンブリ表現上の利点を採用根拠とした。単一部品はCadQuery、named datum・transform・jointで部品関係を表すアセンブリは隔離build123d runtimeへrouteする。詳細は[STR-232 decision](STR-232-assembly-routing.md)を参照する。

この用途別routingは二重管理になるため、ユーザー判断でsupersedeされた。最終production方針は[STR-229 decision](STR-229-build123d-unification.md)のbuild123d単一基盤である。

`text-to-cad`から得たspec-driven inspection、source/prompt hash、neutral STEP check、snapshot gateの考え方はengine移行と分離して採用できる。

## Limitations

- Codex hostがexact model build、trial別token usage、agent generation wall timeを公開しないため、これらは`NOT_EVALUATED`である。
- 詳細仕様と短いengine guideを与えたため両engineがceilingへ達した。曖昧な要求、長い会話、未知featureでの一般的な優劣までは主張しない。
- evaluation timeはsource実行とneutral inspectionの合計で、agent generation時間ではない。
- FEA、manufacturability、IP rating、規格適合性は対象外である。

## Evidence

- `pocs/build123d-migration/benchmark/manifest.json`
- `pocs/build123d-migration/benchmark/specs/`
- `pocs/build123d-migration/benchmark/trials/`
- `pocs/build123d-migration/benchmark/results/summary.json`
- `pocs/build123d-migration/benchmark/results/trials.json`
- `outputs/str231-agent-benchmark/report.md`
