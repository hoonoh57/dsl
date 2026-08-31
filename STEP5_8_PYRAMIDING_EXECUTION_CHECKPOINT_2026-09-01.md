# Step 5-8 Pyramiding / Multi-Position Accounting Checkpoint

Status: **COMPLETE / USER-LOCAL PASS / 2026-09-01 KST**

## 범위

같은 방향의 여러 entry order를 독립 lot으로 보존하면서 aggregate position과 lot별 청산 손익을 결정적으로 관리하는 Step 5-8 기능을 검증했다.

## 구현

- `axes/axis1_dsl/execution/pyramiding_execution.py`
- `tests/test_axis1_pyramiding_execution.py`

## 확정 contract

- 같은 entry order의 partial fill은 동일 lot에 누적한다.
- 같은 방향의 새 entry order는 새 lot을 만든다.
- aggregate 수량/평균단가는 active lot의 수량가중 합으로 계산한다.
- 기본 청산은 FIFO lot allocation이다.
- `lot_id` 지정 청산은 지정 lot만 소비한다.
- lot별 entry fee / exit fee / realized PnL을 독립 기록한다.
- aggregate 수량이 0일 때만 position cycle을 종료한다.
- 반대 방향 동시 exposure, max lot 초과, lot/aggregate over-exit은 broker/accounting mutation 전에 fail-closed한다.
- 기존 Step 5-7 single-position session의 pyramiding 금지 contract는 유지한다.
- migrated whole-fill BacktestEngine과 frozen legacy core는 변경하지 않는다.

## User-local evidence

사용자는 아래 요청된 검사를 모두 `OK`로 확인했다.

```text
test_axis1_pyramiding_execution.py = OK
test_axis1_partial_execution.py = OK
test_axis1_intrabar_lifecycle.py = OK
test_axis1_broker_parity.py = OK
test_frozen_legacy_core_guard.py = OK
```

## 결론

Step 5-8은 PASS 완료다. strict sequential authority에 따라 다음 작업은 Step 5-9 full reference differential fixtures다.
