# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

기존 remediation Steps 1~15는 모두 USER-LOCAL PASS로 완료되었다. 현재부터는 실제 UI 경로에서 이식된 DSL과 차트 상태의 일관성을 검증한다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

기준 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
```

## 현재 영속성 SSOT

사용자 최신 결정:

```text
의미 있는 화면 변경
 -> one logical Chart State
 -> one JSON serialization/restore path
 -> one atomic runtime JSON file
```

canonical runtime state:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

문서 구조:

```text
schemaVersion
visualsVisible
display
workspace
addons
```

`workspace`에는 primary instrument, timeframe, base date, visible count, price display mode, viewport, recent instruments를 보존한다.

`addons[*].state`에는 지표/전략/비교차트 파라미터, pane layout, 선/도형의 정확한 point coordinates 등 Add-on private state를 그대로 JSON-compatible 형태로 보존할 수 있다.

## UIA-1 수정 내용

1. 시작 시 수동 `조회`가 필요했던 문제:

```text
hydrate -> wiring -> automatic loadInitial -> READY
```

2. timeframe 재기동 복원 문제:

기능별 localStorage 또는 timeframe 전용 JSON으로 고치지 않는다. 이전 임시 구현은 제거한다.

```text
full chart-state.json hydrate
 -> workspace restore
 -> primary candle auto-load
 -> add-on/layout/geometry restore
```

3. 이전 physical shard persistence:

```text
_chart.json + addon별 *.json
```

은 unified file이 없는 기존 환경에서 한 번 migration한 뒤 제거한다. 정상 운영 중 semantic state write는 full-document atomic rewrite만 사용한다.

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
JSON persistence에서 계산/의미판정 금지
기능별 persistent side-store 추가 금지
localStorage를 제품 상태 authority로 사용 금지
검증 assertion 약화/skip 금지
```

## UIA-1 user-local 완료 조건

```text
single JSON chart-state focused test PASS
startup automatic-load regression PASS
product server restart roundtrip PASS
chart bridge regression PASS
frozen core guard PASS
```

UI acceptance:

```text
5분봉 + 종목/표시범위/수익률 모드/지표 설정 등 변경
 -> browser 종료
 -> 재기동
 -> 조회 클릭 없이 동일 semantic state 복원
```

파일 acceptance:

```text
runtime chart state directory의 JSON state file = chart-state.json 하나
그 한 문서 안에서 workspace + display + addons 확인
Add-on instance state의 exact point coordinates roundtrip 가능
```

위 조건 PASS 전 다음 UI 기능으로 넘어가지 않는다.

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
