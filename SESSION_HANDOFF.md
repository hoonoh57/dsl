# DSL Session Handoff

Status: **PRIMARY HANDOFF / PROFIT-STRATEGY PRODUCT FLOW / DSL_TRUSTED_01da3bc / CHART_c67d3d8_REMOTE_UNVALIDATED / 2026-09-05 KST**

이 문서는 새 세션이 가장 먼저 읽는 인수인계 문서다. 세부 실행 순서와 장기 TODO는 바로 이어서 `STRATEGY_PRODUCT_FLOW_TODO.md`를 읽는다.

> 중요: 기존 `CURRENT_STATE.md`의 REALDATA2/LF next-boundary 내용은 연구 경로의 과거 상태다. 현재 제품 우선순위는 아래 **profit-strategy product flow**가 우선한다. REALDATA2/LF 연구는 필요성이 다시 생길 때까지 PAUSED다.

## 1. 현재 최상위 목적

DSL 자체를 계속 확장하는 것이 목적이 아니다.

```text
수익 아이디어
 -> DSL 전략 작성/저장
 -> authoritative DSL 검증
 -> 역사 백테스트
 -> Chart WYSIWYG 신호/체결 확인
 -> 실시간 모의매매
 -> 백테스트 vs 모의매매 비교
 -> 최소 fine tuning
 -> 제한적 실거래
 -> 재검증
```

현재 선택한 수익전략을 정확히 표현·백테스트·모의매매하는 데 직접 필요하지 않은 범용 DSL/Chart 기능은 추가하지 않는다.

## 2. 개발 원칙

1. **Core는 결정론적 hard equipment/guard를 우선한다.** 학습/자율성은 Core를 오염시키지 않는다.
2. **동일 기능의 권한은 하나만 둔다.** Chart와 DSL이 각각 전략 계산/검증/실행 semantics를 구현하지 않는다.
3. 구현 전 반드시 `owner layer -> shared path -> state SSOT -> create/delete authority -> adjacent prohibitions`를 확정한다.
4. 구현은 `one-boundary micro-tranche -> focused -> Full -> checkpoint` 순서다.
5. 실패는 `test defect / product defect / authority drift / environment issue / external data defect / unknown`으로 먼저 분류한다. PASS를 위해 assertion/guard를 약화하지 않는다.

broader repository compliance authoritative status는 계속 **REMEDIATION_REQUIRED**다.

## 3. 저장소와 로컬 작업공간 — 절대 혼동 금지

### DSL

```text
repo:
  hoonoh57/dsl
local validation workspace:
  E:\2026\gemini\dsl-main-validation-20260904
trusted executable/test SHA:
  01da3bc6b21c126efd6ffa3b220e2a34de5ef64b
```

이 workspace에서 실행하는 것:

- Python `test_stage1_*.py`
- `scripts/verify_tactical_p1.ps1`
- DSL StrategyWorkspace / BacktestEngine 검증

`strategies.db`는 테스트/실행 중 수정될 수 있다. 기존 원칙대로 임의 reset/stash/delete하지 않는다.

### Chart

```text
repo:
  hoonoh57/cascading-feature-solution
branch:
  product-completion-mvp
local validation workspace:
  E:\2026\gemini\cascade-chart-validation-20260904
previous trusted external checkpoint:
  258fd07ca76214819cec3822b02564e21a1c8680
current remote candidate:
  c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda
status:
  REMOTE_UNVALIDATED
```

이 workspace에서 실행하는 것:

- Node Chart Add-on tests
- Strategy Manager UI/port/runtime tests
- Chart WYSIWYG 검증

### 2026-09-05 작업공간 혼선 기록

사용자가 DSL workspace에서 다음을 실행했다.

```text
git fetch origin product-completion-mvp
 -> fatal: couldn't find remote ref product-completion-mvp

node --test tests/dsl_strategy_manager_workspace_port.test.mjs
 -> Could not find ...
```

분류: **environment/operator workspace mismatch**, product defect 아님.

원인:

```text
current directory = DSL repo
requested branch/tests = Chart repo
```

Chart 원격 브랜치는 실제 존재하며 remote HEAD는 `c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda`다.

## 4. 최근 완료 — DSL Strategy Workspace

사용자 로컬 exact checkout:

```text
01da3bc6b21c126efd6ffa3b220e2a34de5ef64b
```

검증 evidence:

```text
focused: Ran 7 tests / OK
Full: [PASS] Tactical P1 verification completed: mode=Full.
```

따라서 `01da3bc...`는 현재 DSL trusted executable/test checkpoint다.

현재 authoritative StrategyWorkspace:

```text
addons/strategy_manager/workspace.py
 -> core.db strategy CRUD
 -> validate_and_commit()
 -> existing BacktestEngine.run(exact_dsl)
 -> immutable artifact version + validation record
```

핵심 권한:

- DSL exact source/persisted artifact = DSL side SSOT
- validation = existing BacktestEngine path
- UI/client의 ephemeral `validated=true` 같은 상태는 authority 아님
- 새 UI/session은 persisted exact DSL + validation artifact를 통해 검증상태를 복원

## 5. 최근 원격 구현 — Chart DSL-first Strategy Manager

Chart branch remote candidate:

```text
c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda
```

아직 user-local PASS가 없으므로 **trusted로 승격하지 않는다.**

변경 범위:

```text
src/addons/strategy/managed/DslStrategyManagerUi.mjs
src/addons/strategy/managed/StrategyWorkspacePort.mjs
src/addons/strategy/managed/ManagerAddon.mjs
tests/dsl_strategy_manager_workspace_port.test.mjs
```

