# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / WYSIWYG STRATEGY PRODUCT FLOW ACTIVE / DSL_BRIDGE_1A_TRUSTED_27882d2 / CHART_MANAGER_TRUSTED_c67d3d8 / NEXT_1B_CHART_TRANSPORT_REMOTE_UNVALIDATED_23c85f2 / REALDATA2_LF_RESEARCH_PAUSED / REMEDIATION_REQUIRED / 2026-09-05 KST**

이 문서는 새 세션이 가장 먼저 읽는 인수인계 문서다. 세션이 바뀌어도 프롬프트 중심 실험이나 단일 전략 파라미터 튜닝으로 회귀하지 않고, Chart WYSIWYG 전략제품 흐름을 그대로 이어가기 위한 기준이다. `STRATEGY_PRODUCT_FLOW_TODO.md`는 전체 roadmap이며, 현재 checkpoint가 충돌하면 이 문서 + 사용자 exact local test evidence가 우선한다.

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
27882d288f52c98ab48a59b0d7ae2c2de0dcd637
```

사용자 local evidence:

```text
NEXT-1A + Strategy Workspace focused:
  Ran 13 tests / OK
Tactical P1 Full:
  PASS
```

이 PASS로 `addons/strategy_manager/http_bridge.py`의 HTTP adapter contract가 trusted다. 단, **adapter 정의만 trusted이며 아직 FastAPI composition root에 mount되지 않았다.** production endpoint 활성화는 NEXT-1C 책임이다.

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

의미:

```text
active Strategy Manager authoring path = DSL-first
strategyWorkspace capability 없으면 fail-closed
Chart local JMA evaluator로 validation fallback 금지
Runtime subjectViews/generic marker transport regression PASS
```

## 4. 완료된 제품단계

### WYSIWYG-0 — DSL Strategy Workspace — DONE / TRUSTED

```text
StrategyWorkspace
 -> core.db CRUD
 -> exact DSL
 -> BacktestEngine.run(exact_dsl)
 -> artifact_versions
 -> validation_events
```

현재 DSL과 exact validated version이 같을 때만 VALIDATED다. DSL 변경 시 과거 validation은 이력으로 남고 현재 전략은 DRAFT가 된다.

### WYSIWYG-1 — Chart DSL-first Strategy Manager shell — DONE / TRUSTED

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

### NEXT-1A — DSL HTTP adapter contract — DONE / TRUSTED

Trusted executable/test SHA:

```text
27882d288f52c98ab48a59b0d7ae2c2de0dcd637
```

표준 DSL endpoint contract:

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

금지된 직접권한:

```text
HTTP adapter -> core.db 직접접근
HTTP adapter -> BacktestEngine 직접접근
```

## 5. 현재 위치 — NEXT-1B Chart BrowserPort + same-origin proxy

Chart remote candidate:

```text
23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
status: REMOTE_UNVALIDATED
base trusted: c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda
```

변경은 정확히 세 파일이다.

```text
src/adapters/strategy/BrowserStrategyWorkspacePort.mjs
src/shell/index-wysiwyg/StrategyWorkspaceHttpHost.mjs
tests/strategy_workspace_http_transport.test.mjs
```

역할:

```text
DslStrategyManagerUi camelCase request
 -> BrowserStrategyWorkspacePort
 -> same-origin /__cascade/strategy-workspace/*
 -> StrategyWorkspaceHttpHost proxy
 -> DSL /api/strategy-workspace/*
```

Browser adapter에서 transport naming만 한 번 변환한다.

```text
strategyId -> strategy_id
dslCode    -> dsl_code
```

proxy는 전략 의미를 해석/계산하지 않는다. 네 개 고정 endpoint와 HTTP status/payload만 전달한다.

### NEXT-1B에서 일부러 아직 하지 않은 것

```text
scripts/serve.mjs에 proxy mount 안 함
MarketChartWorkspace에 BrowserStrategyWorkspacePort 생성 안 함
capabilities.strategyWorkspace 주입 안 함
DSL main.py에 router mount 안 함
실제 Dialog CRUD network call 안 함
Chart apply/backtest/paper/live 안 함
```

따라서 현재는 **transport contract implemented, production composition not connected** 상태다.

## 6. 바로 다음 할 일 — NEXT-1B local validation

반드시 Chart workspace에서 실행한다.

```powershell
Set-Location E:\2026\gemini\cascade-chart-validation-20260904

git fetch origin product-completion-mvp
git checkout --detach origin/product-completion-mvp
git rev-parse HEAD
```

기대 SHA:

```text
23c85f2252eac6e3087bb9cf4bd502dfe10c5ecf
```

focused transport:

```powershell
node --test tests/strategy_workspace_http_transport.test.mjs
```

기존 DSL-first Manager contract regression:

```powershell
node --test tests/dsl_strategy_manager_workspace_port.test.mjs
node --test tests/managed_strategy_addon.test.mjs
```

판정:

```text
전부 PASS
 -> 23c85f2... Chart transport trusted
 -> NEXT-1C composition + 실제 Dialog CRUD WYSIWYG

FAIL
 -> test defect / product defect / authority drift / environment issue / external data defect / unknown 먼저 분류
 -> assertion/guard 약화 금지
```

## 7. NEXT-1C — production composition + 실제 CRUD WYSIWYG

NEXT-1B가 trusted된 뒤에만 진행한다.

이 tranche에서 연결할 것:

```text
DSL main.py
 -> http_bridge.router mount

Chart scripts/serve.mjs
 -> StrategyWorkspaceHttpHost middleware mount
 -> explicit DSL service base URL

Chart MarketChart composition
 -> BrowserStrategyWorkspacePort
 -> addons.capabilities.strategyWorkspace

Strategy Manager Dialog
 -> 실제 list/create/update/delete
 -> validate + immutable commit
 -> dialog close/reopen 후 exact validation state 복구
```

WYSIWYG 완료조건:

```text
1. Dialog 신규 전략 생성
2. Draft 저장
3. DSL 수정
4. 이전 VALIDATED 상태 자동 무효 확인
5. 검증 후 저장
6. Dialog 재오픈
7. 동일 exact DSL/version이 VALIDATED로 복구
8. 삭제
9. 재오픈 후 삭제 상태 유지
10. Chart는 local JMA evaluator fallback하지 않음
```

이번 NEXT-1C에도 금지:

```text
차트 신호 삽입
Backtest Dialog
Paper/Live
전략별 parameter profile
```

이것들은 bridge CRUD가 WYSIWYG로 닫힌 뒤 별도 tranche로 간다.

## 8. 이후 roadmap

```text
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
  + authoritative report + execution markers

NEXT-5
  same DSL/version/profile realtime Paper
  -> evidence comparison
  -> minimal fine tuning
  -> limited Live
```

## 9. Parameter/Add-on 원칙

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

## 10. 연구/수익실험 상태

Strategy1 JMA baseline은 보존하지만 현재 제품구조 개발을 지배하지 않는다.

```text
REALDATA1 baseline
return +88.6856%
PF 2.9235
MDD -23.9177%
closed trades 15
```

fixed stop 6/8/10%는 REJECTED. 일부 trailing 후보도 material improvement가 없었다. 현재는 개별 숫자 튜닝보다 WYSIWYG 전략제품 경로를 먼저 완성한다.

REALDATA2/LF research는 현재 **PAUSED**다. 현재 profit-strategy product flow에 직접 필요할 때만 재개한다.

broader repository compliance는 계속:

```text
REMEDIATION_REQUIRED
```

## 11. 세션복구 규칙

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
