# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / WYSIWYG STRATEGY PRODUCT FLOW ACTIVE / DSL_WORKSPACE_TRUSTED_01da3bc / CHART_MANAGER_TRUSTED_c67d3d8 / NEXT_1A_HTTP_ADAPTER_REMOTE_UNVALIDATED / REALDATA2_LF_RESEARCH_PAUSED / REMEDIATION_REQUIRED / 2026-09-05 KST**

이 문서는 새 세션이 가장 먼저 읽는 인수인계 문서다. 세션이 바뀌어도 프롬프트 중심 실험으로 회귀하지 않고, Chart WYSIWYG 전략제품 흐름을 그대로 이어가기 위한 기준이다.

## 1. 개발철학

1. **4축/계층 경계를 유지한다.** 직접 import/직접 상태접근보다 표준 Request -> Response 계약을 우선한다.
2. **베이스 전략은 보존하고 공통 기능은 선택 가능한 Add-on으로 확장한다.** optional Add-on OFF는 baseline을 바꾸면 안 된다.
3. **DSL이 전략 의미와 실행 의미의 authority다.** Chart는 DSL parser/JMA/crossover/order timing을 별도로 authoritative 계산하지 않는다.
4. **WYSIWYG가 제품 기준이다.** 보이는 DSL/파라미터/신호/백테스트/Paper/Live가 동일 exact strategy version과 profile을 가리켜야 한다.
5. **micro-tranche만 진행한다.** owner -> shared path -> SSOT -> create/delete authority -> prohibitions -> focused -> WYSIWYG -> Full -> checkpoint 순서를 지킨다.

## 2. 최종 큰 흐름

```text
Strategy Manager Dialog
 -> DSL strategy CRUD
 -> authoritative validate + immutable version
 -> strategy별 parameter/add-on profile CRUD
 -> Chart 적용
 -> DSL authoritative signal/execution WYSIWYG
 -> strategy 단위 Backtest Dialog
 -> same DSL/version/profile Paper
 -> Backtest vs Paper 비교
 -> minimal fine tuning
 -> limited Live
```

프롬프트는 개발 보조도구다. 전략 개발이력/성과의 SSOT가 아니다.

## 3. 작업공간 분리 — 절대 혼용 금지

### DSL

```text
repo: hoonoh57/dsl
branch: main
local:
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
01da3bc6b21c126efd6ffa3b220e2a34de5ef64b
```

사용자 local evidence:

```text
test_stage1_wysiwyg_strategy_workspace.py
  Ran 7 tests / OK
Tactical P1 Full
  PASS
```

### Chart

```text
repo: hoonoh57/cascading-feature-solution
branch: product-completion-mvp
local:
  E:\2026\gemini\cascade-chart-validation-20260904
```

현재 trusted Chart checkpoint:

```text
c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda
```

사용자 local evidence:

```text
tests/dsl_strategy_manager_workspace_port.test.mjs
  5 pass / 0 fail

tests/managed_strategy_addon.test.mjs
  8 pass / 0 fail
```

이번 PASS의 의미:

```text
active Strategy Manager authoring path = DSL-first
strategyWorkspace capability 없으면 fail-closed
Chart local JMA evaluator로 validation fallback 금지
Runtime subjectViews/generic marker transport regression PASS
```

## 4. 완료된 제품단계

### WYSIWYG-0 — DSL Strategy Workspace

Trusted: `01da3bc6...`

```text
StrategyWorkspace
 -> core.db CRUD
 -> exact DSL
 -> BacktestEngine.run(exact_dsl)
 -> artifact_versions
 -> validation_events
```

현재 DSL과 exact validated version이 같을 때만 VALIDATED다. DSL 변경 시 과거 validation은 이력으로 남고 현재 전략은 DRAFT가 된다.

### WYSIWYG-1 — Chart DSL-first Strategy Manager shell

Trusted: `c67d3d8...`

현재 UI:

```text
전략 목록
신규 / 복제 / 삭제
전략명 / 설명
DSL Editor
Draft 저장 요청
검증 후 저장 요청
validation status
```

아직 production HTTP bridge, Chart apply, Backtest Dialog, Paper/Live는 없다.

## 5. 현재 위치 — NEXT-1 production StrategyWorkspace Bridge

NEXT-1을 세 micro-tranche로 고정한다.

```text
NEXT-1A DSL HTTP adapter contract
NEXT-1B Chart BrowserPort + same-origin proxy
NEXT-1C composition + 실제 Dialog CRUD WYSIWYG
```

### NEXT-1A 현재 상태

Remote executable/test candidate:

```text
27882d288f52c98ab48a59b0d7ae2c2de0dcd637
status: REMOTE_UNVALIDATED
```

