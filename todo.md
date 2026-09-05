# todo.md

Status: **ACTIVE TODO / NEXT-1C DIRECT UI WYSIWYG / TWO-DOCUMENT AUTHORITY TRUSTED**

이 문서는 현재 상태와 다음 할 일의 유일한 authority다. 원칙은 `rules.md`만 따른다.

## 1. 현재 위치

제품 흐름:

```text
Strategy Manager CRUD/validation
-> strategy별 Parameter Profile CRUD
-> validated strategy/version/profile Chart apply
-> authoritative DSL signal/execution WYSIWYG
-> strategy Backtest Dialog
-> same DSL/version/profile Paper
-> evidence comparison / minimal fine tuning
-> limited Live
```

현재는 **NEXT-1C production composition + actual Strategy Manager CRUD WYSIWYG**다.

운영문서 authority 복구와 compact focused 검증은 사용자 local **PASS**로 닫혔다.

## 2. 저장소 / 작업공간

### DSL

```text
repo: hoonoh57/dsl
branch: main
workspace: E:\2026\gemini\dsl-main-validation-20260904
```

기존 trusted executable/test:

```text
27882d288f52c98ab48a59b0d7ae2c2de0dcd637
```

NEXT-1C DSL mount:

```text
2cdc5096fd49f684f07c0b0fdf59c470545330a5
mount-focused: user-local PASS
```

현재 UI launcher executable candidate:

```text
3b5dc49bf74ae15f5c165a6637323c8c06bb5cbe
scripts/start_strategy_ui.ps1
status: REMOTE_UNVALIDATED / WYSIWYG NEXT
```

`strategies.db` 수정 상태는 reset/stash하지 않는다.

### Chart

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
workspace: E:\2026\gemini\cascade-chart-validation-20260904
```

기존 trusted checkpoint:

```text
23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
```

NEXT-1C production composition base candidate:

```text
e99bde72886c0afea04e07bfab0bd25fa8ab15b8
```

현재 direct-UI candidate:

```text
e132425be4508674167420b96a44de5b4cc19984
status: REMOTE_UNVALIDATED / WYSIWYG NEXT
```

추가 범위는 UI/composition뿐이다.

```text
ManagerAddon
 -> generic Strategy Manager open request 수신

STEP 4 전략선택 화면
 -> `전략 관리자 열기` 버튼 직접 노출
 -> 전략 의미 계산 없음

operator-entry-route
 -> ?stage=strategies&manager=1
 -> STEP 4 진입
 -> existing generic context-action이 준비되면 Dialog 자동 open
```

## 3. 4축/authority 유지 확인

직접 UI 경로는 다음 계약만 사용한다.

```text
Operator shell
 -> UI open request / generic context action
 -> Strategy Manager Add-on
 -> StrategyWorkspacePort
 -> Browser HTTP Bridge
 -> DSL StrategyWorkspace
 -> core.db / BacktestEngine
```

금지된 권한 이동 없음:

```text
Chart parser 없음
Chart local validation 없음
Chart DB 접근 없음
UI object persistence authority 없음
Bridge의 DSL 의미 해석 없음
```

## 4. 지금 바로 할 일 — 실제 화면 검증

더 이상의 사전 자동검증 단계를 추가하지 않는다. **화면을 먼저 본다.**

두 workspace를 최신 remote로 맞춘 뒤 DSL workspace에서 단 한 명령으로 실행한다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\start_strategy_ui.ps1
```

launcher 동작:

```text
DSL server hidden start
+ Chart server hidden start
+ bridge readiness 확인
+ browser open
+ STEP 4 전략선택 진입
+ Strategy Manager Dialog 자동 open
```

성공 콘솔은 1줄만 허용한다.

```text
[PASS] Strategy UI ready: http://127.0.0.1:5174/?stage=strategies&manager=1
```

실패하면 `[ERROR]/[FAIL]` block만 전달한다.

중지:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\start_strategy_ui.ps1 `
  -Action Stop
```

## 5. 화면 acceptance

Dialog가 바로 뜨면 다음만 실제로 확인한다.

```text
1. Strategy Manager · DSL Dialog가 화면에 보임
2. 신규
3. 전략명/설명/DSL 편집
4. Draft 저장
5. Dialog 닫기 -> STEP 4의 `전략 관리자 열기` 버튼으로 재오픈
6. draft 복구 확인
7. 검증 후 저장
8. VALIDATED + version + SHA 표시 확인
9. 닫기/재오픈 -> exact validation 복구
10. DSL 한 글자 수정 -> 즉시 DRAFT 표시
11. 재검증 -> 새 version
12. 삭제
13. 재오픈 -> 삭제 유지
```

화면이 이상하면 스크린샷 또는 화면에 보이는 오류만 전달한다. 긴 성공 로그는 전달하지 않는다.

## 6. NEXT-1C 종료 조건

실제 WYSIWYG가 PASS한 뒤에만 compact Full을 한 번 수행한다.

```text
WYSIWYG PASS
-> Tactical P1 Full PASS
-> NEXT-1C trusted checkpoint 승격
-> todo.md 갱신
```

그 전에는 NEXT-2로 넘어가지 않는다.

## 7. NEXT-1C 이후

```text
NEXT-2 Global Parameter Catalog + strategy override CRUD
  - common schema/default
  - strategy별 override CRUD
  - reset one/all = override delete
  - Backtest/Paper/Live mode applicability

NEXT-3 validated strategy/version/profile -> selected Chart subject
  - authoritative DSL signal/execution projection

NEXT-4 strategy Backtest Dialog

NEXT-5 same DSL/version/profile realtime Paper
  -> evidence comparison
  -> minimal fine tuning
  -> limited Live
```

## 8. 연구 상태

```text
Strategy1 JMA baseline: preserved evidence
fixed stop 6/8/10%: REJECTED
REALDATA2/LF: PAUSED
adaptive learning: PAUSED
automatic selection/allocation: PAUSED
broader compliance: REMEDIATION_REQUIRED
```
