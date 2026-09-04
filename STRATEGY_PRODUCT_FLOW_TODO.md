# Strategy Product Flow TODO

Status: **ACTIVE PRIMARY TODO / NEXT-1C PRODUCTION COMPOSITION REMOTE_UNVALIDATED / 2026-09-05 KST**

이 문서는 세션이 바뀌어도 큰 흐름, 두 저장소의 역할, trusted/unvalidated SHA, 정확한 다음 micro-tranche를 잃지 않기 위한 실행 TODO다. `SESSION_HANDOFF.md` 다음으로 읽는다.

## A. 최종 제품 흐름

```text
Strategy Manager Dialog
 -> DSL strategy CRUD
 -> authoritative validate + immutable version
 -> strategy별 Global/Add-on parameter profile CRUD
 -> validated strategy를 Chart subject에 적용
 -> authoritative DSL signal/execution WYSIWYG
 -> strategy 단위 Backtest Dialog
 -> same DSL/version/profile realtime Paper
 -> Backtest vs Paper 비교
 -> evidence-based minimal fine tuning
 -> limited Live
```

WYSIWYG invariant:

```text
보이는 DSL
= 저장된 exact DSL
= 검증된 exact DSL/version
= Chart 신호를 만든 DSL
= Backtest한 DSL
= Paper/Live가 사용하는 DSL
```

파라미터 invariant:

```text
Global Parameter Catalog(default)
+ Strategy Override CRUD
= Effective Strategy Parameter Profile
```

공통 항목 schema는 하나이고 값은 전략별 독립 CRUD 가능해야 하며 reset은 override 제거로 기본값을 복원한다.

## B. 절대 개발 규칙

모든 executable 변경 전:

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

```text
Chart가 DSL parser/JMA/crossover/order timing/backtest 의미를 authoritative 재구현
Strategy Manager UI가 DB 직접접근
Runtime/UI 이중 복원권한
Backtest/Paper/Live에 서로 다른 strategy semantics
assertion/guard 약화로 PASS 만들기
한 tranche에 CRUD+Bridge+Apply+Backtest+Paper/Live 혼합
REALDATA2/LF/adaptive learning/automatic selection을 현재 흐름에 끼워넣기
```

실패 분류:

```text
test defect
product defect
authority drift
environment issue
external data defect
unknown
```

## C. 저장소/작업공간

### DSL

```text
repo: hoonoh57/dsl
branch: main
workspace: E:\2026\gemini\dsl-main-validation-20260904
trusted executable/test: 27882d288f52c98ab48a59b0d7ae2c2de0dcd637
current remote executable/test candidate: ddf8aaf007dba91de2b916448246cebede118cf9
```

DSL owner:

```text
strategy CRUD persistence
DSL source SSOT
artifact/version/validation history
BacktestEngine authoritative semantics
later backtest/paper result authority
```

### Chart

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
workspace: E:\2026\gemini\cascade-chart-validation-20260904
trusted executable/test: 23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
current remote executable/test candidate: e99bde72886c0afea04e07bfab0bd25fa8ab15b8
```

Chart owner:

```text
Strategy Manager UX
Browser Request/Response adapter
same-origin transport proxy
generic Runtime chart state/subject view
authoritative DSL result visualization
```

## D. DONE checkpoints

### D1. WYSIWYG-0 Strategy Workspace — DONE/TRUSTED

DSL trusted lineage starts at `01da3bc6...` and remains included in current trusted `27882d...`.

```text
StrategyWorkspace
 -> core.db CRUD
 -> exact DSL
 -> BacktestEngine.run(exact_dsl)
 -> artifact_versions
 -> validation_events
