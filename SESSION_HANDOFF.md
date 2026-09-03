# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / RECONCILED_REMOTE_TAIL / 2026-09-04 KST**

이 문서는 새 세션이 가장 먼저 읽는 사람 중심 인수인계 문서다. 갑작스러운 종료를 고려해 이전 프로젝트 대화의 마지막 exact local evidence와 GitHub 최신 상태를 함께 대조한다.

## 1. 개발철학 — 5개 이내

1. **작고 검증된 전술부터 키운다.** 큰 자동매매 시스템을 한 번에 만들지 않는다.
2. **DSL Core는 범용적이고 결정론적으로 유지한다.** 계산·신호·주문·취소 같은 재사용 기능만 Core에 둔다.
3. **시장/섹터/대장·추종 판단과 orchestration은 Add-on/context 책임이다.** 이런 의미를 Parser/Runtime/Backtest/Broker에 넣지 않는다.
4. **hard equipment / guard가 학습보다 우선한다.** hard guard 실패는 신규 진입/ARM을 막고 살아 있는 pending을 무효화할 수 있어야 한다.
5. **구현 전에 소유계층·기존 공용경로·state SSOT·객체 생성/삭제 권한·인접계층 금지사항을 확정하고, micro-tranche 구현 → focused 검증 → Full 검증 → checkpoint 순서를 지킨다.** 실패는 먼저 분류하고 guard/assertion을 약화하지 않는다.

## 2. 최근 한 일

- `GCANCEL1`, `GCANCEL2`, `VSLICE1`, `LF2`, `LFVAL1`, `LFOUT1`, `LFREAL1`, `LFREAL2`, `LFREAL3`는 trusted Full PASS다.
- 마지막 trusted executable checkpoint는 LFREAL3 `ab4d798c6648ee382e779af81e759cd11bf1cb13`이고, 사용자 로컬 증거는 `Ran 7 tests in 0.001s / OK` 및 `[PASS] Tactical P1 verification completed: mode=Full.`이다.
- 이후 실제 외부 source material로 SK hynix `000660.KS` 일봉 CSV를 찾고 source provenance를 기록했다. pinned source blob은 `84fb250326def7148cce6466026aaecf057e2013`, 483 data rows다.
- `REALDATA1` exact-byte acquisition verifier와 첫 Live Studio Core verification catalog/focused test가 `main`에 추가됐다.
- 그러나 LFREAL3 이후 실행 변경에 대한 사용자 로컬 PASS는 아직 복구되지 않았다. 따라서 현재 `main` HEAD `3a49177a15888922c48c68efd91beac1abcba4a6`은 **REMOTE_UNVALIDATED**이며 trusted checkpoint로 승격하지 않는다.

## 3. 현재 위치

```text
TRUSTED_LOCAL
  LFREAL3 ab4d798c6648ee382e779af81e759cd11bf1cb13

REMOTE_UNVALIDATED tail
  REALDATA1 provenance checkpoint
  -> pinned exact-byte acquisition verifier
  -> first Live Studio verification catalog
  -> focused catalog tests
  -> main HEAD 3a49177a15888922c48c68efd91beac1abcba4a6
```

연구 데이터 경로는 다음 책임 경계를 유지한다.

```text
external historical bytes
 -> LFREAL2 caller-bytes immutable dataset manifest
 -> LFREAL3 manifest-bound deterministic causal rows/snapshots
 -> narrow exact-as-of LF1/LF2 evidence producer
 -> strictly post-observation outcome producer
 -> LFVAL1 / LFOUT1 / LFREAL1 real study
```

LFREAL2는 caller-provided exact bytes의 content identity만 동결한다. provider/network/file I/O 권한, market authenticity 인증, execution/deployment 권한을 얻지 않는다.

LFREAL3는 causal OHLCV row만 admit한다. `return`, `next_close`, `direction` 같은 derived/future-facing source columns는 causal observation feature로 넣지 않는다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

**새 실행 기능을 더 쌓지 말고 현재 remote tail을 먼저 검증한다.**

검증 순서:

```text
1. git pull --ff-only origin main
2. powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\acquire_realdata1_source.ps1
   -> pinned Git blob identity + exact downloaded bytes의 SHA-256 확인
3. python -m unittest -v test_live_validation_catalog.py
4. powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

위 세 검증이 현재 `main` HEAD에서 PASS하면 그 exact SHA를 trusted local point로 승격한다.

그 다음 micro-tranche에서만:

```text
verified exact REALDATA1 bytes
 -> existing LFREAL2 ExternalDatasetFreezer
 -> immutable content_sha256 + dataset_manifest_hash 기록
 -> causal OHLCV-only parser/adapter 경계 검토
 -> LFREAL3 admission focused test
```

LFREAL2 product logic이나 Parser/Runtime/Backtest/Broker에 real-data/provider 특화 의미를 추가하지 않는다.

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

현재 source material/provenance를 확보한 사실과 market-data authenticity 인증은 구분한다. LFREAL2 exact-byte manifest가 아직 생성되지 않았고, real-data LF study도 시작되지 않았다.

수익성 있는 leader/follower edge, 실전 자동선별, validated deployment gating, live trading readiness, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
