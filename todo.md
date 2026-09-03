# todo.md — 한 일 / 할 일

## 한 일

- **권위 파일은 `rules.md` + `todo.md` 두 개뿐이다.** 세션 복구/이어가기는 `rules.md` → `todo.md`만 읽는다.
- `rules.md`에 4축 의미, semantic invariant, semantic gate 불변성, 주기적 STANDARDIZATION CYCLE을 고정했다.
- **Core 축 `src/core/chart` 1차 표준화 완료.**
  - JMA/SMA/EMA feature 계산을 Core에서 제거하고 Add-on-owned `src/addons/indicator/math/`로 내용 변경 없이 이동했다.
  - 기존 generic `ChartAddonSurface`, `ChartCore`, `PaneLegendDescriptor`, `PriceDisplayMode`는 Core primitive로 유지했다.
  - Chart PR #4 CI PASS, main merge `ded98eb6d782d853ed1bd805abc83692d50b3ff1`, main workflow `33720008027` PASS.
  - dsl `vendor/kiwoom-condition`도 `ded98eb6d782d853ed1bd805abc83692d50b3ff1`로 advance했다.
- **4축 baseline 사전감사를 완료했고 구조 교체가 필요한 축을 확정했다.**
  - Core(chart scope) = `STANDARD`.
  - Add-on = `NONSTANDARD`: indicator/research Add-on들이 raw surface/pane/series/marker/region/bar-window/projection live lifecycle을 직접 소유한다.
  - Runtime = `NONSTANDARD`: 기본 계약이 `definition.create(context)` live object이고 `ChartSubjectViewManager`가 owner collection/signature/whole replace lifecycle을 가진다.
  - JSON/Persistence = `PARTIAL/NONSTANDARD`: top-level enabled/visible/state 저장기는 generic이지만 render item 1:1을 강제하지 않아 `subjects[]`, `__layout` collection/restore authority가 존재한다.
  - UI/Composition single path = `NONSTANDARD`: Runtime idle 후 별도 `stabilizePersistedLayout()`/startup viewport 재적용 restore path가 존재한다.
- **구조 교체용 branch를 분리했다.**
  - Chart branch: `standardize/four-axis-render-pipeline`.
  - draft PR #5: `WIP: Standardize four-axis render pipeline`.
  - PR 본문에 `DO NOT MERGE until legacy drawing lifecycle is removed`를 고정했다.
  - main에는 새 descriptor renderer를 아직 활성화하지 않았으며, 완성 전 merge하지 않는다.
- **새 Core drawing grammar 계약을 구현했다.**
  - `src/core/chart/ChartDrawingGrammar.mjs`.
  - primitive kind는 `pane / line / histogram / candlestick / legend / markers / region`으로 제한한다.
  - descriptor는 stable id + plain JSON props/data/layout만 허용한다.
  - callback/function/live handle/non-finite number/non-plain object는 거부한다.
  - parent 관계를 generic grammar에서 검증하고 결과를 deep-freeze한다.
- **generic Runtime renderer를 구현했다.**
  - `src/runtime/chart/ChartDrawingRuntime.mjs`.
  - live authority는 `Map<itemId, liveHandle>`이며 public lifecycle은 `ensure/update/setVisible/remove`다.
  - item shape가 같으면 같은 handle에 data/visibility만 갱신하고, shape가 바뀌면 그 item만 재생성한다.
  - 생성 실패는 그 item의 root handle만 rollback하며 unrelated item은 건드리지 않는다.
  - pane child는 pane가 소유하도록 root-handle ownership을 정리해 Runtime/pane 이중 dispose를 제거했다.
- **generic Runtime locality/ownership test를 추가했다.**
  - A/B 두 item 중 A 변경·삭제가 B lifecycle을 건드리지 않는지 검증한다.
  - pane child가 root pane dispose를 통해 정확히 한 번 정리되는지 검증한다.
  - failed item creation이 unrelated live item을 rollback하지 않는지 검증한다.
- **pure Add-on drawing definition 계약을 구현했다.**
  - `src/runtime/chart/ChartDrawingDefinition.mjs`.
  - 목표 인터페이스는 `describe({ id, state, bars, workspace }) -> immutable drawing descriptor`다.
  - 입력은 deep-freeze되며 Add-on이 state/bars/workspace를 mutation하지 못한다.
  - `describe()`는 synchronous pure function이어야 하며 Promise를 반환하면 거부한다.
  - 반환 descriptor id는 Runtime item id로 강제한다.
- 표준화 PR #5 현재 head는 `56d9ad20649ad380ad38166006f3e7bd30d94c79`이고, 해당 head의 `Verify chart platform` workflow `33721389937`은 PASS했다.
- 이 PASS는 새 generic 부품의 기존 테스트 회귀 없음만 의미한다. **legacy drawing path는 아직 살아 있으므로 Add-on/Runtime/JSON/single-path/global PASS가 아니다.**
- 추가 compare restore/height/timing 보정 패치는 중단 상태다.
- 작업 branch는 dsl `dsl-live-studio`; `origin/main`을 섞지 않는다.
- repo-wide/global compliance는 `REMEDIATION_REQUIRED`다.

## 할 일

- **표준화 PR #5를 계속하되 legacy drawing path가 완전히 제거되기 전에는 merge하지 않는다.**
- 다음 micro-tranche는 pure definition contract를 테스트로 고정한 뒤 단순 indicator의 descriptor 출력부터 증명한다.
  1. `ChartDrawingDefinition` property test: deep-freeze, callback/live data rejection, async describe rejection, returned id 강제, input mutation 차단을 검증한다.
  2. SMA/EMA/JMA의 feature 계산 결과를 이용해 pure one-item descriptor를 생성하는 정의를 추가/전환한다. primary line은 동일 Core grammar(`line`, parent=`primary`)만 사용한다.
  3. 이 단계에서는 새 descriptor path를 제품에서 별도 활성화하지 않는다. 출력 equivalence/contract를 먼저 테스트한다.
  4. Bollinger/SuperTrend/VWAP 및 pane indicator(RSI/MACD/Disparity/DMI/OBV)도 동일 descriptor 방식으로 순차 전환한다.
- indicator descriptor 전환이 끝나면 **RuntimeHost를 한 번의 경계 변경으로** desired item → definition.describe → `ChartDrawingRuntime.ensure/update/remove` 단일 path로 전환한다.
  - Add-on에 raw `surface`, `layout`, drawing handle을 넘기지 않는다.
  - 전환과 동시에 indicator의 legacy `definition.create(context)` drawing implementation을 제거한다. compatibility fallback/feature branch를 남기지 않는다.
- 그 다음 research/compare를 같은 원칙으로 변환한다.
  - async market/bar data는 Add-on-owned pane lifecycle이 아니라 generic data capability 결과 → desired child item descriptor로 만든다.
  - `revision/pending/subjects[] -> replace(owner)` collection orchestration을 제거한다.
- 이후 JSON/Persistence를 independent desired item 구조로 변환하고 compare `subjects[]` 및 restore-only `__layout` authority를 제거한다.
- `MarketChart.whenAddonsIdle()`의 별도 layout restore/stabilize path를 제거해 restart/global/item ON/OFF가 모두 같은 normal apply path를 사용하도록 한다.
- 마지막에 semantic operation recorder로 1/10/1000 cardinality, single-item locality, global/item visibility equivalence, restart==normal apply, idempotence, single-path를 고정한다.
- semantic gate는 제품에 맞춰 완화하지 않는다.
- 전체 4축 baseline이 STANDARD가 되기 전 UIA-1/Chart 구조 PASS를 선언하지 않는다.
- 각 tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
