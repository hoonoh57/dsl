# DSL Session Handoff

Status: **PRIMARY HANDOFF / WYSIWYG STRATEGY PRODUCT FLOW ACTIVE / NEXT-1B TRUSTED / NEXT-1C REMOTE_UNVALIDATED / 2026-09-05 KST**

새 세션은 이 문서를 가장 먼저 읽고 `STRATEGY_PRODUCT_FLOW_TODO.md`를 이어서 읽는다. 프롬프트 대화 자체를 전략 개발이력의 SSOT로 사용하지 않는다.

## 1. 제품 철학

1. **4축/계층 경계 유지**: 축과 저장소 사이 직접 상태접근보다 표준 Request -> Response 계약을 사용한다.
2. **베이스 전략 보존 + Add-on 확장**: optional Add-on OFF는 baseline을 변경하면 안 된다.
3. **전략 의미의 authority는 DSL**: Chart가 parser/JMA/crossover/order timing/backtest 의미를 독립 재구현하지 않는다.
4. **WYSIWYG**: 보이는 DSL/설정/신호/백테스트/Paper/Live는 동일 exact strategy version과 effective parameter profile을 가리켜야 한다.
5. **micro-tranche**: owner -> shared path -> SSOT -> create/delete authority -> prohibitions -> focused -> WYSIWYG -> Full -> checkpoint 순서를 지킨다.

## 2. 최종 제품 흐름

```text
Strategy Manager Dialog
 -> DSL strategy CRUD
 -> authoritative validate + immutable version
 -> strategy별 Global/Add-on parameter override CRUD
 -> validated strategy를 Chart subject에 적용
 -> authoritative DSL signal/execution WYSIWYG
 -> strategy 단위 Backtest Dialog
 -> same DSL/version/profile realtime Paper
 -> Backtest vs Paper 비교
 -> evidence-based minimal fine tuning
 -> limited Live
```

프롬프트는 개발 보조수단일 뿐이다. 전략 DSL, 사용자 파라미터, 검증 버전, 백테스트 결과, Paper/Live 적용상태의 제품 SSOT가 아니다.

## 3. 저장소/작업공간 분리 — 절대 혼용 금지

### DSL

```text
repo: hoonoh57/dsl
branch: main
local validation workspace:
  E:\2026\gemini\dsl-main-validation-20260904
```

책임:

```text
DSL source SSOT
strategy CRUD persistence
artifact/version/validation history
authoritative BacktestEngine semantics
later backtest/paper result authority
```

현재 trusted executable/test checkpoint:

```text
27882d288f52c98ab48a59b0d7ae2c2de0dcd637
```

사용자 local evidence:

```text
NEXT-1A focused combined: Ran 13 tests / OK
Tactical P1 Full: PASS
```

현재 DSL remote executable/test candidate:

```text
ddf8aaf007dba91de2b916448246cebede118cf9
status: REMOTE_UNVALIDATED
scope:
  main.py mounts existing strategy_workspace_router
  test_stage1_strategy_workspace_production_mount.py
```

중요: `strategies.db`는 로컬 실행 side effect가 있을 수 있다. 명시적 지시 없이 stash/reset/checkout/merge하지 않는다.

### Chart

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
local validation workspace:
  E:\2026\gemini\cascade-chart-validation-20260904
```

현재 trusted Chart checkpoint:

```text
23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
```

사용자 local evidence:

```text
strategy_workspace_http_transport: 6 pass / 0 fail
dsl_strategy_manager_workspace_port: 5 pass / 0 fail
managed_strategy_addon: 8 pass / 0 fail
DSL Tactical P1 Full using this Chart checkout: PASS
```

현재 Chart remote executable/test candidate:

```text
e99bde72886c0afea04e07bfab0bd25fa8ab15b8
status: REMOTE_UNVALIDATED
scope:
  scripts/serve.mjs mounts same-origin StrategyWorkspace proxy
  MarketChart composes BrowserStrategyWorkspacePort capability
  strategy_workspace_production_composition.test.mjs
```

## 4. 완료된 WYSIWYG 단계

### WYSIWYG-0 — DSL Strategy Workspace — TRUSTED

```text
StrategyWorkspace
 -> core.db CRUD
 -> exact DSL bytes
 -> BacktestEngine.run(exact_dsl)
 -> artifact_versions
 -> validation_events
 -> exact-match validation recovery
