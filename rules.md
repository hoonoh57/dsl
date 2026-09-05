# rules.md

Status: **SOLE OPERATING RULES AUTHORITY**

이 저장소의 개발·검증·세션복구 운영 원칙은 이 문서 하나가 authority다.

## 1. 운영문서 SSOT

운영문서는 정확히 두 개만 사용한다.

```text
rules.md  = 불변 원칙 / 금지사항 / 운영계약
todo.md   = 현재 상태 / trusted SHA / 진행중 tranche / 다음 할 일
```

새 세션 복구 순서도 오직 다음뿐이다.

```text
1. rules.md
2. todo.md
3. 최근 사용자 local PASS/FAIL evidence
4. trusted SHA와 remote executable diff 확인
```

금지:

- `SESSION_HANDOFF.md`, `CURRENT_STATE.md`, 별도 `*_TODO.md`, 별도 정책문서 등을 현재 운영 authority로 사용
- 여러 문서를 합성하여 현재 상태를 추론
- 새 운영원칙마다 새 Markdown authority 문서를 생성
- 오래된 문서의 상태를 `todo.md`보다 우선

그 외 Markdown은 설계/과거 증거/참고자료일 수 있으나 **세션복구·현재상태·다음 작업 판정에는 사용하지 않는다.** 새 운영 원칙은 반드시 `rules.md`, 진행상태는 반드시 `todo.md`에만 반영한다.

## 2. 개발 전 강제 게이트

모든 executable 변경 전에 다음을 먼저 확정한다.

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

한 tranche에 여러 권한 경계를 섞지 않는다.

## 3. 제품 authority / WYSIWYG

전략 의미와 실행 의미의 authority는 DSL이다. Chart는 DSL parser/JMA/crossover/order timing/backtest 의미를 별도로 authoritative 계산하지 않는다.

```text
보이는 DSL
= 저장된 exact DSL
= 검증된 exact DSL/version
= Chart 신호를 만든 DSL
= Backtest한 DSL
= Paper/Live가 사용하는 DSL
```

파라미터도 같은 원칙을 따른다.

```text
Global Parameter Catalog(default)
+ Strategy Override
= EffectiveStrategyParameters(strategy_id, mode)
```

공통 항목 schema는 하나이고 값은 전략별 독립 CRUD 가능해야 한다. reset은 override 삭제로 기본값을 복원한다.

## 4. 저장소/축 경계

축/저장소 사이 직접 import·직접 DB/상태 접근 대신 표준 Request -> Response 계약을 사용한다.

### DSL owner

- DSL source SSOT
- strategy CRUD persistence
- artifact/version/validation history
- BacktestEngine authoritative semantics
- later Backtest/Paper execution result authority

### Chart owner

- Strategy Manager UX
- Browser Request/Response adapter
- same-origin transport proxy
- generic Runtime chart state / subject view
- authoritative DSL result visualization

금지:

- Chart가 DSL 의미를 재구현
- Strategy Manager UI가 DB 직접 접근
- Runtime/UI 이중 복원권한
- Backtest/Paper/Live가 서로 다른 strategy semantics 사용
- capability 부재 시 로컬 의미 fallback

## 5. Base + Add-on 원칙

베이스 전략은 보존하고 공통 기능은 선택 가능한 Add-on으로 확장한다.

필수 invariant:

```text
BASE = BASE + every optional Add-on OFF
```

적응형/학습형 기능은 Core/기본 DSL 의미를 오염시키지 않는다. deterministic hard guard/equipment를 Core에서 우선한다.

## 6. 실패 분류

수정 전에 반드시 먼저 분류한다.

```text
test defect
product defect
authority drift
environment issue
external data defect
unknown
```

테스트 PASS를 위해 assertion/guard/authority 규칙을 약화하지 않는다.

## 7. 콘솔 운영 원칙

콘솔은 성공 이력을 나열하는 곳이 아니라 실패를 즉시 찾는 디버깅 인터페이스다.

### 성공

기본 출력은 1줄이다.

```text
[PASS] <verification> passed (<count>).
```

### 실패

실패 내용만 기본 콘솔에 남긴다.

```text
[ERROR] <verification> failed (<count>).
[FAIL] <test/stage>
  at <file:line>
  <핵심 assertion/exception message>
```

기본 diagnostic은 약 30~40줄 이내로 유지한다. 더 긴 raw 로그는 실패 후 별도 디버깅 단계에서만 사용한다.

금지:

- 성공한 개별 테스트 이름 수십 줄 출력
- 성공 stdout/stderr를 실패 로그에 혼합
- 기본 검증에서 `python -m unittest -v ...` 직접 사용
- 기본 검증에서 `node --test ...` 직접 사용
- 사용자에게 성공 로그 전체 paste 요구

허용되는 focused 기본 경로:

```text
DSL   : python .\scripts\run_focused_tests.py <targets...>
Chart : npm test -- <test-files...>
```

Full:

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 ...
```

```text
compact output != weaker verification
```

출력량을 줄이기 위해 테스트 수, assertion, guard, stderr 검증을 약화하지 않는다.

## 8. 작업공간 분리

DSL validation workspace:

```text
E:\2026\gemini\dsl-main-validation-20260904
```

Chart validation workspace:

```text
E:\2026\gemini\cascade-chart-validation-20260904
```

다른 repo의 branch/test 명령을 현재 repo에서 실행하지 않는다.

DSL workspace의 `strategies.db` 수정 상태는 명시적 지시 없이 stash/reset/checkout/merge하지 않는다.

## 9. 검증/체크포인트 규칙

순서:

```text
focused
-> 필요한 경우 WYSIWYG
-> Full
-> trusted checkpoint 승격
-> todo.md 갱신
-> 다음 micro-tranche
```

broader compliance가 `REMEDIATION_REQUIRED`이면 좁은 PASS를 전체 PASS로 과장하지 않는다.

## 10. 제품 진행 순서

현재 큰 흐름은 다음 순서를 유지한다.

```text
Strategy Manager CRUD/validation
-> strategy별 Parameter Profile CRUD
-> validated strategy/version/profile Chart apply
-> authoritative signal/execution WYSIWYG
-> strategy Backtest Dialog
-> same DSL/version/profile Paper
-> evidence comparison / minimal fine tuning
-> limited Live
```

REALDATA2/LF/adaptive learning/automatic selection은 현재 제품 흐름에 직접 필요할 때까지 PAUSED다.
