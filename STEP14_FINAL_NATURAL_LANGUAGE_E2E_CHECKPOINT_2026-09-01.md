# Step 14 Final Natural-Language E2E Checkpoint

Status: **COMPLETE / USER-LOCAL PASS / 2026-09-01 KST**

## 확인된 흐름

```text
자연어 원문
 -> External LLM proposal-only structured draft
 -> deterministic local validation + material-assumption human gate
 -> exact PIT AXIS 2 snapshot / filter / rank / top-N
 -> promoted immutable AXIS 3 Condition + Strategy versions
 -> versioned three-axis Bridge
 -> candidate별 AXIS 1 deterministic execution
```

## 대표 수용 결과

- 최근 10일 EMA120 돌파, 현재 재돌파, 기준 Histogram 강도 및 rank는 AXIS 2의 사전계산 exact PIT evidence로 유지된다.
- `수익확보`의 수치가 원문에 없으면 자동 추측하지 않고 material assumption으로 human acceptance를 요구한다.
- candidate의 `selection.reference_hist` evidence는 exact read-only AXIS 1 parent context로 전달되며 binding/hash trace가 보존된다.
- 대표 전략은 기존 범용 EMA / normalized MACD / JMA / state / context / order 기능만 조합한다.
- 수익 미확보 + EMA120 위의 JMA 하락전환은 매도 억제되고, 수익 확보 후 JMA 하락전환은 매도로 이어진다.
- 동일 입력은 동일 request/response hash를 만든다.
- 후순위 candidate parent-context 변조도 첫 AXIS 1 실행 전에 preflight에서 차단된다.
- AXIS 1/2/3 계산 권한, External LLM proposal-only 경계, frozen legacy core 보존을 유지했다.

## 검증 중 발견된 test defect

최종 수용 테스트의 tamper fixture가 immutable tuple을 직접 수정하여 본래 검증 지점에 도달하지 못했다.

분류:

```text
TEST_DEFECT
```

수정:

```text
검증용 tuple -> list 복사본 생성 -> 복사본만 변조
```

제품/Bridge/DSL 계산 로직과 assertion 의미는 변경하지 않았다.

## User-local PASS evidence

```text
test_final_natural_language_e2e.py = OK
test_three_axis_e2e_bridge.py = OK
test_axis1_execution_bridge_contract.py = OK
test_external_llm_authoring_lane.py = OK
test_authoring_continuous_improvement.py = OK
test_frozen_legacy_core_guard.py = OK
```

## 다음 단계

Step 15 `Legacy docs disposition + repo-wide compliance audit`만 남는다.
