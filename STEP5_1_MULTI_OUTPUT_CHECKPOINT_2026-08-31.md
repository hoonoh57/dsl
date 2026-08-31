# Step 5-1 Multi-Output + Destructuring Checkpoint

Status: **COMPLETE / USER-LOCAL PASS / 2026-08-31 KST**

## 결과

AXIS 1 신규기능 5-1의 typed multi-output + destructuring을 완료했다.

사용자 local 검증:

```text
tests/test_axis1_multi_output.py = OK
tests/test_frozen_legacy_core_guard.py = OK
```

## 구현 원칙

검증된 migrated Parser/Semantic/Runtime/Backtest를 직접 대수술하지 않고 신규 문법을 얇은 lowering/facade 층에서 처리한다.

```text
multi-output DSL syntax
 -> typed/fail-closed lowering
 -> migrated DSL runtime/backtest
```

지원 v1:

```text
line, direction = ta.supertrend(...)
upper, middle, lower = ta.bbands(...)
macd, signal, hist, strength = user.macd_normalized_all(...)
```

보장:

```text
반환 component 수 / 대상 변수 수 exact 일치
component type 명시
중복/예약 이름 fail-closed
등록되지 않은 multi-output 함수 fail-closed
원래 DSL line 진단 보존
후속 조건식/백테스트에서 각 component 사용 가능
frozen legacy core 무변경
```

## 결론

Step 5-1은 PASS다. 다음 순서는 Step 5-2 tuple-aware generic projection이며, 차트가 지표값을 다시 계산하지 않고 실행 결과와 multi-output binding metadata만 소비하도록 구현한다.
