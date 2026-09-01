# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-02 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local 결과 + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 정상 콘솔은 최종 `[PASS]` 한 줄만, 실패 시에는 실패한 부분의 오류 구간만 제한된 길이로 출력한다. 전체 원시 로그는 내부 파일에 유지한다.

> 실제 UI 재현이 자동검증보다 우선한다. 실제 UI 실패 상태에서는 PASS로 닫지 않는다.

## 현재 상태

```text
PREVIOUS REMEDIATION = Steps 1 through 15 COMPLETE / USER-LOCAL PASS
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
STATUS = UNMANAGED-PANE AUDIT FIX PINNED / USER-LOCAL AUTO + REAL UI REVALIDATION REQUIRED
```

## JSON 상태 권한

canonical runtime state file:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

한 문서에 workspace/display/addons/layout/geometry를 함께 보존한다.

단일 JSON 파일 존재만으로 SSOT PASS로 인정하지 않는다. 저장된 의미 상태가 실제 재기동 차트 전체 projection과 동일해야 한다.

## 최신 실제 UI failure evidence

전수복원 gate가 최근 다음을 보고했다.

```text
workspace.layout.primaryPanes.priceHeight mismatch
persisted compare-1 / compare-2 / compare-3 pane missing
```

viewport one-bar shift는 이후 수정으로 제거됐다.

## 최신 자동검증 failure evidence

2026-09-02 user-local `verify.bat`:

```text
[ERROR] chart-state-runtime-audit
```

원인은 저장 대상이 아닌 native pane 높이를 persisted ratio의 분모에 포함한 검증 계산 결함이었다.

수정 기준:

```text
persisted managed panes만 상대비율 비교
unmanaged native panes는 persisted ratio 분모에서 제외
persisted pane missing은 hard FAIL 유지
```

runtime audit과 layout stabilizer 양쪽 계산을 동일하게 수정했다.

## Restore gate

```text
hydrate
 -> primary runtime construction
 -> registered Add-ons
 -> primary request ready
 -> compare subjects
 -> persisted managed-pane ratio layout restore
 -> startup viewport reassert
 -> live runtime snapshot
 -> persisted-vs-live exhaustive audit
 -> PASS: persistence attach
 -> FAIL: persistence detached, existing JSON preserved, mismatches reported
```

## Pane layout 의미

저장된 pane 높이는 재기동 시 절대 픽셀이 아니라 저장 대상 pane들 사이의 상대 배치 비율이다.

저장 대상이 아닌 native pane이 존재해도 이 비율 판정에 섞지 않는다. 다만 저장된 pane 자체가 runtime에서 없으면 반드시 실패한다.

## 자동검증 범위

`verify.bat`에는 다음이 포함된다.

```text
whole-chart managed-pane ratio restore
unmanaged native pane coexistence
missing persisted pane fail-closed
compare-subject deferred restore
compare concrete failure propagation
startup viewport authority reassert
exhaustive runtime audit
single JSON persistence
workspace/product restart
console policy
frozen core guard
```

## 다음 사용자 실행

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```

자동검증 PASS 후에만 `start.bat`으로 실제 UI 재기동 검증을 다시 한다.

실제 UI PASS 전 UIA-1 완료 처리 금지.

## 계층 분리

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

- Core: deterministic 의미/계산. repository-root `core/`는 frozen reference이며 수정 금지.
- Bridge / Runtime: lifecycle/state routing/layout projection/runtime audit. 계산 금지.
- Add-ons: 기능별 계산과 private state.
- JSON persistence: serialization/hydrate/atomic write/stale-write rejection만 담당.

## Frozen legacy Core

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제 금지.
