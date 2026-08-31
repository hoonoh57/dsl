# Step 1 AXIS 1 Capability Audit Checkpoint

Status: **STEP 1 COMPLETE / 2026-08-31 KST**

Step 1 결과는 `DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md`가 상세 authority다.

확정 결과:

```text
JMA base numeric value                    implemented
JMA registered direction output           partial / missing as canonical DSL output
JMA normalized slope strength             not implemented as canonical measurement
numeric intermediate chart projection     implemented
threshold / permission generic projection partial
Feature Catalog vs mutable persistence    separated
final AXIS 3 CRUD physical separation     not implemented
```

기존 핵심 gap은 그대로 유지한다.

```text
tuple/multi-output
user-defined functions
bounded loops
on_tick/on_fill rollback model
partial fills/exits
pyramiding/multi-position
full differential fixtures
metadata completeness
full-engine parity
generic projection completeness
```

Frozen legacy `core/`는 변경하지 않았다.

Next authority:

```text
DSL_NEXT_WORK_ORDER.md
CURRENT_STEP = 2
```

다음 작업은 AXIS 1 migration manifest와 boundary 이식 순서를 확정하는 것이다. Step 3 보호 gate 검증이나 Step 4 실제 이식은 Step 2 완료 전에 시작하지 않는다.
