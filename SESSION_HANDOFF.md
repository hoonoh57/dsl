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
- GCANCEL2 executable checkpoint는 `3cd5731a1702f7bfb11878dfd6e34339baa5f163`이다.
- 사용자 로컬 검증은 `Ran 5 tests in 0.004s / OK` 및 `Tactical P1 Full PASS`다.
- 최소 vertical-slice 검토 결과, 현재 부족한 것은 새 Core 기능보다 **context→pending→cancel 조합 검증**으로 판정했다.

## 3. 현재 위치

기존 trusted 기능은 이미 다음 구조를 지원한다.

```text
registered exact DEPLOYMENT ctx.* evidence
 + follower-local deterministic setup
 -> generic pending order with stable id
 -> later ctx.* invalidation
 -> order.cancel(id="...")
 -> BrokerEmulator
```

`PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md`가 deferred-order context orchestration을 별도 검증 대상으로 남겨 두었으므로, 이번에는 제품 코드를 늘리지 않고 test-only tranche로 닫는다.

VSLICE1 remote executable validation checkpoint:

```text
72445456e86b695dc7288ab3a48856fa560463dd
```

새 실행 파일은 `test_stage1_context_pending_order_cancel.py` 하나뿐이며 제품 소스 변경은 없다.

테스트는 `bar_close`와 `next_open`에서 exact DEPLOYMENT context 무효화가 pending LIMIT 주문을 이후 체결 전에 취소하고, 실행 권한이 계속 BrokerEmulator에 있음을 확인한다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

VSLICE1 local trust gate:

```powershell
python -m unittest test_stage1_context_pending_order_cancel.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

두 검증이 모두 PASS하면 VSLICE1을 trusted로 승격하고 **generic mechanical vertical slice가 닫힌 것으로 간주**한다.

그 뒤에는 새 Core grammar/학습/랭킹/allocation을 추가하지 않고, 바깥 Add-on에서 한 개의 결정론적 evidence/tactic 실험으로 이동한다.

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
