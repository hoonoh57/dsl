# DSL Three-Axis Module Boundary

Status: **PHYSICAL SEPARATION AUTHORITY / ACTIVE / 2026-09-01 KST**

이 문서는 세 축의 실제 코드 경계와 허용 의존성을 정의한다.

## 1. Physical roots

```text
axes/
  axis1_dsl/
  axis2_selection/
  axis3_monetization/

bridges/
  contracts/
  axis1_execution_bridge.py
  three_axis_e2e_bridge.py

authoring/
  external_llm/
  continuous_improvement/

acceptance/
  final_natural_language_scenario.py
```

Repository-root `core/`는 frozen legacy reference이며 active product development root가 아니다.

---

## 2. AXIS 1 boundary

```text
axes/axis1_dsl/
```

소유:

```text
Parser / Semantic / lowering
indicator kernel
state / MTF / exact read-only context runtime
broker / execution / backtest
projection
capability/diagnostic registry
```

금지:

```text
axes.axis2_selection import
axes.axis3_monetization import
repository-root core import
universe/rank/Condition lifecycle/Strategy lifecycle/provider lookup
```

---

## 3. AXIS 2 boundary

```text
axes/axis2_selection/
```

소유:

```text
exact-as-of immutable snapshot contract
precomputed feature evidence
selection spec semantics
filter/rank/top-N
CandidateSet + evidence
```

Condition의 filter/rank/top-N **의미**는 AXIS 2에 있다.

금지:

```text
AXIS 1 실행
order 생성
Strategy 실행
Condition/Strategy artifact lifecycle 저장
axes.axis1_dsl import
axes.axis3_monetization import
repository-root core import
```

---

## 4. AXIS 3 boundary

```text
axes/axis3_monetization/
```

소유:

```text
Condition immutable version/lifecycle
Strategy immutable version/lifecycle
lineage
promotion/rejection/archive
CandidateSet + exact artifacts -> StrategyRunPlan
```

Condition artifact는 AXIS 2 selection spec data의 versioned product artifact다. AXIS 3가 selection을 다시 계산한다는 뜻이 아니다.

금지:

```text
AXIS 2 filter/rank 재구현
AXIS 1 Parser/Runtime/Backtest 직접 실행
axes.axis1_dsl import
axes.axis2_selection import
repository-root core import
```

---

## 5. Bridge boundary

### contracts

```text
bridges/contracts/
```

Data-only 규칙:

```text
axes import 금지
authoring/acceptance import 금지
repository-root core import 금지
opaque object 금지
nonfinite input 금지
unknown field fail-closed
versioned schema/hash identity
```

### adapters/routing

현재 explicit composition points:

```text
bridges/axis1_execution_bridge.py
bridges/three_axis_e2e_bridge.py
```

허용:

```text
axis1_execution_bridge -> AXIS 1 public facade
three_axis_e2e_bridge  -> AXIS 2 selection public authority
                          AXIS 3 orchestration public authority
                          AXIS 1 execution Bridge
```

금지:

```text
contract layer에서 axis implementation import
axis 내부 package끼리 직접 import
private runtime object를 Bridge response로 노출
후순위 candidate preflight 실패 전에 일부 AXIS1 실행 시작
```

---

## 6. External authoring boundary

```text
authoring/external_llm/
```

허용:

```text
AXIS 1 capability registry / Parser / Semantic / compile dry-run validation authority
```

금지:

```text
AXIS 2 selection 실행
AXIS 3 CRUD/promotion
AXIS 1 backtest/order execution
three-axis execution Bridge 호출
repository-root core import
external response eval/exec
```

External LLM은 proposal-only다.

---

## 7. Continuous-improvement boundary

```text
authoring/continuous_improvement/
```

입력은 structured `authoring_validation_event/v1` evidence다.

금지:

```text
AXIS 1/2/3 내부 import
Prompt/Skill/Validator 자동 rewrite
DSL capability 자동 등록
Parser/Semantic/Runtime 자동 수정
provider/network 호출
```

결과는 human-reviewed remediation recommendation뿐이다.

---

## 8. Acceptance fixture boundary

```text
acceptance/
```

최종 E2E 검증 fixture는 세 축과 Bridge를 조립할 수 있다. 이 위치는 product execution authority가 아니라 acceptance/test scenario다.

특정 대표 전략을 통과시키기 위한 shortcut을 `axes/` 또는 frozen `core/`에 추가해서는 안 된다.

---

## 9. Cross-axis execution order

```text
AXIS 2 snapshot/spec
 -> CandidateSet
 -> AXIS 3 exact promoted Condition/Strategy + RunPlan
 -> Bridge preflight all selected candidates
 -> AXIS 1 one-symbol execution requests
 -> ordered trace/result
```

이 순서를 `AXIS 2 -> AXIS 1 -> AXIS 3`로 바꾸지 않는다. AXIS 3가 실행 엔진이라는 뜻도 아니다. AXIS 3는 lifecycle/orchestration authority이고 실제 single-instrument execution은 AXIS 1이 한다.

---

## 10. Frozen core

```text
path        = core/
source      = 20b963749052f0d0e42506024a02e4e218a4d05a
tree        = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제/새 runtime dependency를 금지한다.

---

## 11. Compliance rule

현재 architecture 검증은 production source의 import graph와 active authority 문서를 함께 검사한다.

```text
axis sibling direct import 없음
Bridge contract data-only
External authoring no execution authority
Continuous Improvement no automatic mutation authority
critical regression skip/expectedFailure 없음
frozen core tree exact
active docs ownership/order exact
```

과거 문서의 충돌은 `DSL_DOCUMENT_AUTHORITY_INDEX.md`의 disposition을 따른다.
