# rules.md — DSL Permanent Skill / Constitution

이 파일은 DSL 프로젝트의 **유일한 영구 규칙/스킬 파일**이다.

새 세션 복구와 모든 설계·개발·검증 판단은 이 파일 하나로 가능해야 한다. 정상 작업 중 새 규칙 문서, 새 권위 문서, 새 복구 문서를 만들지 않는다.

# 0. 절대 권위와 세션 복구

세션 시작 또는 `세션복구` 요청 시 오직 다음 순서로 읽는다.

```text
1. rules.md  — 영구 규칙
2. todo.md   — 한 일 / 할 일 / 현재 상태
```

그 외 모든 `.md`, 과거 handoff/checkpoint/current-state/work-order/constitution/compliance 문서는 비권위 역사/증거다. `todo.md`가 증거로 지목할 때만 확인한다.

권위 순서:

```text
사용자의 현재 명시적 지시
> rules.md
> todo.md
> 실제 코드/테스트/실행 증거
> 기타 과거 문서/대화
```

일반 기능 요청, 버그, 테스트 실패, 리팩터링, 새 Add-on, 새 세션, 현재 구현과 규칙의 충돌은 `rules.md` 변경 사유가 아니다. 사용자가 헌법/`rules.md` 규칙 변경을 명시적으로 지시한 경우에만 의미를 변경한다.

현재 구현이 `rules.md`와 충돌하면 **구현이 틀린 것**이다. 규칙을 구현에 맞추지 않는다.

`todo.md`는 유일한 가변 인수인계 파일이며 반드시 다음 두 섹션만 유지한다.

```text
## 한 일
## 할 일
```

branch/SHA, 실패 분류, 검증 결과, 다음 작업도 이 두 섹션 안에 기록한다.

---

# 1. 4축 아키텍처 — 의미가 최우선

4축은 파일 위치가 아니라 **동작 의미**다. 이름/폴더가 맞아도 의미가 틀리면 FAIL이다.

## AXIS 1 — Chart Core

Chart Core는 **그리기만 한다**.

Core는 다음 generic drawing grammar만 소유한다.

```text
pane / series / candlestick / line / histogram
marker / legend / axis / region / reference / trend
layout / viewport / time / price primitive
create / ensure / update / remove / show / hide / data update
```

Core는 `compare`, `JMA`, `RSI`, `strategy`, `research`, `condition`, Add-on id, JSON persistence 의미, ON/OFF 정책, restore workflow 같은 feature 의미를 몰라야 한다.

Core에 feature 계산, feature 분기, compatibility branch, feature restore 처리가 있으면 FAIL이다.

## AXIS 2 — Add-on

Add-on은 **무엇을 그릴지 확장**한다.

Add-on의 책임:

```text
자기 feature 계산/의미
자기 item의 type/props/data/layout 계산
한 item을 generic drawing descriptor로 변환
```

Add-on이 하면 안 되는 것:

```text
Core primitive 재구현
raw pane/series/live handle lifecycle 직접 소유
다른 Add-on 상태 직접 접근
UI pane 직접 생성
전체 collection lifecycle 상태기계
feature-specific pending/revision/retry/restore orchestration
Runtime/Bridge 역할 복제
```

같은 feature item이 N개라면 **한 item descriptor 함수가 N번 호출**되는 구조여야 한다.

## AXIS 3 — Bridge / Runtime

Bridge/Runtime은 **desired state를 Core grammar로 feature-blind하게 번역**한다.

입력 기준형:

```text
id
type
enabled / visible
props / data
optional order / layout
```

의미상 허용 lifecycle vocabulary:

```text
ensure(id, type, props)
update(id, props)
remove(id)
```

이름은 달라도 의미는 같아야 한다.

Runtime live authority의 기준형:

```text
Map<itemId, liveHandle>
```

처리는 generic desired/live diff다.

```text
desired - live => ensure(item)
live - desired => remove(item)
intersection   => 필요한 경우 update(item)
```

모든 type에 동일한 infrastructure queue/revision/batching은 가능하지만 item 독립성을 깨면 안 된다. feature별 owner 전체 replace, collection signature, restore queue/settle state는 금지다.

## AXIS 4 — JSON

JSON은 **desired state persistence only**다.

저장 가능:

```text
item id / type / definition id
enabled / visible
props / data reference / order / layout
workspace desired state
```

저장 금지:

```text
live object / pane handle / series handle
promise / pending / retry
lifecycle revision authority
restore mode / runtime completion state
executable callback
```

JSON은 무엇을 ON/OFF하고 어떤 값으로 보일지만 선언한다.

---

# 2. 4축 핵심 불변식 — 절대 완화 금지

