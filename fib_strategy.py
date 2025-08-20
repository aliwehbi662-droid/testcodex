# fib_strategy.py
import backtrader as bt

class FibRetrace(bt.Strategy):
    params = dict(
        lookback=60,          # bars to search for swing high/low
        risk_per_trade=0.01,  # 1% of equity risked per trade
        target='extension',   # 'extension' or 'swing'
        retrace=0.618,        # trigger level
        stop_level=0.786      # stop beyond deeper retrace
    )

    def __init__(self):
        self.stop_price = None
        self.take_profit = None

    def _swing(self):
        """Return (trend_is_up, low, high) based on most recent swing within lookback."""
        if len(self.data) < self.p.lookback:
            return None

        highs = list(self.data.high.get(size=self.p.lookback))
        lows  = list(self.data.low.get(size=self.p.lookback))

        hh = max(highs); hh_idx = highs.index(hh)   # 0 = oldest
        ll = min(lows);  ll_idx = lows.index(ll)

        trend_up = hh_idx > ll_idx  # last extreme is the high => uptrend swing (low -> high)
        low, high = ll, hh
        return trend_up, low, high

    def _position_size(self, entry, stop):
        risk = abs(entry - stop)
        if risk <= 0:
            return 0
        cash = self.broker.getcash()
        # size in asset units
        size = (cash * self.p.risk_per_trade) / risk
        return max(0, size)

    def next(self):
        swing = self._swing()
        if not swing:
            return

        c = float(self.data.close[0])
        trend_up, low, high = swing
        rng = high - low
        if rng <= 0:
            return

        if trend_up:
            lvl_retrace = high - self.p.retrace * rng       # e.g., 61.8% pullback
            lvl_stop    = high - self.p.stop_level * rng     # deeper, e.g., 78.6%
            tp = (high + 0.618 * rng) if self.p.target == 'extension' else high

            if not self.position:
                # Entry on cross back above the retrace level (bounce)
                if self.data.close[-1] < lvl_retrace <= c:
                    size = self._position_size(c, lvl_stop)
                    if size > 0 and lvl_stop < c:
                        self.buy(size=size)
                        self.stop_price = lvl_stop
                        self.take_profit = tp
            else:
                if c <= self.stop_price:
                    self.close()
                elif c >= self.take_profit:
                    self.close()

        else:
            # Downtrend swing (high -> low). Mirror logic for shorts.
            lvl_retrace = low + self.p.retrace * rng
            lvl_stop    = low + self.p.stop_level * rng
            tp = (low - 0.618 * rng) if self.p.target == 'extension' else low

            if not self.position:
                # Entry on cross back below the retrace level (pullback sell)
                if self.data.close[-1] > lvl_retrace >= c:
                    size = self._position_size(c, lvl_stop)
                    if size > 0 and lvl_stop > c:
                        self.sell(size=size)
                        self.stop_price = lvl_stop
                        self.take_profit = tp
            else:
                if c >= self.stop_price:
                    self.close()
                elif c <= self.take_profit:
                    self.close()
