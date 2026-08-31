# Step 5-9 Reference Differential Checkpoint

Status: **COMPLETE / USER-LOCAL PASS / 2026-09-01 KST**

## 완료 내용

AXIS 1 지표/함수 계산을 독립된 test-side NumPy reference와 differential 비교하는 검증층을 완료했다.

검증 범위:

```text
moving / rolling
recursive / trend
range / event-history
JMA / Supertrend / BBands
normalized MACD components
registered ta/user runtime mapping
multi-output lowering
NaN / warmup / flat-edge fixtures
```

Reference fixture는 `axes.axis1_dsl` 및 frozen legacy `core/`를 expected 계산에 사용하지 않는다.

## User-local evidence

사용자가 요청된 다음 검사를 모두 `OK`로 확인했다.

```text
test_axis1_reference_differential.py = OK
test_axis1_indicator_parity.py = OK
test_axis1_pyramiding_execution.py = OK
test_axis1_partial_execution.py = OK
test_frozen_legacy_core_guard.py = OK
```

## 보존 원칙

```text
production indicator/runtime 계산 로직 변경 없음
reference 결과에 맞춘 tolerance 완화 없음
frozen legacy core 변경 없음
```

## 다음 authority

Step 5-10 `full-engine batch/streaming parity`로 이동한다.
