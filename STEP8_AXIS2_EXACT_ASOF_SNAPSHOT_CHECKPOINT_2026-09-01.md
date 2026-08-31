# Step 8 AXIS 2 Exact-As-Of Snapshot Checkpoint

Status: **COMPLETE / USER-LOCAL PASS / 2026-09-01 KST**

## 완료 범위

AXIS 2가 provider/precompute 단계에서 이미 계산된 cross-market / cross-symbol evidence를 정확한 시점 기준 immutable snapshot으로만 소비하도록 v1 계약을 고정했다.

구현:

```text
axes/axis2_selection/snapshots/exact_asof.py
axes/axis2_selection/snapshots/point_in_time_snapshot.v1.schema.json
tests/test_axis2_exact_asof_snapshot.py
```

확정 규칙:

```text
exact as_of / knowledge_cutoff only
future observation 금지
mixed cutoff / formula version 금지
missing/invalid 값 default synthesis 금지
nearest-time / fill-forward / interpolation 금지
rank evidence가 있으면 peer-group contract까지 immutable 보존
canonical SHA-256 snapshot identity
AXIS 1 / AXIS 3 / provider / frozen core runtime dependency 없음
```

## 사용자 로컬 검증

사용자가 다음 검사를 모두 `OK`로 보고했다.

```text
test_axis2_exact_asof_snapshot.py = OK
test_axis1_execution_bridge_contract.py = OK
test_frozen_legacy_core_guard.py = OK
```

## 다음 권한

Step 8 checkpoint가 성립했으므로 다음 순서인 **Step 9 AXIS 2 selection engine / core selectors**를 시작할 수 있다.

Step 9는 이 snapshot 위에서만 filter / frozen-rank 또는 frozen-value ordering / top-N을 수행하며 provider 호출이나 AXIS 1 DSL 계산으로 값을 재생성하지 않는다.
