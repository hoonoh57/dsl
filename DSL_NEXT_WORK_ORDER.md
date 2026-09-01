# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

기존 remediation Steps 1~15는 모두 USER-LOCAL PASS로 완료되었다. 현재부터는 새 제품 검증 tranche인 UI 일관성 검증을 수행한다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 startup/workspace state restore
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

기준 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
```

## 완료된 기반

```text
Steps 1~15 = COMPLETE / USER-LOCAL PASS
Final checkpoint = STEP15_REPO_WIDE_COMPLIANCE_CHECKPOINT_2026-09-01.md
```

이 완료 상태는 UI 검증 중 임의로 되돌리거나 검증을 약화하지 않는다.

## UIA-1 현재 결함과 수정

첫 번째 시작 결함:

```text
프로그램 시작 직후 primary candle chart 빈 화면
수동 조회가 최초 load trigger
```

분류:

```text
Bridge / Runtime startup ordering defect
```

수정:

```text
persistence hydrate / UI wiring
 -> 기존 loadInitial() 자동 1회
 -> READY
```

두 번째 시작상태 결함:

```text
5분봉을 실제 표시한 뒤 브라우저 종료/재기동
 -> 다시 일봉으로 시작
```

초기 localStorage-only 보존 방식은 managed browser lifecycle에서 durable product state로 충분하지 않았다.

분류:

```text
JSON persistence boundary defect
```

수정:

```text
chart timeframe(period + interval)
 -> shell preference port
 -> Bridge / Runtime route
 -> persistence/chart_workspace/timeframe_json.mjs
 -> .runtime/dsl-stack/chart-workspace-timeframe.json
 -> 다음 browser bootstrap에서 hydrate
 -> MarketChartWorkspace가 복원값으로 자동 loadInitial()
```

영속성 규칙:

```text
schemaVersion 명시
지원 월/주/일 + 지원 분봉/틱 interval만 허용
지원되지 않는 값 저장 거부
ordered PUT save
browser unload 시 latest state beacon POST
DSL 제품 JSON port가 localStorage fallback보다 우선
```

경계:

```text
DSL/Core 계산 변경 없음
Add-on 전략/timeframe validation 변경 없음
strategy/add-on JSON과 workspace JSON 분리
Bridge / Runtime = route/adaptation only
JSON persistence = schema validation + atomic file read/write only
JSON persistence에서 Axis/Core/Add-on import 금지
root frozen core 변경 없음
```

## UIA-1 user-local 완료 조건

```text
startup-load focused test PASS
chart shell timeframe preference test PASS
browser JSON persistence port test PASS
server JSON persistence restart test PASS
persistence layer separation guard PASS
chart bridge server regression PASS
frozen core guard PASS
UI: 분 -> 5 -> 조회 -> browser 종료 -> 재기동
UI: 조회 클릭 없이 5분봉과 candle 자동 복원
```

위 조건 PASS 전 다음 UI 기능으로 넘어가지 않는다.

## 이후 UI 기능 검증 순서

각 UI 기능을 하나씩 다음 순서로 검증한다.

```text
1. UI에서 기능 선택/작성
2. 실행
3. 화면 결과와 deterministic engine 결과 확인
4. 실패 시 원인 계층 분류
5. 해당 계층에서만 최소 수정
6. focused regression
7. 관련 cross-layer regression
8. frozen core guard
9. 같은 UI 동작 재확인
```

## 수정 분리 원칙

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

절대 규칙:

```text
repository-root core/ 수정 금지
UI를 맞추기 위해 engine 결과 덮어쓰기 금지
Bridge/Runtime에서 지표/전략/선별 재계산 금지
Add-on 문제를 Core 특례로 흡수 금지
JSON persistence에서 계산/보정 금지
Axis 1/2/3 책임 혼합 금지
검증완화/skip/compatibility exception 금지
```

실패는 수정 전에 UI defect / Bridge-Runtime defect / Core semantic defect / Add-on defect / Persistence-schema defect / Test defect / Environment issue / Authority drift / Unknown 중 하나로 먼저 분류한다.
