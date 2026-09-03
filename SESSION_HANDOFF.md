# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / STARTUP RESTORE RACE FIX REMOTE PASS / USER-LOCAL REVALIDATION PENDING / 2026-09-03 KST**

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
STATUS = STARTUP RESTORE RACE FIX REMOTE PASS / USER-LOCAL REVALIDATION PENDING
```

## 현재 단일 정상 구조

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

UI의 pane / bar-window / projection / legend 생성·복원 권한은 제거된 상태를 유지한다.

## 2026-09-03 실제 UI 재기동 실패

사용자 로컬 자동검증은 다음 상태에서 PASS했다.

```text
dsl-live-studio = 3c4dcff
vendor/kiwoom-condition = 1d7277e
verify.bat = [PASS] current verification passed
```

그러나 실제 재기동 acceptance에서는 다음 fail-closed 오류가 발생했다.

```text
compare-1 height expected 52 actual missing
compare-2 height expected 108 actual missing
compare-3 height expected 327 actual missing
workspace primary/recent instrument name expected "" actual resolved name
```

분류:

```text
PRIMARY = PRODUCT DEFECT / startup restore completion race
SECONDARY = runtime audit semantic drift / instrument display-name enrichment
```

pane height 값 자체의 계산 오류로 분류하지 않는다. `actual missing`은 감사 시점에 live pane record가 완성되지 않았음을 뜻했다.

## 근본 원인과 수정

`CompareSubjectsRuntimeAddon`의 연속 reconcile이 같은 owner/signature에 대해 겹칠 수 있었고, 최신 `#pending`이 이전 실제 pane 생성 작업보다 먼저 끝날 수 있었다. 그 결과 `whenIdle()`이 restore completion authority가 되지 못하는 경쟁조건이 있었다.

수정:

```text
Compare Runtime reconcile = serialized promise chain
whenIdle() = all prior/in-flight compare lifecycle work 포함
same-owner reconcile overlap = forbidden by regression test
```

또한 startup에서 종목명이 catalog/API로 보강되는 것은 instrument identity 변경이 아니므로 runtime-state audit은 `name`을 비권위 표시 메타데이터로 취급한다. `kind + code` identity는 계속 엄격 검증한다.

금지사항은 그대로다.

```text
pane 높이 보정으로 missing을 숨기지 않음
UI restore path 재도입 금지
Core feature-specific branch 금지
code/kind identity audit 완화 금지
```

## 실제 실행 repo 연결

```text
dsl-live-studio
 -> vendor/kiwoom-condition
 -> condition1516/chart-platform
```

현재 검증 완료 Chart commit:

```text
kiwoom-condition/main = b6ca51b5256349bf3f0dea2ede3c45449cd2e34a
```

원격 검증 evidence:

```text
PR #2 Add-on boundary audit = PASS
PR #2 Chart platform npm test = PASS (95 tests)
main push Verify chart platform = PASS
```

이는 이번 변경분 검증이며 repository-wide compliance clearance를 뜻하지 않는다.

## 지금 사용자에게 요청할 검증

사용자 작업 브랜치는 `main`이 아니라 `dsl-live-studio`다.

로컬 generated/state evidence를 보존한 채:

```text
git pull --ff-only
git submodule update --init --recursive
.\verify.bat
```

그 뒤 **기존 저장 JSON을 지우지 말고** 동일한 Market Chart를 완전 종료/재기동한다.

최우선 acceptance:

```text
별도 재조회/재추가 없이 compare-1/2/3 pane 자동 복원
저장된 pane 높이 복원
STATE RESTORE ERROR 없음
```

그 다음 add / replace / select / delete / TF sync / 동일지표 ON/OFF를 확인한다.

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
