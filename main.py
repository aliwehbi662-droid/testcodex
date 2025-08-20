# main.py
import datetime as dt
import backtrader as bt
import yfinance as yf
from fib_strategy import FibRetrace

def fetch_df(ticker="AAPL", start="2018-01-01", end=None, interval="1d"):
    end = end or dt.date.today().isoformat()
    df = yf.download(ticker, start=start, end=end, interval=interval, auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError(f"No data for {ticker}")
    return df

def run(ticker="AAPL", cash=10000, commission=0.0005, lookback=60, timeframe="1d"):
    df = fetch_df(ticker, interval=timeframe)
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
    run(ticker="AAPL", timeframe="1d")
    # Try crypto intraday backtest (needs enough data; beware of gaps/slippage):
    # run(ticker="BTC-USD", timeframe="1h")
