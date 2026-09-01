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
CURRENT_SUBSTEP = UIA-1 startup restore / automatic primary chart load
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

현재 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
```

## UIA-1 현재 수정

사용자 화면에서 시작 직후 KOSPI 001 / 일봉 UI는 복원됐지만 candle chart가 비어 있고, `조회`를 눌러야 최초 화면이 렌더되는 문제가 확인됐다.

원인 분류:

```text
Bridge / Runtime startup ordering defect
```

코드상 `MarketChartWorkspace.mount()`는 persistence hydrate와 UI/runtime 연결까지만 수행하고 기존 manual `loadInitial()` 호출 없이 READY를 반환했다.

최소 수정:

```text
state hydrate
 -> UI/runtime wiring
 -> existing loadInitial() 자동 1회 await
 -> READY
```

수정 소유 위치는 chart-platform shell/runtime이며 DSL Core, Add-on 계산, JSON schema는 변경하지 않았다.

같은 chart-platform에 focused regression을 추가했고 `dsl-live-studio`는 수정된 submodule revision을 pin한다.

별도 관찰:

```text
현재 chart = 1일
persisted DSL strategy timeframe = 1m
```

이 mismatch는 기존 fail-closed Add-on 검증이며 base candle startup defect와 분리한다. 이를 해결한다는 이유로 Core/Bridge에서 timeframe을 자동 변조하지 않는다.

## UIA-1 다음 검증

사용자 local:

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
node --test vendor\kiwoom-condition\condition1516\chart-platform\tests\market-chart-workspace-initial-load.test.mjs
node --test chart_bridge\chart_platform_server.test.mjs
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

그 뒤 UI 재시작 후:

```text
조회 클릭 없이 시작 직후 candle chart 표시
Add-on 오류가 있더라도 base candle chart 유지
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
