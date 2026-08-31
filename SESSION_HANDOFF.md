# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 5-4 / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 검증된 migrated core는 안정된 실행 장비처럼 유지한다. 신규 DSL 기능은 가능한 한 명시적 contract + 얇은 lowering/facade 층으로 격리해 기존 메인 로직 오염을 피한다.

---

## 현재 작업

```text
CURRENT_STEP = 5
CURRENT_SUBSTEP = 5-4 user-defined functions
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
Step 1 기존 DSL 남은 기능 점검 = COMPLETE
Step 2 AXIS 1 migration 설계/순서 = COMPLETE
Step 3 Frozen Core 보호 gate = COMPLETE / USER-LOCAL PASS
Step 4 AXIS 1 9개 migration boundary = COMPLETE / USER-LOCAL PASS
Step 5-1 multi-output + destructuring = COMPLETE / USER-LOCAL PASS
Step 5-2 tuple-aware generic projection = COMPLETE / USER-LOCAL PASS
Step 5-3 capability/function metadata = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP5_3_CAPABILITY_METADATA_CHECKPOINT_2026-08-31.md
```

5-3 user-local evidence:

```text
tests/test_axis1_capability_metadata.py = OK
tests/test_axis1_generic_projection.py = OK
tests/test_frozen_legacy_core_guard.py = OK
```

---

## 현재 5-4 구현

목표:

```text
반복 계산식을 전략 내부의 이름 있는 순수 함수로 작성할 수 있게 하되
실행 runtime에 동적 함수 권한을 추가하지 않고 compile 전에 deterministic expression으로 소거
```

구현 파일:

```text
axes/axis1_dsl/core/user_functions.py
axes/axis1_dsl/runtime/axis1_runtime.py
axes/axis1_dsl/execution/axis1_backtest.py
tests/test_axis1_user_functions.py
```

문법 예:

```text
function centered(source, period) {
    basis = ta.sma(source, period)
    return source - basis
}

strength = centered(close, 20)
```

현재 contract:

```text
strategy top-level 함수 선언
위치 인수만 허용
ordered local + final return expression
순수 계산만 허용
외부 시장값/ctx는 암묵 참조 금지 -> 함수 인수로 명시 전달
builtin/user-function 합성 허용
직접/간접 recursion 금지
if/loop/state/order/on_bar 등 함수 내부 control/mutation 금지
함수 호출은 기존 expression으로 inline
inline 후 기존 Semantic이 실제 scalar/series/bool/string type을 검증
함수 선언 line은 blank line으로 보존해 downstream 오류 line 유지
```

Lowering 순서:

```text
user functions
 -> multi-output
 -> migrated parser/semantic/runtime/backtest
 -> generic projection
```

Backtest diagnostics에는 함수 이름/parameter/local/line의 공개 정의정보만 보존한다. 함수 실행 자체는 runtime registry가 아니라 compile-time inline이다.

---

## Frozen legacy Core — 절대 보존

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

금지:

```text
core/ 수정 / 이동 / 삭제 / 신규 파일 추가
expected frozen hash 변경으로 위반 수용
새 feature를 frozen core에 역이식
신규기능 때문에 migrated core를 불필요하게 대수술
5-5 bounded loop 선행 구현
검증완화
```

---

## 다음 순서

```text
5-4 user-defined functions                 CURRENT
5-5 bounded loops
5-6 on_tick / on_fill commit/rollback
5-7 partial fills / partial exits
5-8 pyramiding / multi-position
5-9 reference differential fixtures
5-10 full-engine batch/streaming parity
6 machine-readable capability/diagnostic registry
7 Bridge common + AXIS 1 execution contract
8 AXIS 2 exact-as-of snapshot contract
9 AXIS 2 selection engine
10 AXIS 3 Condition/Strategy CRUD
11 3축 E2E Bridge
12 External LLM Authoring Lane
13 Continuous Improvement tooling
14 natural-language E2E acceptance
15 legacy docs + repo-wide compliance audit
```

---

## 사용자 커뮤니케이션 / 콘솔

```text
사용자 화면 = 한 일 / 할 일
정상 콘솔 = 가능하면 [PASS] 한 줄
실패 콘솔 = 디버깅에 필요한 최소 원인/위치
기계용 상세정보 = 내부 관리
```

---

## 다음 exact action

사용자 local에서:

```text
python -m unittest discover -s tests -p "test_axis1_user_functions.py" -v
python -m unittest discover -s tests -p "test_axis1_multi_output.py" -v
python -m unittest discover -s tests -p "test_axis1_generic_projection.py" -v
python -m unittest discover -s tests -p "test_axis1_capability_metadata.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 5-4 checkpoint 후 5-5 bounded loops로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 원칙/assertion을 약화하지 않는다.