하나라도 위반하면 `4-AXIS FAIL`이다. 기존 PASS/merge/구현으로 덮지 않는다.

## 2.1 CARDINALITY

```text
1 item과 N item의 알고리즘은 동일하다.
N은 반복 횟수일 뿐 새로운 lifecycle 상태를 만들지 않는다.
```

1개와 1000개 때문에 다른 signature/owner/settle/revision/pending 체계가 생기면 FAIL.

## 2.2 LOCALITY

```text
N개 중 한 item 변경은 그 item lifecycle에만 영향을 준다.
```

1000개 중 #537 OFF라면 #537 operation만 발생해야 한다. 나머지 999개를 폐기/재생성하면 FAIL.

## 2.3 RESTORE EQUIVALENCE

```text
restart/restore는 별도 lifecycle이 아니다.
```

저장 JSON을 다시 읽어 최초 ON과 동일한 `ensure/update/remove` 경로를 실행한다. restart 전용 restore/reconcile/stabilize/settle 상태기계가 있으면 FAIL.

## 2.4 VISIBILITY EQUIVALENCE

전체 ON/OFF와 부분 ON/OFF는 같은 effective-state 계산과 같은 item operation으로 귀결된다.

```text
effectiveVisible = globalVisible && item.enabled && item.visible
```

전체 OFF/ON은 동일 item operation의 반복이어야 한다.

## 2.5 IDEMPOTENCE

```text
apply(S)
apply(S)
=> 두 번째 apply에서 불필요한 lifecycle 변화 0
```

## 2.6 SINGLE PATH

정상 그리기 경로는 정확히 하나다.

```text
JSON desired state
 -> Add-on one-item descriptor/type
 -> generic Runtime/Bridge diff + translation
 -> Chart Core generic grammar
```

UI/Add-on/Runtime/Persistence 어디에도 두 번째 pane/series/restore lifecycle 경로를 두지 않는다.

## 2.7 SCALE-INDEPENDENT COMPLEXITY

```text
1 item    = same pipeline
10 items  = same pipeline x10
1000 items= same pipeline x1000
```

개수 증가 때문에 새로운 알고리즘 종류/완료판정/restore 단계/feature queue가 생기면 구조 결함이다.

---

# 3. 4축 PASS 정의

`4축 PASS`는 아래를 모두 통과해야 한다.

```text
A. structural boundary
B. semantic operation
C. cardinality
D. locality
E. restore equivalence
F. visibility equivalence
G. idempotence
H. single path
```

import/token/파일 위치 검사만 통과한 것은 4축 PASS가 아니다.

---

# 4. 필수 자동검증 계약

테스트는 현재 구현을 보존하기 위해 만들지 않고 `rules.md`에서 직접 파생한다.

semantic operation recorder로 최소 다음을 검증한다.

```text
1 item ON             => ensure 1회
1000 items ON         => 같은 ensure 1000회
1000 중 #537 OFF      => #537만 remove/update
#537 다시 ON          => #537만 ensure/update
global OFF/ON         => 동일 item operation 반복
restart saved state   => fresh normal apply와 같은 semantic trace
같은 state 두 번 apply => 두 번째 lifecycle 변화 0
한 item props/layout 변경 => 그 item update만
1/10/1000             => operation 종류 동일, 횟수만 증가
```

Static boundary 검사는 보조 gate이며 semantic property gate를 대체할 수 없다.

### 테스트 약화 금지

```text
assertion 완화
skip
allowlist
grandfather exception
fallback으로 오류 숨김
tolerance 임의 확대
expected를 현재 구현에 맞춤
```

을 green 목적으로 하지 않는다.

### SEMANTIC GATE IMMUTABILITY — 검증기 샛길 영구 금지

`rules.md` 의미가 변경되지 않는 한 semantic gate의 **판정 의미를 변경하거나 완화할 수 없다.**

제품이 gate에 실패한 사실은 gate 수정 사유가 아니며 기본 판정은 제품/아키텍처 결함이다.

`test defect`는 오직 다음만 인정한다.

```text
테스트가 rules.md 기존 불변식을 잘못 구현
fixture/recorder가 사실과 다른 입력/trace 생성
실행환경 때문에 rules.md와 무관한 오판 발생
```

수정 후 검증은 기존과 동일하거나 더 강해야 한다.

절대 금지:

```text
제품 실패 -> gate 기준 변경 -> PASS
현재 구현에 맞춰 semantic expected 재작성
특정 feature/commit/legacy 예외
WYSIWYG 실패 때문에 invariant 완화
semantic FAIL을 static PASS로 대체
```

Coverage 강화는 기존 `rules.md` invariant의 누락 사례를 추가할 때만 허용한다.

