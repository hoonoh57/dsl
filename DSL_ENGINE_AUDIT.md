# Quant DSL 핵심 엔진 감사 및 DSL 2.0 기준

작성일: 2026-08-25

## 결론

현재 엔진은 SMA/JMA 교차 같은 단순 벡터 조건의 시제품으로는 동작하지만, LLM이 자유롭게 생성한 전략을 안전하게 수용하는 핵심 엔진으로는 부족하다. UI와 프롬프트 기능 확장보다 파서·실행 모델·주문 체결·지표 정합성 개선이 우선이다.

## 출시 차단 결함(P0)

1. **알 수 없는 문장을 조용히 무시한다.** 할당문으로 인식되지 않는 `if`, `for`, 오탈자, 잘못된 블록이 오류 없이 누락될 수 있다. 검증 성공이 전체 로직 실행을 의미하지 않는다.
2. **주문 블록이 문법적으로 검증되지 않는다.** `on(...) { ... }` 블록을 정규식으로 제거하고 표준 이름의 신호 배열만 읽는다. 주문 함수가 틀려도 결과가 성공할 수 있다.
3. **정규식은 중첩 블록과 완전한 문법을 처리할 수 없다.** 문자열, 주석, 괄호, 중첩 스코프에 대한 토큰화·구문 트리가 없다.
4. **시계열형과 스칼라형의 정적 타입 검사가 없다.** 숫자 조건, 불리언 지표, 다중 출력 함수의 오용이 런타임까지 미뤄진다.
5. **신호 계산과 체결 시점이 명시되지 않는다.** 종가를 이용해 같은 종가에 체결하는 현재 동작은 `process_on_close` 정책으로 선언되어야 하며, 기본 다음 봉 체결과 구분해야 한다.
6. **백테스트와 실시간 실행의 동일성 계약이 없다.** 열린 봉, 틱 업데이트, 확정 봉, 재계산/롤백 상태를 정의하지 않았다.

## 심각 결함(P1)

### 실행 모델

- 전체 배열을 한 번 계산하므로 상태 변수, 조건부 실행, 이벤트 순서, 체결 이후 재계산을 표현할 수 없다.
- `if/else`, 제한 반복, 사용자 함수, 준비→확인→실행 단계, cooldown, 연속 손실 상태가 없다.
- 워밍업/minimum period가 메타데이터로 관리되지 않는다.
- 동일 봉에서 long/short가 함께 발생하면 long이 암묵적으로 우선한다.
- 신호 지속과 신호 발생 edge를 언어 차원에서 구분하지 않는다.

### 주문·회계

- Market 외 Limit, Stop, StopLimit, 주문 취소·만료·OCO가 없다.
- 부분 체결, 부분 청산, 피라미딩, 다중 포지션, 주문 상태 수명주기가 없다.
- 손절·익절을 종가만으로 판정해 봉중 체결을 재현하지 못한다.
- 슬리피지는 진입에만 적용되고 청산에는 적용되지 않는다.
- 세금·수수료가 거래 방향과 체결 단계별로 정확히 모델링되지 않는다.
- 승률 분모가 진입 횟수이고 미청산 거래까지 포함해 통계가 왜곡될 수 있다.
- 체결 우선순위와 같은 봉 내 고가/저가 경로 가정이 없다.

### 시간과 데이터

- DSL의 `timeframe`과 사용자가 선택한 실제 데이터 주기가 일치하는지 검사하지 않는다.
- 멀티타임프레임/다중 종목 데이터 컨텍스트가 없다.
- 시간 정렬, 중복 봉, 결측 봉, 거래정지, 세션/휴장 검증이 없다.
- higher-timeframe 확정값과 진행 중 값의 lookahead/repainting 정책이 없다.

### 지표

- 공식 함수 목록에 비해 구현 범위가 매우 작다.
- ATR은 Wilder RMA가 아니라 EMA를 사용하므로 일반적인 TA-Lib/Pine 결과와 다를 수 있다.
- ADX도 해당 ATR/평활 방식 차이의 영향을 받는다.
- MACD가 signal/histogram 없는 단일 출력이다.
- BBANDS 구현은 있으나 런타임 함수 등록과 다중 출력 규칙이 없다.
- 각 지표에 시그니처, 출력형, lookback, NaN 정책, 증분 상태, 참조 구현 정보가 없다.
- Python 반복 rolling 구현은 지표 수와 기간 증가 시 확장성이 낮다.

## 벤치마크에서 채택할 기준

### TradingView Pine Script

- 데이터셋을 과거부터 현재까지 **bar-by-bar로 순차 실행**하고 매 봉 결과를 커밋한다.
- 실시간 열린 봉은 틱마다 다시 실행하며 확정 상태로 롤백하는 모델을 명시한다.
- 전략은 기본적으로 확정 봉에서 실행하되 tick/fill 재계산 정책을 선택할 수 있다.
- history reference, 조건 스코프, 사용자 함수, 반복, 타입 시스템을 언어 차원에서 정의한다.
- 다른 종목/주기의 데이터 요청과 repainting 위험을 명시적으로 다룬다.

### TA-Lib

- 지표를 cycle, momentum, overlap, pattern, statistic, volatility, volume 등으로 분류한다.
- 각 함수에 공식 입력·출력·수식·소스 연결을 제공한다.
- 다중 출력과 lookback을 함수 계약의 일부로 다룬다.

### Backtrader

- 지표의 minimum period가 전략 실행 가능 시점을 결정한다.
- `prenext`, `nextstart`, `next` 같은 수명주기와 주문·체결 알림을 분리한다.
- 주문은 생성 즉시 체결 결과가 아니라 식별자와 상태를 가진 객체다.

