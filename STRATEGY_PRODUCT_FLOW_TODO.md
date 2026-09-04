# Strategy Product Flow TODO

Status: **ACTIVE PRIMARY TODO / WYSIWYG STRATEGY PRODUCT FLOW / 2026-09-05 KST**

이 문서는 세션이 바뀌어도 현재 큰 흐름, 두 저장소 역할, trusted/unvalidated checkpoint, 정확한 다음 micro-tranche를 잃지 않기 위한 실행 TODO다. 새 세션에서는 `SESSION_HANDOFF.md` 다음으로 이 문서를 읽는다.

## 1. 최종 제품 흐름

```text
Strategy Manager Dialog
 -> DSL strategy CRUD
 -> authoritative validate + immutable version
 -> strategy별 Global/Add-on parameter profile CRUD
 -> validated strategy를 선택 Chart subject에 적용
 -> authoritative DSL signal/execution result를 Chart에 WYSIWYG 표시
 -> strategy 단위 Backtest Dialog
 -> 동일 DSL/version/profile로 realtime Paper
 -> Backtest vs Paper 비교
 -> evidence-based fine tuning
 -> limited Live
```

프롬프트는 개발 보조도구일 뿐이다. 전략 DSL, 사용자 설정값, 검증 버전, 백테스트 결과, Paper/Live 적용상태의 제품 SSOT가 되어서는 안 된다.

WYSIWYG 목표:

```text
보이는 DSL
= 저장된 DSL
= 검증된 exact DSL/version
= 차트 신호를 만든 DSL
= 백테스트한 DSL
= Paper/Live가 사용하는 DSL
```

파라미터도 동일 원칙을 따른다.

```text
Global Parameter Catalog(default)
+ Strategy Override CRUD
= Effective Strategy Parameter Profile
```

항목 schema는 공통이고 값은 전략별 독립 CRUD 가능해야 한다. 각 override는 기본값 복원이 가능해야 한다. Backtest/Paper/Live 적용범위도 profile에서 선택 가능해야 한다.

## 2. 절대 개발 경계

모든 구현 전에 다음을 확정한다.

```text
owner layer
 -> existing shared/common path
 -> state SSOT
 -> object create/delete authority
 -> adjacent-layer prohibitions
 -> one-boundary micro-tranche
 -> focused verification
 -> WYSIWYG verification when applicable
 -> Full verification
 -> checkpoint
```

금지:

- Chart가 DSL parser/runtime/JMA/crossover/order timing을 authoritative하게 재구현하지 않는다.
- Strategy Manager UI가 SQLite/MySQL을 직접 읽고 쓰지 않는다.
- 동일 기능에 Runtime 복원경로와 UI 복원경로를 동시에 만들지 않는다.
- Backtest/Paper/Live가 서로 다른 strategy semantics를 갖지 않는다.
- test PASS를 위해 assertion/guard를 약화하지 않는다.
- 한 tranche에 CRUD + Bridge + Chart apply + Backtest + Paper/Live를 섞지 않는다.
- REALDATA2/LF research, adaptive learning, automatic selection/allocation은 현재 profit-strategy product flow에 직접 필요할 때까지 PAUSED다.

실패는 먼저 다음 중 하나로 분류한다.

```text
test defect
product defect
authority drift
environment issue
external data defect
unknown
```

## 3. 저장소와 로컬 작업공간 — 절대 혼용 금지

### DSL repository

```text
repo: hoonoh57/dsl
branch: main
local validation workspace:
  E:\2026\gemini\dsl-main-validation-20260904
```

책임:

- DSL source SSOT
- strategy CRUD persistence
- artifact/version/validation history
- authoritative DSL validation
- existing BacktestEngine execution semantics
- later historical backtest/paper execution result authority

현재 trusted executable/test checkpoint:

```text
01da3bc6b21c126efd6ffa3b220e2a34de5ef64b
```

사용자 local evidence:

```text
Strategy Workspace focused: Ran 7 tests / OK
Tactical P1 Full: PASS
```

현재 remote executable/test candidate:

```text
27882d288f52c98ab48a59b0d7ae2c2de0dcd637
status: REMOTE_UNVALIDATED
scope: NEXT-1A HTTP adapter contract only
```

중요: `27882d288...`는 아직 `main.py` production mount를 하지 않았다. 즉 **HTTP adapter 정의/계약만 존재하며 실제 server endpoint composition은 NEXT-1C 전까지 완료로 간주하지 않는다.**

### Chart repository

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
local validation workspace:
  E:\2026\gemini\cascade-chart-validation-20260904
