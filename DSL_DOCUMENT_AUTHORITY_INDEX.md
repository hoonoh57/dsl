# DSL Document Authority Index

Status: **DOCUMENT AUTHORITY SSOT / ACTIVE / 2026-09-01 KST**

이 문서는 루트에 누적된 설계·실험·구현 기록이 최신 제품 권한과 충돌하지 않도록 문서의 지위를 고정한다.

## 1. 읽는 순서

새 세션 또는 작업 재개 시 우선순위는 다음과 같다.

```text
1. SESSION_HANDOFF.md
2. DSL_NEXT_WORK_ORDER.md
3. CURRENT_STATE.md
4. DSL_DOCUMENT_AUTHORITY_INDEX.md
5. 현재 active architecture/policy 문서
6. checkpoint/evidence 문서
7. historical 문서
```

더 최신의 user-local PASS evidence와 사용자 결정이 오래된 문서보다 우선한다.

## 2. ACTIVE AUTHORITY

현재 제품 구조와 운영 규칙을 정의한다.

```text
SESSION_HANDOFF.md
DSL_NEXT_WORK_ORDER.md
CURRENT_STATE.md
DSL_DOCUMENT_AUTHORITY_INDEX.md
DSL_THREE_AXIS_FINAL_TARGET.md
DSL_THREE_AXIS_MODULE_BOUNDARY.md
DSL_FROZEN_CORE_MIGRATION_POLICY.md
DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md
DSL_EXTERNAL_LLM_STRATEGY_AUTHORING_POLICY.md
DSL_AUTHORING_CONTINUOUS_IMPROVEMENT_POLICY.md
DSL_HUMAN_COMMUNICATION_OUTPUT_POLICY.md
```

Axis-local README는 각 package의 현재 책임을 설명하는 보조 active 문서다.

```text
axes/axis1_dsl/README.md
axes/axis2_selection/README.md
axes/axis3_monetization/README.md
```

## 3. FROZEN AUDIT / MIGRATION EVIDENCE

다음 문서는 당시 결정과 검증 근거를 보존한다. 현재 런타임 권한을 새로 정의하지 않는다.

```text
DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
DSL_AXIS1_MIGRATION_MANIFEST.md
STEP*_CHECKPOINT_*.md
STEP*.md 형태의 완료 checkpoint
```

Checkpoint는 완료 사실의 evidence이며 active architecture를 덮어쓸 수 없다.

## 4. HISTORICAL / NON-AUTHORITATIVE

기존 연구·실험·구현 tranche 문서는 삭제하지 않고 역사적 기록으로 보존한다. 아래 범주의 문서는 현재 architecture/runtime SSOT가 아니다.

```text
DSL_LIVE_STUDIO_FEATURE_CATALOG_V2.md
DSL_LIVE_STUDIO_FEATURE_CATALOG_V3.md
DSL_LIVE_STUDIO_FEATURE_CATALOG_V4.md
CTX*.md
E*.md
H*.md
ADAPTIVE_*.md
과거 범위탐지/실험/sidecar/개별 integration implementation 기록
```

이 문서들의 예전 경로, 상태, feature count, 실험 결론은 현재 machine-readable capability registry, 3축 architecture, Bridge contract 또는 최신 checkpoint와 충돌할 경우 적용하지 않는다.

특히 정적 Feature Catalog 문서의 과거 개수는 현재 기능 지원 SSOT가 아니다.

```text
current support SSOT = axes/axis1_dsl/core/capability_diagnostic_registry.py
현재 축 경계         = DSL_THREE_AXIS_MODULE_BOUNDARY.md
현재 실행 순서       = DSL_NEXT_WORK_ORDER.md
현재 완료상태         = CURRENT_STATE.md + latest checkpoint
```

## 5. 최종 권한 분리

```text
AXIS 1 = single-instrument deterministic DSL/runtime/execution
AXIS 2 = immutable exact-PIT selection semantics, filter/rank/top-N/evidence
AXIS 3 = versioned Condition/Strategy artifact lifecycle + orchestration
Bridge = versioned Request -> Response composition only
External LLM = proposal only
Continuous Improvement = evidence analysis only; automatic mutation 없음
Chart = supplied projection/evidence 표시; 계산 권한 없음
```

Condition의 **선별 의미**는 AXIS 2가 소유하고 Condition의 **버전/계보/승격 lifecycle**은 AXIS 3가 소유한다.

## 6. Legacy core

repository-root `core/`는 historical reference이자 immutable frozen tree다.

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

현재 제품 코드는 frozen `core/`를 신규 기능 개발 위치나 permanent runtime dependency로 사용하지 않는다.

## 7. 문서 변경 원칙

새 architecture 결정이 생기면 먼저 active authority 문서를 갱신한다. historical 문서를 과거 사실 보존 목적으로 다시 쓰지 않는다.

오래된 문서와 현재 문서가 충돌할 때 compatibility exception을 추가하는 대신 이 authority index와 active 문서를 기준으로 충돌을 제거한다.
