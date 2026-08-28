# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / 2026-08-28 KST**

이 문서는 새 세션이 가장 먼저 읽는 사람 중심 인수인계 문서다. 갑작스러운 종료를 고려해 이전 프로젝트 대화의 마지막 exact local evidence와 GitHub 최신 상태를 함께 대조한다.

## 1. 개발철학 — 5개 이내

1. **작고 검증된 전술부터 키운다.** 큰 자동매매 시스템을 한 번에 만들지 않는다.
2. **DSL Core는 범용적이고 결정론적으로 유지한다.** 계산·신호·주문·취소 같은 재사용 기능만 Core에 둔다.
3. **시장/섹터/대장·추종 판단은 Add-on 책임이다.** 이런 의미를 Parser/Runtime에 넣지 않는다.
4. **hard equipment / guard가 학습보다 우선한다.** 적응형 기능은 optional sidecar로 격리한다.
5. **micro-tranche 단위로 구현 → focused 검증 → Full 검증 → checkpoint 후 다음으로 간다.**

## 2. 최근 한 일

- `LF1`은 trusted Full PASS 상태다. 대장/추종 관계는 관찰 증거이며 주문 권한은 없다.
- `GCANCEL1` trusted: `BrokerEmulator.cancel_client_order(...)`가 명시적 `client_order_id`를 fail-closed로 해석하고 기존 Broker cancel lifecycle에 위임한다.
- `GCANCEL2` trusted: generic DSL `order.cancel(id="...")`가 Backtest timing을 거쳐 trusted Broker cancellation primitive로 연결된다.
- GCANCEL2 executable checkpoint는 `3cd5731a1702f7bfb11878dfd6e34339baa5f163`이다.
- 사용자 로컬 검증은 `Ran 5 tests in 0.004s / OK` 및 `Tactical P1 Full PASS`다.

## 3. 현재 위치

현재 최소 실행 조합은 다음까지 trusted다.

```text
external leader/sector evidence
 -> follower-local setup
 -> generic pending LIMIT/STOP/STOP_LIMIT intent with stable id
 -> generic order.cancel(id="...")
 -> BrokerEmulator lifecycle
```

GCANCEL2 timing은 causal하다.

- `next_open`: 직전 완료봉의 cancel intent를 다음 봉 가격 매칭 전에 적용한다.
- `bar_close`: 현재 봉 가격 매칭 후 close-confirmed cancel intent를 적용한다.

대장/추종, sector, peer-symbol, allocation, learned-policy 의미는 Core에 추가하지 않았다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

다음은 새 기능 추가가 아니라 **최소 vertical-slice 충분성 검토**다.

1. 기존 Add-on/context 경로만으로 간단한 invalidate/not-invalidate 조건을 만들 수 있는지 본다.
2. 한 추종 setup이 pending 주문 하나를 만들고 이후 trusted `order.cancel(id=...)`로 취소되는지 본다.
3. 부족한 부분이 있으면 그것이 진짜 generic primitive인지, 단순 orchestration인지 구분한다.
4. adaptive learning, ranking 확대, allocation, 새 grammar 없이 첫 동작을 구성한다.
5. 실제 generic gap이 확인될 때만 다음 Core tranche를 연다.

## 5. 세션복구 규칙

새 프로젝트 세션에서 사용자가 `세션복구`라고 입력하면:

1. 이 문서를 먼저 읽는다.
2. 이전 프로젝트 대화 마지막 부분에서 이 문서 이후 exact local test evidence / 결정이 있는지 확인한다.
3. 마지막 trusted executable SHA와 GitHub `main` 사이 실행 변경분을 비교한다.
4. `CURRENT_STATE.md` 및 authority 문서를 적용한다.
5. 문서가 stale이면 실제 코드 + exact local evidence + 최근 대화 결정으로 보정한다.
6. 첫 답변은 개발철학 / 최근 한 일 / 앞으로 할 일 세 부분만 짧게 보여준다.

새 GitHub 실행 코드에 local PASS가 없으면 `REMOTE_UNVALIDATED`로 취급한다. 사용자 PC에만 존재하고 대화/GitHub에 흔적이 없는 상태만 복구 불가능하다.

## 6. 금지된 과장

현재 수익성 있는 leader/follower edge, 실전 자동선별, live trading readiness, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