제품 구조 수정과 semantic gate의 판정 의미 변경을 같은 tranche에서 수행하지 않는다. 규칙 의미 변경이 필요하면 사용자의 명시적 헌법 변경 지시가 먼저다.

---

# 5. 금지되는 오염 패턴

이름이 generic이어도 다음은 금지다.

```text
feature-specific whole-collection signature/revision/pending/retry
feature-specific restore settle state/queue
owner 전체 replace를 feature semantic으로 사용
한 item 변경 시 N item 전체 폐기/재생성
restart 전용 lifecycle
UI persistent pane/series restore
JSON live completion authority
Core feature special-case/feature 계산
Runtime feature-name branch
Add-on raw live pane/series lifecycle 소유
Add-on generic Core primitive 재구현
```

---

# 6. 새 Add-on의 유일한 확장 방식

```text
1. Add-on에 one-item type/descriptor와 feature 계산 정의
2. 필요한 경우에만 Core에 재사용 가능한 generic primitive 추가
3. generic Runtime registry/translator 사용
4. JSON desired item ON
5. 기존 동일 item pipeline으로 draw
```

새 Add-on 때문에 Runtime/Core에 feature-specific branch/restore/reconcile/queue가 필요하면 설계 FAIL이다.

---

# 7. UI 규칙

UI는 desired-state 입력기/관찰자다.

허용:

```text
add/remove/enable/disable/select/props 변경 요청
runtime snapshot 관찰
상태 표시
```

금지:

```text
persistent pane/series 생성
bar-window/projection lifecycle 소유
restart 복원
JSON과 별도 product-state side-store
```

UI ON/OFF와 재기동 JSON ON/OFF는 같은 state read/write path로 Runtime에 도달해야 한다.

---

# 8. Persistence 규칙

제품 chart desired-state SSOT는 하나의 JSON persistence다.

금지:

```text
동일 기능의 두 번째 JSON
localStorage/UI private persistence authority
feature-specific hidden side-store
DB와 JSON의 동일 chart-state 이중 authority
```

Persistence는 serialization/deserialization만 하며 객체 생성/restore 판단을 하지 않는다.

---

# 9. 프로젝트/축 간 분리

```text
축 사이 직접 import 금지
다른 축 내부 DB/state 직접 접근 금지
상호연동 = 표준 Request -> Response Bridge/Contract
```

각 축 내부 구현은 독립적으로 변경 가능해야 하며 상호연동 변경은 표준 입출력 계약/adapter에서 흡수한다.

---

# 10. DSL 제품 로직 안정성

```text
정해진 장비/조건/threshold 우선
병사/전략에 무제한 자율권 금지
학습/자율 기능은 확장 가능하되 메인 로직을 자주 변경시키지 않음
복잡한 가능성 때문에 안정된 주력 경로를 오염시키지 않음
```

증거 부족/불리한 조건에서는 `NO_TRADE`가 정상 결과다.

---

# 11. 개발/수정 절차

모든 변경은 micro-tranche로 한다.

```text
1. 실패 분류
2. rules.md 불변식 충돌 확인
3. 한 boundary change
4. static boundary gate
5. semantic 4축 property gate
6. focused behavior test
7. 필요 시 WYSIWYG/user-local acceptance
8. todo.md 갱신
9. 다음 tranche
```

구조가 불명확하면 코드를 먼저 쓰지 않는다. 정상 단일 경로를 먼저 추적한다.

실제 UI 실패는 자동테스트 PASS로 덮지 않는다.

`4축 PASS`와 repo-wide/global PASS를 혼동하지 않는다. 전체 remediation이 남으면 `REMEDIATION_REQUIRED`를 유지한다.

---

# 12. 주기적 4축 표준화 감사 — 기능 우선 개발의 누적 오염 제거

기능 구현이 먼저 진행되는 개발 단계에서는 동작하는 비표준 부품이 누적될 수 있음을 정상적인 개발 위험으로 인정한다. **동작한다는 이유로 표준 부품으로 간주하지 않는다.**

따라서 제품은 기능개발과 별도로 반복되는 **STANDARDIZATION CYCLE**을 반드시 가진다.

## 12.1 감사 트리거

다음 중 하나가 발생하면 새 대형 기능 확장보다 4축 표준화 감사를 우선한다.

```text
주요 기능군/마일스톤 완료 후
새 대형 기능군 개발에 들어가기 전
동일 영역에서 구조성 product defect가 반복될 때
restore/reconcile/pending/revision/whole-replace 같은 복잡도 증가가 관찰될 때
4축 PASS 또는 안정 baseline을 선언하기 전
사용자가 표준화/구조감사를 지시할 때
```

사소한 기능 하나마다 전수감사를 반복할 필요는 없지만, 위 트리거를 임의로 건너뛸 수 없다.

## 12.2 감사 순서

