# rules.md — DSL Permanent Skill / Constitution

이 파일은 DSL 프로젝트의 **유일한 영구 규칙 파일**이다.

이 프로젝트를 새 세션에서 복구하거나 이어갈 때 필요한 규칙은 이 파일 하나에 완결되어 있어야 한다. 정상 작업 중에는 새 규칙 문서, 새 권위 문서, 새 복구 문서를 만들지 않는다.

## 0. 절대 권위와 세션 복구

세션 시작 또는 `세션복구` 요청 시 순서는 오직 다음 두 개다.

```text
1. rules.md  — 영구 불변 규칙
2. todo.md   — 한 일 / 할 일 / 현재 상태
```

그 외 모든 `.md`, 과거 handoff, checkpoint, current-state, work-order, constitution, compliance 문서는 **비권위 역사/증거 자료**다. 복구를 위해 읽지 않는다. `todo.md`가 특정 파일/커밋/로그를 증거로 명시적으로 지목할 때만 그 대상을 확인할 수 있다.

권위 순서:

```text
사용자의 현재 명시적 지시
> rules.md
> todo.md
> 실제 코드/테스트/실행 증거
> 기타 모든 과거 문서/대화
```

단, 사용자의 일반 기능 요청은 `rules.md`를 자동 변경하지 않는다. **사용자가 명시적으로 `rules.md 규칙을 변경하라`고 지시한 경우에만** 이 파일의 규칙 의미를 변경할 수 있다.

### rules.md 변경 금지

정상 개발 중 다음은 `rules.md` 수정 사유가 아니다.

```text
버그
테스트 실패
리팩터링
새 기능
새 Add-on
새 세션
새 Runtime
새 UI
새 persistence
현재 구현과 규칙의 충돌
```

현재 구현이 이 파일과 충돌하면 **구현이 틀린 것**이다. 규칙을 구현에 맞추지 않는다.

### todo.md 규칙

`todo.md`는 유일한 가변 인수인계 파일이다. 내용은 반드시 두 섹션만 유지한다.

```text
## 한 일
## 할 일
```

현재 branch/SHA, 실패 분류, 검증 결과, 다음 정확한 작업도 이 두 섹션 안에만 기록한다. 작업 tranche가 끝날 때마다 `todo.md`만 갱신한다.

---

# 1. 4축 아키텍처 — 의미가 최우선

4축은 파일 위치 규칙이 아니라 **동작 의미 규칙**이다. 파일/폴더/이름이 4축처럼 보여도 아래 의미를 위반하면 FAIL이다.

## AXIS 1 — Chart Core

Chart Core는 **그리기만 한다**.

Core가 알아도 되는 것:

```text
pane
series
candlestick
line
histogram
marker
legend
axis
region
reference/trend primitive
layout primitive
generic viewport/time/price primitive
```

Core가 몰라야 하는 것:

```text
compare
strategy
research
condition
feature name
Add-on id의 의미
JSON persistence 의미
ON/OFF 정책
restore 정책
사용자 기능 workflow
```

Core는 generic primitive의 생성/수정/삭제/그리기만 제공한다. feature-specific 분기, compatibility branch, 특별 restore 처리를 넣지 않는다.

## AXIS 2 — Add-on

Add-on은 **무엇을 그릴지 확장**한다.

Add-on의 책임:

```text
자기 feature의 의미
자기 item을 generic drawing descriptor로 변환
자기 feature의 private semantic state 정규화
자기 item의 type/props 계산
```

Add-on이 하면 안 되는 것:

```text
Core primitive 재구현
다른 Add-on 상태 직접 접근
UI pane 직접 생성
전체 collection lifecycle 상태기계
feature-specific pending/revision/retry/restore orchestration
N개 item 전체를 별도 restore 모드로 재구축
Runtime/Bridge 역할 복제
```

같은 feature item이 N개라면 Add-on은 **한 item을 descriptor로 만드는 동일 함수가 N번 호출되는 구조**여야 한다.

## AXIS 3 — Bridge / Runtime

Bridge/Runtime은 **그리는 방법을 generic하게 번역**한다.

Runtime이 받아야 하는 것은 기능명이 아니라 다음과 같은 generic desired item이다.

```text
id
type
enabled/visible
props
optional order/layout
```

