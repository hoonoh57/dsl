# DSL Frozen Core / Three-Axis Migration Policy

Status: **ACTIVE TRANSITION AUTHORITY / IMMUTABLE LEGACY CORE / 2026-08-31 KST**

이 문서는 기존 검증 DSL Core를 영구 기준본으로 보존하면서 새 3축 구조로 전환하는 방법을 정의한다.

이 문서가 활성화되는 즉시 기존 문서의 다음 표현은 폐기한다.

```text
"안정화 후 기존 Core를 AXIS 1 폴더로 물리 이동한다"
```

새 권한 규칙은 다음과 같다.

```text
기존 검증 Core는 이동하지 않는다.
기존 검증 Core는 수정하지 않는다.
기존 검증 Core는 영구 reference baseline으로 보존한다.
새 3축 구조는 별도 새 폴더에 이식/재편성한다.
이식 완료 후 새 구조를 독립 검증한다.
검증 전에는 새 구조가 기존 Core를 대체했다고 주장하지 않는다.
```

---

## 1. Frozen legacy Core

현재 frozen source path:

```text
core/
```

Freeze source checkpoint:

```text
branch: dsl-live-studio
commit: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

`core/`는 이후 신규 기능 개발 위치가 아니다.

금지:

```text
core/ 파일 수정
core/ 파일 삭제
core/ 내부 신규 파일 추가
새 3축 기능을 위해 core/에 compatibility exception 추가
새 AXIS 구조에서 core/ 내부 객체를 직접 import하여 영구 의존성으로 사용
```

허용:

```text
읽기
기존 regression 실행
동일 입력에 대한 golden/reference 비교
새 AXIS 1 이식 시 source reference로 사용
```

이 freeze는 기존 Core의 기능 부족까지 영구 고정한다는 뜻이 아니다. 기능 개발 위치만 새 AXIS 1으로 전환한다는 뜻이다.

---

## 2. New three-axis development root

새 제품 구현은 다음 별도 구조에서 진행한다.

```text
axes/
  axis1_dsl/
    core/
    indicators/
    runtime/
    execution/
    tests/
    README.md

  axis2_selection/
    engine/
    conditions/
    ranking/
    tests/
    README.md

  axis3_monetization/
    strategies/
    crud/
    evaluation/
    tests/
    README.md

bridges/
  contracts/
  adapters/
  routing/
  tests/
```

새 AXIS 1은 `core/`를 rename/move해서 만드는 것이 아니다.

```text
frozen core/
   |
   | explicit migration tranche
   v
axes/axis1_dsl/
```

즉 source는 보존하고 target을 새로 만든다.

---

## 3. Migration 전에 DSL capability gap을 정확히 확정한다

이식 작업은 단순 파일 복사가 아니다. 이식 전에 현재 DSL 구현 상태를 Parser / Semantic / Runtime / Indicator / Backtest / Broker / Tests 기준으로 감사한다.

최소 감사 대상:

```text
Parser / AST fail-closed boundary
scalar / series / bool / string type system
arithmetic / comparison / boolean composition
history reference
state / on_bar / nested if-else
MTF confirmed-bar semantics
parent-context binding
indicator registry and signatures
multi-output / tuple return capability
user-defined functions
bounded loops
on_tick / on_fill lifecycle + rollback
order lifecycle
partial fills / partial exits
pyramiding / multi-position accounting
visual/projection contract
batch / streaming parity
TA-Lib / external reference differential coverage
```

각 항목은 다음 중 하나로 판정한다.

```text
IMPLEMENTED_AND_TRUSTED
IMPLEMENTED_NEEDS_VERIFICATION
PARTIAL
NOT_IMPLEMENTED
DEFERRED_BY_POLICY
```

감사 결과는 `DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md`에 기록한다.

---

## 4. 현재 확인된 주요 미구현/보완 기능은 migration 이후 최우선 AXIS 1 backlog다

현재 코드와 기존 엔진 감사에서 이미 확인된 핵심 backlog:

```text
1. tuple / multi-output indicator return
2. bounded loops
3. user-defined functions
4. on_tick / on_fill execution + rollback semantics
5. partial fills / partial exits
6. pyramiding / multi-position accounting
7. full TA-Lib/reference differential fixture coverage
```

이 목록은 "나중에 해도 되는 기능"이라는 의미가 아니다.

전환 순서 때문에 잠시 구현 위치만 새 AXIS 1으로 옮긴다.

```text
현재 기능 audit 확정
 -> frozen Core 그대로 AXIS 1에 이식/재편성
 -> 기존 trusted behavior parity 검증
 -> AXIS 1 migration checkpoint
 -> 위 미구현/보완 DSL 기능 우선 개발
 -> 각 기능 micro-tranche focused test
 -> AXIS 1 full regression
