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

사용자 UI에서 연속으로 두 가지 시작상태 복원 결함이 확인됐다.

첫 번째:

```text
프로그램 시작 직후 toolbar/state는 보이지만 primary candle chart는 빈 화면
수동으로 조회를 눌러야 최초 candle/indicator render 시작
```

분류:

```text
Bridge / Runtime UI startup ordering defect
```

수정:

```text
persistence hydrate / UI wiring 완료
 -> 기존 manual 조회와 동일한 loadInitial() 자동 1회 await
 -> READY
```

두 번째:

```text
1분봉을 선택한 뒤 화면을 다시 열면 차트가 다시 일봉으로 시작
```

분류:

```text
UI workspace persistence defect
```

원인은 chart workspace가 표시 봉 수와 최근 종목만 기억하고 timeframe은 매번 `day`로 하드 초기화하던 것이다.

수정:

```text
사용자가 선택한 chart timeframe(period + interval)을 workspace preference로 저장
 -> 시작 시 저장값을 strict validation
 -> 저장값이 유효하면 default day보다 먼저 복원
 -> 복원된 timeframe으로 기존 loadInitial() 자동 실행
```

지원 주기는 현재 chart source가 허용하는 월/주/일, 모든 지원 분봉 interval, 모든 지원 tick interval만 그대로 허용한다. 손상되거나 지원되지 않는 저장값은 기본 일봉으로 fail-closed fallback한다.

경계:

```text
DSL/Core 계산 변경 없음
Add-on 전략/timeframe 검증 변경 없음
전략/지표 JSON schema에 workspace UI preference를 혼입하지 않음
root frozen core 변경 없음
```

## UIA-1 user-local 완료 조건

```text
focused startup-load test PASS
workspace timeframe persistence test PASS
chart bridge server regression PASS
frozen core guard PASS
UI 시작 직후 조회 클릭 없이 candle chart 표시
1분봉 선택 후 재시작해도 1분봉 유지 + 자동 candle load
Add-on 오류가 있어도 base candle chart는 표시
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