```

책임:

- Strategy Manager UX
- standard Request -> Response bridge client
- generic Runtime chart state / subject view
- authoritative DSL/backtest result 시각화
- later strategy assignment/WYSIWYG projection

현재 trusted Chart checkpoint:

```text
c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda
```

사용자 local evidence:

```text
node --test tests/dsl_strategy_manager_workspace_port.test.mjs
  5 pass / 0 fail

node --test tests/managed_strategy_addon.test.mjs
  8 pass / 0 fail
```

의미:

- active Strategy Manager authoring UI는 DSL-first다.
- CRUD/검증 요청은 `strategyWorkspace` port로만 보낸다.
- capability가 없으면 fail-closed한다.
- Chart local JMA evaluator로 검증 fallback하지 않는다.
- 기존 subjectViews/Runtime generic transport 회귀는 PASS했다.

## 4. 완료된 큰 단계

### WYSIWYG-0 Strategy Workspace persistence/validation — DONE / TRUSTED

DSL `01da3bc6...`

```text
StrategyWorkspace
 -> core.db CRUD
 -> exact DSL bytes
 -> BacktestEngine.run(exact_dsl)
 -> artifact_versions
 -> validation_events
 -> current DSL exact-match validation recovery
```

DSL 한 글자 변경 시 이전 validation은 이력으로 남지만 현재 strategy는 DRAFT가 된다.

### WYSIWYG-1 Chart DSL-first Strategy Manager shell — DONE / TRUSTED

Chart `c67d3d8...`

현재 Dialog 책임:

```text
전략 목록
신규 / 복제 / 삭제
전략명 / 설명
DSL editor
Draft 저장 요청
검증 후 저장 요청
validation status 표시
```

아직 production HTTP bridge, Chart apply, Backtest Dialog는 없다.

## 5. 현재 작업 — NEXT-1 StrategyWorkspace production bridge

NEXT-1은 세 개의 micro-tranche로 나눈다.

### NEXT-1A — DSL HTTP adapter contract

상태:

```text
IMPLEMENTED REMOTELY / REMOTE_UNVALIDATED
candidate: 27882d288f52c98ab48a59b0d7ae2c2de0dcd637
```

신규:

```text
addons/strategy_manager/http_bridge.py
test_stage1_strategy_workspace_http_bridge.py
```

표준 endpoint contract:

```text
GET    /api/strategy-workspace/strategies
POST   /api/strategy-workspace/draft
DELETE /api/strategy-workspace/strategies/{strategy_id}
POST   /api/strategy-workspace/validate-commit
```

권한:

```text
HTTP adapter
 -> StrategyWorkspace only
 -> core.db / BacktestEngine 직접접근 금지
```

중요: 아직 FastAPI composition root에 mount하지 않았다.

#### NEXT-1A 바로 다음 검증

**DSL workspace에서만 실행:**

```powershell
Set-Location E:\2026\gemini\dsl-main-validation-20260904

git fetch origin main
git checkout --detach origin/main
git rev-parse HEAD
```

기대 HEAD는 docs 변경 여부에 따라 `27882d288...` 이후가 될 수 있다. executable/test diff의 핵심 candidate는 `27882d288...`다.

focused:

```powershell
python -m unittest -v `
  test_stage1_strategy_workspace_http_bridge.py `
  test_stage1_wysiwyg_strategy_workspace.py
```

그 후:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\verify_tactical_p1.ps1 `
  -Mode Full `
  -ChartRepo ..\cascade-chart-validation-20260904
```

PASS하면 NEXT-1A trusted로 승격한다.

### NEXT-1B — Chart BrowserPort + same-origin proxy

NEXT-1A trusted 뒤에만 진행한다.

목적:

```text
DslStrategyManagerUi
 -> StrategyWorkspacePort
 -> BrowserStrategyWorkspacePort
 -> /__cascade/strategy-workspace/*
 -> Chart shell proxy
```

구현할 것:

- listStrategies
- saveDraft
- deleteStrategy
- validateAndCommit
- camelCase UI payload -> snake_case DSL payload adapter
- non-2xx / network failure fail-closed
- DSL server unavailable 시 local evaluator fallback 금지

이 tranche에서는 아직 MarketChart capability composition까지 연결하지 않아도 된다. BrowserPort/proxy 자체 계약을 focused test로 닫는다.

### NEXT-1C — composition + 실제 Strategy Manager WYSIWYG CRUD

NEXT-1B trusted 뒤에만 진행한다.

