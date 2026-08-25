strategy "JMA_7_50_Cross" {
    timeframe = "1d"

    close_sma60 = ta.sma(close, 60)
    jma_fast = ta.jma(close, 7, 50, 2)
    jma_slow = ta.jma(close, 50, 50, 4)

    long_entry = close >= close_sma60 and ta.crossover(jma_fast, jma_slow)
    long_exit = ta.crossunder(jma_fast, jma_slow)
    short_entry = false
    short_exit = false

    on(long_entry) {
        order.buy(type = "MARKET")
    }

    on(long_exit) {
        order.close_long()
    }
}
