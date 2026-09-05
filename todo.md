# todo.md

Status: **ACTIVE TODO / NEXT-1C BASE-CHART STRATEGY MANAGER WYSIWYG / LAUNCHER MARKER FIX REMOTE_UNVALIDATED**

이 문서는 현재 상태와 다음 할 일의 유일한 authority다. 원칙은 `rules.md`만 따른다.

## 1. 현재 위치

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

운영문서 authority 복구와 compact focused 검증은 사용자 local PASS다. 지금은 자동테스트를 더 늘리지 않고 실제 UI를 우선 검증한다.

## 2. UI / 4축 authority

```text
기본화면 = Market Chart
Strategy Manager = Chart Add-on
```

정상 경로:

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

권한:

```text
Chart = UX / Add-on host / visualization / Request-Response transport
DSL   = strategy source / CRUD / validation / version / Backtest semantics
```

금지:

```text
Chart parser / local DSL validation / DB 접근
UI persistence authority
Bridge 전략 의미 해석
로컬 evaluator fallback
```

## 3. 저장소 / 작업공간

### DSL

```text
repo: hoonoh57/dsl
branch: main
workspace: E:\2026\gemini\dsl-main-validation-20260904
trusted executable/test: 27882d288f52c98ab48a59b0d7ae2c2de0dcd637
NEXT-1C mount-focused user PASS: 2cdc5096fd49f684f07c0b0fdf59c470545330a5
launcher executable candidate: daf1e338614667dbb7a6dfc461a45658ec397b27
```

launcher 계약:

```text
2xx만 READY
DSL /api/strategy-workspace/strategies 실제 2xx 확인
Chart /__cascade_health 실제 app marker 확인
ManagerAddon.mjs 실제 2xx + ASCII marker 확인
DslStrategyManagerUi.mjs 실제 2xx + ASCII marker 확인
확인 후에만 브라우저 open
```

`strategies.db` 로컬 수정 상태는 reset/stash하지 않는다.

### Chart

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
workspace: E:\2026\gemini\cascade-chart-validation-20260904
trusted checkpoint: 23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
NEXT-1C production composition base: e99bde72886c0afea04e07bfab0bd25fa8ab15b8
current direct WYSIWYG candidate: f968da7c1c6dc10c1a8f38920f68a191ea4084e8
```

포함:

```text
chart.html
src/shell/chart-direct-entry.mjs
src/addons/strategy/managed/ManagerAddon.mjs
scripts/serve.mjs
```

## 4. 실제 화면/서버 실패와 교정

### A. Manager module activation 실패

사용자 evidence:

```text
ADDON ERROR · [primary] Chart add-on strategy.manager activation failed:
Failed to fetch dynamically imported module: .../ManagerAddon.mjs
```

교정:

```text
ManagerAddon activation 필수경로
-> DslStrategyManagerUi
-> StrategyWorkspacePort

legacy ManagedStrategyCatalog/JMA graph
-> activation 이후 async compatibility-only
-> 실패해도 Manager CRUD activation을 막지 않음
```

### B. Chart server duplicate response crash

사용자 evidence:

```text
ERR_HTTP_HEADERS_SENT: Cannot write headers after they are sent to the client
scripts/serve.mjs sendJson()
```

분류:

```text
product/composition defect
```

교정:

```text
middleware가 이미 응답을 시작/완료했으면 다음 middleware로 넘기지 않음
이미 headers가 전송된 뒤 예외가 발생하면 상위 catch의 두 번째 sendJson 금지
서버 프로세스를 ERR_HTTP_HEADERS_SENT로 죽이지 않음
```

### C. Windows PowerShell 5.1 UI module marker 오판

사용자 evidence:

```text
[FAIL] Strategy Manager UI module is not being served by the active Chart process:
.../DslStrategyManagerUi.mjs
```

분류:

```text
launcher/test tooling defect
```

원인/교정:

```text
이전 marker: `Strategy Manager · DSL`
-> UTF-8 BOM 없는 .ps1을 Windows PowerShell 5.1이 읽을 때 비ASCII 문자 비교 오판 가능

현재 marker: `export class DslStrategyManagerUi`
-> ASCII only
-> 실제 모듈 identity만 확인
```

제품/Chart authority 코드는 이 교정에서 변경하지 않았다.

## 5. 지금 바로 할 일 — 화면만 재검증

DSL workspace에서 최신 main만 받은 뒤 launcher를 다시 한 번 실행한다. Chart workspace는 이미 `f968da7...`이면 추가 변경이 필요 없다.

기대 URL:

```text
http://127.0.0.1:5174/chart.html?manager=1
```

기대 화면:

```text
기본 Market Chart
+ Strategy Manager · DSL Dialog 자동 open
```

실패 시 launcher의 짧은 `[ERROR]/[FAIL]` 또는 화면 오류만 전달한다.

## 6. 화면 acceptance

```text
1. 기본 Market Chart가 보임
2. Strategy Manager · DSL Dialog 자동 open
3. Dialog 닫기 -> 기본 Chart
4. Chart 우클릭 -> Strategy Manager… -> 동일 Dialog
5. 신규 전략 작성
6. Draft 저장
7. 닫기/재오픈 -> draft 복구
8. 검증 후 저장 -> VALIDATED + version + SHA
9. DSL 한 글자 수정 -> 즉시 DRAFT
10. 재검증 -> 새 version
11. 삭제
12. 재오픈 -> 삭제 유지
```

## 7. NEXT-1C 종료 조건

```text
실제 Base Chart + Add-on WYSIWYG PASS
-> compact Tactical P1 Full PASS
-> trusted checkpoint 승격
-> todo.md 갱신
```

그 전에는 NEXT-2로 넘어가지 않는다.

## 8. 이후 순서

```text
NEXT-2 Global Parameter Catalog + strategy override CRUD
NEXT-3 validated strategy/version/profile -> selected Chart subject
NEXT-4 strategy Backtest Dialog
NEXT-5 same DSL/version/profile realtime Paper
-> evidence comparison / minimal fine tuning
-> limited Live
```

연구 상태:

```text
Strategy1 JMA baseline: preserved evidence
fixed stop 6/8/10%: REJECTED
REALDATA2/LF: PAUSED
adaptive learning: PAUSED
automatic selection/allocation: PAUSED
broader compliance: REMEDIATION_REQUIRED
```
