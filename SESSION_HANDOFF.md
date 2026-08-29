# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / 2026-08-29 KST**

이 문서는 강제 세션 전환 시 가장 먼저 읽는 복구 문서다. 사용자가 `세션복구`라고 입력하면 아래 순서로 현재 맥락을 복원한다. 오래된 연구 흐름보다 **가장 최근의 사용자 결정 + exact local PASS evidence + 현재 GitHub branch 상태**를 우선한다.

## 1. 개발철학 — 반드시 먼저 복구

1. **메인 제품축은 `UI → LLM 프롬프트/인간매개 → DSL → deterministic Core 실행/검증 → 결과 UI`다.** 연구 sidecar가 이 축을 대체하면 안 된다.
2. **DSL Core는 범용·결정론적·단일 instrument 중심으로 유지한다.** Parser/Semantic/Runtime/Backtest/Broker가 최종 권한을 가진다. LLM은 DSL 작성자이지 실행 권한자가 아니다.
3. **hard equipment / hard guard가 학습·자율성보다 우선한다.** soldier autonomy, adaptive learning, leader/follower 연구는 optional sidecar이며 Core 로직을 흔들면 안 된다.
4. **기능 존재 ≠ 성공.** 각 기능은 실제 예제 DSL을 통해 Parser → Semantic → Runtime/Backtest → Broker/diagnostics까지 통과하고, 필요한 경우 invariant까지 증명해야 PASS다.
5. **micro-tranche discipline을 지킨다.** 작은 변경 → focused test → Full → trusted checkpoint. 실패는 먼저 `test defect / product defect / authority drift / environment issue / unknown`으로 분류하고 guard/contract를 약화하지 않는다.

## 2. 큰 방향 전환 — 삼천포 방지용 핵심

과거 LFREAL1~3까지 leader/follower 연구 sidecar를 만들었지만, 사용자가 이후 명확히 메인축을 다음으로 재지정했다.

```text
기존 핵심 제품 방향
UI
 -> 자연어/LLM 요청 프롬프트
 -> 인간매개 LLM 결과
 -> local DSL
 -> Parser/Semantic
 -> deterministic Runtime/Backtest/Broker
 -> chart/result/validation
 -> UI feedback
```

따라서:

- LF1/LF2/LFVAL/LFOUT/LFREAL은 **보존된 연구 sidecar**다.
- LFREAL4 같은 추가 연구 아키텍처 확장은 사용자가 명시적으로 다시 요청하기 전에는 하지 않는다.
- `ux-max-ui`는 workflow/UI 실험 브랜치일 뿐 제품 기준선이 아니다.
- 새 제품 기준선은 `dsl-live-studio` branch의 **독립 direct-core Live Studio**다.
- `app_ui.py` legacy demo path를 제품 성능 측정에 재사용하지 않는다.

## 3. 현재 제품 아키텍처

Branch:

```text
dsl-live-studio
```

실제 평가 경로:

```text
사용자/LLM DSL
 -> DSLParser
 -> DSLSemanticAnalyzer
 -> DSLRuntime
 -> BacktestEngine
 -> BrokerEmulator
 -> executions / trades / rejects / MFE / MAE / equity / diagnostics
```

`live_studio_main.py`는 legacy `app_ui.py`를 import하지 않는다.

데이터 의미도 분리한다:

```text
SYNTHETIC_ENGINE_FIXTURE
= DSL/Core 기능 계측용

CALLER_SUPPLIED_MARKET
= caller가 제공한 OHLCV를 Core에서 평가
```

caller-supplied는 자동으로 real-market authenticity를 증명하지 않는다.

## 4. 최근 완료된 trusted 작업

### Live Studio direct-core + Feature Catalog v1

Trusted baseline:

```text
c9c5122d799d6c0cb30d45eb37890d16b582d322
```

Local evidence:

```text
python -m unittest test_live_studio_core_path.py
Ran 5 tests in 0.019s
OK

python -m unittest test_live_studio_feature_catalog.py
Ran 5 tests in 1.198s
OK

[PASS] Tactical P1 verification completed: mode=Full.
```

v1 의미:

```text
FUNCTION_SPECS SSOT
 -> 카테고리별 실제 예제 DSL
 -> Parser PASS
 -> Semantic PASS
 -> real BacktestEngine PASS
```

TA / math / logic / state / session / MTF + grammar / orders / next_open / risk settings를 executable catalog로 검증했다.

### Feature Catalog v2 invariant harness

Trusted executable baseline:

```text
5f8fe52a60c299a0e241d14ca3b99f2a485ef4c5
```

Local evidence:

```text
python -m unittest test_live_studio_feature_invariants.py
Ran 5 tests in 0.039s
OK

python -m unittest test_live_studio_core_path.py
Ran 5 tests in 0.017s
OK

python -m unittest test_live_studio_feature_catalog.py
Ran 5 tests in 1.249s
OK

[PASS] Tactical P1 verification completed: mode=Full.
```

v2 invariant set:

```text
context.exact_binding
context.missing_fail_closed
execution.entry_gate_suppression
execution.next_open_timing
execution.entry_time_window
execution.max_entries_per_day
order.stop_fill
order.stop_limit_fill
order.day_expiry
order.stable_client_cancel
mtf.confirmed_only
```

### v2 invariant UI integration

Trusted UI integration checkpoint:

```text
089b727204088f5ac5dbd6ac041e470f4df2a8c4
```

Local evidence:

```text
test_live_studio_invariant_ui.py
Ran 4 tests in 0.025s
OK

test_live_studio_feature_invariants.py
Ran 5 tests in 0.038s
OK

test_live_studio_core_path.py
Ran 5 tests in 0.017s
OK

test_live_studio_feature_catalog.py
Ran 5 tests in 1.258s
OK

[PASS] Tactical P1 verification completed: mode=Full.
```