Runtime의 의미상 허용 operation은 다음 세 가지로 제한한다.

```text
ensure(id, type, props)
update(id, props)
remove(id)
```

이름은 달라도 의미가 같아야 한다.

Runtime은 feature-blind여야 한다. `compare`, `strategy`, `condition` 같은 기능별 lifecycle branch를 만들지 않는다.

Runtime이 유지할 수 있는 live authority의 기준형은 다음이다.

```text
Map<itemId, liveHandle>
```

그리고 desired/live 차이는 generic set/diff로 처리한다.

```text
desired - live  => ensure(item)
live - desired  => remove(item)
intersection    => update(item) if props changed
```

성능을 위한 generic batching/queue는 가능하지만 **의미상 item 독립성**을 깨면 안 된다. feature별 collection 상태기계, feature별 owner 전체 replace, feature별 restore queue는 금지다.

## AXIS 4 — JSON

JSON은 **desired state persistence only**다.

JSON이 저장할 수 있는 것:

```text
item id
type / definition id
enabled
visible
props
order
layout value
workspace desired state
```

JSON이 소유하면 안 되는 것:

```text
live object
pane handle
series handle
retry
pending
promise
revision-based lifecycle authority
restore mode
runtime completion state
executable callback
```

JSON은 무엇을 ON/OFF 하고 어떤 props로 보일지만 선언한다.

---

# 2. 4축 핵심 불변식 — 절대 완화 금지

아래 불변식 중 하나라도 위반하면 `4-AXIS FAIL`이다. 기존 테스트 PASS, 기존 구현, 과거 merge, 과거 문서로 덮을 수 없다.

## 2.1 CARDINALITY INVARIANT

```text
1개 item과 N개 item의 알고리즘은 동일해야 한다.
N은 반복 횟수일 뿐 새로운 lifecycle 상태를 만들지 않는다.
```

예:

```text
1개 ON     => ensure(item-1)
1000개 ON  => 동일 ensure(item)를 1000개 id에 반복
```

1000개라서 별도 collection signature, owner replace, settle state, feature revision, feature pending chain이 생기면 FAIL이다.

## 2.2 LOCALITY INVARIANT

```text
N개 중 한 item 변경은 그 item에만 영향을 준다.
```

예:

```text
1000개 중 #537 OFF
=> remove(#537)만 발생
=> 나머지 999개 liveHandle은 생성/폐기/재복원되지 않는다.
```

한 item 변경 때문에 전체 owner/collection을 폐기 후 재생성하면 FAIL이다.

## 2.3 RESTORE EQUIVALENCE INVARIANT

```text
restore는 별도 lifecycle이 아니다.
```

프로그램 재기동은 저장 JSON을 다시 읽고 **최초 ON과 동일한 generic ensure/update/remove 경로**를 실행하는 것뿐이다.

금지:

```text
restoreCompare(...)
startupCompareReconcile(...)
restore-only feature queue
restart-only pane reconstruction
UI restore path
별도 restore signature/state machine
```

재시작과 최초 실행의 operation trace가 의미상 같지 않으면 FAIL이다.

## 2.4 VISIBILITY EQUIVALENCE INVARIANT

전체 ON/OFF와 부분 ON/OFF는 같은 계산으로 귀결되어야 한다.

기준형:

```text
effectiveVisible = globalVisible && item.enabled && item.visible
```

그 결과만 generic operation에 반영한다.

```text
부분 OFF  => 해당 item remove/hide/update
전체 OFF  => 동일 item operation을 대상 item 전체에 반복
전체 ON   => 동일 ensure/update를 대상 item 전체에 반복
```

global 전용 restore/lifecycle 경로를 만들지 않는다.

## 2.5 IDEMPOTENCE INVARIANT

동일 desired state를 두 번 읽어도 두 번째 실행은 live object를 불필요하게 재생성하지 않아야 한다.

```text
apply(S)
apply(S)
=> 두 번째 apply에서 의미상 lifecycle 변화 0
```

## 2.6 SINGLE-PATH INVARIANT

하나의 기능을 그리는 정상 경로는 하나뿐이다.

```text
JSON desired state
 -> Add-on item descriptor/type registry
 -> generic Runtime/Bridge diff + translation
 -> Chart Core generic primitive
```

