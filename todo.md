# todo.md — 한 일 / 할 일

## 한 일

- **권위 파일을 2개로 고정했다.** 앞으로 세션 복구/이어가기는 `rules.md` → `todo.md`만 읽는다. 기존 `SESSION_HANDOFF.md`, `CURRENT_STATE.md`, `DSL_NEXT_WORK_ORDER.md`, 각종 constitution/checkpoint/compliance 문서는 비권위 역사/증거 자료이며 복구 권위로 읽지 않는다.
- `rules.md`를 **유일한 영구 스킬/헌법 파일**로 만들었다. 정상 개발/버그/리팩터링/새 세션 때문에 수정하지 않는다. 사용자가 명시적으로 `rules.md 규칙 변경`을 지시한 경우에만 의미를 바꾼다.
- `rules.md`에 4축 의미를 고정했다.
  - Chart Core = generic 그리기만 한다.
  - Add-on = 그리는 종류/type/props 의미만 확장한다.
  - Bridge/Runtime = feature-blind generic `ensure/update/remove(id)` 번역만 한다.
  - JSON = desired state의 ON/OFF/props/order/layout persistence only.
- 4축의 핵심 semantic invariant를 영구 규칙으로 고정했다.
  - **CARDINALITY**: 1개와 1000개는 같은 algorithm이고 반복 횟수만 다르다.
  - **LOCALITY**: 1000개 중 1개 OFF는 그 1개 lifecycle만 바뀐다.
  - **RESTORE EQUIVALENCE**: 재시작은 별도 restore path가 아니라 저장 JSON을 다시 읽어 normal `ensure/update/remove`를 실행한다.
  - **VISIBILITY EQUIVALENCE**: 전체 ON/OFF와 부분 ON/OFF는 같은 effective-state 계산과 같은 item operation으로 귀결된다.
  - **IDEMPOTENCE**: 동일 state 재적용은 불필요한 live object 재생성을 만들지 않는다.
  - **SINGLE PATH**: `JSON -> Add-on descriptor/type -> generic Runtime/Bridge -> Core draw` 경로 하나만 존재한다.
- 기존의 “파일 위치/import/token 검사만으로 4축 PASS” 판정을 폐기했다. 앞으로 4축 PASS는 structural + semantic operation + cardinality + locality + restore + visibility + idempotence + single-path가 모두 PASS해야 한다.
- **semantic gate 샛길을 영구 차단했다.** `rules.md` 의미가 바뀌지 않는 한 semantic gate의 판정 의미를 변경/완화할 수 없고, 제품 실패는 gate 수정 사유가 아니다. `test defect`는 기존 `rules.md` 불변식을 잘못 구현한 테스트/fixture/환경 오류에만 한정하며 수정 후 검증은 동일하거나 더 강해야 한다. 제품을 통과시키기 위한 예외·assertion 축소·expected 재정의·feature/legacy 예외는 검증 오염으로 금지한다. 제품 구조 수정과 semantic gate 판정 의미 수정을 같은 tranche에서 하지 않는다. 이 잠금은 `rules.md` commit `7164c372dc87516b0c68afd42d9c32ee0537baf7`에 반영됐다.
- 현재 반복된 compare pane restore 문제는 더 이상 개별 height/race/signature 버그로만 보지 않는다. **collection-oriented lifecycle orchestration이 item-oriented declarative rendering을 대체한 구조 결함 가능성이 확인된 상태**다.
- 현재 Chart 쪽 원격 기준은 `vendor/kiwoom-condition = e272e18adbb4530f0edfe5046a19e3b7e0272606`이다. 이 commit까지의 patch는 방어적 수정으로 남아 있으나 **최종 정상 구조로 승인된 것은 아니다**.
- `rules.md` 생성 commit: `899996547496e3b7ae918c4aef338f1871caec5e`.
- 작업 branch는 계속 `dsl-live-studio`다. `origin/main`을 현재 작업 branch에 섞지 않는다.
- repo-wide/global compliance는 여전히 `REMEDIATION_REQUIRED`다.

## 할 일

- **추가 compare restore 보정 패치를 중단한다.** height fallback, timing 재시도, compare 전용 pending/revision/signature/restore settle을 더 추가하지 않는다.
- 다음 tranche의 첫 작업은 `rules.md`에서 직접 파생된 **4축 semantic gate** 구축이다. 현재 구현을 살리기 위한 테스트가 아니라 현재 구현을 심사하는 테스트여야 한다.
- semantic operation recorder로 최소 다음을 자동 검증한다.
  - 1 item ON → generic ensure 1회.
  - 1000 items ON → 같은 ensure 1000회, 새로운 collection lifecycle 0.
  - 1000개 중 #537 OFF → #537만 remove/hide/update, 나머지 999개 lifecycle 변화 0.
  - #537 다시 ON → #537만 ensure/update.
  - global OFF/ON → 동일 item operation 반복.
  - restart apply(saved JSON) → fresh normal apply(saved JSON)와 의미상 동일 operation trace.
  - 같은 JSON 두 번 apply → 두 번째 lifecycle 변화 0.
- 이 semantic gate로 현재 `CompareSubjectsRuntimeAddon`, `ChartSubjectViewManager`, layout/runtime restore 경로를 심사한다. `whole collection signature`, `owner 전체 replace`, feature-specific revision/pending/restore state가 cardinality/locality/restore invariant를 위반하면 **architecture defect**로 판정하고 삭제/축소 대상으로 잡는다.
- 목표 구조는 오직 다음이다.
  - `JSON desired item`
  - `-> Add-on의 one-item descriptor/type 변환`
  - `-> generic Runtime desired/live diff`
  - `-> ensure/update/remove(id)`
  - `-> Chart Core generic draw`
- 1개/10개/1000개에서 operation 종류가 같고 횟수만 달라질 때까지 UIA-1을 PASS로 닫지 않는다.
- 구조 정리 후에만 기존 저장 JSON으로 실제 WYSIWYG 재기동을 다시 한다. 재기동은 별도 restore 검증이 아니라 normal desired-state apply의 동일성 확인이어야 한다.
- 각 tranche 종료 시 **새 문서를 만들지 말고 이 `todo.md`의 `한 일 / 할 일`만 갱신한다.**