```

따라서 3축 전환 때문에 DSL 고유 기능 개발이 장기간 보류되어서는 안 된다.

---

## 5. Migration parity gate

새 AXIS 1은 기존 `core/`의 trusted behavior를 먼저 재현해야 한다.

최소 parity gate:

```text
registered feature catalog baseline parity
registered execution invariant parity
Parser fail-closed parity
Semantic type/error parity
Runtime deterministic output parity
Backtest/Broker trade-result parity
MTF/context causal parity
existing focused additive indicator parity
chart projection contract parity
```

동일 입력을 frozen `core/`와 새 AXIS 1에 넣었을 때 의도적으로 변경하지 않은 기능의 결과는 일치해야 한다.

차이가 발생하면 먼저 다음으로 분류한다.

```text
migration defect
legacy defect discovered during migration
test defect
authority drift
environment issue
unknown
```

원인을 분류하지 않은 채 assertion을 완화하지 않는다.

---

## 6. New capability development after parity

Parity gate를 통과한 이후 신규 DSL 기능은 `axes/axis1_dsl/`에서만 개발한다.

특히 multi-output 기능은 다음과 같은 일반 계약을 목표로 한다.

```text
indicator -> tuple/multi-output typed value
assignment/destructuring -> named DSL values
semantic analyzer -> output arity/type validation
runtime -> deterministic tuple materialization
projection -> selected outputs without chart-side recomputation
```

예를 들어 MACD/BBANDS/Supertrend 같은 다중 출력 성격의 지표를 component 문자열 우회에만 의존하지 않고 일반적인 DSL multi-output contract로 표현할 수 있어야 한다.

구체 문법은 별도 micro-tranche에서 결정하며 frozen `core/`에는 역이식하지 않는다.

---

## 7. Bridge isolation remains mandatory

새 3축 구조에서도 축 간 상호작용은 versioned Request -> Response 계약만 허용한다.

```text
AXIS 2 -> CandidateSetResponse
AXIS 3 -> StrategyExecutionRequest
AXIS 1 -> ExecutionResponse + projections
AXIS 3 -> Monetization/ValidationResponse
```

다음은 금지한다.

```text
AXIS 2 -> AXIS 1 internal import
AXIS 3 -> AXIS 1 runtime class import
AXIS 3 -> AXIS 2 DB/internal state access
frozen core/ -> 새 축 runtime dependency
```

---

## 8. Legacy documents after migration

기존 Core 관련 문서는 migration/검증 기간에는 유지한다.

새 AXIS 1이 trusted replacement로 승격된 뒤에는 문서를 다음 세 종류로 분류한다.

```text
KEEP      = historical evidence / regression authority / architectural rationale
ARCHIVE   = 더 이상 현재 구현을 설명하지 않지만 감사 가치가 있는 문서
RETIRE    = 새 authority와 완전히 중복되어 복구 시 혼동만 만드는 문서
```

문서 폐기/아카이브는 별도 tranche로 수행한다.

중요: 문서 정리와 frozen `core/` 보존은 별개다. 문서를 RETIRE하더라도 `core/` source baseline은 삭제하지 않는다.

---

## 9. Completion criteria

이 전환이 완료되었다고 말하려면 다음이 모두 필요하다.

```text
frozen core/ 변경 없음
새 axes/ + bridges/ 구조 존재
AXIS 1 capability gap audit 완료
AXIS 1 migration parity PASS
AXIS 2/3와 직접 내부 참조 없음
Bridge v1 contract 검증
신규 DSL 기능 개발 위치가 AXIS 1으로 전환
legacy docs disposition 결정
```

Broader repository compliance가 `REMEDIATION_REQUIRED`이면 위 migration PASS와 별개로 repository-wide compliance PASS를 주장하지 않는다.
