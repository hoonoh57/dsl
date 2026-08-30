# H1 Range / No-Trade Detector Decision

작성일: 2026-08-31
상태: COMPETITION RESULT / ENTRY_GATE 미연결

## 1. 결론

현재 deterministic F1~F10 경쟁 fixture에서는 **ADX 단독이 Range/Trend 분리 성능 1위**다.

```text
ADX
range_allow = 0.204
trend_allow = 1.000
separation  = 0.796
```

비교 조합은 횡보 허용률을 더 낮췄지만 정상 추세까지 희생했고 전체 separation도 ADX 단독보다 낮았다.

```text
ADX AND normalized_range
range_allow = 0.080
trend_allow = 0.750
separation  = 0.670

ADX AND JMA slope
range_allow = 0.156
trend_allow = 0.866
separation  = 0.710

ADX AND (normalized_range OR JMA slope)
range_allow = 0.168
trend_allow = 0.900
separation  = 0.732
```

따라서 normalized range/JMA slope를 ADX에 상시 결합하는 composite hard gate는 채택하지 않는다.

## 2. 결정 근거

### 저변동 추세 보존

F9 low-vol trend:

```text
ADX                  1.000
ADX + normalized     0.000
ADX + JMA            0.600
ADX + (range OR JMA) 0.600
```

단순 폭/기울기 조건을 붙이면 사람이 실제로 거래할 수 있는 저변동 추세를 과도하게 차단한다.

### ADX의 남은 약점

ADX는 다음 transition/shock fixture에서 잔존 허용이 있다.

```text
F7 false breakout: 0.328
F8 gap then range: 0.488
```

그러나 이 결함을 range detector 내부에서 normalized range/JMA를 상시 AND하는 방식으로 해결하면 정상 추세 손실이 커진다.

따라서 이 문제는 **별도 transition/shock guard**로 분리한다.

## 3. 소유권 분리

```text
Range Detector
  목적: 횡보/비추세 상태 차단
  1차 주센서: ADX

Transition / Shock Guard
  목적: gap 직후, false breakout, shock 잔존 상태의 일시적 진입 억제
  별도 state/equipment로 설계

BacktestEngine.entry_gate
  위 장비들의 최종 permission만 소비
```

Range Detector가 gap/false-breakout/setup-memory까지 모두 책임지지 않는다.

## 4. 현재 판정

- ADX: `PRIMARY_CANDIDATE`
- normalized_range: `DIAGNOSTIC_SENSOR`, 상시 gate 미채택
- JMA absolute slope: `DIAGNOSTIC_SENSOR`, 상시 gate 미채택
- VHF current threshold: `REJECTED_AS_HARD_GATE`
- ADX composite: `NOT_SELECTED`
- entry_gate integration: `DEFERRED`

## 5. 다음 tranche

1. F7/F8를 겨냥한 Transition / Shock Guard 계약 정의
2. gap shock cooldown / false breakout cooldown 후보 경쟁
3. ADX Range Detector와 orthogonal guard를 결합한 permission 시험
4. 정상 추세 보존이 확인되면 `BacktestEngine.entry_gate`에 연결
5. synthetic fixture 통과 후 실제 시장 데이터 구간에서 별도 검증

중요: 현재 결과는 deterministic synthetic competition의 1차 설계 근거이며 실전 수익성이나 일반화 성능을 증명하지 않는다.
