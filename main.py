# main.py
import datetime as dt
import backtrader as bt
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from fib_strategy import FibRetrace

def fetch_df(ticker="AAPL", start="2018-01-01", end=None, interval="1d"):
    end = end or dt.date.today().isoformat()
    df = yf.download(ticker, start=start, end=end, interval=interval, auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError(f"No data for {ticker}")
    # yfinance sometimes returns timezone aware indices and multi-index columns
    if hasattr(df.index, 'tz_localize'):
        df.index = df.index.tz_localize(None)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df


def _swing_from_df(df: pd.DataFrame, lookback: int):
    """Return (trend_up, low, high) using a pandas DataFrame."""
    if len(df) < lookback:
        return None
    highs = df['High'].tail(lookback)
    lows = df['Low'].tail(lookback)
    hh = highs.max(); hh_idx = highs.idxmax()
    ll = lows.min();  ll_idx = lows.idxmin()
    trend_up = hh_idx > ll_idx
    low, high = float(ll), float(hh)
    return trend_up, low, high


def fib_levels(low: float, high: float, trend_up: bool):
    diff = high - low
    if diff <= 0:
        return {}
    if trend_up:
        return {
            "0.0": high,
            "0.236": high - 0.236 * diff,
            "0.382": high - 0.382 * diff,
            "0.5": high - 0.5 * diff,
            "0.618": high - 0.618 * diff,
            "0.786": high - 0.786 * diff,
            "1.0": low,
        }
    else:
        return {
            "0.0": low,
            "0.236": low + 0.236 * diff,
            "0.382": low + 0.382 * diff,
            "0.5": low + 0.5 * diff,
            "0.618": low + 0.618 * diff,
            "0.786": low + 0.786 * diff,
            "1.0": high,
        }


def multi_timeframe_analysis(ticker="AAPL", lookback=60):
    """Analyse 4H, 1H and 15m charts and plot Fibonacci levels."""
    # 60 days of data gives enough for 15m without hitting API limits
    start = (dt.date.today() - dt.timedelta(days=59)).isoformat()
    df15 = fetch_df(ticker, start=start, interval="15m")
    if df15.empty:
        raise RuntimeError("No 15m data")
    # Resample for higher timeframes
    agg = {
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }
    df1h = df15.resample('1H').agg(agg).dropna()
    df4h = df15.resample('4H').agg(agg).dropna()

    s4 = _swing_from_df(df4h, lookback)
    s1 = _swing_from_df(df1h, lookback)
    s15 = _swing_from_df(df15, lookback)

    if not all([s4, s1, s15]):
        raise RuntimeError("Not enough data to compute swings")

    aligned = s4[0] == s1[0] == s15[0]
    trend_up, low15, high15 = s15
    levels = fib_levels(low15, high15, trend_up)
    diff = high15 - low15
    entry = levels.get("0.618")
    stop = levels.get("0.786")
    tp = high15 + 0.618 * diff if trend_up else low15 - 0.618 * diff

    if aligned:
        print(f"Aligned trend {'up' if trend_up else 'down'}.")
        print(f"Entry: {entry:.2f}  Stop: {stop:.2f}  TP: {tp:.2f}")
    else:
        print("Trends do not align across timeframes")

    # Plot 15m chart with fibonacci levels and orders
    plt.figure(figsize=(12, 6))
    plt.plot(df15.index, df15['Close'], label='Close')
    for name, price in levels.items():
        plt.axhline(price, linestyle='--', alpha=0.5, label=name)
    plt.axhline(entry, color='green', linewidth=1.5, label='Entry')
    plt.axhline(stop, color='red', linewidth=1.5, label='Stop')
    plt.axhline(tp, color='blue', linewidth=1.5, label='TP')
    plt.title(f"{ticker} 15m Fibonacci")
    plt.legend(loc='best')
    plt.tight_layout()
    plt.savefig('fib_analysis.png')


def run(ticker="AAPL", cash=10000, commission=0.0005, lookback=60, timeframe="1d", start="2018-01-01"):
    df = fetch_df(ticker, start=start, interval=timeframe)
    data = bt.feeds.PandasData(dataname=df)

    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(FibRetrace, lookback=lookback, risk_per_trade=0.01, target='extension')
    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission=commission)
    # NOTE: position sizing is handled inside the strategy (risk-based)

    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"Final Portfolio Value:    {cerebro.broker.getvalue():.2f}")
    # Optional: plot locally
    # cerebro.plot()

if __name__ == "__main__":
    # Multi-timeframe Fibonacci analysis with plotting
    multi_timeframe_analysis(ticker="AAPL")
    # Backtest on 15m timeframe using the simple FibRetrace strategy
    run(ticker="AAPL", timeframe="15m", start=(dt.date.today() - dt.timedelta(days=59)).isoformat())
    # Example alternative: crypto intraday backtest (beware of gaps/slippage)
    # run(ticker="BTC-USD", timeframe="1h")