목적:

```text
Chart MarketChart composition
 -> capabilities.strategyWorkspace
 -> BrowserStrategyWorkspacePort
 -> Chart proxy
 -> mounted DSL HTTP adapter
 -> StrategyWorkspace
```

여기서 처음으로 실제 Dialog에서 다음을 검증한다.

```text
신규 전략 생성
 -> Draft 저장
 -> Dialog 재오픈 후 복구
 -> DSL 수정
 -> validation DRAFT 전환
 -> 검증 후 저장
 -> exact version VALIDATED 복구
 -> 삭제
```

완료조건:

```text
DSL focused PASS
Chart focused PASS
실제 Dialog WYSIWYG CRUD PASS
Tactical P1 Full PASS
```

## 6. NEXT-2 — Strategy별 Global/Add-on Parameter Profile

Bridge가 trusted된 뒤 구현한다. 차트 적용보다 먼저 parameter SSOT를 완성할 수 있으며, 실제 순서는 NEXT-1C 종료 시 기존 저장구조를 확인해 결정한다.

원칙:

```text
GlobalParameterCatalog
  parameter key/type/unit/min/max/system default/global default

StrategyParameterOverride
  strategy_id
  parameter_key
  value
  apply_backtest
  apply_paper
  apply_live

EffectiveStrategyParameters(strategy_id, mode)
  Strategy override > Global default > System hard default
```

기본 공통 항목 후보:

```text
signal fill mode
commission
sell tax
slippage simulation
allocation
stop loss
take profit
trailing activation/distance
sideways guard
peak drawdown exit
max holding bars/time
force exit/end-of-day
reentry cooldown
```

모든 Add-on은 default OFF 또는 기존 baseline과 동일한 default를 가져야 한다.

필수 contract:

```text
BASE
= BASE + every optional Add-on OFF
```

전략 A override 변경이 전략 B에 영향을 주면 FAIL이다.

## 7. NEXT-3 — validated strategy apply to Chart

검증된 exact DSL/version + effective parameter profile을 선택 subject에 연결한다.

Chart는 계산하지 않고 DSL authoritative result contract를 받는다.

최소 result identity:

```text
strategy id/version/dsl_sha256
parameter profile identity
instrument/timeframe identity
source/bar identity
signal events
execution events
required overlay/indicator series
execution/validation authority metadata
```

기존 Runtime `subjectViews`와 generic marker transport를 재사용한다.

## 8. NEXT-4 — strategy 단위 Backtest Dialog

```text
validated strategy/version
+ parameter profile
+ symbol/timeframe
+ start/end period
 -> existing BacktestEngine
 -> report
 -> same result를 Chart signal/execution markers로 projection
```

최소 비교지표:

```text
total return
profit factor
MDD
trade count / closed trades
win rate
total cost
open position
MFE / MAE / giveback when available
```

## 9. NEXT-5 — realtime Paper, then limited Live

Historical WYSIWYG가 동일 authority로 일치한 뒤에만 Paper로 간다.

```text
same validated DSL/version/profile
 -> realtime observations
 -> same deterministic semantics
 -> paper broker
 -> execution ledger
 -> Chart projection
```

Live는 actual broker fill이 체결 SSOT다. Backtest/Paper의 slippage simulation 값으로 실제 체결가를 덮어쓰지 않는다.

## 10. Strategy1 연구 기준선 — 보존만 하고 현재 제품개발을 지배하지 않음

기존 `examples/jma_cross.dsl`은 JMA 7/50 cross + SMA60 trend filter, long-only다.

REALDATA1 baseline 핵심:

```text
closed trades: 15
return: +88.6856%
PF: 2.9235
MDD: -23.9177%
```

slippage 0.20%에서도 약 +80.92%, PF 2.649로 유지됐다.

고정 stop 6/8/10%는 수익/PF를 악화시켜 REJECTED다. trailing 일부 후보도 material improvement가 없었다. 이 실험을 근거로 Core 기능을 무한 추가하지 않는다.

## 11. 새 세션 복구 체크

새 세션에서 반드시 다음 순서로 확인한다.

```text
1. SESSION_HANDOFF.md
2. STRATEGY_PRODUCT_FLOW_TODO.md
3. 사용자 마지막 local focused/Full evidence
4. DSL repo current HEAD vs trusted executable diff
5. Chart product-completion-mvp HEAD vs trusted Chart diff
6. 현재 NEXT micro-tranche 하나만 진행
```

항상 답변은 간단히:

```text
한 일
할 일
```

으로 구분한다.
