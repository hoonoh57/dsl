# H1 Range / No-Trade Detector Decision

작성일: 2026-08-31
상태: COMPETITION RESULT / ADX-ONLY ENTRY_GATE CANDIDATE

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

Transition / Shock Guard도 broad hard gate로는 채택하지 않는다. 2차 competition에서 정상 고변동 추세 손실이 너무 컸다.

```text
ADX
range_allow = 0.204
trend_allow = 1.000
separation  = 0.796

ADX AND ShockGuard
range_allow = 0.178
trend_allow = 0.822
separation  = 0.644
```

따라서 H1 1차 entry permission 통합 후보는 **ADX Range Guard 단독**으로 축소한다.

## 2. 결정 근거

### 저변동 추세 보존

F9 low-vol trend:

```text
ADX                  1.000
ADX + normalized     0.000
ADX + JMA            0.600
ADX + (range OR JMA) 0.600
ADX + ShockGuard     1.000
```

단순 폭/기울기 조건을 붙이면 사람이 실제로 거래할 수 있는 저변동 추세를 과도하게 차단한다.

### 고변동 추세 보존

F10 high-vol trend에서 ShockGuard가 과도하게 차단했다.

```text
ADX                 1.000
ShockGuard          0.288
ADX + ShockGuard    0.288
```

component 진단 결과 주된 원인은 `false_breakout` 판정이었다.

```text
F10 component allow

gap_shock              1.000
large_bar_shock        0.816
false_breakout         0.304
post_breakout_failure  0.944
```

즉 noisy/high-volatility trend에서 prior range boundary를 반복적으로 넘나드는 정상 가격행동을 false breakout으로 과잉 판정한다.

현재 synthetic evidence에서는 이 guard가 F7/F8을 개선하는 폭보다 F10 정상 추세를 훼손하는 비용이 훨씬 크다.

### ADX의 남은 약점

ADX는 다음 fixture에서 잔존 허용이 있다.

```text
F7 false breakout: 0.328
F8 gap then range: 0.488
```

ShockGuard 결합 후:

```text
F7: 0.328 -> 0.272
F8: 0.488 -> 0.440
```

개선폭은 제한적이다.

또한 현재 F8 fixture는 close가 약 100에서 108로 점프하지만 fixture helper가 `open[i] = close[i-1]`로 생성하므로 **실제 OHLC gap fixture가 아니다**. 따라서 F8은 gap guard 성능 근거로 사용하지 않는다. Gap guard는 별도 실제-gap fixture에서 검증해야 한다.

## 3. 소유권 분리

```text
Range Detector
  목적: 횡보/비추세 상태 차단
  1차 주센서: ADX
  H1 1차 hard-gate 후보

Transition / Shock Guard
  목적: gap 직후 / false breakout / shock 잔존 상태의 일시적 진입 억제
  현재 상태: DIAGNOSTIC / DEFERRED
  broad hard gate로는 미채택

BacktestEngine.entry_gate
  최종 boolean permission만 소비
```

Range Detector가 gap/false-breakout/setup-memory까지 모두 책임지지 않는다.

## 4. 현재 판정

- ADX: `PRIMARY_CANDIDATE_FOR_H1_ENTRY_GATE`
- normalized_range: `DIAGNOSTIC_SENSOR`, 상시 gate 미채택
- JMA absolute slope: `DIAGNOSTIC_SENSOR`, 상시 gate 미채택
- VHF current threshold: `REJECTED_AS_HARD_GATE`
- ADX composite: `NOT_SELECTED`
- Transition / Shock Guard: `DEFERRED_AS_BROAD_HARD_GATE`
- false_breakout guard: `OVERBLOCKS_HIGH_VOL_TREND`
- gap guard: `INSUFFICIENT_COMPETITION_FIXTURE`
- H1 first integration target: `ADX_ONLY`

## 5. 다음 tranche

1. ADX permission을 별도 equipment output으로 고정한다.
2. 기존 `BacktestEngine.entry_gate`에 **ADX permission만** 연결하는 최소 integration test를 만든다.
3. sideways fixture에서 반복 진입 감소를 검증한다.
4. trend fixture에서 정상 진입 손실을 검증한다.
5. named gate reason/evidence는 다음 tranche로 분리한다.
6. ShockGuard는 실제-gap / noisy-trend 전용 fixture가 충분히 준비되기 전까지 entry gate에 연결하지 않는다.

중요: 현재 결과는 deterministic synthetic competition의 1차 설계 근거이며 실전 수익성이나 일반화 성능을 증명하지 않는다.