```

### D2. WYSIWYG-1 DSL-first Chart Strategy Manager — DONE/TRUSTED

Chart lineage includes `c67d3d8...`.

```text
전략 목록
신규 / 복제 / 삭제
전략명 / 설명
DSL editor
Draft 저장 요청
검증 후 저장 요청
validation status
```

No Chart local validation fallback.

### D3. NEXT-1A DSL HTTP adapter — DONE/TRUSTED

Trusted executable/test: `27882d288...`

User evidence:

```text
focused combined: Ran 13 tests / OK
Tactical P1 Full: PASS
```

Contract:

```text
GET    /api/strategy-workspace/strategies
POST   /api/strategy-workspace/draft
DELETE /api/strategy-workspace/strategies/{strategy_id}
POST   /api/strategy-workspace/validate-commit
```

### D4. NEXT-1B Chart BrowserPort + proxy — DONE/TRUSTED

Trusted Chart: `23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf`

User evidence:

```text
transport: 6/6 PASS
DSL Manager port: 5/5 PASS
managed strategy regression: 8/8 PASS
Tactical P1 Full with Chart checkout: PASS
```

Transport:

```text
UI contract
 -> BrowserStrategyWorkspacePort
 -> /__cascade/strategy-workspace/*
 -> fixed proxy gateway
 -> /api/strategy-workspace/*
```

## E. NOW — NEXT-1C production composition + actual CRUD WYSIWYG

### E1. Implemented remotely

DSL candidate `ddf8aaf...`:

```text
main.py
 -> imports strategy_workspace_router
 -> app.include_router(strategy_workspace_router)

test_stage1_strategy_workspace_production_mount.py
 -> verifies real FastAPI app paths/methods
```

Chart candidate `e99bde7...`:

```text
MarketChart.mjs
 -> BrowserStrategyWorkspacePort default capability
 -> Runtime receives capabilities.strategyWorkspace

serve.mjs
 -> DslStrategyWorkspaceHttpGateway
 -> DSL_STRATEGY_WORKSPACE_URL optional env
 -> default http://127.0.0.1:8000
 -> strategyWorkspaceProxyMiddleware in routeApi

tests/strategy_workspace_production_composition.test.mjs
```

### E2. NEXT-1C forbidden scope

이번 tranche에서 다음은 구현하지 않는다.

```text
strategy parameter UI
Chart strategy apply
signal marker generation from DSL
Backtest Dialog
paper/live
Core/Parser/Runtime/Backtest/Broker semantics 변경
```

### E3. Focused verification

#### DSL workspace

```powershell
Set-Location E:\2026\gemini\dsl-main-validation-20260904

git fetch origin main
git checkout --detach origin/main
git rev-parse HEAD

python -m unittest -v `
  test_stage1_strategy_workspace_production_mount.py `
  test_stage1_strategy_workspace_http_bridge.py `
  test_stage1_wysiwyg_strategy_workspace.py
```

#### Chart workspace

```powershell
Set-Location E:\2026\gemini\cascade-chart-validation-20260904

git fetch origin product-completion-mvp
git checkout --detach origin/product-completion-mvp
git rev-parse HEAD

node --test tests/strategy_workspace_production_composition.test.mjs
node --test tests/strategy_workspace_http_transport.test.mjs
node --test tests/dsl_strategy_manager_workspace_port.test.mjs
node --test tests/managed_strategy_addon.test.mjs
```

#### Full

```powershell
Set-Location E:\2026\gemini\dsl-main-validation-20260904

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\verify_tactical_p1.ps1 `
  -Mode Full `
  -ChartRepo ..\cascade-chart-validation-20260904
```

### E4. Actual WYSIWYG acceptance — 반드시 focused+Full PASS 후

DSL server:

```powershell
Set-Location E:\2026\gemini\dsl-main-validation-20260904
python .\main.py
```

Chart server: 별도 PowerShell 창

```powershell
Set-Location E:\2026\gemini\cascade-chart-validation-20260904
npm start
```

기본 bridge target은 `http://127.0.0.1:8000`이다. 다른 DSL endpoint면 Chart server 실행 전 `DSL_STRATEGY_WORKSPACE_URL` 환경변수로 지정한다.

Dialog acceptance:

```text
1. Strategy Manager open
2. 신규 작성
3. Draft 저장
4. 닫기/재오픈 -> draft 복구
5. 검증 후 저장 -> VALIDATED + version
6. 닫기/재오픈 -> exact validation 복구
7. DSL 한 글자 수정 -> DRAFT
8. 재검증 -> 새 version
9. 삭제
10. 닫기/재오픈 -> 삭제 유지
```

PASS해야 NEXT-1C DONE/TRUSTED로 닫는다.

## F. NEXT — Global Parameter / Add-on Profile

NEXT-1C가 닫힌 뒤 바로 진행한다.

### F1. Global Parameter Catalog

공통 항목 정의:

```text
key
type
unit
min/max/default
supported modes
Add-on metadata
```

초기 inventory는 기존 StrategySettings를 재사용한다.

```text
total capital / allocation
signal fill mode
commission
sell tax
slippage
stop loss
take profit
trailing enabled/activation/distance
entry time window
max entries/day
```

새로운 공통 Add-on 후보는 기존 항목 정렬 이후 micro-tranche로 추가한다.

```text
sideways guard
peak drawdown exit
max holding bars/time
force exit/end-of-day
breakeven
reentry cooldown
```

### F2. Strategy Override CRUD

```text
Global default
 + strategy-specific override
 = EffectiveStrategyParameters(strategy_id, mode)
```

필수 기능:

```text
CREATE override
READ effective value + origin(default/override)
UPDATE override
RESET one = override delete
RESET all = all overrides delete
strategy A 변경이 B에 영향 없음
Backtest/Paper/Live 적용범위 선택
```

필수 invariant:

```text
BASE = BASE + every optional Add-on OFF
```

## G. AFTER PARAMETER PROFILE

```text
NEXT-3 validated strategy/version/profile -> selected Chart subject
  -> authoritative DSL signal/execution result projection

NEXT-4 Backtest Dialog
  -> 기간/종목/전략/profile
  -> return/PF/MDD/trades/cost/equity/MFE/MAE/giveback
  -> WYSIWYG execution markers

NEXT-5 realtime Paper
  -> same DSL/version/profile
  -> backtest vs paper comparison

NEXT-6 minimal fine tuning
  -> one hypothesis per tranche
  -> no broad grid optimization

NEXT-7 limited Live
  -> only after backtest + WYSIWYG + Paper revalidation
```

## H. Research status

```text
Strategy1 JMA baseline: preserved evidence
fixed stop 6/8/10%: rejected
some trailing candidates: no material improvement
REALDATA2/LF: PAUSED
adaptive learning: PAUSED
automatic selection/allocation: PAUSED
broader compliance: REMEDIATION_REQUIRED
```

## I. Session recovery

`세션복구` 시:

```text
1. SESSION_HANDOFF.md
2. STRATEGY_PRODUCT_FLOW_TODO.md
3. recent user local evidence
4. exact trusted SHA vs remote executable diff (DSL)
5. exact trusted SHA vs remote executable diff (Chart)
6. NOW tranche one only
```

응답은 `한 일 / 할 일`로 짧게 시작한다.
