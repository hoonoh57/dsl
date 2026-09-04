# Strategy Product Flow TODO

Status: **ACTIVE PRIMARY TODO / NEXT-1B REMOTE_UNVALIDATED / 2026-09-05 KST**

이 문서는 세션이 바뀌어도 전략제품 개발의 큰 흐름과 정확한 현재 위치를 유지하기 위한 실행 TODO다. 새 세션은 `SESSION_HANDOFF.md`를 먼저 읽고 이 문서를 이어서 읽는다.

## A. 최종 제품 목표

```text
Strategy Manager Dialog
 -> DSL strategy CRUD
 -> authoritative validation + immutable version
 -> strategy별 parameter/add-on profile CRUD
 -> validated strategy를 Chart subject에 적용
 -> authoritative signal/execution WYSIWYG
 -> strategy별 Backtest Dialog
 -> 동일 DSL/version/profile realtime Paper
 -> Backtest vs Paper 비교
 -> evidence-based fine tuning
 -> limited Live
```

프롬프트는 개발 보조창이다. 전략 DSL, 설정, 검증이력, 백테스트 성과, Paper/Live 적용상태의 SSOT가 아니다.

WYSIWYG 계약:

```text
보이는 DSL
= 저장된 exact DSL
= 검증된 exact DSL/version
= 차트 신호를 만든 DSL
= 백테스트한 DSL
= Paper/Live가 사용하는 DSL
```

파라미터 계약:

```text
Global Parameter Catalog(default)
+ Strategy Override CRUD
= EffectiveStrategyParameters(strategy_id, mode)
```

항목 schema는 공통, 값은 전략별 CRUD 가능, RESET은 override 삭제로 기본값 복원, 적용 mode는 Backtest/Paper/Live별 선택 가능해야 한다.

## B. 공통 개발 게이트

모든 executable 변경 전에:

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

- Chart가 DSL parser/runtime/JMA/crossover/order timing을 authoritative 재구현하지 않는다.
- UI Add-on이 SQLite/MySQL을 직접 읽고 쓰지 않는다.
- 같은 기능을 Runtime/UI 등 두 계층이 각각 복원하지 않는다.
- Backtest/Paper/Live가 다른 strategy semantics를 갖지 않는다.
- PASS를 위해 assertion/guard/authority test를 약화하지 않는다.
- 한 tranche에 CRUD + bridge + chart apply + backtest + paper/live를 섞지 않는다.
- REALDATA2/LF, adaptive learning, automatic selection/allocation은 현재 profit-product flow에 직접 필요할 때까지 PAUSED다.

실패 분류:

```text
test defect
product defect
authority drift
environment issue
external data defect
unknown
```

## C. 저장소/작업공간 — 절대 혼용 금지

### DSL

```text
repo   hoonoh57/dsl
branch main
local  E:\2026\gemini\dsl-main-validation-20260904
```

책임:

```text
DSL source SSOT
strategy CRUD persistence
artifact/version/validation history
authoritative BacktestEngine semantics
later backtest/paper result authority
```

현재 trusted executable/test:

```text
27882d288f52c98ab48a59b0d7ae2c2de0dcd637
```

local evidence:

```text
NEXT-1A + Strategy Workspace focused: Ran 13 tests / OK
Tactical P1 Full: PASS
```

### Chart

```text
repo   hoonoh57/cascading-feature-solution
branch product-completion-mvp
local  E:\2026\gemini\cascade-chart-validation-20260904
```

현재 trusted:

```text
c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda
```

local evidence:

```text
DSL-first Strategy Manager: 5 pass / 0 fail
managed strategy regression: 8 pass / 0 fail
```

현재 remote candidate:

```text
23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
status: REMOTE_UNVALIDATED
scope: NEXT-1B transport only
```

## D. 완료 단계

### DONE-0 DSL Strategy Workspace

Trusted.

```text
StrategyWorkspace
 -> core.db CRUD
 -> BacktestEngine.run(exact_dsl)
 -> artifact_versions
 -> validation_events
```

현재 DSL과 exact validated artifact가 동일할 때만 VALIDATED. DSL 변경 시 이전 검증은 이력으로 보존되고 현재 전략은 DRAFT.

### DONE-1 Chart DSL-first Strategy Manager shell

Trusted.

```text
전략 목록
신규 / 복제 / 삭제
전략명 / 설명
DSL Editor
Draft 저장 요청
검증 후 저장 요청
validation status
```

Chart local JMA evaluator는 authoring validation fallback이 아니다.

### DONE-2 NEXT-1A DSL HTTP adapter contract

Trusted executable/test:

```text
27882d288f52c98ab48a59b0d7ae2c2de0dcd637
```

contract:

```text
GET    /api/strategy-workspace/strategies
POST   /api/strategy-workspace/draft
DELETE /api/strategy-workspace/strategies/{strategy_id}
POST   /api/strategy-workspace/validate-commit
```

HTTP adapter는 `StrategyWorkspace`만 호출한다. DB/Backtest 직접권한 없음.

주의: 아직 DSL `main.py`에 mount하지 않았다. adapter contract trusted != production endpoint active.

## E. CURRENT — NEXT-1B Chart transport

Remote candidate:

```text
23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
```

변경 3파일:

```text
src/adapters/strategy/BrowserStrategyWorkspacePort.mjs
src/shell/index-wysiwyg/StrategyWorkspaceHttpHost.mjs
tests/strategy_workspace_http_transport.test.mjs
```

transport flow:

```text
DslStrategyManagerUi
 -> StrategyWorkspacePort
 -> BrowserStrategyWorkspacePort
 -> /__cascade/strategy-workspace/*
 -> StrategyWorkspaceHttpHost
 -> DSL /api/strategy-workspace/*
```

