# todo.md — 한 일 / 할 일

## 한 일

- **권위 파일을 2개로 고정했다.** 세션 복구/이어가기는 `rules.md` → `todo.md`만 읽는다. 기타 과거 문서는 비권위 역사/증거다.
- `rules.md`를 유일한 영구 스킬/헌법 파일로 고정했다.
- 4축 의미를 고정했다.
  - Chart Core = generic drawing grammar only.
  - Add-on = feature 계산 + one-item descriptor/type/props/data/layout only.
  - Bridge/Runtime = feature-blind desired/live diff + generic `ensure/update/remove(id)` only.
  - JSON = independent desired-state persistence only.
- 4축 semantic invariant를 고정했다: CARDINALITY, LOCALITY, RESTORE EQUIVALENCE, VISIBILITY EQUIVALENCE, IDEMPOTENCE, SINGLE PATH, SCALE-INDEPENDENT COMPLEXITY.
- static/import/token 검사만으로 4축 PASS를 선언하지 못하게 했고 semantic property gate를 필수화했다.
- **semantic gate 샛길을 영구 차단했다.** 제품 실패를 이유로 gate 의미를 완화/변경할 수 없고 `test defect`는 기존 rules 의미를 잘못 구현한 테스트/fixture/환경 오류에만 한정한다.
- **주기적 4축 STANDARDIZATION CYCLE을 헌법에 추가했다.** 기능 우선 개발 중 비표준 부품이 누적될 수 있음을 개발 위험으로 인정하되, 주요 milestone 완료/새 대형 기능군 진입 전/구조성 결함 반복/restore·reconcile·pending·revision 복잡도 증가/4축 PASS 선언 전에는 `Core -> Add-on -> Runtime -> JSON/Persistence -> UI single-path` 순서의 전수감사를 의무화한다. `NONSTANDARD`는 기능이 동작하고 기존 테스트가 green이어도 `product defect + architecture defect`로 판정하고 표준화 완료 전 새 구조 확장을 중지한다. 이 규칙은 `rules.md` commit `e361177171b1bfd3c662be580673518f2086ffc5`에 반영됐다.
- 현재 Chart 구현의 baseline 사전감사를 시작했고 이미 4축 PASS가 아님을 확인했다.
  - Core: `src/core/chart/JmaSeries.mjs`, `MovingAverageSeries.mjs`에 JMA/SMA/EMA feature 계산 의미가 존재한다.
  - Add-on: `SmaAddon`, `RsiAddon` 등이 raw `surface.createLineSeries/createPane`를 직접 호출하고 live series/pane lifecycle을 소유한다.
  - Runtime: `ChartRuntimeHost`가 Add-on에 raw surface/layout lifecycle capability를 넘기며 `ChartSubjectViewManager`는 owner collection/signature/replace lifecycle을 가진다.
  - Runtime/Layout: `ChartPaneLayoutManager`가 `__layout`을 읽고 `stabilizePersistedLayout()` restore 전용 frame-loop/완료판정을 수행한다.
  - JSON/Persistence: generic enabled/visible/state 저장 기반은 있으나 `research.compare-subjects` 한 node의 `subjects[]`와 restore-only `__layout`이 item 독립 desired-state 규칙에 맞지 않는다.
- 기존 `audit-addon-boundaries.mjs`는 import/feature-identity/provider-bypass 중심의 static gate라 위 semantic 오염을 검출하지 못했다.
- 현재 Chart 기준은 `vendor/kiwoom-condition = e272e18adbb4530f0edfe5046a19e3b7e0272606`이며 최종 정상 구조로 승인된 상태가 아니다.
- 작업 branch는 `dsl-live-studio`다. `origin/main`을 현재 작업 branch에 섞지 않는다.
- repo-wide/global compliance는 `REMEDIATION_REQUIRED`다.

## 할 일

- **현재 작업을 rules.md의 첫 STANDARDIZATION CYCLE로 수행한다.** 추가 compare restore 보정 패치는 중단한다.
- semantic gate 구현보다 먼저 **4축 baseline 전수감사와 비표준 부품 표준화**를 완료한다. 비표준 부품 위에 새 표준 계층을 덧씌우지 않는다.
- 순서는 고정한다.
  1. **Core 감사/표준화**: chart Core 전 파일을 심사해 generic drawing/time/viewport/layout primitive만 남기고 JMA/SMA/EMA 등 feature 계산을 Add-on semantic 영역으로 이동한다. Core grammar를 `무엇을 어떻게 한다` 형태로 확정한다.
  2. **Add-on 감사/표준화**: 모든 chart Add-on의 raw surface/pane/series lifecycle 소유를 제거하고 one-item descriptor + feature 계산만 남긴다.
  3. **Bridge/Runtime 감사/표준화**: Add-on에 raw lifecycle surface를 넘기지 않고 `Map<itemId, liveHandle>` + generic `ensure/update/remove(id)`만 유지한다. owner whole-replace, collection signature, restore queue/settle을 제거한다.
  4. **JSON 감사/표준화**: 각 render item을 독립 desired item으로 저장하고 global/item enabled/visible/props/layout을 같은 read/write path로 처리한다. Compare의 `subjects[]` collection lifecycle authority와 restore-only `__layout`을 제거/변환한다.
  5. **Baseline 표준화 검증**: `JSON -> Add-on one-item descriptor -> generic Runtime -> Core grammar` 단일 경로를 확인한다.
  6. **Semantic gate 고정**: 1/10/1000 cardinality, single-item locality, global/item visibility equivalence, restart==normal apply, idempotence를 operation trace로 검증한다.
- 각 micro-tranche는 기존 필수 behavior를 보존하되, 기존 테스트가 비표준 구조를 요구하면 rules 기준으로 교체한다. gate를 제품에 맞춰 완화하지 않는다.
- 4축 baseline이 모두 STANDARD/PASS가 되기 전에는 UIA-1 또는 Chart 구조 PASS를 선언하지 않는다.
- 구조 표준화 후에만 기존 저장 JSON으로 실제 WYSIWYG 재기동을 수행한다.
- 각 tranche 종료 시 새 문서를 만들지 않고 이 `todo.md`의 `한 일 / 할 일`만 갱신한다.