UI, persistence, Add-on, Runtime 중 어느 곳에도 두 번째 pane/series/restore lifecycle 경로를 두지 않는다.

## 2.7 SCALE-INDEPENDENT COMPLEXITY INVARIANT

feature item 수가 늘어도 **알고리즘 종류가 늘면 안 된다**.

```text
1 item   : same pipeline
10 items : same pipeline x10
1000 items: same pipeline x1000
```

개수 증가 때문에 새로운 상태 종류, 새로운 완료판정, 새로운 restore 단계, 새로운 feature-specific queue가 필요하면 구조 결함이다.

---

# 3. 4축 PASS의 정의

앞으로 `4축 PASS`는 아래를 모두 통과했을 때만 말할 수 있다.

```text
A. structural boundary PASS
B. semantic operation PASS
C. cardinality invariant PASS
D. locality invariant PASS
E. restore equivalence PASS
F. visibility equivalence PASS
G. idempotence PASS
H. single-path PASS
```

파일 위치나 import 검사만 통과한 것은 `4축 PASS`가 아니다.

---

# 4. 필수 자동검증 계약

테스트는 현재 구현을 보존하기 위해 만들지 않는다. **이 rules.md에서 직접 파생**한다.

최소 semantic operation recorder를 둔다. 실제 Core를 그리지 않아도 Runtime이 어떤 generic operation을 발생시키는지 trace로 검증한다.

필수 property tests:

```text
TEST 1 — one item
1 item ON
=> ensure 1회

TEST 2 — many items
1000 items ON
=> 같은 ensure operation 1000회
=> feature-specific collection lifecycle 0

TEST 3 — local OFF
1000개 중 #537 OFF
=> #537만 remove/hide/update
=> 나머지 999개 lifecycle 변화 0

TEST 4 — local ON
#537 다시 ON
=> #537만 ensure/update

TEST 5 — global OFF/ON
global OFF
=> item-level 동일 operation 반복
global ON
=> item-level 동일 operation 반복

TEST 6 — restart equivalence
fresh apply(saved JSON)와 restart apply(saved JSON)의
semantic operation trace가 동일

TEST 7 — idempotence
같은 JSON을 연속 두 번 적용
=> 두 번째 lifecycle 변화 0

TEST 8 — order/props isolated update
한 item props/layout 변경
=> 그 item update만 발생

TEST 9 — 1/10/1000 cardinality property
operation 종류는 동일하고 횟수만 N에 따라 증가
```

### 금지 검증 방식

다음만 검사하고 4축 PASS라 하지 않는다.

```text
feature token 문자열 없음
직접 import 없음
특정 함수명 없음
UI에 createPane 문자열 없음
테스트 몇 개 PASS
```

이 검사는 보조 static gate일 뿐이다. semantic property gate가 반드시 함께 있어야 한다.

### 테스트 약화 금지

green을 만들기 위해 다음을 하지 않는다.

```text
assertion 완화
skip
allowlist
grandfather exception
fallback으로 오류 숨김
tolerance를 임의 확대
expected를 현재 구현에 맞춤
```

### SEMANTIC GATE IMMUTABILITY — 검증기 샛길 영구 금지

`rules.md`의 4축 의미와 불변식이 변경되지 않는 한 **semantic gate의 판정 의미는 변경하거나 완화할 수 없다.**

제품 코드가 semantic gate에 실패했다는 사실은 gate 수정 사유가 아니다. 그 경우 기본 판정은 **제품/아키텍처 결함**이다.

`test defect`는 오직 다음 경우에만 인정한다.

```text
테스트 코드가 rules.md의 기존 불변식을 잘못 구현함
테스트 fixture/recorder 자체가 사실과 다른 입력 또는 trace를 생성함
테스트 실행환경 문제로 rules.md와 무관한 오판이 발생함
```

`test defect` 수정은 반드시 **기존 rules.md 의미를 그대로 보존하면서 동일하거나 더 강한 검증**이 되어야 한다. 제품을 통과시키기 위한 예외, 허용범위 확대, assertion 축소, expected 재정의는 `test defect`가 아니라 **검증 오염**이며 금지한다.

다음은 절대 금지다.

