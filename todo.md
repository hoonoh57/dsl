# todo.md — 한 일 / 할 일

## 한 일

- **권위 파일은 `rules.md` + `todo.md` 두 개뿐이다.** 세션 복구/이어가기는 `rules.md` → `todo.md`만 읽는다.
- `rules.md`에 4축 의미, semantic invariant, semantic gate 불변성, 주기적 STANDARDIZATION CYCLE을 고정했다.
- 현재 Chart baseline은 전체 4축 PASS가 아니며 STANDARDIZATION CYCLE 진행 중이다.
- **Core 축 `src/core/chart` 표준화 tranche를 완료했다.**
  - 감사 대상 6개 중 `ChartAddonSurface.mjs`, `ChartCore.mjs`, `PaneLegendDescriptor.mjs`, `PriceDisplayMode.mjs`는 generic chart/time/viewport/display primitive로 유지했다.
  - 비표준 feature 계산이던 `JmaSeries.mjs`, `MovingAverageSeries.mjs`를 Core에서 제거했다.
  - JMA 계산은 `src/addons/indicator/math/JmaMath.mjs`, SMA/EMA 계산은 `src/addons/indicator/math/MovingAverageMath.mjs`로 **내용 변경 없이 이동**했다.
  - `SmaAddon.mjs`, `EmaAddon.mjs`, `JmaAddon.mjs`는 import 경로만 Add-on-owned math로 변경했다. 계산/표시 behavior는 변경하지 않았다.
  - Runtime/JSON/Persistence/UI/adapter는 이 tranche에서 변경하지 않았다.
  - Chart PR #4 `Standardize Chart Core indicator semantics` CI에서 `audit:addon-boundaries` + 전체 `npm test` PASS.
  - Chart main merge commit `ded98eb6d782d853ed1bd805abc83692d50b3ff1`; main push workflow `33720008027` PASS.
  - `vendor/kiwoom-condition`을 `ded98eb6d782d853ed1bd805abc83692d50b3ff1`로 advance했다.
  - 현재 감사 범위인 `src/core/chart`는 **STANDARD**로 분류한다. 이것은 전체 Core/4축/global PASS 선언이 아니다.
- 이미 확인된 다음 비표준 축:
  - Add-on: raw `surface.createLineSeries/createPane` 호출과 live series/pane visibility/dispose lifecycle 소유.
  - Runtime: raw surface/layout capability 전달, `ChartSubjectViewManager` owner collection/signature/replace lifecycle.
  - Runtime/Layout: `ChartPaneLayoutManager.stabilizePersistedLayout()` restore 전용 frame-loop.
  - JSON/Persistence: `research.compare-subjects` 한 node의 `subjects[]` collection과 restore-coupled `__layout`.
- 추가 compare restore 보정 패치는 중단 상태다.
- 작업 branch는 `dsl-live-studio`; `origin/main`을 섞지 않는다.
- repo-wide/global compliance는 `REMEDIATION_REQUIRED`다.

## 할 일

- **다음 순서는 Add-on 전수감사/표준화다.** Runtime/JSON을 먼저 고치지 않는다.
- 모든 chart Add-on을 검사해 raw `context.surface`, `createPane`, `create*Series`, `setVisible`, `dispose`, Add-on-owned pane/series handle 및 collection lifecycle을 `STANDARD / NONSTANDARD / UNKNOWN`으로 분류한다.
- 단순 line indicator(SMA/EMA/JMA)부터 one-item descriptor 계약의 최소 형태를 확정한다. Add-on은 feature 계산 + `id/type/props/data/layout` descriptor만 제공하고 live drawing handle을 소유하지 않는 상태가 목표다.
- 기존 Runtime이 descriptor를 아직 소비하지 못한다면 비표준 Add-on 위에 compatibility/이중 active path를 추가하지 않는다. Add-on 감사 결과와 필요한 generic contract를 먼저 확정한 뒤 다음 Runtime tranche에서 단일 경로로 전환한다.
- Add-on 감사가 끝나기 전에는 Add-on 축 PASS를 선언하지 않는다.
- 그 다음 고정 순서:
  1. Add-on 표준화
  2. Bridge/Runtime 표준화 — `Map<itemId, liveHandle>` + generic `ensure/update/remove`
  3. JSON/Persistence 표준화 — independent desired item
  4. UI/single-path 연결 확인
  5. semantic operation gate 고정
- semantic gate는 제품에 맞춰 완화하지 않는다.
- 전체 4축 baseline이 STANDARD가 되기 전 UIA-1/Chart 구조 PASS를 선언하지 않는다.
- 각 tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`만 갱신한다.
