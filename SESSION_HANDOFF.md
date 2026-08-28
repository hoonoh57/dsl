# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / 2026-08-28 KST**

이 문서는 새 세션이 가장 먼저 읽는 사람 중심 인수인계 문서다. 갑작스러운 종료를 고려해 이전 프로젝트 대화의 마지막 exact local evidence와 GitHub 최신 상태를 함께 대조한다.

## 1. 개발철학 — 5개 이내

1. **작고 검증된 전술부터 키운다.** 큰 자동매매 시스템을 한 번에 만들지 않는다.
2. **DSL Core는 범용적이고 결정론적으로 유지한다.** 계산·신호·주문·취소 같은 재사용 기능만 Core에 둔다.
3. **시장/섹터/대장·추종 판단과 orchestration은 Add-on/context 책임이다.** 이런 의미를 Parser/Runtime/Backtest/Broker에 넣지 않는다.
4. **hard equipment / guard가 학습보다 우선한다.** hard guard 실패는 신규 진입/ARM을 막고 살아 있는 pending을 무효화할 수 있어야 한다.
5. **micro-tranche 단위로 구현 → focused 검증 → Full 검증 → checkpoint 후 다음으로 간다. 실패는 먼저 분류하고 guard를 약화하지 않는다.**

## 2. 최근 한 일

- `GCANCEL1`, `GCANCEL2`, `VSLICE1`은 trusted Full PASS다.
- VSLICE1 checkpoint `72445456e86b695dc7288ab3a48856fa560463dd`에서 generic mechanical vertical slice가 닫혔다.
- LF2 initial checkpoint `14bf03f1f9473a607d4330e4d06f9d0ef9bdd219`의 docstring source-contract defect를 수정했다.
- LF2 fix executable checkpoint는 `5a6e6e53c089ed108d19fa729cba84874e856388`이다.
- 사용자 로컬 post-fix focused 검증은 `Ran 6 tests in 0.001s / OK`다. Full은 LF2가 아니라 sibling Chart SSOT contract에서 차단됐다.

## 3. 현재 위치

LF2는 focused PASS지만 아직 trusted Full PASS는 아니다.

```text
LF1 OBSERVATION_ONLY relation result
+ selected/local follower
+ local setup pass/fail
+ local hard-guard pass/fail
+ explicit relation_still_valid
+ active pending identity when present
 -> ARM_PENDING / HOLD / HOLD_PENDING / CANCEL_PENDING
```

Authority boundary:

```text
mode = OBSERVATION_ONLY
operational_authority = false
execution_authority = false
```

Hard guard는 deterministic veto다. 신규 ARM을 막고 active pending에는 `CANCEL_PENDING` 의도를 낼 수 있다.

현재 Full blocker는 외부 sibling Chart repository `cascading-feature-solution`의 `STABLE-PANE-003` contract다.

Remote Chart `main`은 다음처럼 source/test가 서로 일치한다.

```text
StablePaneIdentitySurface
 -> ResponsiveChartSurface(stablePanes)
```

하지만 사용자 로컬 Chart source에는 remote에 없는 `PrimaryPaneLayoutSurface`가 추가되어:

```text
StablePaneIdentitySurface
 -> PrimaryPaneLayoutSurface
 -> ResponsiveChartSurface(primaryLayout)
```

가 되었고, local test는 여전히 `ResponsiveChartSurface(stablePanes)`를 기대한다.

따라서 현재 DSL Full 실패 분류는 **environment issue — local external dependency drift**다. LF2/DSL product defect로 보지 않는다. Chart guard/test나 DSL Full verifier를 약화하지 않는다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

먼저 사용자 로컬 Chart repo의 local-only 변경을 식별한다.

```powershell
git -C E:\2026\opus\typescript\cascading-feature-solution status --short
git -C E:\2026\opus\typescript\cascading-feature-solution log -5 --oneline --decorate
git -C E:\2026\opus\typescript\cascading-feature-solution diff -- src/adapters/chart/BrowserChartSurfaceFactory.mjs tests/stable_pane_identity_surface.test.mjs
```

이 결과로 `PrimaryPaneLayoutSurface`가 의도된 최신 architecture change인지 accidental local drift인지 판정한다.

- 의도된 변경이면 Chart test/contract를 해당 architecture에 맞춰 별도 Chart tranche로 정합화한다.
- accidental drift이면 trusted Chart state로 되돌린 뒤 DSL Full verifier를 재실행한다.

그 후 동일 LF2 checkout에서 Full PASS를 받아야 LF2를 trusted로 승격한다.

LF2 trust 뒤에도 즉시 deployment authority를 주지 않는다. 별도 Train/Validation/OOS/Harsh evidence tranche가 필요한지 먼저 판단한다. adaptive learning, ranking 확대, allocation, live selection, 새 DSL grammar는 자동으로 열지 않는다.

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

현재 수익성 있는 leader/follower edge, 실전 자동선별, validated deployment gating, live trading readiness, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
