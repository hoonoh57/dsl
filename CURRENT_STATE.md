# Quant DSL Current State

Status: **FINAL THREE-AXIS BASELINE PASS / UI CONSISTENCY ACCEPTANCE ACTIVE**  
Updated: 2026-09-02 KST

## Recovery authority

```text
1. SESSION_HANDOFF.md
2. DSL_NEXT_WORK_ORDER.md
3. CURRENT_STATE.md
4. DSL_DOCUMENT_AUTHORITY_INDEX.md
5. DSL_IMPLEMENTATION_COMPLIANCE_GATE.md
6. active architecture/policy documents
7. checkpoints/evidence
8. historical documents
```

## Current branch

```text
dsl-live-studio
```

`main`은 현재 작업 권한이 아니다.

기존 strict remediation Steps 1~15는 모두 **COMPLETE / USER-LOCAL PASS**다.

## Current active work — UIA-1

목표:

```text
meaningful UI state
 -> one logical Chart State
 -> one JSON persistence path
 -> Runtime-owned object graph
 -> next-session semantic exact restore
```

canonical runtime state:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

## Latest real-UI failure

```text
persisted compare-1 / compare-2 / compare-3 pane missing
```

이 오류는 저장 JSON이 틀렸다는 뜻이 아니라 JSON에 존재하는 persistent object가 Runtime에서 생성되지 않았다는 뜻이다.

## Root cause now confirmed

기본 차트 엔진을 다시 추적한 결과 `research.compare-subjects`만 일반 Add-on lifecycle을 우회하고 있었다.

```text
현재 위반 구조
JSON compare node
 -> registered Runtime Add-on: state normalize only
 -> UI Workspace / ShellController: compare pane 직접 생성
```

따라서 JSON state authority와 object lifecycle authority가 둘로 갈라져 선택적 복원 실패가 발생했다.

정상 구조는 다음 하나뿐이다.

```text
JSON compare node
 -> Runtime registration/reconcile
 -> Compare Runtime Add-on
 -> generic subjectViews capability
 -> compare pane create/dispose/visible/state
```

UI shell은 add/replace/remove/select를 state-port에 기록하는 역할만 갖는다.

## Implementation compliance gate

`DSL_IMPLEMENTATION_COMPLIANCE_GATE.md`를 신규 active authority로 추가했다.

모든 production 수정 전에 반드시:

```text
owner boundary 확정
existing generic engine end-to-end 추적
state SSOT 확정
persistent object lifecycle authority 확정
금지 인접계층 명시
architecture invariant test 선행
```

을 수행한다.

`verify.bat`은 이제 기능 테스트보다 먼저 `architecture-compliance`를 실행한다. 구조 위반이면 후속 behavior test가 PASS여도 전체 검증은 FAIL이다.

현재 compare 구현은 새 architecture gate가 의도적으로 차단해야 하는 known violation이다. 이 위반을 제거하기 전 추가 높이/비율/타이밍 보정은 금지한다.

## Four-boundary authorities

제품 실행:

```text
AXIS 1
AXIS 2
AXIS 3
Bridge
```

UI/Chart:

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

두 경계를 모두 통과해야 구현 가능하다.

## Current status

```text
LATEST REAL UI FAILURE = CONFIRMED
COMPARE OBJECT-LIFECYCLE AUTHORITY VIOLATION = CONFIRMED
IMPLEMENTATION COMPLIANCE POLICY = ACTIVE
ARCHITECTURE GATE = INSTALLED
NEXT = REFACTOR COMPARE TO RUNTIME-OWNED JSON ATTACH/DETACH
USER-LOCAL REVALIDATION = NOT REQUESTED YET
UIA-1 = NOT PASS YET
```

## Frozen legacy Core

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under repository-root `core/`.
