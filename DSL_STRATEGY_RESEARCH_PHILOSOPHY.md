# DSL Strategy Research Philosophy

Status: **ACTIVE DESIGN AUTHORITY / STRATEGY RESEARCH / 2026-08-31 KST**

이 문서는 DSL을 단순한 지표 호출 언어가 아니라, **검증된 Core를 오염시키지 않으면서 새로운 수익 전략을 반복적으로 만들고 비교할 수 있는 전략 연구 언어**로 발전시키기 위한 현재 철학을 고정한다.

## 1. 궁극적 목표

목표는 하나의 좋은 전략을 Core에 하드코딩하는 것이 아니다.

```text
좋은 종목을 먼저 고른다
 -> 전략이 사용할 측정값을 DSL로 자유롭게 조합한다
 -> 신호 수를 줄이고 고품질 진입만 남긴다
 -> 차트에서 왜 허용/차단됐는지 눈으로 검증한다
 -> 별도 Strategy CRUD에서 새 전략으로 버전 관리한다
 -> 여러 종목/날짜/timeframe에서 재검증한다
```

DSL은 전략을 결정하지 않는다. **전략가가 원하는 조합을 제한 없이 표현할 수 있게 하는 것이 DSL의 책임**이다.

## 2. 절대 보존할 Baseline

현재 차트에 정상 삽입된 기본 `ta.macd` 교차 전략은 **Baseline**이다.

```text
MACD_BASELINE_V1
```

이 Baseline은 파라미터 튜닝이나 예외 조항으로 덮어쓰지 않는다. 기본 DSL Feature Catalog의 예제는 기능 검증 SSOT이며, 수익전략 연구를 위해 직접 수정하지 않는다.

새 전략은 반드시 별도 Strategy CRUD에서 생성한다.

```text
Feature Catalog = DSL 기능 검증 / 기준선 / 불변
Strategy CRUD   = 전략 실험 / 복제 / 버전 / 삭제 / 비교
```

기존 globally validated Core 로직에 특정 종목, 특정 venue, 특정 timeframe, 특정 전략만을 위한 예외 분기를 삽입하지 않는다. 기존 로직 변경이 필요하다면 전체 입력/실행 경로에 균일하게 적용되는 일반 계약이어야 한다.

## 3. 전략 개선의 3개 층

### A. 기존 DSL 조합만으로 개선

가장 먼저 현재 DSL로 표현 가능한 조합을 사용한다.

예:

```text
MACD crossover
AND close > EMA120
AND normalized_histogram >= H
AND/OR JMA normalized slope >= J
AND session/day position condition
```

파라미터, 비교, 산술, AND/OR/NOT, crossover, 상태, risk/exit 등을 Strategy CRUD에서 바꾼다. Core와 지표 구현은 건드리지 않는다.

### B. 새로운 측정값이 필요할 때만 additive User Indicator 추가

기존 DSL 조합으로 표현할 수 없고 새로운 **측정값** 자체가 부족할 때만 새 사용자지표를 추가한다.

이미 확보된 예:

```text
user.macd_normalized(...)
  - macd
  - signal
  - hist
  - hist_abs_pct

session.day_return_pct()
```

새 지표는 시장 상태를 숫자로 반환해야 하며, 매매전략 자체를 내부에 숨기면 안 된다.

좋은 구조:

```text
Indicator -> 측정값 반환
DSL       -> 측정값 비교/조합
Strategy  -> threshold, AND/OR, trigger, permission 결정
```

### C. 전략 시스템 수준 확장

필요가 실제로 확인될 때만 다음을 별도 계층으로 확장한다.

```text
Universe / cross-sectional selection
Permission / hard gate
Market / sector / symbol context
Execution
Risk / sizing
```

이 기능들도 가능한 한 Core에 전략 의미를 박지 않고 일반적인 입력·정렬·필터·순위·계산 능력으로 제공한다.

## 4. 파라미터 무한탐색보다 차트 계측을 우선한다

특정 구간의 손실 신호를 없애기 위해 MACD 12/26/9를 계속 바꾸는 방식은 과최적화 위험이 크다.

현재 철학은 다음 순서를 우선한다.

```text
차트에서 반복 손실/수익 구조 관찰
 -> 원인을 설명할 수 있는 측정값 확인
 -> 정규화된 값과 후보 threshold를 차트에 표시
 -> 수평선/required line과 실제 series를 눈으로 비교
 -> 가설 수립
 -> 새 Strategy CRUD 생성
 -> 다른 종목/날짜/timeframe에서 재검증
 -> 그 후에만 백테스트/parameter search 확대
```

차트는 단순 결과 표시기가 아니라 **전략 개발 계측기**다.

## 5. Normalized MACD Histogram의 역할

Raw MACD Histogram은 가격대가 다른 종목끼리 직접 비교하기 어렵다.

현재 사용자지표의 핵심 관측값:

```text
hist_abs_pct = abs(MACD - Signal) / abs(Close) * 100
```

이 값은 가격 단위를 제거한 공통 척도로 사용한다. 초기 목적은 다음 두 가지다.

```text
1. 동일 종목의 과거 수익/손실 구간에서 momentum strength 비교
2. 가격대가 다른 종목 간 momentum strength 비교
```

`0.5` 같은 값은 현재 **후보 수평선**일 뿐 최종 상수가 아니다. 차트에서 여러 종목/날짜를 보며 수익구간 레벨과 잡음구간 레벨을 관찰한 후 전략 threshold 후보로 승격한다.

