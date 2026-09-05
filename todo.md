# todo.md

Status: **ACTIVE TODO / NEXT-1C BASE-CHART STRATEGY MANAGER WYSIWYG / TWO-DOCUMENT AUTHORITY TRUSTED**

이 문서는 현재 상태와 다음 할 일의 유일한 authority다. 원칙은 `rules.md`만 따른다.

## 1. 현재 위치

제품 흐름:

```text
Base Market Chart
-> Strategy Manager Add-on
-> DSL strategy CRUD / authoritative validation / immutable version
-> strategy별 Parameter Profile CRUD
-> validated strategy/version/profile Chart apply
-> authoritative DSL signal/execution WYSIWYG
-> Backtest Dialog
-> same DSL/version/profile Paper
-> limited Live
```

현재는 **NEXT-1C: 기본 Chart 위 Strategy Manager Add-on의 실제 CRUD WYSIWYG**다.

운영문서 authority 복구와 compact focused 검증은 사용자 local **PASS**다.

## 2. 핵심 UI 원칙 — 이번 교정

Strategy Manager는 Operator Workbench/전략선택 단계의 기능이 아니다.

```text
기본화면 = Market Chart
Strategy Manager = Chart Add-on
```

정상 UI 경로:

```text
MarketChartWorkspace
-> MarketChart
-> ChartRuntimeHost
-> strategy.manager Add-on
-> DslStrategyManagerUi
-> StrategyWorkspacePort
-> BrowserStrategyWorkspacePort
-> same-origin proxy
-> DSL StrategyWorkspace
```

2026-09-05에 잘못 추가했던 다음 경로는 모두 원복했다.

```text
Operator STEP 4 `전략 관리자 열기`
operator-entry-route
Operator shell의 Strategy Manager 직접 composition
```

Operator UI는 이번 NEXT-1C Strategy Manager 검증과 **무관**하다.

## 3. 저장소 / 작업공간

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

NEXT-1C DSL production mount:

```text
2cdc5096fd49f684f07c0b0fdf59c470545330a5
mount-focused: user-local PASS
```

현재 launcher candidate:

```text
5e81572b19a7ad9fd10bbb6598d64a9ccdb8584e
scripts/start_strategy_ui.ps1
```

launcher는 이제 Operator 화면이 아니라 다음 URL을 연다.

```text
http://127.0.0.1:5174/chart.html?manager=1
```

`strategies.db` 로컬 수정 상태는 reset/stash하지 않는다.

### Chart

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
workspace: E:\2026\gemini\cascade-chart-validation-20260904
```

trusted checkpoint:

```text
23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
```

NEXT-1C production composition base candidate:

```text
e99bde72886c0afea04e07bfab0bd25fa8ab15b8
```

이 base에는 이미:

```text
MarketChart
-> capabilities.strategyWorkspace = BrowserStrategyWorkspacePort

serve.mjs
-> same-origin StrategyWorkspace proxy
```

가 연결되어 있다.

현재 direct base-Chart WYSIWYG candidate:

```text
b49408291ef8ea870acccb803513a68f2a4a5e08
```

`e99bde7...` 대비 실제 diff는 두 파일뿐이다.

```text
chart.html
src/shell/chart-direct-entry.mjs
```

역할:

```text
chart.html
-> 기존 Market Chart만 전체 화면으로 host
-> Chart Add-on context menu/dialog companion 제공

chart-direct-entry.mjs
-> 기존 MarketChartWorkspace mount
-> ?manager=1이면 활성화된 strategy.manager Add-on의
   기존 `Strategy Manager…` context action만 자동 실행
```

Chart 전략 의미/DB/validation authority는 추가하지 않았다.

## 4. 4축 / authority 불변조건

```text
Chart = UX / Add-on host / visualization / Request-Response transport
DSL   = strategy source / CRUD / validation / version / Backtest semantics
```

금지 상태 유지:

```text
Chart parser 없음
Chart local DSL validation 없음
Chart DB 접근 없음
UI persistence authority 없음
Bridge 전략 의미 해석 없음
로컬 evaluator fallback 없음
```

## 5. 지금 바로 할 일 — 화면 먼저

자동테스트를 더 추가하지 않는다. 두 workspace를 최신 remote로 맞춘 후 **한 명령으로 실제 Chart + Add-on Dialog를 본다.**

DSL workspace:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\start_strategy_ui.ps1
```

기대:

```text
기본 Market Chart 전체화면
+ Strategy Manager · DSL Dialog 자동 open
```

성공 콘솔:

```text
[PASS] Strategy UI ready: http://127.0.0.1:5174/chart.html?manager=1
```

Dialog를 닫으면 **그 뒤에 기본 Chart가 그대로 보여야 한다.**

또한 Chart 영역 우클릭 시 기존 Add-on 메뉴의:

```text
Strategy Manager…
```

으로 같은 Dialog를 다시 열 수 있어야 한다.

## 6. 화면 acceptance

```text
1. 기본 Market Chart가 배경/기본화면으로 보임
2. Strategy Manager · DSL Dialog가 그 Chart 위에 Add-on으로 열림
3. Dialog 닫기 -> 기본 Chart로 복귀
4. Chart 우클릭 -> Strategy Manager… -> 동일 Dialog 재오픈
5. 신규 전략 작성
6. Draft 저장
7. 닫기/재오픈 -> draft 복구
8. 검증 후 저장 -> VALIDATED + version + SHA
9. DSL 한 글자 수정 -> 즉시 DRAFT
10. 재검증 -> 새 version
11. 삭제
12. 재오픈 -> 삭제 유지
```

화면이 이상하면 스크린샷 또는 화면의 오류만 전달한다. 긴 로그는 전달하지 않는다.

## 7. NEXT-1C 종료 조건

```text
실제 Base Chart + Add-on WYSIWYG PASS
-> compact Tactical P1 Full PASS
-> NEXT-1C trusted checkpoint 승격
-> todo.md 갱신
```

그 전에는 NEXT-2로 넘어가지 않는다.

## 8. NEXT-1C 이후

```text
NEXT-2 Global Parameter Catalog + strategy override CRUD
NEXT-3 validated strategy/version/profile -> selected Chart subject
NEXT-4 strategy Backtest Dialog
NEXT-5 same DSL/version/profile realtime Paper
-> evidence comparison / minimal fine tuning
-> limited Live
```

## 9. 연구 상태

```text
Strategy1 JMA baseline: preserved evidence
fixed stop 6/8/10%: REJECTED
REALDATA2/LF: PAUSED
adaptive learning: PAUSED
automatic selection/allocation: PAUSED
broader compliance: REMEDIATION_REQUIRED
```
