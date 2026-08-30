# DSL H1 Range / No-Trade Detector Competition

작성일: 2026-08-31
상태: DESIGN / COMPETITION SPEC — 구현 승인 아님

## 1. 목적

이 문서는 H1 Do-Not-Trade Intelligence의 첫 장비인 **Range / No-Trade Detector** 후보를 동일 기준으로 경쟁시키기 위한 시험 규격이다.

목표는 '횡보를 잘 맞히는 지표'가 아니다. 전략 실행 관점에서 다음을 만족하는 장비를 찾는다.

1. 횡보/잡음 구간의 불필요한 진입을 최대한 차단한다.
2. 추세 발생/재개 구간을 과도하게 늦게 허용하지 않는다.
3. 미래값/lookahead 없이 bar-by-bar 동일 결과를 낸다.
4. 전략 신호를 재계산하지 않고 기존 `BacktestEngine.entry_gate`에 boolean permission만 공급할 수 있다.
5. 왜 차단됐는지 결정론적으로 설명 가능해야 한다.

최종 출력 계약 후보:

```text
range_score          number
trend_score          number
trade_permitted      boolean
reason_code           stable enum/string
```

장비는 주문을 만들지 않는다. 전략 신호와 주문 의미는 DSL Core/Broker 권한이다.

---

## 2. 현재 사용할 수 있는 Core 센서

현재 `CoreTALib` 및 FUNCTION_SPECS에 다음 기반이 존재한다.

### C1. VHF

현재 구현 의미:

```text
VHF(N) = abs(highest(close,N) - lowest(close,N))
         / sum(abs(close - close[1]), N)
```

해석:
- 한 방향으로 진행하면 분자가 누적 이동에 가까워져 상대적으로 높아진다.
- 같은 범위 안을 왕복하면 분모가 커지고 상대적으로 낮아진다.
- 방향 자체를 알려주지 않는다.

장점:
- 횡보성/왕복성을 직접 겨냥한다.
- 가격 수준과 비교적 독립적이다.

위험:
- 짧고 강한 변동/갭에서 순간적으로 높아질 수 있다.
- 임계값 하나로 모든 종목/주기를 고정하면 과적합 위험이 있다.

### C2. ADX

현재 구현은 Wilder RMA 기반 `+DM/-DM -> DI -> DX -> ADX`이다.

해석:
- 방향과 무관한 추세 강도 센서.
- 낮으면 방향성이 약할 가능성이 높고, 높으면 진행성이 강할 가능성이 높다.

장점:
- 추세강도라는 해석이 명확하다.
- VHF와 다른 실패유형을 측정한다.

위험:
- 후행성이 있어 새로운 추세 시작을 늦게 허용할 수 있다.
- 급격한 변동 직후 높은 값이 남을 수 있다.

### C3. Normalized Range

현재 `ta.nrange(N)`은 `highest(high,N) - lowest(low,N)`의 절대 가격폭이다.
단독으로는 가격 수준이 다른 종목을 비교할 수 없으므로 장비에서는 정규화가 필수다.

후보:

```text
nrange_pct = nrange(N) / close
nrange_atr = nrange(N) / ATR(N)
```

해석:
- 박스/압축의 물리적 폭을 측정.

위험:
- 작은 범위라도 지속 방향성이 있을 수 있으므로 이것만으로 횡보 판정 금지.

### C4. JMA Slope

현재 `ta.jma`는 원본 chart engine 포트와 동일한 recursive state를 사용한다.

장비 후보:

```text
jma_slope_pct = (JMA[t] - JMA[t-k]) / close[t-k]
abs_jma_slope = abs(jma_slope_pct)
```

해석:
- 사용자가 직접 화면에서 보는 '기준선의 기울기'를 수치화한다.
- 절대 slope 기준선 아래이면 진입금지 장비로 사용할 수 있다.

장점:
- 사람이 차트에서 즉시 인식하는 진행성에 가깝다.
- 명시적 절대 기준선을 제공할 수 있다.

위험:
- length/k/threshold에 민감하다.
- 평활로 인해 추세 시작에 지연이 생길 수 있다.

### C5. Volatility Compression

현재 ATR/stdev/highest/lowest가 있어 DSL/Core primitive만으로 계산 가능하다.