정확한 진입시점에서 Histogram을 어떤 봉의 값으로 평가할지, 현재값/최근값/확장속도 중 무엇을 사용할지는 미결정이다. 차트 관찰과 실제 데이터 검증 없이 먼저 하드코딩하지 않는다.

## 6. JMA strength와의 조합

현재 사용하는 JMA 계열에서 전략이 활용하고자 하는 관측값은 다음 세 종류다.

```text
상승추세 값
하락추세 값
정규화된 slope strength
```

특히 세 번째 slope strength는 정규화된 추세 강도 후보다.

전략은 다음 조합을 모두 표현할 수 있어야 한다.

```text
MACD crossover AND hist_strength >= H
MACD crossover AND jma_strength >= J
MACD crossover AND (hist_strength >= H OR jma_strength >= J)
MACD crossover AND hist_strength >= H AND jma_strength >= J
```

어느 조합이 좋은지는 Core가 정하지 않는다. Strategy CRUD가 결정하고 차트/백테스트가 검증한다.

## 7. Position과 동적 required strength

`session.day_return_pct()`는 현재 공급된 OHLCV에서 당일 시가 대비 위치를 범용적으로 반환한다.

Position을 쓰게 되면 고정 수평선 하나보다 **required strength series**가 더 적합할 수 있다.

예:

```text
actual_hist_strength
required_hist_strength(position)

actual >= required -> permission
actual <  required -> block
```

Position 가중치/구간은 아직 연구 대상이다. 특정 +3%, +7%, +10% 구간을 코드에 먼저 박지 않는다.

## 8. 차트 관측성 계약

전략 판단에 사용한 값은 차트가 다시 계산하면 안 된다.

```text
DSL/Runtime 계산
 -> MACD
 -> Signal
 -> Histogram
 -> normalized Histogram
 -> JMA strength
 -> position pct
 -> required threshold
 -> permission bool
 -> trigger/result
        ↓
Chart는 동일 값을 그대로 표시
```

차트에서 필요한 기본 표현:

```text
indicator series
normalized strength series
고정 threshold 수평선
동적 required-strength line
ALLOW / BLOCK / BUY / SELL marker
```

이 원칙 덕분에 차트에 보이는 이유와 Backtest/실전 DSL 판단 이유가 동일해진다.

## 9. 장기 Universe 방향

궁극적인 전략 방향은 단일 종목 내부 신호만이 아니다.

예상 흐름:

```text
지수 고베타 종목
주도섹터 / 대장주 / 추종종목 관계
Close > EMA120
Normalized Histogram strength/rank
기타 상대강도/자금흐름
        ↓
선별된 강세 후보
        ↓
MACD + JMA + normalized strength로 2~3회의 고품질 진입
```

따라서 장기적으로는 다음 두 영역을 구분한다.

```text
DSL SYMBOL   = 한 종목 내부의 indicator/trigger/permission/execution
DSL UNIVERSE = 여러 종목 사이의 filter/rank/top-N/relative selection
```

Universe 기능은 필요가 실제로 확인된 뒤 일반적인 cross-sectional 기능으로 설계한다. 현재 전략 연구를 이유로 성급하게 복잡한 Universe 언어를 만들지 않는다.

## 10. Timeframe 권한

등록 Feature Catalog의 `timeframe = "1d"`는 예제/fixture 기본값일 뿐 차트 실행의 고정 제약이 아니다.

차트에 DSL을 삽입할 때 실행 timeframe authority는 **현재 차트 timeframe**이다.

```text
1분 차트  -> DSL 1m
5분 차트  -> DSL 5m
15분 차트 -> DSL 15m
일봉 차트 -> DSL 1d
```

특정 timeframe 예외를 Core에 넣지 않는다.

## 11. 전략 연구 Workflow

새 아이디어는 다음 순서를 따른다.

```text
1. Baseline 전략 동결
2. 차트에서 문제점 분류
3. 기존 DSL 조합으로 표현 가능한지 확인
4. 가능하면 새 Strategy CRUD만 생성
5. 불가능하면 부족한 일반 문법 vs 부족한 측정값을 구분
6. 측정값 부족이면 additive User Indicator 추가
7. 차트에 중간값/threshold/permission을 표시
8. 동일 종목 다른 구간 + 다른 종목 + 다른 timeframe에서 검증
9. 그 후 통계적/백테스트 검증
10. 채택/폐기/후속 버전을 Strategy CRUD에 기록
```

코딩은 로직이 결정된 후 한다. 연구되지 않은 threshold, range 의미, position weight를 Core에 먼저 고정하지 않는다.

## 12. 다음 개발 감사 항목

현재 즉시 확인할 것은 새 전략 코딩이 아니라 **DSL 조합 능력 audit**이다.

```text
- normalized Histogram 값을 전략이 직접 받을 수 있는가
- JMA의 상승/하락/slope strength를 각각 받을 수 있는가
- session.day_return_pct()를 받을 수 있는가
- 위 값들 간 + - * / 및 비교가 가능한가
- AND / OR / NOT으로 자유롭게 결합 가능한가
- threshold를 strategy parameter/input으로 변경 가능한가
- 전략 중간값과 threshold를 차트에 그대로 반환/표시 가능한가
- Strategy CRUD가 Feature Catalog와 완전히 분리되어 있는가
```

모두 가능하면 Core를 수정하지 않는다. 부족한 부분만 가장 작은 additive tranche로 보완한다.
