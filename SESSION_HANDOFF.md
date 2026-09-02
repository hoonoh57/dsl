# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / COMPARE RUNTIME OWNERSHIP REMOTE PASS / USER-LOCAL REVALIDATION PENDING / 2026-09-02 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local 결과 + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 정상 콘솔은 최종 `[PASS]` 한 줄만, 실패 시에는 실패한 부분의 오류 구간만 제한된 길이로 출력한다. 전체 원시 로그는 내부 파일에 유지한다.

> 실제 UI 재현이 자동검증보다 우선한다. 실제 UI 실패 상태에서는 PASS로 닫지 않는다.

> 모든 production 로직 수정 전에 `DSL_IMPLEMENTATION_COMPLIANCE_GATE.md`를 먼저 적용한다. 구조가 불명확하면 코드를 쓰지 않고 generic engine 경로를 먼저 추적한다.

## 현재 상태

```text
PREVIOUS REMEDIATION = Steps 1 through 15 COMPLETE / USER-LOCAL PASS
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
STATUS = COMPARE RUNTIME OWNERSHIP REFACTOR REMOTE PASS / USER-LOCAL REVALIDATION PENDING
```

## 확정된 근본 원인

저장 JSON 자체가 틀린 것이 아니었다.

```text
JSON에는 compare-1 / compare-2 / compare-3 + layout 존재
Runtime 실제 object graph에는 compare pane missing
```

비교종목만 일반 Add-on lifecycle을 우회하여 JSON state authority와 persistent object lifecycle authority가 분리되어 있었다.

구 위반 구조:

```text
JSON compare node
 -> registered Runtime Add-on: state normalize only
 -> UI Workspace / ShellController: persistent compare pane 직접 생성
```

## 현재 구현된 단일 정상 경로

```text
chart-state JSON
 -> Runtime registration/reconcile
 -> Compare Runtime Add-on
 -> generic subjectViews / ChartSubjectViewManager
 -> persistent compare pane
```

UI shell은 다음만 수행한다.

```text
add / replace / remove / select / timeframe
 -> state-port write
```

UI의 pane / bar-window / projection / legend 생성·복원 권한은 제거되었다.

## 실제 실행 repo 연결

```text
dsl-live-studio
 -> vendor/kiwoom-condition
 -> condition1516/chart-platform
```

현재 `dsl-live-studio`의 `vendor/kiwoom-condition` gitlink는 다음 검증 완료 commit을 가리킨다.

```text
kiwoom-condition/main = 1d7277eb2040c6d7c79a243573d2598bc5c8584c
```

해당 Chart platform 원격 검증:

```text
Add-on boundary audit = PASS
Chart platform npm test = 93 / 93 PASS
```

이는 이번 변경분 검증이며 repository-wide compliance clearance를 뜻하지 않는다.

## 신규 구현 준수 게이트

`DSL_IMPLEMENTATION_COMPLIANCE_GATE.md`가 active authority다.

production 수정 전에 반드시:

```text
owner boundary
existing generic engine path
state SSOT
persistent object lifecycle authority
forbidden adjacent-layer behavior
architecture invariant regression
```

을 확정한다.

`verify.bat`은 기능 테스트보다 먼저 architecture-compliance와 generic Add-on boundary audit을 실행하고, compare runtime ownership 회귀검증도 포함한다.

## 지금 사용자에게 요청할 검증

사용자 작업 브랜치는 `main`이 아니라 `dsl-live-studio`다.

로컬 dirty state (`strategies.db`, `artifact_history/...`)를 보존한 채 다음 순서만 사용한다.

```text
git pull --ff-only
git submodule update --init --recursive
verify.bat
```

그 뒤 실제 UI에서 다음을 확인한다.

```text
비교종목 추가
선택 비교종목 교체
선택
삭제
pane 높이 변경 후 재기동 복원
저장된 비교종목 pane의 재기동 자동 복원
TF 동기
동일지표 ON/OFF
```

가장 중요한 acceptance는 재기동 후 별도 재조회/재추가 없이 저장된 compare pane이 Runtime object graph에 자동 복원되는 것이다.

## 절대 금지

```text
origin/main pull로 현재 작업브랜치를 섞지 않는다.
reset --hard로 user-local generated/state evidence를 지우지 않는다.
UI-created persistent comparison panes를 되살리지 않는다.
Runtime restore path와 UI restore path를 동시에 두지 않는다.
Core/Runtime에 feature-specific compatibility branch를 넣지 않는다.
test allowlist/assertion weakening/fallback으로 green을 만들지 않는다.
실제 UI PASS 전 UIA-1 완료를 선언하지 않는다.
repository-wide compliance PASS를 선언하지 않는다.
```

## Frozen legacy Core

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제 금지.
