# todo.md — 한 일 / 할 일

## 한 일

- **권위 파일을 2개로 고정했다.** 앞으로 세션 복구/이어가기는 `rules.md` → `todo.md`만 읽는다. 기존 `SESSION_HANDOFF.md`, `CURRENT_STATE.md`, `DSL_NEXT_WORK_ORDER.md`, 각종 constitution/checkpoint/compliance 문서는 비권위 역사/증거 자료이며 복구 권위로 읽지 않는다.
- `rules.md`를 **유일한 영구 스킬/헌법 파일**로 만들었다. 정상 개발/버그/리팩터링/새 세션 때문에 수정하지 않는다. 사용자가 명시적으로 `rules.md 규칙 변경`을 지시한 경우에만 의미를 바꾼다.
- `rules.md`에 4축 의미를 고정했다.
  - Chart Core = generic 그리기만 한다.
  - Add-on = 그리는 종류/type/props 의미만 확장한다.
  - Bridge/Runtime = feature-blind generic `ensure/update/remove(id)` 번역만 한다.
  - JSON = desired state의 ON/OFF/props/order/layout persistence only.
- 4축의 핵심 semantic invariant를 영구 규칙으로 고정했다: CARDINALITY, LOCALITY, RESTORE EQUIVALENCE, VISIBILITY EQUIVALENCE, IDEMPOTENCE, SINGLE PATH.
- 기존의 “파일 위치/import/token 검사만으로 4축 PASS” 판정을 폐기했다. 앞으로 4축 PASS는 structural + semantic operation + cardinality + locality + restore + visibility + idempotence + single-path가 모두 PASS해야 한다.
- **semantic gate 샛길을 영구 차단했다.** `rules.md` 의미가 바뀌지 않는 한 semantic gate의 판정 의미를 변경/완화할 수 없고, 제품 실패는 gate 수정 사유가 아니다. `test defect`는 기존 `rules.md` 불변식을 잘못 구현한 테스트/fixture/환경 오류에만 한정하며 수정 후 검증은 동일하거나 더 강해야 한다. 제품을 통과시키기 위한 예외·assertion 축소·expected 재정의·feature/legacy 예외는 검증 오염으로 금지한다.
- **현재 구현의 4축 baseline 사전감사를 시작했고 이미 PASS가 아님을 확인했다.**
  - Core: `src/core/chart/JmaSeries.mjs`, `MovingAverageSeries.mjs`에 JMA/SMA/EMA feature 계산 의미가 존재한다. `Core = generic draw only` 위반 후보가 아니라 실제 구조 위반으로 분류한다.
  - Add-on: `SmaAddon`, `RsiAddon` 등이 `context.surface.createLineSeries/createPane`를 직접 호출하고 live series/pane 생성·visibility·dispose lifecycle을 소유한다. `Add-on = one-item descriptor/type/props` 규칙에 맞지 않는다.
  - Runtime: `ChartRuntimeHost`는 add-on에 raw `surface`/layout lifecycle capability를 넘겨 현재 비표준 Add-on lifecycle을 허용한다. `ChartSubjectViewManager`는 owner collection/signature/replace lifecycle을 가진다.
  - Runtime/Layout: `ChartPaneLayoutManager`는 `__layout` persistence를 읽어 `stabilizePersistedLayout()`의 frame-loop/restore completion 상태기계를 실행한다. `restart == normal apply` 규칙에 맞지 않는다.
  - JSON/Persistence: `ChartAddonStateStore`와 persistence client의 enabled/visible/state 저장 자체는 generic 기반이지만, `research.compare-subjects` 한 node 안의 `subjects[]`가 여러 render item을 collection으로 묶고 `__layout`을 별도 restore 대상으로 사용한다. item 독립 desired-state 형태로 표준화가 필요하다.
- 기존 `audit-addon-boundaries.mjs`는 import/feature-identity/provider-bypass 중심의 static gate라 위 semantic 오염을 PASS시킬 수 있었던 원인이 확인됐다.
- 현재 Chart 쪽 기준은 `vendor/kiwoom-condition = e272e18adbb4530f0edfe5046a19e3b7e0272606`이며 최종 정상 구조로 승인된 상태가 아니다.
- 작업 branch는 계속 `dsl-live-studio`다. `origin/main`을 현재 작업 branch에 섞지 않는다.
- repo-wide/global compliance는 계속 `REMEDIATION_REQUIRED`다.

## 할 일

- **추가 compare restore 보정 패치를 중단한다.** height fallback, timing 재시도, compare 전용 pending/revision/signature/restore settle을 더 추가하지 않는다.
- semantic gate 구현보다 먼저 **4축 baseline 전수감사와 비표준 부품 표준화**를 수행한다. 기존 비표준 부품 위에 새 표준 계층을 덧씌우지 않는다.
- 순서는 고정한다.
  1. **Core 감사/표준화**: chart Core의 모든 파일을 심사해 generic drawing/time/viewport/layout primitive만 남긴다. JMA/SMA/EMA 등 feature 계산은 Add-on semantic 영역으로 이동한다. Core grammar를 `무엇을 어떻게 한다` 형태의 generic primitive contract로 확정한다.
  2. **Add-on 감사/표준화**: 모든 chart Add-on을 심사해 raw surface/pane/series lifecycle 소유를 제거한다. Add-on은 one-item `id/type/props/data/layout` descriptor와 feature 계산만 제공한다.
  3. **Bridge/Runtime 감사/표준화**: Add-on에 raw lifecycle surface를 넘기지 않는다. generic desired/live `Map<itemId, liveHandle>` + `ensure/update/remove(id)`만 유지한다. owner whole-replace, subject collection signature, feature restore queue/settle을 제거한다.
  4. **JSON 감사/표준화**: 각 render item을 독립 desired item으로 저장한다. global/item enabled/visible/props/layout을 같은 read/write path로 처리한다. Compare의 `subjects[]` collection lifecycle authority와 restore-only `__layout` 사용을 제거/변환한다.
  5. **Baseline 표준화 검증**: 위 4축이 표준 부품만으로 연결되고 `JSON -> Add-on descriptor -> generic Runtime -> Core grammar` 단일 경로가 확인된 뒤에만 semantic operation gate를 구현한다.
  6. **Semantic gate 고정**: 1/10/1000 cardinality, single-item locality, global/item visibility equivalence, restart==normal apply, idempotence를 operation trace로 검증한다.
- 표준화 과정의 각 micro-tranche는 기존 기능 behavior test를 유지하되, 기존 테스트가 비표준 구조를 요구하면 제품에 맞춰 gate를 완화하지 않는다. `rules.md`와 충돌하는 기존 테스트/구현은 authority 기준으로 분류해 교체한다.
- 4축 baseline이 전부 PASS하기 전에는 UIA-1 또는 Chart 구조 PASS를 선언하지 않는다.
- 구조 표준화 후에만 기존 저장 JSON으로 실제 WYSIWYG 재기동을 다시 한다. 재기동은 별도 restore 검증이 아니라 normal desired-state apply 동일성 확인이다.
- 각 tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`의 `한 일 / 할 일`만 갱신한다.