transport naming 변환은 Browser adapter 한 곳에서만:

```text
strategyId -> strategy_id
dslCode    -> dsl_code
```

proxy는 strategy 의미를 계산하지 않고 endpoint/status/payload만 전달한다.

이번 tranche에서 일부러 미구현:

```text
DSL main.py router mount
Chart scripts/serve.mjs middleware mount
MarketChart composition에서 BrowserStrategyWorkspacePort 생성
capabilities.strategyWorkspace 주입
실제 Dialog network CRUD
Chart signal apply
Backtest Dialog
Paper/Live
parameter profile
```

### NEXT-1B 검증 명령 — Chart workspace

```powershell
Set-Location E:\2026\gemini\cascade-chart-validation-20260904

git fetch origin product-completion-mvp
git checkout --detach origin/product-completion-mvp
git rev-parse HEAD
```

기대:

```text
23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
```

focused:

```powershell
node --test tests/strategy_workspace_http_transport.test.mjs
node --test tests/dsl_strategy_manager_workspace_port.test.mjs
node --test tests/managed_strategy_addon.test.mjs
```

판정:

```text
ALL PASS
 -> 23c85f2 trusted
 -> NEXT-1C만 진행

FAIL
 -> 먼저 defect classification
 -> assertion/guard 약화 금지
```

## F. NEXT-1C — production composition + CRUD WYSIWYG

NEXT-1B PASS 뒤에만 시작.

owner/authority:

```text
DSL composition root
 -> http_bridge.router mount only

Chart shell composition
 -> StrategyWorkspaceHttpHost middleware mount
 -> explicit DSL service base URL

Chart composition
 -> BrowserStrategyWorkspacePort
 -> addons.capabilities.strategyWorkspace
```

WYSIWYG 검증 시나리오:

```text
1 신규 strategy 생성
2 Draft 저장
3 DSL 수정
4 이전 VALIDATED가 즉시 현재값에서 무효 확인
5 검증 후 저장
6 Dialog 닫기
7 Dialog 재오픈
8 exact DSL/version VALIDATED 복구
9 전략 수정 후 DRAFT 확인
10 삭제
11 재오픈 후 삭제 유지
```

NEXT-1C에도 금지:

```text
Chart signal insertion
Backtest Dialog
Paper/Live
parameter profile
```

완료 시 production CRUD bridge가 처음으로 닫힌다.

## G. NEXT-2 — Global Parameter Catalog + Strategy Override CRUD

목적:

```text
공통 parameter schema
+ global default
+ strategy override CRUD
+ per-item reset to default
+ strategy reset-all
+ Backtest/Paper/Live applicability
```

우선순위:

```text
Strategy override
 > Global default
 > System hard default
```

초기 catalog 후보:

```text
signal fill mode
commission_pct
sell_tax_pct
slippage simulation
stop loss
take profit
trailing stop
sideways guard
peak drawdown exit
max holding bars/time
force exit/end-of-day
reentry cooldown
```

필수 불변식:

```text
BASE = BASE + every optional Add-on OFF
전략 A override가 전략 B에 영향 없음
RESET = override 제거 -> global default 복귀
```

## H. NEXT-3 — validated strategy apply to Chart

입력 SSOT:

```text
validated strategy id/version/exact DSL
+ EffectiveStrategyParameters
+ instrument/timeframe/bar identity
```

출력 표준계약은 시작 전에 기존 Backtest/Runtime result를 inventory한 뒤 최소 필드만 고정:

```text
strategy identity/version
parameter profile identity
instrument/timeframe/source identity
indicator/overlay series
signal events
execution events
authority metadata
```

Chart는 crossover/JMA/order timing을 다시 계산하지 않는다.

## I. NEXT-4 — strategy Backtest Dialog

```text
strategy 선택
instrument 선택
period 선택
parameter profile 선택
 -> existing DSL BacktestEngine
 -> authoritative report
 -> Chart WYSIWYG signal/execution markers
```

최소 report:

```text
total return
profit factor
MDD
trade count / closed trades
total cost
open position
MFE / MAE / giveback when available
```

## J. NEXT-5 — realtime Paper -> Fine tuning -> Limited Live

```text
same exact DSL/version/profile
 -> realtime observation
 -> same deterministic semantics
 -> paper broker
 -> execution ledger
 -> Chart projection
```

Backtest와 Paper의 차이는 별도 전략엔진이 아니라 market timing/fill source 차이로 제한.

Paper evidence 이후에만:

```text
한 번에 한 가설 수정
broad grid/과최적화 금지
large winner 보존 확인
Backtest + WYSIWYG + Paper 재검증
limited Live
```

## K. 현재 전략 연구 참고값 — 제품 흐름보다 우선하지 않음

Strategy1 JMA baseline:

```text
return +88.6856%
PF 2.9235
MDD -23.9177%
closed trades 15
```

fixed stop 6/8/10%는 REJECTED. 일부 trailing 후보도 material improvement가 없었다. 현재는 개별 숫자 튜닝보다 WYSIWYG 전략제품 경로 완성이 우선이다.

REALDATA2/LF research: **PAUSED**.

broader compliance:

```text
REMEDIATION_REQUIRED
```

## L. 세션복구 규칙

사용자가 `세션복구`라고 하면:

```text
1 SESSION_HANDOFF.md
2 STRATEGY_PRODUCT_FLOW_TODO.md
3 최근 사용자 exact local PASS evidence
4 DSL trusted vs remote diff
5 Chart trusted vs product-completion-mvp diff
6 CURRENT 단계 하나만 계속
```

첫 답변은 짧게:

```text
한 일
할 일
```
