# Quant DSL 공식 Playbook
문서 버전: 1.4.0

이 문서는 Quant DSL을 생성·수정하는 LLM에 전달하는 유일한 공식 학습자료다. 검증 전 결과는 저장된 적용본을 덮어쓰지 않는다.

## 결과물 분류
- `indicator`: 가격 또는 보조 영역에 표시하는 지표
- `signal`: 조건이 성립한 봉에 표시하는 신호
- `strength`: bullish, bearish, neutral 상태 또는 연속 강도
- `strategy`: 진입·청산 조건을 포함하는 실행 전략
- `drawing`: 추세선, 가격 박스, 영역, 오더블록 등 사용자형식

현재 실행기 1.0은 결과물을 `strategy` 컨테이너 안의 시계열과 조건으로 컴파일한다. drawing은 전용 렌더러 추가 전까지 경계 시계열과 신호로 표현한다.

## 문법
```dsl
strategy "이름" {
    timeframe = "5m"
    변수 = 식
    state cooldown = 0
    on_bar {
        if (청산조건) {
            cooldown = 10
        } else {
            if (cooldown > 0) {
                cooldown = cooldown - 1
            }
        }
        진입허용 = cooldown == 0
    }
    조건 = 불리언_식
    on(조건) { order.buy(type = "MARKET") }
    on(조건) { order.close_long() }
    on(조건) { order.sell_short(type = "MARKET") }
    on(조건) { order.close_short() }
}
```
- 할당은 선언된 순서대로 계산한다.
- 지원 연산: `+ - * / % **`, 비교, `and`, `or`, `not`.
- 과거 봉은 `[0]` 이상의 정수만 허용하며 미래 데이터 참조는 금지한다.
- 설명용 의사코드, 생략 기호, 정의되지 않은 함수는 출력하지 않는다.
- 일반 수식은 벡터로 계산하며, 지속 상태와 `if/else`는 `state` 및 단일 `on_bar` 블록에서 봉 순서대로 실행한다.
- 무제한 `for/while`, 재귀, 사용자 함수 선언은 지원하지 않는다.
- 전체 DSL을 하나의 `dsl` 코드 블록으로 반환한다.
- 모든 문장은 파서가 이해해야 하며 미인식 문장은 검증 실패한다.
- 동일한 변수의 중복 선언과 시장 데이터 이름의 재할당은 금지한다.

## 표준 신호
`long_entry`, `long_exit`, `short_entry`, `short_exit`를 사용한다. 지표와 중간 조건은 의미 있는 변수명으로 선언한다.

## 타입 시스템

- `scalar<number>`: 기간, 배수, 임계값 같은 단일 숫자
- `scalar<bool>`: 단일 논리값
- `series<number>`: OHLCV와 지표처럼 봉마다 값이 있는 숫자 시계열
- `series<bool>`: 신호와 조건처럼 봉마다 참/거짓이 있는 시계열
- `input`에는 scalar만 할당할 수 있다.
- 산술·비교 함수에는 숫자형, `and/or/not`에는 boolean형만 사용한다.
- `on(...)`에는 `scalar<bool>` 또는 `series<bool>`만 사용할 수 있다.
- 함수별 인수 개수와 반환형은 Capability Manifest를 따라야 한다.
- `ta.value_when(0, condition, series)`의 `0`은 가장 최근 조건 발생값이며, 아직 발생하지 않은 구간은 `NaN`이다.

## 검증 규칙
1. 등록된 데이터와 함수만 사용한다.
2. 모든 변수는 사용 전에 선언한다.
3. 주문 조건은 불리언 또는 불리언 시계열이어야 한다.
4. 0 이하의 지표 기간을 사용하지 않는다.
5. 미래 참조, 외부 파일, 네트워크, 임의 코드 실행은 금지한다.
6. 기존 결과물을 수정할 때 사용자가 제거하라고 하지 않은 동작은 보존한다.
7. 현재 주문 명령은 `order.buy`, `order.sell_short`, `order.close_long`, `order.close_short`, `order.close_position`이다.
8. 진입 주문 유형은 `MARKET`, `LIMIT`, `STOP`, `STOP_LIMIT`이다. 가격 인수는 `limit`, `stop`, 수명은 `tif="GTC"|"DAY"`, 연동 취소는 `oco`를 쓴다.
9. `on` 조건은 반드시 boolean 또는 boolean series여야 한다.