후보:

```text
atr_pct = ATR(N) / close
std_pct = stdev(close,N) / close
range_compression = nrange(N) / rolling_reference
```

해석:
- 에너지/변동성 압축을 측정한다.

주의:
- 저변동 = 횡보는 아니다. 완만한 추세와 구분하기 위해 진행성 센서와 조합해야 한다.

---

## 3. 경쟁 철학: 단일 지표 우승이 아니라 Sensor Fusion

다음 네 질문은 서로 다르다.

```text
왕복하고 있는가?        -> VHF
추세 강도가 있는가?     -> ADX
기준선이 실제 기울었나? -> JMA slope
가격 범위가 압축됐나?   -> normalized range / volatility
```

따라서 경쟁은 두 단계로 한다.

### Stage 1 — 단독 센서 평가

각 센서를 동일 fixture에서 단독 gate로 시험하여 특성을 측정한다.

### Stage 2 — 결정론적 조합 평가

Stage 1 결과를 바탕으로 2~3개 센서만 조합한다.

예시(문법 승인 아님):

```text
NO_TRADE_RANGE =
    abs_jma_slope < slope_floor
    AND vhf < vhf_floor
    AND adx < adx_floor
```

또는 보수적으로:

```text
trade_permitted =
    abs_jma_slope >= slope_floor
    AND (vhf >= vhf_floor OR adx >= adx_floor)
```

학습 모델이 임계값이나 결론을 임의 변경하지 않는다. 모든 threshold/version은 실험 identity에 포함한다.

---

## 4. 표준 Fixture 설계

실제 데이터 이전에 detector 의미 자체를 검증할 deterministic fixture를 만든다.

### F1. Flat Noise

- 중심값 주위 작은 랜덤 왕복.
- 기대: 대부분 `NO_TRADE`.

### F2. Wide Choppy Range

- 폭은 크지만 방향 없이 상하 왕복.
- 핵심 시험: 단순 volatility/range 센서가 이를 추세로 오인하지 않아야 한다.
- 기대: `NO_TRADE` 비율 높음.

### F3. Smooth Uptrend

- 작은 노이즈를 가진 지속 상승.
- 기대: warm-up 이후 빠르게 `TRADE_ALLOWED`.

### F4. Smooth Downtrend

- 지속 하락.
- 방향과 무관한 tradeability detector라면 F3와 대칭적인 허가 성능을 보여야 한다.

### F5. Range -> Breakout -> Trend

세 구간을 명시한다.

```text
RANGE        [0..A)
BREAKOUT     [A..B)
TREND        [B..end)
```

가장 중요한 fixture.

측정:
- RANGE에서 false positive entry permission
- breakout 후 허가까지 지연 bar 수
- 허가 후 다시 range로 잘못 복귀하는 횟수

### F6. Trend -> Exhaustion -> Range

추세 종료 후 장비가 언제 진입금지로 복귀하는지 측정한다.

### F7. Fake Breakout

- range 상단 잠깐 돌파 후 즉시 복귀.
- 기대: 즉시/과도한 permission을 최소화.

### F8. Gap Shock + Range

- 큰 gap/1회 shock 후 횡보.
- ADX/VHF가 shock 때문에 장시간 추세로 오인하는지 시험.

### F9. Low-volatility Trend

- 변동성은 낮지만 꾸준한 진행.
- compression 센서가 이를 횡보로 잘못 차단하는지 시험.

### F10. Volatile Trend

- 큰 진폭을 동반하지만 순방향 진행.
- wide range 자체를 횡보로 오인하면 실패.

---

## 5. 평가 Metric

### M1. Range Block Rate

정답 range 구간에서:

```text
blocked_range_bars / labeled_range_bars
```

높을수록 좋다.

### M2. Trend Allow Rate

정답 trend 구간에서:

```text
allowed_trend_bars / labeled_trend_bars
```

높을수록 좋다.

### M3. Breakout Release Delay

실제 breakout/trend 시작 bar 이후 `trade_permitted=true`가 안정적으로 발생할 때까지 bar 수.

낮을수록 좋다.

### M4. False Release Count

range 중 permission이 켜졌다가 다시 꺼지는 episode 수.