```

현재 DSL이 검증 버전과 한 글자라도 달라지면 과거 validation은 이력으로 남지만 현재 전략은 DRAFT다.

### WYSIWYG-1 — Chart DSL-first Strategy Manager shell — TRUSTED

현재 Dialog:

```text
전략 목록
신규 / 복제 / 삭제
전략명 / 설명
DSL Editor
Draft 저장 요청
검증 후 저장 요청
validation status
```

Chart는 로컬 JMA evaluator로 validation fallback하지 않는다.

### NEXT-1A — DSL HTTP adapter contract — TRUSTED

```text
GET    /api/strategy-workspace/strategies
POST   /api/strategy-workspace/draft
DELETE /api/strategy-workspace/strategies/{strategy_id}
POST   /api/strategy-workspace/validate-commit
```

HTTP adapter -> StrategyWorkspace only. DB/Backtest 직접 소유 금지.

### NEXT-1B — Chart BrowserPort + same-origin proxy contract — TRUSTED

```text
DslStrategyManagerUi
 -> StrategyWorkspacePort
 -> BrowserStrategyWorkspacePort
 -> /__cascade/strategy-workspace/*
 -> StrategyWorkspace proxy gateway
 -> /api/strategy-workspace/*
```

UI camelCase request는 Browser adapter에서만 DSL snake_case contract로 변환한다. Proxy는 전략 의미를 해석하지 않는다.

## 5. 현재 작업 — NEXT-1C production composition + 실제 CRUD WYSIWYG

현재 remote 구현:

DSL:

```text
main.py
 -> app.include_router(strategy_workspace_router)
```

Chart:

```text
MarketChart
 -> capabilities.strategyWorkspace = BrowserStrategyWorkspacePort

serve.mjs
 -> DslStrategyWorkspaceHttpGateway
 -> DSL_STRATEGY_WORKSPACE_URL or default http://127.0.0.1:8000
 -> strategyWorkspaceProxyMiddleware in API route chain
```

이번 tranche의 금지:

```text
차트 신호 삽입
전략별 parameter UI
historical backtest dialog
paper/live execution
Chart-side strategy calculation
Core/Parser/Runtime/Backtest/Broker semantics 변경
```

## 6. 바로 다음 검증

### A. DSL workspace

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

### B. Chart workspace

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

### C. Full

DSL workspace에서:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\verify_tactical_p1.ps1 `
  -Mode Full `
  -ChartRepo ..\cascade-chart-validation-20260904
```

PASS하면 executable candidates를 trusted로 승격한 뒤 실제 WYSIWYG를 수행한다.

## 7. NEXT-1C 실제 WYSIWYG acceptance

DSL server와 Chart server를 각각 실행한 뒤 Strategy Manager Dialog에서 실제로 확인한다.

```text
1. Dialog open
2. 신규 전략 작성
3. Draft 저장
4. Dialog 닫기/재오픈 -> draft persistence 확인
5. DSL 검증 후 저장 -> VALIDATED + version 표시
6. 닫기/재오픈 -> exact validated 상태 복구
7. DSL 한 글자 수정 -> DRAFT 표시
8. 다시 검증 -> 새 version
9. 삭제
10. 닫기/재오픈 -> 삭제 유지
```

이 acceptance가 통과하기 전에는 NEXT-1C를 완료로 기록하지 않는다.

## 8. NEXT-2 이후 순서

```text
NEXT-2 Global Parameter Catalog + strategy override CRUD
  - 공통 항목 schema/default
  - strategy별 개별값 CRUD
  - override 삭제 = 기본값 복원
  - Backtest/Paper/Live 적용범위

NEXT-3 validated strategy/version/profile -> selected Chart subject
  - authoritative signal/execution result projection

NEXT-4 strategy 단위 Backtest Dialog
  - 기간/종목/전략/profile 선택
  - metrics/trades/equity/execution marker

NEXT-5 same DSL/version/profile realtime Paper
  -> Backtest vs Paper evidence
  -> minimal fine tuning
  -> limited Live
```

## 9. Parameter/Add-on 원칙

```text
Global Parameter Catalog(default)
+ Strategy Override
= EffectiveStrategyParameters(strategy_id, mode)
```

공통 schema, 전략별 독립 값 CRUD, 기본값 복원이 핵심이다.

후보 항목:

```text
signal fill mode
commission / sell tax / slippage simulation
stop loss / take profit
trailing stop
sideways guard
peak drawdown exit
max holding bars/time
force exit/end-of-day
reentry cooldown
```

필수 invariant:

```text
BASE = BASE + every optional Add-on OFF
```

## 10. 연구 상태

Strategy1 JMA baseline과 기존 risk/slippage 연구 결과는 보존하지만 현재 제품구조를 지배하지 않는다. Fixed stop 6/8/10%는 REJECTED. REALDATA2/LF/adaptive learning/automatic selection은 현재 **PAUSED**다.

broader repository compliance는 계속:

```text
REMEDIATION_REQUIRED
```

## 11. 세션복구 규칙

사용자가 `세션복구`라고 하면:

```text
1. SESSION_HANDOFF.md
2. STRATEGY_PRODUCT_FLOW_TODO.md
3. 최근 사용자 local PASS/FAIL evidence
4. DSL trusted SHA vs main executable diff
5. Chart trusted SHA vs product-completion-mvp diff
6. 현재 NEXT micro-tranche 하나만 계속
```

첫 답변은 짧게 `한 일 / 할 일`로 구분한다.
