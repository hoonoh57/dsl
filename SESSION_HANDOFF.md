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

### 2. 1분봉 재시작 시 일봉으로 복귀

사용자가 1분봉을 선택하고 화면을 다시 열면 timeframe이 다시 일봉으로 초기화되는 문제가 이어서 확인됐다.

분류:

```text
UI workspace persistence defect
```

원인은 chart workspace가 최근 종목/표시 봉 수는 기억하지만 timeframe은 항상 `day`로 초기화하던 것이다.

최소 수정:

```text
chart timeframe(period + interval) workspace preference 저장
 -> 시작 시 strict validation
 -> 유효한 저장값을 default day보다 먼저 적용
 -> 그 timeframe으로 startup loadInitial() 실행
```

월/주/일, 현재 지원되는 모든 분봉 interval, 모든 tick interval을 같은 규칙으로 처리한다. 잘못된 저장값은 사용하지 않고 기본 일봉으로 돌아간다.

이 workspace preference는 전략/지표 Add-on JSON과 별개의 UI 상태다. 이를 전략 JSON schema에 섞거나 DSL Core/Bridge에서 timeframe을 자동 보정하지 않는다.

수정 소유 위치는 chart-platform shell/UI state이며 DSL Core, Add-on 계산, frozen legacy core는 변경하지 않았다.

## UIA-1 다음 검증

사용자 local:

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
node --test vendor\kiwoom-condition\condition1516\chart-platform\tests\market-chart-workspace-initial-load.test.mjs
node --test vendor\kiwoom-condition\condition1516\chart-platform\tests\workspace-timeframe-preference.test.mjs
node --test chart_bridge\chart_platform_server.test.mjs
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

그 뒤 UI 재시작 후:

```text
조회 클릭 없이 시작 직후 candle chart 표시
분 -> 1 선택 후 화면 재시작
재시작 직후 1분봉 그대로 유지
저장된 1분봉으로 candle chart 자동 조회
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
