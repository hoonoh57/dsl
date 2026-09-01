# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

기존 remediation Steps 1~15는 모두 USER-LOCAL PASS로 완료되었다. 현재는 실제 UI 경로에서 이식된 DSL과 차트 상태의 일관성을 검증한다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = AUTO USER-LOCAL PASS / REAL UI REVALIDATION REQUIRED
```

기준 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
DSL_HUMAN_COMMUNICATION_OUTPUT_POLICY.md
```

## 현재 영속성 SSOT

```text
의미 있는 화면 변경
 -> one logical Chart State
 -> monotonic stateRevision
 -> one JSON serialization/restore path
 -> one atomic runtime JSON file
```

canonical runtime state:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

문서 범위:

```text
workspace
  instrument / timeframe / base date / visible count
  price mode / viewport / recent instruments
  primary price + volume pane layout
display
addons
  enabled/visible / parameters / private state
  add-on pane layout / geometry points
```

## 실제 UI 실패에서 추가 확인된 원인

```text
older queued full-state save
latest browser-close full-state save
 -> request completion/order inversion
 -> older document may overwrite latest document
```

수정:

```text
every semantic state mutation -> stateRevision +1
full JSON -> stateRevision persisted
JSON writes -> serialized
stale lower-revision write -> rejected
```

회귀검증은 실제 실패 순서를 포함한다.

```text
latest close-state POST
 -> delayed older PUT
 -> restore
 -> latest SuperTrend/layout/workspace must remain
```

2026-09-01 사용자 로컬 자동 재검증:

```text
verify.bat -> [PASS] current verification passed
```

## UIA-1 완료 조건

이제 남은 조건은 실제 UI 재검증이다.

```text
SuperTrend 삽입
메인/서브 패널 높이 변경
브라우저 종료
재기동
 -> SuperTrend 복원
 -> 메인/서브 높이 복원
 -> 기존 timeframe/workspace 유지
 -> PERSISTENCE ERROR 없음
```

실제 UI 복원 PASS 전 다음 UI 기능으로 넘어가지 않는다.

## 수정 경계

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

절대 규칙:

```text
repository-root core/ 수정 금지
UI 상태를 Core 하드코딩으로 복원 금지
Bridge/Runtime에서 지표/전략/선별 계산 금지
Add-on 기능특례를 Core에 흡수 금지
JSON persistence에서 계산/지표 의미판정 금지
기능별 persistent side-store 추가 금지
localStorage를 제품 상태 authority로 사용 금지
검증 assertion 약화/skip 금지
older state가 latest revision을 overwrite하는 것 금지
```

## 이후 UI 기능 검증 순서

```text
1. UI에서 기능 선택/작성
2. 실행
3. 화면 결과와 deterministic engine 결과 확인
4. 실패 원인 계층 분류
5. 해당 계층만 최소 수정
6. focused regression
7. cross-layer regression
8. frozen core guard
9. 동일 UI 동작 재확인
```
