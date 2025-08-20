# Fibonacci Retracement Bot (Backtest)

A minimal backtesting harness for a Fibonacci-retracement strategy using Backtrader.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Multi-timeframe Fibonacci analysis

Run the example script to compute aligned Fibonacci levels on 4H, 1H and 15m charts.
The script saves a `fib_analysis.png` plot and performs a simple 15m backtest:

```bash
python main.py
```