의도:

- Strategy Manager authoring을 DSL-first editor로 전환
- 신규/복제/삭제/Draft 저장/검증 요청을 `strategyWorkspace` request-response port로 전달
- port가 없으면 fail-closed
- active authoring path가 Chart local JMA evaluator로 fallback하지 않음
- 기존 Runtime subject-state 구조는 이후 authoritative chart projection을 위해 보존

이번 tranche에 **없는 것**:

- production HTTP Bridge
- chart apply
- historical backtest UI
- paper/live execution

## 6. 지금 바로 다음 할 일 — NEXT-0

먼저 Chart candidate를 올바른 Chart workspace에서 검증한다.

```powershell
Set-Location E:\2026\gemini\cascade-chart-validation-20260904

git fetch origin product-completion-mvp
git checkout --detach origin/product-completion-mvp
git rev-parse HEAD
```

기대:

```text
c67d3d8de9cfefbdfa7c0e72c4a7e1dc0b025fda
```

focused:

```powershell
node --test tests/dsl_strategy_manager_workspace_port.test.mjs
node --test tests/managed_strategy_addon.test.mjs
```

둘 다 PASS하면 `c67d3d8...`를 Chart trusted checkpoint로 승격한다.

FAIL이면 먼저 결함 분류 후 제품/테스트 경계를 수정한다. 기존 계약을 임의로 약화하지 않는다.

## 7. NEXT-1 — StrategyWorkspace HTTP Bridge 하나만

NEXT-0 PASS 후 구현한다.

```text
Chart DslStrategyManagerUi
 -> StrategyWorkspacePort
 -> standard HTTP request/response bridge
 -> DSL addons/strategy_manager/workspace.py
 -> core.db / BacktestEngine
```

이번 tranche 허용:

- list strategies
- save draft
- delete strategy
- validate + commit
- exact request/response contract
- unavailable/error fail-closed

금지:

- chart signal insertion
- backtest report UI
- paper/live
- Chart-side direct DB
- Chart-side DSL/JMA evaluator

## 8. 이후 큰 흐름

세부사항은 `STRATEGY_PRODUCT_FLOW_TODO.md`가 authoritative TODO다.

```text
NEXT-0 Chart DSL-first manager local validation
 -> NEXT-1 production StrategyWorkspace HTTP Bridge
 -> NEXT-2 authoritative validated strategy -> Chart subject apply
 -> NEXT-3 historical BacktestEngine report -> Chart WYSIWYG
 -> NEXT-4 same validated DSL -> realtime paper trading
 -> NEXT-5 evidence-based fine tuning -> limited live
```

각 NEXT는 이전 단계가 trusted되기 전 시작하지 않는다.

## 9. Strategy1 기준선

기존 `examples/jma_cross.dsl`:

```text
JMA 7/50 cross
+ SMA60 trend filter
+ long only
+ JMA crossunder exit
```

REALDATA1 baseline:

```text
closed trades = 15
total return = +88.68557782060891%
profit factor = 2.9234729545115528
MDD = -23.917654587375857%
win rate = 46.666666666666664%
total cost = 326745.03218364983
open position = 1
```

이는 promising baseline이지 profitability proof가 아니다.

Trade diagnostics에서 average MFE가 realized return보다 상당히 커 profit giveback 가능성이 보였지만, stop/trailing refinement 전에 execution model의 gap/intrabar causality를 먼저 확인해야 한다.

특히 현재 BacktestEngine risk-exit 검토 포인트:

- long stop gap-through 시 stop price 고정 fill의 낙관성 가능성
- daily OHLC trailing이 같은 bar의 새 high와 low 순서를 암묵적으로 가정할 가능성
- stop + target same-bar precedence를 deterministic contract로 명시할 필요

Core 수정은 실제 전략 backtest correctness를 막는 defect로 확인될 때만 mandatory ownership gate 후 진행한다.

## 10. 연구 경로 상태

REALDATA1 causal dataset/LFREAL3까지의 기존 trusted evidence는 보존한다.

REALDATA2/LF leader-follower 연구는 **삭제한 것이 아니라 PAUSED**다.

현재 profit-strategy path를 위해 직접 필요하지 않으므로 다음으로 진행하지 않는다:

- REALDATA2 LFREAL2/LFREAL3
- multi-symbol LF1/LF2
- adaptive learning
- automatic selection/allocation

## 11. 세션복구 규칙

새 세션에서 사용자가 `세션복구`라고 하면:

1. 이 `SESSION_HANDOFF.md`를 먼저 읽는다.
2. `STRATEGY_PRODUCT_FLOW_TODO.md`를 읽는다.
3. 최근 conversation의 exact local PASS/FAIL가 문서 이후인지 확인한다.
4. DSL repo와 Chart repo/workspace를 구분한다.
5. 각 저장소에서 `trusted`와 `REMOTE_UNVALIDATED`를 분리한다.
6. 현재 `NEXT-n` 하나만 수행한다.
7. 구현 전에 ownership gate를 적는다.
8. focused -> Full -> checkpoint 후 다음 단계로 이동한다.

문서가 stale하면 exact local evidence + 실제 코드 + 최근 사용자 결정이 우선한다.

## 12. 현재 한 줄 상태

```text
DSL StrategyWorkspace 01da3bc... = TRUSTED
Chart DSL-first Manager c67d3d8... = REMOTE_UNVALIDATED
NEXT = Chart workspace에서 c67d3d8 focused validation
THEN = StrategyWorkspace production HTTP Bridge only
```