### QuantConnect LEAN

- 데이터 통합(consolidator), 지표 업데이트, 알고리즘 이벤트, 주문 처리를 분리한다.
- 여러 주문 유형과 체결 모델을 독립 계층으로 제공한다.
- 소비 데이터와 이벤트 처리량이 성능을 결정하므로 증분 계산을 기본으로 삼는다.

## DSL 2.0 필수 계층

1. **Lexer/Parser**: 정규식이 아닌 토큰·AST·소스 위치, 알 수 없는 문법 전면 거부.
2. **Semantic Analyzer**: 심볼, 함수 오버로드, 스칼라/series/condition/tuple/visual 타입 검사.
3. **Capability Registry**: 함수 시그니처, 카테고리, 출력, lookback, batch/incremental 구현, 참조 정합성.
4. **Bar Runtime**: 확정 봉과 실시간 tick, 상태 커밋/롤백, 이벤트 순서, 결정적 실행.
5. **Data Context**: symbol/timeframe/session, MTF 정렬, confirmed/unconfirmed 정책, lookahead 차단.
6. **Broker Emulator**: 주문 수명주기, 체결 정책, 비용, 부분체결, 우선순위, 포지션 회계.
7. **Visual Runtime**: plot/signal/color/line/box/zone를 계산 결과와 분리된 출력 계약으로 관리.
8. **Diagnostics**: lexer→parser→semantic→runtime→broker→visual 단계별 코드와 행·열·수정 힌트.
9. **Differential Tests**: TA-Lib/Pine/참조 소스와 고정 데이터셋 결과 비교.
10. **Compatibility Layer**: 기존 DSL 1.0을 AST로 변환하되 무시되는 문장이 없게 fail-closed 처리.

## 구현 우선순위

### Phase A — 신뢰 경계

- 모든 미인식 문법을 오류 처리
- 주문 블록 실제 파싱 및 검증
- 함수 레지스트리와 타입 검사
- timeframe/data 검증
- 미래 참조·비결정적 계산 차단

### Phase B — 정확성

- 참조 지표 정합성 테스트 세트
- 확정 봉/다음 봉 체결 모델
- 수수료·세금·슬리피지·손절/익절 회계 교정
- 거래 및 성과 통계 교정

### Phase C — 표현력

- 상태 변수, if/else, 제한 반복, 사용자 함수
- on_bar/on_tick/on_fill 이벤트
- MTF/다중 종목 컨텍스트
- plot/signal/line/box/zone 출력

### Phase D — 성능과 운영

- 지표 증분 상태와 공유 계산 DAG
- 데이터/지표 결과 캐시
- batch와 streaming 동일성 테스트
- fuzz/property/differential 테스트

## 통과 기준

- 어떤 소스 행도 실행되거나 명시적 오류가 나야 하며 조용히 무시되면 안 된다.
- 같은 입력·설정은 batch와 streaming에서 동일한 확정 봉 결과를 내야 한다.
- 공식 참조 지표와 합의된 허용오차 안에서 일치해야 한다.
- 모든 주문의 생성·접수·체결·취소·거절 이력을 재현할 수 있어야 한다.
- 미래 정보 사용 여부와 repainting 정책이 결과물 메타데이터에 기록되어야 한다.
- LLM Playbook은 구현·테스트에서 자동 생성되어 문서와 런타임이 어긋나지 않아야 한다.

## 구현 상태

- 2026-08-25: fail-closed AST 파서 도입. 미인식 문장, 중복 변수, 시장 데이터 덮어쓰기 차단.
- 2026-08-25: 주문 이벤트 AST와 지원 명령·인수 검증 도입. 백테스터가 파싱된 이벤트를 실행하도록 전환.
- 2026-08-25: boolean 이벤트 조건 검사, 동일 이벤트의 진입·청산 충돌 차단.
- 2026-08-25: `bar_close`/`next_open` 체결 정책, 동일 봉 재진입 차단, OHLC 손절·익절, 청산 슬리피지와 승률 계산 교정.
- 2026-08-25: scalar/series, number/boolean 정적 타입, 함수 arity와 input/event 타입 검증 도입.
- 2026-08-25: edge/cooldown/hold/persist/latch/count/regime 결정적 상태 연산과 batch/streaming prefix 동일성 테스트 도입.
- 2026-08-25: 일반 persistent `state`와 중첩 `on_bar if/else` 봉 단위 실행기 도입.
- 2026-08-25: 완료된 상위 봉만 정렬하는 비재도색 MTF 컨텍스트와 주말 간격 회귀 테스트 도입.
- 2026-08-25: MARKET/LIMIT/STOP/STOP_LIMIT 주문 객체, 접수·트리거·체결·OCO 취소·DAY 만료 및 백테스트 지연 체결 도입.
- 2026-08-25: Wilder RMA를 추가하고 ATR/RSI/ADX 평활을 참조 방식으로 교정.
- 남은 확장 과제: 부분 체결·피라미딩·다중 포지션, on_tick/on_fill 롤백, tuple 지표 출력, 제한 반복·사용자 함수, 전체 TA-Lib differential fixture.

## 참고한 공식 자료

- TradingView Pine execution model: https://www.tradingview.com/pine-script-docs/language/execution-model/
- TradingView strategies: https://www.tradingview.com/pine-script-docs/concepts/strategies/
- TradingView repainting: https://www.tradingview.com/pine-script-docs/concepts/repainting/
- TradingView other timeframes/data: https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/
- TA-Lib functions: https://ta-lib.org/functions/
- Backtrader strategy lifecycle: https://www.backtrader.com/docu/strategy/
- QuantConnect order types: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-types
