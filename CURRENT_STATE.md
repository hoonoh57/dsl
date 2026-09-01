# Quant DSL Current State

Status: **FINAL THREE-AXIS BASELINE PASS / UI CONSISTENCY ACCEPTANCE ACTIVE**  
Updated: 2026-09-01 KST

## Recovery authority

세션 전환 시 읽는 순서:

```text
1. SESSION_HANDOFF.md
2. DSL_NEXT_WORK_ORDER.md
3. CURRENT_STATE.md
4. DSL_DOCUMENT_AUTHORITY_INDEX.md
5. active architecture/policy documents
6. checkpoints/evidence
7. historical documents
```

## Current branch

```text
dsl-live-studio
```

`main`은 현재 작업 권한이 아니다.

## Completed baseline

기존 strict remediation Steps 1~15는 모두 **COMPLETE / USER-LOCAL PASS**다. Final baseline checkpoint는 `STEP15_REPO_WIDE_COMPLIANCE_CHECKPOINT_2026-09-01.md`다.

이 baseline PASS는 유지되며 UI acceptance는 별도 신규 제품 검증 tranche다.

## Current active work — UI consistency acceptance

목적:

```text
UI 입력/복원
 -> Bridge/Runtime 전달과 lifecycle
 -> deterministic engine
 -> Add-on 조합/표시
 -> JSON 저장/복원
```

전 구간의 의미가 일관적인지 실제 UI에서 하나씩 확인한다.

현재 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
```

수정 계층 분리:

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

## UIA-1 — startup restore

발견:

```text
프로그램 시작 직후 toolbar/state만 보이고 primary candle chart는 빈 화면
수동 조회 후에는 candle/indicator render 정상 시작
```

분류:

```text
Bridge / Runtime startup ordering defect
```

원인과 수정:

```text
기존: persistence hydrate -> UI/runtime wiring -> READY
수정: persistence hydrate -> UI/runtime wiring -> existing loadInitial() 1회 await -> READY
```

chart-platform shell/runtime만 최소 수정했고 focused regression을 추가했다. DSL branch는 수정된 chart-platform submodule revision을 pin한다.

변경하지 않은 것:

```text
AXIS1 DSL/Core 계산
Add-on 전략/timeframe 검증
JSON persistence schema/state 의미
repository-root frozen core
```

현재 보이는 `1일 chart vs DSL 1m` 오류는 별도 Add-on fail-closed validation이며 startup candle 복원과 혼합하지 않는다.

UIA-1은 아직 **REMOTE_UNVALIDATED**다. user-local focused regression과 실제 UI 재시작 확인 전 PASS로 닫지 않는다.

## Final product architecture

```text
AXIS 2 exact-PIT selection
 -> Candidate Set + evidence
 -> AXIS 3 exact promoted Condition/Strategy versions + RunPlan
 -> versioned Bridge all-candidate preflight
 -> AXIS 1 deterministic single-instrument execution
```

권한:

```text
AXIS 1 = DSL parser/semantic/runtime/indicators/state/execution/backtest/projection
AXIS 2 = precomputed immutable PIT snapshot consumption + filter/rank/top-N/evidence
AXIS 3 = Condition/Strategy immutable version lifecycle + lineage + promotion + orchestration
Bridge = data-only contracts + explicit cross-axis composition
External LLM = proposal-only authoring
Continuous Improvement = structured evidence analysis only; automatic mutation 없음
Chart/UI = supplied result/projection 표시 + user interaction, 계산 authority 없음
```

## Frozen legacy Core

repository-root `core/`는 영구 불변이다.

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under `core/`.
