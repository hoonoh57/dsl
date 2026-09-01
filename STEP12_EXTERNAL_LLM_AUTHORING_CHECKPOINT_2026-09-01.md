# Step 12 External LLM Authoring Lane Checkpoint

Status: **COMPLETE / USER-LOCAL PASS / 2026-09-01 KST**

## 완료 범위

External LLM은 전략 초안 제안만 담당하고 실행 권한을 갖지 않는 human-mediated authoring lane을 구현했다.

```text
natural-language request
 -> generated machine-contract prompt
 -> external_strategy_draft/v1
 -> deterministic local validation
 -> ACCEPTED_DRAFT / correction / blocked
```

## 확정 계약

- AXIS 1 capability truth는 machine-readable capability registry에서 생성한다.
- AXIS 2 feature/data-source/context identity는 호출자가 exact inventory로 주입하며 이름을 추측하지 않는다.
- strict draft schema, capability, data-source, axis-boundary, timeframe/causality, DSL parser/semantic, compile dry-run, acceptance 순서로 fail-closed 검증한다.
- 미지원 capability는 `BLOCKED_NEEDS_CAPABILITY`, material ambiguity는 explicit human acceptance 전 `BLOCKED_USER_CLARIFICATION`이다.
- correction prompt는 원 요청과 request_id를 보존하고 exact validator error를 전달한다.
- correction iteration은 bounded이며 외부 LLM 자동호출은 하지 않는다.
- `authoring_validation_event/v1` 구조화 evidence를 만들 수 있다.
- `ACCEPTED_DRAFT`는 실행/저장/승격을 의미하지 않는다.

## 권한 경계

```text
External LLM output eval/exec 금지
Authoring Lane의 AXIS 2 selection 실행 금지
Authoring Lane의 AXIS 3 CRUD/promotion 실행 금지
Authoring Lane의 AXIS 1 backtest/order 실행 금지
frozen legacy core 수정/import 금지
```

## User-local PASS evidence

```text
test_external_llm_authoring_lane.py = OK
test_three_axis_e2e_bridge.py = OK
test_axis3_crud_orchestration.py = OK
test_axis1_capability_diagnostic_registry.py = OK
test_frozen_legacy_core_guard.py = OK
```

Assertions/contracts were not weakened and frozen `core/` was not modified.

Step 13 Continuous Improvement analysis tooling may now begin.