기존 구현/테스트를 정답으로 두지 않고 `rules.md`를 기준으로 다음 순서로 전수 심사한다.

```text
1. Core
2. Add-on
3. Bridge/Runtime
4. JSON/Persistence
5. UI/단일경로 연결 확인
```

각 부품을 다음 셋 중 하나로 판정한다.

```text
STANDARD        — rules.md 의미를 만족
NONSTANDARD     — 기능은 동작하지만 4축 의미 위반
UNKNOWN         — 증거 부족, PASS 금지
```

`NONSTANDARD`는 테스트가 green이어도 **product defect + architecture defect**다.

## 12.3 표준화 우선 규칙

감사에서 NONSTANDARD가 발견되면 그 영역에 새 구조/우회/보정 기능을 덧붙이지 않는다.

```text
비표준 부품 식별
-> 표준 generic contract 확정
-> 비표준 부품 교체/이동/축소
-> 기존 기능 behavior 보존 검증
-> semantic 4축 gate 검증
-> WYSIWYG 필요 시 확인
-> STANDARD 확정
-> 기능개발 재개
```

비표준 구조 위에 compatibility layer, fallback, 추가 reconcile, restore 보정을 쌓아 green을 만들면 FAIL이다.

## 12.4 Baseline-first 규칙

대규모 구조 개선/새 semantic gate/새 rendering pipeline을 만들기 전에 **현재 4축 baseline을 먼저 감사**한다.

기존 Core/Add-on/Runtime/JSON 부품 자체가 비표준이면 먼저 표준화한다. 비표준 부품을 기준으로 새 표준 계층이나 검증기를 만들지 않는다.

## 12.5 표준화 완료 조건

표준화 cycle은 다음이 모두 성립해야 종료할 수 있다.

```text
Core = generic grammar only
Add-on = one-item descriptor + feature semantics only
Runtime = feature-blind desired/live diff + generic lifecycle only
JSON = independent desired items persistence only
restart = normal apply
1 item = N items의 동일 algorithm 반복
single path = exactly one
semantic gate = PASS
기존 필수 behavior = PASS
```

하나라도 미확정이면 표준화 완료/PASS를 선언하지 않는다.

---

# 13. Git/원격 작업 안전

가능하면 원격 GitHub에서 수정하고 사용자는 pull/test한다.

금지:

```text
현재 branch 확인 없이 origin/main pull
reset --hard로 사용자 generated/state evidence 삭제
불필요한 rebase/force push
사용자 dirty state 덮기
테스트 약화 merge
```

동적 branch/SHA/submodule 값은 `todo.md`에만 둔다.

---

# 14. 세션 간 작업 방식

새 세션은 과거 대화를 기억한다고 가정하지 않는다.

```text
rules.md 처음부터 끝까지 읽기
todo.md 읽기
필요 시 현재 repo/branch/SHA 확인
todo.md 첫 미완료 작업부터 계속
```

이미 답이 있는 질문을 다시 묻지 않는다. 진행 보고는 기본적으로 `한 일 / 할 일` 형식을 사용한다.

---

# 15. 오염 방지 최종 판정 질문

코드 작성/merge 전 전부 YES여야 한다.

```text
Q1. item 1개와 1000개가 같은 algorithm인가?
Q2. 한 item 변경이 다른 item lifecycle을 건드리지 않는가?
Q3. restart가 normal ON/apply와 같은 path인가?
Q4. global OFF/ON이 item OFF/ON의 동일 operation 반복인가?
Q5. Runtime이 feature 이름을 몰라도 되는가?
Q6. Add-on은 feature 계산 + one-item descriptor만 추가하는가?
Q7. Core는 generic drawing grammar만 수행하는가?
Q8. JSON은 desired state만 저장하는가?
Q9. UI는 desired-state command만 쓰는가?
Q10. 정상 lifecycle path가 정확히 하나인가?
Q11. 현재 baseline의 비표준 부품 위에 새 표준 계층을 얹고 있지 않은가?
Q12. 마지막 주요 milestone 이후 표준화 감사가 필요한 시점은 아닌가?
```

하나라도 NO면 구현 진행/merge를 멈추고 architecture defect 또는 standardization-required로 분류한다.

---

# 16. 목적

이 파일의 목적은 AI가 4축을 기억하게 하는 것이 아니다.

```text
세션이 달라져도
기능개발이 오래 누적되어도
현재 구현이 동작해도
기존 테스트가 PASS해도

비표준 부품을 정기적으로 발견해 표준화하고,
rules.md semantic invariant 위반 구현을
정상 구조로 인정하지 못하게 한다.
```

**복구에는 rules.md + todo.md 두 파일만 사용한다. 새 권위 문서를 만들지 않는다.**