# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / 2026-08-29 KST**

이 문서는 새 세션이 가장 먼저 읽는 사람 중심 인수인계 문서다. 갑작스러운 종료를 고려해 이전 프로젝트 대화의 마지막 exact local evidence와 GitHub 최신 상태를 함께 대조한다.

## 1. 개발철학 — 5개 이내

1. **작고 검증된 전술부터 키운다.** 큰 자동매매 시스템을 한 번에 만들지 않는다.
2. **DSL Core는 범용적이고 결정론적으로 유지한다.** 계산·신호·주문·취소 같은 재사용 기능만 Core에 둔다.
3. **시장/섹터/대장·추종 판단과 orchestration은 Add-on/context 책임이다.** 이런 의미를 Parser/Runtime/Backtest/Broker에 넣지 않는다.
4. **hard equipment / guard가 학습보다 우선한다.** hard guard 실패는 신규 진입/ARM을 막고 살아 있는 pending을 무효화할 수 있어야 한다.
5. **micro-tranche 단위로 구현 → focused 검증 → Full 검증 → checkpoint 후 다음으로 간다. 실패는 먼저 분류하고 guard를 약화하지 않는다.**

## 2. 최근 한 일

- `GCANCEL1`, `GCANCEL2`, `VSLICE1`, `LF2`, `LFVAL1`, `LFOUT1`, `LFREAL1`, `LFREAL2`, `LFREAL3`는 trusted Full PASS다.
- LFREAL2 trusted executable checkpoint는 `10861c232d03937c5ae77e2be32cd1873a5ff977`이다.
- LFREAL3 trusted executable checkpoint는 `ab4d798c6648ee382e779af81e759cd11bf1cb13`이다.
- LFREAL3 사용자 로컬 검증은 `Ran 7 tests in 0.001s / OK` 및 `[PASS] Tactical P1 verification completed: mode=Full.`이다.
- 저장소에는 여전히 authoritative real-market LF dataset이 없다. 여기서부터는 구조 확장을 멈추고 실제 source material 확보를 우선한다.

## 3. 현재 위치

```text
LF1 OBSERVATION_ONLY relation evidence
+ local deterministic setup / hard guard
 -> LF2 ARM_PENDING / HOLD / HOLD_PENDING / CANCEL_PENDING evidence
 -> LFVAL1 TRAIN / VALIDATION / OOS / HARSH stability validation
 -> LFOUT1 exact frozen outcome validation
 -> LFREAL1 non-fixture provenance/admission contract
 -> LFREAL2 external caller-bytes immutable dataset manifest
 -> LFREAL3 manifest-bound deterministic causal rows/snapshots
```

LFREAL3 trusted contract:

```text
row_count == manifest.record_count
row.symbol in manifest.symbols
unique (symbol,time)
exact first/last observation boundary
finite/basic-valid OHLCV
visible rows = rows where row.time <= knowledge_cutoff
future_rows_excluded = true
```

No nearest lookup, fill-forward, interpolation, provider access, file I/O, strategy replay, LF semantics, order authority, or deployment authority is added.

Authority/claim boundary:

```text
LFREAL3:
  mode = RESEARCH_ROWS_ONLY / CAUSAL_RESEARCH_SNAPSHOT_ONLY
  operational_authority = false
  execution_authority = false
  deployment_authority = false
  market_data_authenticity_verified = false
  real_data_claim = false
```

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

**실제 source material이 나타나기 전까지 architecture expansion을 멈춘다.**

다음 실질 단계:

```text
external historical bytes
 -> LFREAL2 freeze/content hash
 -> source origin 별도 검증
 -> LFREAL3 deterministic rows/snapshots
 -> narrow exact-as-of LF1/LF2 evidence producer
 -> strictly post-observation outcome producer
 -> LFVAL1 / LFOUT1 / LFREAL1 real study
```

실제 bytes가 없는데 parser/provider/framework를 더 만들거나 fixture를 real study로 가장하지 않는다.

automatic selection, allocation, adaptive learning, new DSL grammar, live deployment gate는 계속 보류한다.

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

현재 external real-market dataset 확보/인증, real-data LF study, 수익성 있는 leader/follower edge, 실전 자동선별, validated deployment gating, live trading readiness, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