현재 Live Studio UI는 일반 기능 catalog와 invariant catalog를 구분해 선택/실행할 수 있다.

## 5. 현재 작업 중 — 세션 전환 시 가장 중요

**Feature Catalog v3 invariant tranche가 현재 REMOTE_UNVALIDATED 상태다.**

Executable checkpoint:

```text
72013531fca28ea832808a0d3a89f12da3607762
```

문서 포함 최신 remote 이후 commit이 더 있을 수 있으므로 GitHub branch head를 반드시 확인한다.

v3 추가 invariant:

```text
order.oco_sibling_cancel
order.gtc_persistence
order.close_long
order.close_short
order.close_position
execution.pending_suppressed_position_occupied
execution.same_bar_reentry
execution.risk_exit_precedence
```

주의:

- `hard_guard_precedence`라는 과장된 이름은 쓰지 않는다.
- 현재 Core에서 직접 관측 가능한 것은 risk exit(STOP/TP/trailing)가 strategy exit보다 먼저 적용되는 우선순위이므로 `risk_exit_precedence`로 검증한다.
- v3는 아직 사용자 로컬 PASS 증거가 없으므로 trusted로 승격하지 않는다.

## 6. 바로 다음에 할 일

첫 작업은 v3 local gate 확인이다.

```powershell
git pull --ff-only origin dsl-live-studio
python -m unittest test_live_studio_feature_invariants_v3.py
python -m unittest test_live_studio_feature_invariants.py
python -m unittest test_live_studio_core_path.py
python -m unittest test_live_studio_feature_catalog.py
powershell -ExecutionPolicy Bypass -File .\scripts\verify_tactical_p1.ps1 -Mode Full
```

결과가 모두 PASS이면:

1. v3를 trusted checkpoint로 승격한다.
2. 필요하면 v3 invariant도 Live Studio UI에 통합한다.
3. 그 다음까지도 우선순위는 **DSL 전체 기능 계약 검증**이다.
4. 전체 실행 matrix가 충분히 닫힌 뒤 실전 historical data adapter / provenance / richer evaluation UI / LLM authoring loop로 간다.

실패하면 먼저 실패 기능 하나를 분류한다:

```text
test defect
product defect
contract mismatch / authority drift
environment issue
unknown
```

테스트나 guard를 약화해 PASS시키지 않는다.

## 7. 보존해야 할 이전 trusted 연구 자산

다음은 삭제/무효화하지 않는다. 다만 현재 메인 개발축은 아니다.

```text
CTXDSL1 + CTXBT1 99bb2e5f5a248dc61cddb23677b5798b258848f2
CTXINT3           7f77694658d7155806e97bdafcc543e2c7bfeae8
LF1               5ec230c8bbada60f0e4b9fe945a5380d7c405fe2
GCANCEL1          583c5362ca5ea57e62353a963cd5a2cfb0addfad
GCANCEL2          3cd5731a1702f7bfb11878dfd6e34339baa5f163
VSLICE1           72445456e86b695dc7288ab3a48856fa560463dd
LF2               5a6e6e53c089ed108d19fa729cba84874e856388
LFVAL1            283af6e8ed046324698b9ff49e95f5044131f453
LFOUT1            ca4d5309a658de02f970e341bbf86ad87ab327ae
LFREAL1           5aa1da3268f1f3e031aa6d607a4d3a5921f03e58
LFREAL2           10861c232d03937c5ae77e2be32cd1873a5ff977
LFREAL3           ab4d798c6648ee382e779af81e759cd11bf1cb13
```

Research sidecar는 Core를 오염시키지 않는 optional extension으로 보존한다.

## 8. `세션복구` 명령 규칙

새 세션에서 사용자가 `세션복구`라고 입력하면 질문부터 하지 말고 다음 순서로 복구한다.

1. **이 `SESSION_HANDOFF.md`를 가장 먼저 읽는다.**
2. 프로젝트의 최신 대화에서 이 문서 이후 사용자 결정/로컬 PASS가 있는지 확인한다.
3. 현재 GitHub branch/head와 문서의 current-work checkpoint를 비교한다.
4. `CURRENT_STATE.md`와 관련 authority 문서를 확인한다.
5. 문서가 stale이면 **최신 사용자 결정 + exact local evidence + 실제 코드**를 우선해 보정한다.
6. 새 remote 실행 코드/테스트에 local PASS가 없으면 반드시 `REMOTE_UNVALIDATED`로 취급한다.
7. 첫 답변은 아래 **정확히 3개 짧은 섹션**만 보여준다.

```text
개발철학      <= 5개
최근 한 일    <= 5개
앞으로 할 일  <= 5개
```

첫 복구 답변에서 LF 연구 연혁을 장황하게 설명하지 않는다. 현재 메인축과 현재 작업을 먼저 말한다.

## 9. 금지된 방향 이탈 / 과장

다음을 임의로 시작하거나 주장하지 않는다.

- LFREAL4 등 연구 sidecar 추가 확장
- adaptive soldier autonomy 때문에 Core grammar/runtime를 반복 변경
- 자동 leader selection / allocation / live deployment gating
- real-market authenticity가 검증되지 않은 데이터를 real study라고 부르기
- synthetic fixture 성능을 실전 수익성으로 해석
- legacy demo backtest를 최신 DSL 실행 결과라고 표시
- repository-wide compliance PASS 주장

`REMEDIATION_REQUIRED`는 broader repository compliance의 authoritative 상태다.