```text
제품 실패 -> gate 기준 변경 -> PASS
현재 구현을 기준으로 semantic expected 재작성
특정 feature/commit/legacy 구현만 통과시키는 semantic 예외
실제 WYSIWYG 실패를 이유로 semantic invariant 완화
semantic gate FAIL을 단순 static PASS로 대체
```

semantic gate의 **coverage 강화**는 허용한다. 단, 기존 rules.md에서 이미 요구하는 invariant의 누락 사례를 추가하는 것만 가능하며 기존 판정 의미를 약화할 수 없다.

제품 구조 수정과 semantic gate의 **판정 의미 수정**을 같은 tranche에서 수행하지 않는다. `rules.md` 의미 변경이 필요하다고 판단되면 개발자가 임의로 바꾸지 않고 사용자의 명시적 `rules.md 규칙 변경` 지시가 먼저 있어야 한다.

새 세션도 이전 PASS, 현재 구현, 테스트 편의 때문에 이 조항을 재해석하거나 우회할 수 없다.

실패하면 먼저 분류한다.

```text
product defect
test defect
authority drift
environment issue
unknown
```

4축 invariant 위반은 `architecture defect`를 추가로 명시한다.

---

# 5. 금지되는 오염 패턴

다음은 이름이 generic이어도 원칙상 금지다.

```text
feature-specific whole-collection signature
feature-specific collection revision
feature-specific pending promise chain
feature-specific restore settle state
feature-specific retry state machine
owner 전체 replace를 feature semantic으로 사용
한 item 변경 시 N item 전체 폐기/재생성
restart 전용 lifecycle
UI가 persistent pane/series를 직접 복원
JSON이 live completion을 저장
Core에 feature special-case
Runtime에 feature name branch
Add-on이 generic Core primitive를 재구현
```

Generic Runtime 자체가 내부적으로 revision/queue를 사용할 수는 있다. 단, **모든 type에 동일하고 item 독립성을 보존하는 infrastructure mechanism**이어야 하며 feature collection의 의미 상태가 되어서는 안 된다.

---

# 6. 새 Add-on의 유일한 확장 방식

새 그리기 종류를 추가할 때 기존 Runtime/Core를 feature-specific하게 고치지 않는다.

정상 순서:

```text
1. Add-on에 type/descriptor 정의
2. 필요하면 Core에 재사용 가능한 generic primitive 추가
3. generic Runtime registry가 type을 번역
4. JSON item을 ON
5. 기존 동일 item pipeline으로 draw
```

새 Add-on 하나 때문에 Runtime에 `if featureX`, `switch featureX`, 전용 restore/reconcile/queue가 필요하면 설계 실패다.

---

# 7. UI 규칙

UI는 명령/desired-state 입력기다.

UI가 할 수 있는 것:

```text
JSON/state-port에 add/remove/enable/disable/select/props 변경 요청
현재 generic runtime snapshot 관찰
상태 표시
```

UI가 하면 안 되는 것:

```text
persistent pane 생성
series lifecycle 소유
bar-window lifecycle 소유
projection lifecycle 소유
restart 복원
JSON과 별도 side-store 유지
```

UI에서 누른 ON/OFF와 프로그램 재기동에서 읽은 ON/OFF는 **같은 state write/read 경로**로 Runtime에 도달해야 한다.

---

# 8. Persistence 규칙

제품 상태의 SSOT는 정해진 JSON persistence 하나다.

금지:

```text
동일 기능의 두 번째 JSON
localStorage product-state authority
UI private persistence
feature-specific hidden side-store
DB와 JSON이 동시에 같은 chart desired-state authority 소유
```

Persistence는 serialization/deserialization만 한다. 객체 생성/restore 판단을 하지 않는다.

---

# 9. 프로젝트 간/축 간 분리 규칙

독립 축/모듈은 물리적으로 분리하고 직접 내부 침범을 금지한다.

```text
축 사이 직접 import 금지
다른 축 내부 DB/state 직접 접근 금지
상호연동 = 표준 Request -> Response Bridge/Contract
```

각 축의 내부 구현은 독립적으로 고도화할 수 있어야 하며, 상호연동 변경은 표준 입출력 계약/adapter에서 흡수한다.

---

# 10. DSL 제품 로직 안정성 규칙

