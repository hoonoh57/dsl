# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 현재 단계는 지금까지 이식한 DSL 기능을 실제 UI 경로에서 하나씩 일관성 검증하는 단계다.

## 현재 상태

```text
PREVIOUS REMEDIATION = Steps 1 through 15 COMPLETE / USER-LOCAL PASS
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 startup/workspace state restore
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

현재 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
```

## UIA-1 현재 수정

### 1. 시작 직후 빈 차트

사용자 화면에서 시작 직후 UI는 보이지만 candle chart가 비어 있고 `조회`를 눌러야 최초 화면이 렌더되는 문제가 확인됐다.

분류:

```text
Bridge / Runtime startup ordering defect
```

최소 수정:

```text
state hydrate
 -> UI/runtime wiring
 -> existing loadInitial() 자동 1회 await
 -> READY
```

### 2. 선택 timeframe 재기동 복원 실패

1분봉/5분봉을 실제로 띄운 뒤 브라우저를 종료하고 재기동해도 다시 일봉으로 시작하는 문제가 확인됐다.

초기 localStorage preference 방식은 현재 managed browser 재기동 경로에서 제품 수준의 durable restore를 보장하지 못했으므로 최종 영속성 권한으로 사용하지 않는다.

분류:

```text
JSON persistence boundary defect
```

수정:

```text
UI timeframe 선택
 -> chart shell preference port
 -> Bridge의 versioned JSON file persistence
 -> 다음 bootstrap에서 JSON을 먼저 hydrate
 -> 기존 MarketChartWorkspace mount
 -> 복원된 timeframe으로 startup loadInitial()
```

제품 영속 파일:

```text
.runtime/dsl-stack/chart-workspace-timeframe.json
```

파일은 schemaVersion + timeframe(period/interval)만 저장한다. 월/주/일과 현재 지원되는 분봉/틱 interval만 허용하며 지원되지 않는 값은 저장 단계에서 fail-closed한다.

브라우저 종료 직전에는 최신값을 beacon으로 같은 JSON route에 다시 전송한다. 정상 선택 변경도 ordered PUT queue로 즉시 저장한다.

chart-platform standalone에서는 기존 localStorage fallback을 유지하지만, DSL 제품에서는 주입된 JSON persistence port가 우선권을 가진다. 따라서 전략/지표 Add-on JSON이나 DSL Core에 workspace timeframe을 혼입하지 않는다.

경계:

```text
DSL/Core 계산 변경 없음
Add-on 전략/timeframe 검증 변경 없음
Chart workspace preference와 strategy/add-on JSON 분리 유지
Bridge는 저장/복원만 수행하고 timeframe 의미를 재계산하지 않음
root frozen core 변경 없음
```

## UIA-1 다음 검증

사용자 local:

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
node --test vendor\kiwoom-condition\condition1516\chart-platform\tests\market-chart-workspace-initial-load.test.mjs
node --test vendor\kiwoom-condition\condition1516\chart-platform\tests\workspace-timeframe-preference.test.mjs
node --test chart_bridge\browser\WorkspaceTimeframeJsonPersistence.test.mjs
node --test chart_bridge\workspace_timeframe_persistence.test.mjs
node --test chart_bridge\chart_platform_server.test.mjs
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

그 뒤 UI에서:

```text
분 -> 5 -> 조회
5분봉 표시 확인
브라우저 종료
start.bat 또는 restart.bat로 재기동
조회 클릭 없이 5분봉 + candle 자동 복원
```

을 확인한다. PASS 전 다음 기능으로 넘어가지 않는다.

## UI 검증 수정 원칙

사용자가 명시한 계층 분리:

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

수정 사유가 생기면 먼저 어느 계층의 결함인지 분류하고 그 계층에서만 최소 수정한다.

### Core

현재 제품의 deterministic DSL 의미/계산 계층이다. 신규 수정 위치는 `axes/axis1_dsl/`이며 repository-root `core/`는 frozen reference로 계속 불변이다.

### Bridge / Runtime

request/response validation, UI-to-contract adaptation, lifecycle/routing, context binding을 소유한다. 지표/전략/선별을 재계산하거나 누락값을 보정하지 않는다.

### Add-ons

범용 Core 위의 기능별 조합/확장을 소유한다. Add-on 요구를 Core나 Bridge의 제품특례로 숨기지 않는다.

### JSON persistence

schema/version/hash 저장·복원만 소유하며 계산/조건판정/주문의미/실행값 보정을 하지 않는다.

## Frozen legacy Core

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제 금지.