사람이 횡보 중 여러 번 매수하게 만드는 핵심 위험이므로 낮을수록 좋다.

### M5. Gate Churn

`trade_permitted` boolean 상태 전환 횟수.

너무 높으면 장비 자체가 새로운 whipsaw source가 된다.

### M6. Strategy Suppression Benefit

기준 전략(예: SMA crossover)을 동일 fixture에 실행해:

```text
baseline entries
vs
gated entries
```

그리고 range 구간 entry 수가 얼마나 감소했는지 측정한다.

중요: 이 metric은 detector가 전략 신호를 계산한다는 뜻이 아니다. 기존 `entry_gate` 효과를 평가하기 위한 소비자 시험이다.

### M7. Trend Opportunity Loss

기준 전략에서 trend 구간에 발생한 유효 진입 후보 중 gate가 차단한 비율.

낮을수록 좋다.

### M8. Determinism / Prefix Parity

동일 입력에서:
- batch 결과
- streaming/prefix 결과

의 확정 bar permission이 완전히 같아야 한다.

### M9. Lookahead Safety

미래 bar를 추가해도 과거 확정 `trade_permitted` 결과가 변하면 FAIL.

---

## 6. 합격 기준

정확한 수치 threshold는 경쟁시험 결과 전에 고정하지 않는다. 다만 다음은 hard gate다.

1. M8 determinism/prefix parity: 100% 동일.
2. M9 lookahead safety: 과거 결과 변경 0건.
3. F2 Wide Choppy Range와 F9 Low-volatility Trend를 동시에 구분하지 못하는 후보는 단독 표준 장비로 채택하지 않는다.
4. F5에서 breakout release가 지나치게 늦는 후보는 단독 hard gate로 채택하지 않는다.
5. 단일 종목/단일 fixture에서만 우수한 threshold는 채택하지 않는다.
6. threshold는 가격 단위 절대값보다 가능한 한 정규화된 값으로 정의한다. 예외는 명시적으로 사용자가 요구한 장비 절대기준선이다.

---

## 7. 첫 경쟁 Matrix

| 후보 | 왕복 Range | Wide Choppy | Low-vol Trend | Breakout 속도 | 설명 가능성 | 현재 구현 재사용 |
|---|---:|---:|---:|---:|---:|---:|
| VHF | 높음 기대 | 높음 기대 | 중~높음 기대 | 중간 | 높음 | YES |
| ADX | 중간 | 중간 | 위험 | 느릴 수 있음 | 높음 | YES |
| normalized range | 중간 | 낮음 위험 | 낮음 위험 | 빠름 | 높음 | YES (조합 필요) |
| JMA abs slope | 높음 기대 | 중~높음 | 높음 기대 | parameter 의존 | 매우 높음 | YES |
| volatility compression | 중간 | 낮음 위험 | 낮음 위험 | 빠름 | 높음 | YES |

이 표는 가설이며 PASS 판정이 아니다.

---

## 8. 권장 첫 구현 형태

새 DSL grammar/function을 추가하지 않고 먼저 **독립 Equipment**로 구현한다.

```text
OHLCV
  -> RangeDetectorEquipment
       - vhf
       - adx
       - normalized_range
       - jma_abs_slope
       - trade_permitted
       - reason_code
  -> BacktestEngine.entry_gate
  -> existing DSL strategy
```

Chart는 동일 output을 보조 pane/하단 장비로 표시할 수 있으나 계산 권한은 장비 구현 한 곳에 둔다.

### 금지

- Chart가 자체 threshold 판단
- DSL strategy마다 detector 수식 복제
- BacktestEngine 내부에 VHF/JMA 의미 하드코딩
- 학습 모델이 threshold를 런타임에서 임의 변경

---

## 9. 다음 구현 tranche

1. `RangeDetectorEquipment` pure deterministic evaluator
2. F1~F10 deterministic fixtures
3. 후보 단독 경쟁 test
4. metric report 생성
5. 결과를 보고 조합 2~3개만 선정
6. `entry_gate` 연결 테스트
7. 이후 실제 KOSPI/KOSDAQ 구간 WYSIWYG 검증

실제 시장 구간에서 좋게 보인다는 이유로 fixture/test 기준을 사후 변경하지 않는다.