신규:

```text
addons/strategy_manager/http_bridge.py
test_stage1_strategy_workspace_http_bridge.py
```

HTTP contract:

```text
GET    /api/strategy-workspace/strategies
POST   /api/strategy-workspace/draft
DELETE /api/strategy-workspace/strategies/{strategy_id}
POST   /api/strategy-workspace/validate-commit
```

권한:

```text
HTTP adapter -> StrategyWorkspace only
```

금지:

```text
HTTP adapter -> core.db 직접접근
HTTP adapter -> BacktestEngine 직접접근
Chart local evaluator fallback
Chart apply/backtest/paper/live를 이번 tranche에 추가
```

중요: **NEXT-1A adapter는 아직 main FastAPI composition에 mount되지 않았다.** endpoint production wiring 완료로 주장하지 않는다.

현재 DSL `main` HEAD는 docs-only checkpoint가 `27882d...` 뒤에 있을 수 있다. executable trust는 local PASS 전까지 `01da3bc...`에 머문다.

## 6. 바로 다음 할 일

반드시 DSL workspace로 이동한다.

```powershell
Set-Location E:\2026\gemini\dsl-main-validation-20260904

git fetch origin main
git checkout --detach origin/main
git rev-parse HEAD
```

focused:

```powershell
python -m unittest -v `
  test_stage1_strategy_workspace_http_bridge.py `
  test_stage1_wysiwyg_strategy_workspace.py
```

그 다음 Full:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\verify_tactical_p1.ps1 `
  -Mode Full `
  -ChartRepo ..\cascade-chart-validation-20260904
```

PASS하면:

```text
NEXT-1A trusted
 -> NEXT-1B Chart BrowserStrategyWorkspacePort + same-origin proxy
```

FAIL이면 먼저:

```text
test defect / product defect / authority drift / environment issue / external data defect / unknown
```

으로 분류한다. assertion/guard를 약화하지 않는다.

## 7. NEXT-1B / NEXT-1C 이후 순서

```text
NEXT-1B
  Browser StrategyWorkspace Port
  + Chart shell proxy
  + network/error fail-closed

NEXT-1C
  DSL HTTP adapter FastAPI mount
  + Chart capabilities.strategyWorkspace composition
  + 실제 Strategy Manager CRUD/validation WYSIWYG

NEXT-2
  Global Parameter Catalog
  + strategy별 override CRUD
  + 기본값 복원
  + Backtest/Paper/Live 적용범위

NEXT-3
  validated strategy/version/profile -> selected Chart subject
  + authoritative signal/execution result projection

NEXT-4
  strategy 단위 Backtest Dialog
  + 기간/종목/전략/profile 선택
  + report + execution markers

NEXT-5
  same DSL/version/profile realtime Paper
  -> evidence comparison
  -> minimal fine tuning
  -> limited Live
```

## 8. Parameter/Add-on 원칙

공통 항목 정의는 Global Catalog에 둔다. 값은 전략별 CRUD 가능해야 한다.

```text
Global default
 + Strategy override
 = EffectiveStrategyParameters(strategy_id, mode)
```

우선순위:

```text
Strategy override
 > Global default
 > System hard default
```

RESET은 override를 제거하여 기본값으로 복원하는 방식이 원칙이다.

공통 Add-on 후보:

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

필수 contract:

```text
BASE = BASE + every optional Add-on OFF
```

## 9. 연구/수익실험 상태

Strategy1 JMA baseline은 보존하지만 현재 제품구조 개발을 지배하지 않는다.

```text
REALDATA1 baseline
return +88.6856%
PF 2.9235
MDD -23.9177%
closed trades 15
```

slippage 0.20%에서도 약 +80.92%, PF 2.649였다. fixed stop 6/8/10%는 REJECTED. 일부 trailing 후보도 material improvement가 없었다.

REALDATA2/LF research는 현재 **PAUSED**다. WYSIWYG 전략제품 흐름에 직접 필요할 때만 재개한다.

broader repository compliance는 계속:

```text
REMEDIATION_REQUIRED
```

## 10. 세션복구 규칙

사용자가 `세션복구`라고 하면:

```text
1. SESSION_HANDOFF.md 읽기
2. STRATEGY_PRODUCT_FLOW_TODO.md 읽기
3. 최근 사용자 local test evidence 확인
4. DSL trusted SHA vs remote executable/test diff 확인
5. Chart trusted SHA vs product-completion-mvp diff 확인
6. 현재 NEXT micro-tranche 하나만 계속
```

첫 답변은 짧게:

```text
한 일
할 일
```

으로 구분한다.
