# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / GENERIC SUBJECT RESTORE ATOMICITY REMOTE PASS / USER-LOCAL REVALIDATION PENDING / 2026-09-03 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local 결과 + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 실제 UI 재현이 자동검증보다 우선한다. 실제 UI 실패 상태에서는 PASS로 닫지 않는다.

> 모든 production 수정 전에 4축을 먼저 검증한다: Core = generic drawing/rendering SSOT, Runtime = feature-blind lifecycle/capability, Add-on = feature semantics/private state, JSON = persistence only.

> 구조 위반을 height fallback, UI restore path, test 완화로 숨기지 않는다.

## 현재 상태

```text
PREVIOUS REMEDIATION = Steps 1 through 15 COMPLETE / USER-LOCAL PASS
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
STATUS = GENERIC SUBJECT RESTORE ATOMICITY REMOTE PASS / USER-LOCAL REVALIDATION PENDING
```

## 4축 단일 정상 경로

```text
JSON persistence
 -> Runtime registration/reconcile
 -> Compare Add-on semantics
 -> generic Runtime subjectViews / ChartSubjectViewManager
 -> generic pane layout/rendering primitives
```

UI shell은 add / replace / remove / select / timeframe state command만 수행한다. UI의 persistent pane / bar-window / projection / legend 생성·복원 권한은 없다.

## 최신 실제 UI 실패

이전 startup race 수정 `b6ca51b` 적용 후에도 실제 재기동에서 다음 오류가 재현됐다.

```text
compare-1 height expected 52 actual missing
compare-2 height expected 108 actual missing
compare-3 height expected 327 actual missing
```

`actual missing`은 높이 값 계산 문제가 아니라 Runtime의 live pane record 부재다.

## 추가 확인된 근본 원인

generic `ChartSubjectViewManager.replace()`가 복원 도중 subject 하나라도 실패하면 해당 실패 view의 pane은 폐기했지만 owner signature를 남길 수 있었다. 일부 성공 view도 owner에 남는 비원자 상태가 가능했다.

그 뒤 같은 JSON/signature 재시도가 오면 기존 구현은 signature만 보고 settled로 즉시 return할 수 있었다. 이 경우 실제 pane이 없거나 일부만 존재해도 상위 `whenIdle()`은 성공처럼 끝날 수 있고, 최종 layout audit에서 `actual missing`이 발생한다.

## 현재 수정

수정은 feature-blind Runtime 한 곳으로 제한했다.

```text
ChartSubjectViewManager.replace
 -> same signature no-op 조건 = 실제 mounted view count까지 완전 일치
 -> subject restore 하나라도 실패 = 해당 owner가 이번 revision이면 owner 제거
 -> 이번 replace에서 생성된 모든 성공 view/pane도 rollback
 -> 같은 signature 재시도 = 실제 전체 rebuild
```

추가 generic regression은 2개 subject 중 두 번째가 일시 실패하는 상황에서:

```text
첫 replace = reject
부분 성공 pane 포함 active panes = 0
동일 signature 재시도 = 두 subject 모두 다시 생성
최종 active panes = 2
```

를 강제한다.

## 4축 준수 판정

```text
Core = 변경 없음
Runtime = generic subject lifecycle atomicity만 수정 / compare 문자열·분기 없음
Add-on = 변경 없음
JSON = 변경 없음 / 실행 권한 추가 없음
UI alternate restore path = 없음
pane height fallback = 없음
```

Add-on boundary audit와 전체 Chart platform test가 PR #3 및 main push에서 PASS했다.

## 실제 실행 repo 연결

```text
dsl-live-studio
 -> vendor/kiwoom-condition
 -> condition1516/chart-platform
```

검증 완료 Chart commit:

```text
kiwoom-condition/main = e272e18adbb4530f0edfe5046a19e3b7e0272606
```

원격 evidence:

```text
PR #3 Add-on boundary audit = PASS
PR #3 npm test = PASS
main push Verify chart platform = PASS
```

이는 이번 변경분 검증이며 repository-wide compliance clearance를 뜻하지 않는다.

## 지금 사용자에게 요청할 검증

사용자 작업 브랜치는 `dsl-live-studio`다. 기존 generated/state evidence와 `chart-state.json`을 삭제하지 않는다.

```text
git pull --ff-only
git submodule update --init --recursive
.\verify.bat
```

그 뒤 동일 저장 상태로 Market Chart를 완전 종료/재기동한다.

최우선 acceptance:

```text
별도 재조회/재추가 없이 compare-1/2/3 자동 복원
52 / 108 / 327 저장 높이 복원
STATE RESTORE ERROR 없음
```

통과 후 add / replace / select / delete / TF sync / 동일지표 ON/OFF를 확인한다.

## 절대 금지

```text
origin/main pull로 현재 작업브랜치를 섞지 않는다.
reset --hard로 user-local generated/state evidence를 지우지 않는다.
UI-created persistent comparison panes를 되살리지 않는다.
Runtime restore path와 UI restore path를 동시에 두지 않는다.
Core/Runtime에 feature-specific compatibility branch를 넣지 않는다.
JSON을 live object authority로 만들지 않는다.
pane height workaround로 missing pane을 숨기지 않는다.
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
