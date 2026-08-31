# Step 4 Boundary 9 Backtest + Projection Parity Checkpoint

Status: **COMPLETE / USER-LOCAL PASS / 2026-08-31 KST**

## 결과

마지막 migration boundary인 Backtest + Projection Output을 새 AXIS 1 경계로 이식하고 frozen legacy와 focused parity를 완료했다.

User-local 최종 판정:

```text
test_axis1_backtest_projection_parity.py = OK
test_frozen_legacy_core_guard.py = OK
```

초기 parity 실행에서 2개 오류가 있었으나 원인은 migration product가 아니라 **test defect**였다.

```text
잘못된 fixture: order.close_long(type = "MARKET")
legacy parser도 close order 인수를 허용하지 않음
수정: order.close_long()
```

검증 기준/실행코드/frozen core를 완화하거나 변경하지 않고 test input만 legacy-valid DSL로 수정한 뒤 PASS를 확인했다.

## 완료 범위

```text
trade sequence / fills / quantity
metrics numeric
markers / candles / equity
closed trades / risk exits
numeric indicator projection / JMA trend-color projection
timeframe mismatch fail-closed
prepared exact-time context binding
new AXIS 1 backtest/context adapter의 frozen-core/provider import 부재
```

## Step 4 최종 판정

9개 migration boundary 모두 user-local PASS다.

```text
1 Parser / AST                         PASS
2 Function Registry                    PASS
3 Assignment Flow + Semantic           PASS
4 Indicator Kernel                     PASS
5 State + Bar Runtime                  PASS
6 MTF + Read-Only Context Binding      PASS
7 DSL Runtime                          PASS
8 Broker                               PASS
9 Backtest + Projection Output         PASS
```

따라서 Step 4 `AXIS 1 경계별 이식 + parity`는 COMPLETE다.

Frozen legacy `core/`는 계속 immutable golden reference로 유지한다.

다음 작업은 순서대로 Step 5-1 `tuple / multi-output typed return + destructuring`이다.
