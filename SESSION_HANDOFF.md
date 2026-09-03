# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / REALDATA1_LFREAL2_MANIFEST_LOCALLY_TRUSTED / 2026-09-04 KST**

이 문서는 새 세션이 가장 먼저 읽는 사람 중심 인수인계 문서다. 갑작스러운 종료를 고려해 이전 프로젝트 대화의 마지막 exact local evidence와 GitHub 최신 상태를 함께 대조한다.

## 1. 개발철학 — 5개 이내

1. **작고 검증된 전술부터 키운다.** 큰 자동매매 시스템을 한 번에 만들지 않는다.
2. **DSL Core는 범용적이고 결정론적으로 유지한다.** 계산·신호·주문·취소 같은 재사용 기능만 Core에 둔다.
3. **시장/섹터/대장·추종 판단과 orchestration은 Add-on/context 책임이다.** 이런 의미를 Parser/Runtime/Backtest/Broker에 넣지 않는다.
4. **hard equipment / guard가 학습보다 우선한다.** hard guard 실패는 신규 진입/ARM을 막고 살아 있는 pending을 무효화할 수 있어야 한다.
5. **구현 전에 소유계층·기존 공용경로·state SSOT·객체 생성/삭제 권한·인접계층 금지사항을 확정하고, micro-tranche 구현 → focused 검증 → Full 검증 → checkpoint 순서를 지킨다.** 실패는 먼저 분류하고 guard/assertion을 약화하지 않는다.

## 2. 최근 한 일

- `GCANCEL1`, `GCANCEL2`, `VSLICE1`, `LF2`, `LFVAL1`, `LFOUT1`, `LFREAL1`, `LFREAL2`, `LFREAL3`는 trusted Full PASS다.
- REALDATA1 source provenance, exact-byte acquisition verifier, Live Studio verification catalog, PowerShell 5.1 verification-harness fixes를 포함한 이전 executable tail은 `4ebde8647cd0caede3c9cb4e6f210bc5a1f7d630`에서 trusted였다.
- 이후 Core를 수정하지 않고 `tools/freeze_realdata1_dataset.py` edge adapter와 focused test를 추가했다.
- 사용자 로컬 clean validation checkout에서 해당 tranche를 검증했다.
- **현재 trusted executable/test checkpoint는 `2a20f49cd3ae69b1f340496f27b8621d034c98ed`이다.** 이후 docs-only commit은 이 executable SHA를 바꾸지 않는다.
- focused 결과: `Ran 12 tests in 0.024s / OK`.
- 실제 REALDATA1 LFREAL2 freeze 결과:
  - `bytes=57541`
  - `content_sha256=fffbeaece7a769e063c3803ad184265aa751d9f417e3e72e2862045cad10f5ba`
  - `dataset_manifest_hash=8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982`
- 동일 exact checkout에서 `[PASS] Tactical P1 verification completed: mode=Full.`을 확보했다.
- LFREAL2 product logic, Parser/Runtime/Backtest/Broker authority는 변경하지 않았다.

## 3. 현재 위치

```text
TRUSTED_LOCAL_EXECUTABLE
  2a20f49cd3ae69b1f340496f27b8621d034c98ed

REALDATA1 exact content identity
  pinned Git blob SHA-1: 84fb250326def7148cce6466026aaecf057e2013
  exact bytes: 57541
  SHA-256: fffbeaece7a769e063c3803ad184265aa751d9f417e3e72e2862045cad10f5ba

TRUSTED LFREAL2 MANIFEST
  dataset_manifest_hash: 8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982
  symbol: 000660.KS
  timeframe: 1d
  first_observation: 20240415000000
  last_observation: 20260413000000
  record_count: 483

market_data_authenticity_verified = false
real_data_claim = false
```

연구 데이터 경로는 다음 책임 경계를 유지한다.

```text
external historical bytes
 -> LFREAL2 caller-bytes immutable dataset manifest       [DONE / TRUSTED]
 -> LFREAL3 manifest-bound deterministic causal rows      [NEXT]
 -> narrow exact-as-of LF1/LF2 evidence producer
 -> strictly post-observation outcome producer
 -> LFVAL1 / LFOUT1 / LFREAL1 real study
```

LFREAL2는 caller-provided exact bytes의 content identity만 동결한다. provider/network/file I/O 권한, market authenticity 인증, execution/deployment 권한을 얻지 않는다.

LFREAL3는 causal OHLCV row만 admit한다. `return`, `next_close`, `direction` 같은 derived/future-facing source columns는 causal observation feature로 넣지 않는다.

broader repo compliance는 계속 **REMEDIATION_REQUIRED**다.

## 4. 바로 다음에 할 일

다음 micro-tranche는 하나뿐이다.

```text
trusted LFREAL2 manifest
+ exact REALDATA1 local CSV
 -> causal OHLCV-only edge parser/adapter
 -> existing LFREAL3 CausalRowProducer.admit
 -> deterministic row_bundle_hash / exact boundary validation
```

구현 전 고정 경계:

```text
owner layer: tools/ edge adapter outside Core
existing shared path: LFREAL3 CausalRowProducer.admit
state SSOT: trusted LFREAL2 dataset_manifest_hash + LFREAL3 row bundle
create authority: explicit caller source path + manifest path -> edge parser -> LFREAL3 only
delete authority: none
forbidden: Parser/Runtime/Backtest/Broker/Core provider/file/network authority; future-facing column admission; source-specific LFREAL3 semantics
```

edge parser는 `date, open, high, low, close, volume`만 causal row로 변환하고 symbol은 manifest의 `000660.KS`를 사용한다. daily date는 manifest와 일치하는 `YYYYMMDD000000` observation key로 정규화한다.

source bytes SHA-256, manifest hash, record count, first/last observation, required causal columns 중 하나라도 다르면 fail closed 해야 한다. 기존 LFREAL3 product logic은 이 source 때문에 수정하지 않는다.

이 tranche가 focused + Full PASS된 뒤에만 exact-as-of LF1/LF2 evidence producer로 간다.

automatic selection, allocation, adaptive learning, new DSL grammar, live deployment gate는 계속 보류한다.

## 5. 세션복구 규칙

새 프로젝트 세션에서 사용자가 `세션복구`라고 입력하면:

1. 이 문서를 먼저 읽는다.
2. 이전 프로젝트 대화 마지막 부분에서 이 문서 이후 exact local test evidence / 결정이 있는지 확인한다.
3. 마지막 trusted executable SHA와 GitHub `main` 사이 실행 변경분을 비교한다.
4. `CURRENT_STATE.md` 및 authority 문서를 적용한다.
5. 문서가 stale이면 실제 코드 + exact local evidence + 최근 대화 결정으로 보정한다.
6. 첫 답변은 개발철학 / 최근 한 일 / 앞으로 할 일 세 부분만 짧게 보여준다.

새 GitHub 실행 코드/테스트에 local PASS가 없으면 `REMOTE_UNVALIDATED`로 취급한다. docs-only HEAD와 trusted executable SHA를 혼동하지 않는다.

## 6. 금지된 과장

REALDATA1 exact source-byte identity와 LFREAL2 immutable manifest identity가 확인된 사실과 market-data authenticity 인증은 구분한다. LFREAL3 actual-row admission과 real-data LF study는 아직 시작되지 않았다.

```text
market_data_authenticity_verified = false
real_data_claim = false
```

수익성 있는 leader/follower edge, 실전 자동선별, validated deployment gating, live trading readiness, repository-wide compliance PASS를 주장하지 않는다.

`REMEDIATION_REQUIRED`가 broader compliance의 authoritative 상태다.
