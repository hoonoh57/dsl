# Strategy Product Flow TODO

Status: **ACTIVE PRIMARY TODO / PROFIT-STRATEGY PATH / 2026-09-05 KST**

이 문서는 세션이 바뀌어도 현재 큰 흐름과 두 저장소의 역할을 잃지 않기 위한 실행 TODO다. `SESSION_HANDOFF.md` 다음으로 읽는다.

## 1. 최종 목표

```text
수익 아이디어
 -> DSL 전략 작성/저장
 -> authoritative DSL 검증/commit
 -> 역사 데이터 백테스트
 -> Chart WYSIWYG 신호/체결 검증
 -> 실시간 모의매매
 -> 백테스트 vs 모의매매 비교
 -> 최소 fine tuning
 -> 제한적 실거래
 -> 재검증
```

DSL/Chart 자체의 범용 기능 확장은 목적이 아니다. **현재 선택한 수익전략을 정확히 표현·검증·백테스트·모의매매하는 데 직접 필요한 결함/기능만 추가한다.**

## 2. 절대 경계

구현 전 항상 다음 순서를 확정한다.

```text
owner layer
 -> existing shared/common path
 -> state SSOT
 -> object create/delete authority
 -> adjacent-layer prohibitions
 -> one-boundary micro-tranche
 -> focused verification
 -> Full verification
 -> checkpoint
```

금지:

- Chart가 별도 전략 계산엔진/JMA 계산을 authoritative validator로 소유하지 않는다.
- DSL Core/Parser/Runtime/Backtest/Broker를 연구 편의나 UI 편의 때문에 수정하지 않는다.
- 동일 기능의 Runtime 복원경로 + UI 복원경로 같은 이중 권한을 만들지 않는다.
- test PASS를 위해 assertion/guard/contract를 약화하지 않는다.
- REALDATA2/LF research, adaptive learning, automatic selection/allocation은 현재 profit-strategy path와 직접 필요할 때까지 보류한다.
- 한 tranche에서 CRUD + Bridge + Chart apply + Backtest + Paper/Live를 동시에 구현하지 않는다.

## 3. 저장소/작업공간 분리 — 혼선 방지 필수

### DSL repository

```text
repo: hoonoh57/dsl
local validation workspace:
  E:\2026\gemini\dsl-main-validation-20260904
trusted executable/test SHA:
  01da3bc6b21c126efd6ffa3b220e2a34de5ef64b
```

DSL 책임:

- DSL source SSOT
- strategy CRUD persistence
- immutable artifact/version validation record
- authoritative DSL validation path
- existing `BacktestEngine` execution semantics
- later historical backtest result generation

현재 Strategy Workspace authoritative path:

```text
addons/strategy_manager/workspace.py
 -> core.db CRUD
 -> validate_and_commit()
 -> existing BacktestEngine.run(exact_dsl)
 -> artifact version + validation record
```

### Chart repository

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
local validation workspace:
  E:\2026\gemini\cascade-chart-validation-20260904
previous trusted external Chart checkpoint:
  258fd07ca76214819cec3822b02564e21a1c8680
current remote executable/test candidate:
  c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda
candidate status:
  REMOTE_UNVALIDATED until user-local focused tests pass
```

Chart 책임:

- DSL strategy editor/manager UX
- request -> response bridge client
- Runtime-owned generic chart state/subject selection
- authoritative DSL/backtest result를 시각화
- later strategy assignment display / WYSIWYG signal-execution projection

Chart가 소유하지 않는 것:

- DSL parser/runtime semantics
- local JMA strategy validator
- independent backtest engine
- broker/order execution authority
- SQLite/MySQL direct persistence authority from Add-on UI

## 4. 현재 완료된 큰 변화

### DSL side — DONE / TRUSTED

`01da3bc6b21c126efd6ffa3b220e2a34de5ef64b`

사용자 로컬 evidence:

```text
focused: Ran 7 tests / OK
Full: [PASS] Tactical P1 verification completed: mode=Full.
```

의미:

- `StrategyWorkspace`가 strategy CRUD를 기존 DB 경로로 수행한다.
- DSL 검증은 parallel parser가 아니라 existing `BacktestEngine.run()`을 사용한다.
- exact DSL bytes와 validation artifact/version이 연결된다.
- 새 세션/UI는 ephemeral client flag가 아니라 persisted validation artifact로 검증상태를 복원한다.

### Chart side — IMPLEMENTED REMOTELY / NOT YET LOCALLY TRUSTED

`c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda`

변경 범위:

```text
src/addons/strategy/managed/DslStrategyManagerUi.mjs
src/addons/strategy/managed/StrategyWorkspacePort.mjs
src/addons/strategy/managed/ManagerAddon.mjs
tests/dsl_strategy_manager_workspace_port.test.mjs
```

의미:

- Strategy Manager 신규 작성경로를 DSL-first editor로 전환.
- CRUD/검증은 `strategyWorkspace` Request -> Response port로만 요청.
- capability가 없으면 fail-closed.
- active authoring path가 Chart의 `evaluateManagedStrategy()` / JMA local evaluator로 fallback하지 않음.
- 기존 Runtime state/subject-view 구조는 다음 tranche를 위해 보존.
- 아직 production HTTP Bridge, 차트 적용, 백테스트 UI, paper/live는 추가하지 않음.

## 5. 지금 바로 할 일 — NEXT-0

**Chart candidate `c67d3d8...`의 local validation.**

중요: 이 명령은 DSL workspace가 아니라 반드시 Chart workspace에서 실행한다.

```powershell
Set-Location E:\2026\gemini\cascade-chart-validation-20260904