## 실행 및 체결 정책

- `bar_close`: 확정된 현재 봉의 종가 신호를 현재 종가에 체결한다.
- `next_open`: 확정된 이전 봉의 신호를 다음 봉 시가에 체결한다.
- 같은 봉에서 포지션을 청산한 직후에는 다시 진입하지 않는다.
- 손절과 익절이 같은 OHLC 봉에서 모두 닿으면 보수적으로 손절이 먼저 발생한 것으로 처리한다.
- 슬리피지와 거래비용은 진입·청산 및 매수·매도 방향에 맞춰 반영한다.

## 상태와 cascading 조건

- `state.edge(condition)`: 조건이 false에서 true로 전환된 첫 봉만 true
- `state.falling_edge(condition)`: true에서 false로 전환된 첫 봉만 true
- `state.ready_after(trigger, bars)`: trigger 봉과 이후 지정 봉 동안 false
- `state.hold(condition, bars)`: 발생 조건을 이후 지정 봉 동안 유지
- `state.persist(condition, bars)`: 조건이 지정 봉 이상 연속 충족된 경우 true
- `state.latch(set_condition, reset_condition[, initial])`: set/reset 사이의 상태 기억
- `state.count(condition, reset_condition)`: reset 사이의 조건 발생 횟수
- `state.regime(bullish, bearish[, initial])`: bullish/bearish 조건에 따라 1/-1 상태 유지

상태 함수는 미래 값을 참조하지 않으며, 전체 batch 계산과 매 봉 streaming prefix 계산의 확정 봉 결과가 동일해야 한다. 복합 전략은 원시 조건→국면→준비→확인→재진입 제한→최종 신호 순서로 상태 함수를 조합한다.

## 멀티 타임프레임

- `mtf.open/high/low/close/volume("1d")`는 현재 진행 중인 상위 봉이 아니라 직전에 완료된 상위 봉만 반환한다.
- `mtf.sma("1d", 20)`도 완료된 상위 종가만 사용한다.
- lookahead/repainting 선택지는 제공하지 않으며 미래값 사용은 검증 실패 대상이다.

## 검증된 예제
```dsl
strategy "JMA_Filtered_Cross" {
    timeframe = "5m"
    sma60 = ta.sma(close, 60)
    fast = ta.jma(close, 7, 50, 2)
    slow = ta.jma(close, 50, 50, 4)
    strength = ta.adx(14)
    cooldown_ok = ta.bars_since(ta.crossunder(fast, slow)) > 10
    long_entry = close >= sma60 and strength > 20 and cooldown_ok and ta.crossover(fast, slow)
    long_exit = ta.crossunder(fast, slow)
    short_entry = false
    short_exit = false
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}
```

## 운영 오류 지식
- `지원하지 않는 함수`: Capability Manifest에 있는 대체 함수만 사용해 전체 DSL을 다시 작성한다.
- `정의되지 않은 변수`: 할당 순서를 바로잡고 사용 전 변수를 선언한다.
- `과거 참조 오류`: 음수 인덱스를 제거한다.
- 오류가 전달되면 기존 의도를 보존하면서 전체 DSL을 다시 반환한다.

## 변경 이력
- 1.4.0: 일반 `state`, 중첩 `on_bar if/else`, 확정값 전용 MTF, LIMIT/STOP/STOP_LIMIT 주문 수명주기, Wilder RMA/ATR/RSI/ADX 추가.
- 1.3.0: 결정적 상태 함수와 cascading 조건, batch/streaming prefix 동일성 규칙 추가.
- 1.2.0: scalar/series 및 number/boolean 정적 타입, 함수 arity, input 타입 검증 추가.
- 1.1.0: fail-closed AST 파서, 주문 이벤트 검증, 명시적 체결 정책과 회계 규칙 추가.
- 1.0.0: 최초 공식 문법, 결과물 분류, 검증 규칙, 운영 오류 지식 통합.
