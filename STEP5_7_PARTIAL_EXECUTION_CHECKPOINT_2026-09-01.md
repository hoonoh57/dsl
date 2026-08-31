# Step 5-7 Partial Execution Checkpoint — 2026-09-01

Status: **COMPLETE / USER-LOCAL PASS**

## 범위

Step 5-7 `partial fills / partial exits`만 완료했다.

구현:

```text
axes/axis1_dsl/execution/partial_execution.py
tests/test_axis1_partial_execution.py
```

확정 contract:

```text
주문 requested / cumulative filled / remaining quantity 분리
PARTIALLY_FILLED 상태 명시
각 fill slice 별도 기록
weighted average fill price 유지
partial cancel은 이미 체결된 수량을 되돌리지 않음
single position partial entry/partial exit accounting
entry fee proportional allocation
exit slice별 realized gross/net PnL
position quantity가 0일 때만 완전 종료
각 fill slice를 on_fill provisional state event로 전달 가능
```

Step 5-8 경계도 검증했다.

```text
새 entry order로 기존 position에 추가 진입 = fail-closed
pyramiding/multi-position accounting은 Step 5-8 전까지 미구현
```

## 사용자 로컬 검증

사용자가 다음 검사를 모두 `OK`로 보고했다.

```text
test_axis1_partial_execution.py
test_axis1_intrabar_lifecycle.py
test_axis1_broker_parity.py
test_frozen_legacy_core_guard.py
```

## 보호 확인

```text
frozen legacy core 수정 없음
migrated BrokerEmulator 직접 수정 없음
migrated BacktestEngine 직접 수정 없음
기존 whole-fill 경로 변경 없음
```

따라서 Step 5-7을 닫고 Step 5-8 `pyramiding / multi-position accounting`으로 이동한다.
