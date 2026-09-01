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

기존 strict remediation Steps 1~15는 모두 **COMPLETE / USER-LOCAL PASS**다.

```text
Step 1  legacy capability audit
Step 2  migration manifest/boundaries
Step 3  frozen core guard
Step 4  AXIS 1 migration parity
Step 5  additive DSL/execution capabilities + verification
Step 6  capability/diagnostic registry
Step 7  common Bridge + AXIS 1 execution contract
Step 8  AXIS 2 exact-as-of snapshot
Step 9  AXIS 2 selection engine
Step 10 AXIS 3 CRUD + orchestration
Step 11 three-axis E2E Bridge
Step 12 External LLM authoring lane
Step 13 Continuous Improvement analysis
Step 14 final natural-language E2E acceptance
Step 15 repo-wide compliance + legacy-document disposition
```

Final baseline checkpoint:

```text
STEP15_REPO_WIDE_COMPLIANCE_CHECKPOINT_2026-09-01.md
```

이 baseline PASS는 유지되며 UI acceptance는 별도 신규 제품 검증 tranche다.

## Current active work — UI consistency acceptance

목적:

```text
지금까지 이식한 DSL 기능을 실제 UI에서 기능별로 실행
 -> UI 입력 의미
 -> Bridge/Runtime 전달
 -> deterministic engine 실행
 -> 화면 표시
 -> JSON 저장/복원
이 전 구간에서 의미가 동일한지 확인
```

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

수정은 오류 원인을 먼저 분류한 뒤 해당 계층에서만 수행한다.

금지:

```text
UI 통과를 위한 Core 결과 덮어쓰기
Bridge/Runtime의 지표·전략·선별 재계산
Add-on 요구를 Core 특례로 흡수
JSON persistence의 계산/자동보정
cross-axis 직접 내부의존
검증 assertion 약화
repository-root frozen core 수정
```

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
Continuous Improvement = evidence analysis only; automatic mutation 없음
Chart/UI = supplied result/projection 표시 + user interaction, 계산 authority 없음
```

## AXIS 1 support truth

현재 지원 여부의 machine-readable SSOT:

```text
axes/axis1_dsl/core/capability_diagnostic_registry.py
```

Historical static Feature Catalog count는 현재 지원 여부의 권한이 아니다.

## Frozen legacy Core

repository-root `core/`는 영구 불변이다.

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under `core/`.

## Next action

```text
사용자가 UI에서 첫 DSL 기능을 실행
 -> 결과 또는 오류 evidence 공유
 -> 계층 분류
 -> 필요 시 최소 수정 + regression
 -> 동일 UI 동작 재검증
```
