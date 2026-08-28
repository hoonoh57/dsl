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
- `GCANCEL1` 완료 및 trusted 승격: `BrokerEmulator.cancel_client_order(...)`가 명시적 `client_order_id`를 fail-closed로 해석하고 기존 Broker `cancel(...)` lifecycle에 위임한다.
- GCANCEL1 executable checkpoint는 `583c5362ca5ea57e62353a963cd5a2cfb0addfad`이다.
- 사용자 로컬 검증은 `Ran 5 tests in 0.000s / OK` 및 `Tactical P1 Full PASS`다.
- 그 다음 `GCANCEL2`를 원격 구현했다: generic DSL `order.cancel(id="...")` → Backtest timing → trusted Broker cancel primitive 연결이다.

## 3. 현재 위치

GCANCEL2 executable remote checkpoint:

```text
3cd5731a1702f7bfb11878dfd6e34339baa5f163
```

현재 상태는 **REMOTE_UNVALIDATED**다.

GCANCEL2의 causal timing:

- `next_open`: 직전 완료봉의 cancel intent를 다음 봉에서 가격 매칭 전에 적용한다.
- `bar_close`: 현재 봉 가격 매칭이 끝난 뒤 close-confirmed cancel intent를 적용하고, 그 다음 신규 deferred order를 제출한다.

변경 실행 축은 다음 세 파일뿐이다.

```text
core/dsl_parser.py
core/backtest.py
test_stage1_dsl_pending_order_cancel.py
```

대장/추종, sector, peer-symbol, allocation, learned-policy 의미는 추가하지 않았다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

GCANCEL2 local trust gate만 수행한다.

```powershell
python -m unittest test_stage1_dsl_pending_order_cancel.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

두 검증이 모두 PASS하면 GCANCEL2를 trusted로 승격한다.

그 다음에는 자동으로 복잡한 대장/추종 orchestration을 확장하지 않는다. 먼저 **현재 generic 예약주문 + 취소 기능만으로 최소 vertical slice에 충분한지** 판단한다.

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

현재 수익성 있는 leader/follower edge, 실전 자동선별, live trading readiness, trusted GCANCEL2, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
