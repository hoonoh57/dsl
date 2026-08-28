# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / 2026-08-28 KST**

이 문서는 새 세션이 가장 먼저 읽는 사람 중심 인수인계 문서다. 갑작스러운 종료를 고려해 이전 프로젝트 대화의 마지막 exact local evidence와 GitHub 최신 상태를 함께 대조한다.

## 1. 개발철학 — 5개 이내

1. **작고 검증된 전술부터 키운다.** 큰 자동매매 시스템을 한 번에 만들지 않는다.
2. **DSL Core는 범용적이고 결정론적으로 유지한다.** 계산·신호·주문·취소 같은 재사용 기능만 Core에 둔다.
3. **시장/섹터/대장·추종 판단은 Add-on/context 책임이다.** 이런 의미를 Parser/Runtime/Backtest/Broker에 넣지 않는다.
4. **hard equipment / guard가 학습보다 우선한다.** 적응형 기능은 optional sidecar로 격리한다.
5. **micro-tranche 단위로 구현 → focused 검증 → Full 검증 → checkpoint 후 다음으로 간다.**

## 2. 최근 한 일

- `GCANCEL1` trusted: 명시적 `client_order_id` 취소가 기존 Broker lifecycle에 위임된다.
- `GCANCEL2` trusted: generic DSL `order.cancel(id="...")`가 Backtest timing을 거쳐 Broker cancellation primitive로 연결된다.
- `VSLICE1` trusted: exact DEPLOYMENT `ctx.*` 무효화가 pending LIMIT 주문을 `bar_close`/`next_open` 모두에서 causal하게 취소하는 조합을 test-only로 검증했다.
- VSLICE1 executable validation checkpoint는 `72445456e86b695dc7288ab3a48856fa560463dd`이다.
- 사용자 로컬 검증은 `Ran 2 tests in 0.039s / OK` 및 `Tactical P1 Full PASS`다.

## 3. 현재 위치

현재 generic mechanical vertical slice는 닫힌 것으로 간주한다.

```text
registered exact DEPLOYMENT ctx.* evidence
 + follower-local deterministic setup
 -> generic pending order with stable id
 -> later ctx.* invalidation
 -> order.cancel(id="...")
 -> BrokerEmulator
```

VSLICE1은 `test_stage1_context_pending_order_cancel.py` 하나만 추가했고 제품 소스는 변경하지 않았다.

따라서 현재 부족한 것은 새 Core primitive가 아니라 외부 Add-on에서 실제 evidence/tactic을 만드는 문제다.

대장/추종, sector, peer-symbol, ranking, allocation, learned-policy 의미는 계속 Core 밖에 둔다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

다음 개발축은 Core 확장이 아니라 **작은 결정론적 Add-on evidence/tactic 실험**이다.

1. 외부 evidence source 하나만 고른다.
2. follower-local setup 하나만 정의한다.
3. hard guard를 가장 먼저 적용한다.
4. 이미 trusted인 `ctx.*` / pending order / `order.cancel(id=...)` / BrokerEmulator만 재사용한다.
5. focused backtest evidence가 나온 뒤에만 다음 확장을 판단한다.

adaptive learning, ranking 확대, portfolio allocation, 새 grammar는 현재 보류한다.

## 5. 세션복구 규칙

새 프로젝트 세션에서 사용자가 `세션복구`라고 입력하면:

1. 이 문서를 먼저 읽는다.
2. 이전 프로젝트 대화 마지막 부분에서 이 문서 이후 exact local test evidence / 결정이 있는지 확인한다.
3. 마지막 trusted executable SHA와 GitHub `main` 사이 실행 변경분을 비교한다.
4. `CURRENT_STATE.md` 및 authority 문서를 적용한다.
5. 문서가 stale이면 실제 코드 + exact local evidence + 최근 대화 결정으로 보정한다.
6. 첫 답변은 개발철학 / 최근 한 일 / 앞으로 할 일 세 부분만 짧게 보여준다.

새 GitHub 실행 코드/테스트에 local PASS가 없으면 `REMOTE_UNVALIDATED`로 취급한다.

## 6. 금지된 과장

현재 수익성 있는 leader/follower edge, 실전 자동선별, live trading readiness, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