메인 DSL 로직은 단순하고 예측 가능하게 유지한다.

```text
정해진 장비/조건/threshold를 우선 사용
병사/전략에 무제한 자율권을 주지 않음
학습/자율 기능은 확장 가능하도록 열어두되 메인 로직을 자주 변경시키지 않음
복잡한 가능성 때문에 안정된 주력 경로를 오염시키지 않음
```

시장/전략 실행은 증거가 부족하거나 조건이 불리하면 `NO_TRADE`가 정상 결과다.

---

# 11. 개발/수정 절차

모든 변경은 micro-tranche로 한다.

```text
1. 실패 분류
2. rules.md 불변식과 충돌 여부 확인
3. 한 개 boundary change만 수행
4. static boundary gate
5. semantic 4축 property gate
6. focused behavior test
7. 필요 시 실제 WYSIWYG/user-local acceptance
8. todo.md 갱신
9. 다음 tranche
```

구조가 불명확하면 코드를 먼저 쓰지 않는다. 정상 단일 경로를 추적한 뒤 수정한다.

실제 UI 실패는 자동테스트 PASS로 덮지 않는다.

`4축 PASS`와 `repo-wide/global PASS`를 혼동하지 않는다. 저장소 전체 remediation이 남아 있으면 `REMEDIATION_REQUIRED`를 유지한다.

정상 성공 콘솔 출력은 가능하면 최종 `[PASS]` 한 줄로 유지하고 상세 로그는 파일/CI에 둔다.

---

# 12. Git/원격 작업 안전 규칙

사용자가 직접 소스를 수동 편집하게 하지 않는다. 가능하면 원격 GitHub에서 수정하고 사용자는 pull/test한다.

금지:

```text
현재 작업 branch를 확인하지 않고 origin/main pull
reset --hard로 사용자 generated/state evidence 삭제
불필요한 rebase/force push
사용자 dirty state를 덮는 작업
테스트를 약화해 merge
```

branch/SHA/submodule의 **현재 값은 todo.md**에 둔다. rules.md에는 동적 SHA를 넣지 않는다.

Frozen legacy 경계가 todo.md 또는 코드 gate에 지정되어 있으면 그 경계를 유지하며 임의 수정하지 않는다.

---

# 13. 세션 간 작업 방식

새 세션의 AI는 과거 대화를 기억한다고 가정하지 않는다.

세션 복구 시 반드시:

```text
rules.md를 처음부터 끝까지 읽는다.
todo.md를 읽는다.
현재 repo/branch/SHA가 todo와 맞는지 필요 시 확인한다.
그 다음 todo.md의 첫 번째 미완료 항목부터 계속한다.
```

사용자에게 이미 답이 있는 질문을 다시 묻지 않는다.

진행 보고는 기본적으로 짧게:

```text
한 일
할 일
```

형식을 사용한다.

---

# 14. 오염 방지 최종 판정 질문

코드를 쓰거나 merge하기 전에 아래 질문에 전부 `YES`여야 한다.

```text
Q1. item이 1개든 1000개든 같은 algorithm인가?
Q2. 한 item OFF가 다른 item lifecycle을 건드리지 않는가?
Q3. restart가 normal ON과 같은 path인가?
Q4. global OFF/ON이 item OFF/ON과 같은 operation의 반복인가?
Q5. Runtime이 feature 이름을 몰라도 되는가?
Q6. Add-on은 type/props 의미만 추가하는가?
Q7. Core는 generic draw primitive만 수행하는가?
Q8. JSON은 desired state만 저장하는가?
Q9. UI는 desired-state command만 쓰는가?
Q10. 정상 lifecycle path가 정확히 하나인가?
```

하나라도 `NO`면 구현을 진행하지 말고 `architecture defect`로 분류한다.

---

# 15. 이 파일의 목적

이 파일의 목적은 AI가 4축을 기억하는 것이 아니다.

목적은:

```text
AI가 세션마다 달라져도
현재 구현이 아무리 오래 살아남았어도
기존 테스트가 PASS했어도

rules.md의 semantic invariant를 위반한 구현은
정상 구조로 인정하지 못하게 하는 것
```

이다.

**복구에는 rules.md + todo.md 두 파일만 사용한다. 새 권위 문서를 만들지 않는다.**