git fetch origin product-completion-mvp
git checkout --detach origin/product-completion-mvp
git rev-parse HEAD
```

기대 SHA:

```text
c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda
```

focused:

```powershell
node --test tests/dsl_strategy_manager_workspace_port.test.mjs
node --test tests/managed_strategy_addon.test.mjs
```

판정:

```text
둘 다 PASS
 -> c67d3d8...를 Chart trusted checkpoint로 승격
 -> NEXT-1 진행

FAIL
 -> 먼저 test defect / product defect / authority drift / environment issue / external data defect / unknown 분류
 -> assertion/guard 약화 금지
```

## 6. NEXT-1 — production StrategyWorkspace HTTP Bridge

NEXT-0가 PASS된 뒤에만 진행한다.

목적:

```text
Chart DslStrategyManagerUi
 -> StrategyWorkspacePort
 -> standard HTTP request/response bridge
 -> DSL addons/strategy_manager/workspace.py
 -> core.db / BacktestEngine
```

이 tranche에서만 구현할 것:

- list strategies
- save draft
- delete strategy
- validate + commit
- exact request/response schema
- bridge unavailable/error fail-closed

이 tranche에서 금지:

- 차트 신호 삽입
- historical backtest 화면
- paper/live execution
- Chart-side strategy calculation
- direct DB access from Chart

완료조건:

```text
focused Bridge contract PASS
+ existing Chart managed strategy regression PASS
+ DSL focused StrategyWorkspace PASS
+ appropriate Full verification PASS
```

## 7. NEXT-2 — authoritative strategy apply to Chart

NEXT-1이 trusted된 뒤 진행한다.

목적:

- 사용자가 검증된 DSL strategy를 선택 subject에 연결.
- Chart는 strategy 자체를 계산하지 않고 DSL authoritative result를 받는다.
- generic Runtime `subjectViews` / marker transport를 재사용한다.

먼저 정의해야 할 표준 result contract 예:

```text
strategy identity/version
instrument/timeframe identity
source/bar identity
signal events
execution events
indicator/overlay series needed for WYSIWYG
validation/backtest authority metadata
```

정확한 schema는 NEXT-2 시작 시 기존 DSL result 구조를 먼저 확인하고 최소 필드만 고정한다.

금지:

- Chart `StrategyModel.mjs`를 새 authoritative engine으로 부활
- DSL과 Chart가 각각 crossover/JMA/order timing을 재계산
- UI가 객체 생성권한과 실행권한을 동시에 소유

## 8. NEXT-3 — historical backtest from Chart

NEXT-2가 trusted된 뒤 진행한다.

흐름:

```text
selected validated DSL strategy
+ selected instrument/timeframe/history request
 -> DSL existing BacktestEngine
 -> authoritative report
 -> Chart report + WYSIWYG execution markers
```

비교지표 최소:

- total return
- profit factor
- MDD
- trade count / closed trades
- total cost
- open position
- MFE/MAE/giveback diagnostics when available

현재 Strategy1 baseline evidence는 유지하되, trailing/stop refinement 전에 execution semantics의 gap/intrabar causality를 반드시 검토한다.

## 9. NEXT-4 — real-time paper trading

Historical WYSIWYG가 동일 authority로 일치한 뒤에만 진행한다.

목적:

```text
same validated DSL/version
 -> realtime observations
 -> same deterministic strategy semantics
 -> paper broker
 -> execution ledger
 -> Chart projection
```

백테스트와 paper의 차이는 별도 전략엔진이 아니라 market timing/fill source 차이로 제한한다.

## 10. NEXT-5 — fine tuning, then limited live

Paper evidence가 충분한 뒤:

- baseline vs paper discrepancy 분석
- 한 번에 한 가설만 수정
- large trend winner 보존 여부 확인
- broad parameter grid/과최적화 금지
- limited live 전 backtest + WYSIWYG + paper 재통과

## 11. Strategy1 현재 연구 기준선

기존 `examples/jma_cross.dsl`:

```text
JMA 7/50 cross
+ SMA60 trend filter
+ long only
+ crossunder exit
```

신뢰된 REALDATA1 baseline 핵심:

```text
closed trades: 15
total return: +88.68557782060891%
profit factor: 2.9234729545115528
MDD: -23.917654587375857%
win rate: 46.666666666666664%
total cost: 326745.03218364983
open position at dataset end: 1
```

이는 promising baseline이지 profitability proof가 아니다.

## 12. 세션복구 체크리스트

새 세션에서 `세션복구` 요청 시:

1. `SESSION_HANDOFF.md`를 읽는다.
2. 이 `STRATEGY_PRODUCT_FLOW_TODO.md`를 읽는다.
3. 최근 사용자 로컬 PASS/FAIL evidence가 문서보다 최신인지 확인한다.
4. DSL과 Chart 저장소를 혼동하지 않는다.
5. 각 저장소의 trusted SHA와 remote-unvalidated SHA를 분리한다.
6. 현재 `NEXT-n` 하나만 진행한다.
7. 구현 전 mandatory ownership gate를 다시 적는다.
8. focused -> Full -> checkpoint 후 다음 TODO로 이동한다.

## 13. 현재 한 줄 상태

```text
DSL StrategyWorkspace = TRUSTED
Chart DSL-first Manager authoring = REMOTE_UNVALIDATED
NEXT = validate Chart c67d3d8... in E:\2026\gemini\cascade-chart-validation-20260904
then = production HTTP Bridge only
```
