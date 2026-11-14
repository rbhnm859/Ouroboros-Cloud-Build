"""V74-R17 native-tick minute reference oracle (corrected forward semantics).

Mirrors V74R17TickMinute.Add / FilledBinMid / Features in
HarmonyBot-V71/src/Architecture/HarmonyBotV74.R17TickState.cs so the tick
time-direction correction can be verified by executable golden fixtures and
property tests on every CI run, without a .NET test project.

The accumulator is defined ONLY for an oldest-to-newest feed. Feeding it
newest-to-oldest is reproduced here on purpose (TICK_ORDER_LEGACY) so the
corruption it caused stays pinned as a regression control:
  * dt = max(0, timeUtc - LastTime) collapses to 0 for every interior tick
    (SumDt / SumDtSq / MaxDt die, feature channels 1,2,3 become constants)
  * FirstMid / LastMid swap, inverting channels 4,7,9 and every bin channel
  * Up / Down and MaxUpRun / MaxDownRun swap
  * BinLastMid keeps the earliest tick of each bin instead of the latest
"""
import datetime as dt
import math

MINUTES = 12
BINS = 8
CHANNELS = 28
STATIC = 9
TICK_ORDER_FORWARD = 'FORWARD'
TICK_ORDER_LEGACY = 'REVERSED_LEGACY'


class TickMinute:
    def __init__(self, open_utc):
        self.open = open_utc
        self.count = 0
        self.first_time = None
        self.last_time = None
        self.first_mid = 0.0
        self.last_mid = 0.0
        self.min_mid = math.inf
        self.max_mid = -math.inf
        self.sum_dt = 0.0
        self.sum_dt_sq = 0.0
        self.max_dt = 0.0
        self.path = 0.0
        self.sq_move = 0.0
        self.sum_spread = 0.0
        self.sum_spread_sq = 0.0
        self.max_spread = 0.0
        self.up = 0
        self.down = 0
        self.flat = 0
        self.reversals = 0
        self.last_direction = 0
        self.current_run = 0
        self.max_up_run = 0
        self.max_down_run = 0
        self.last_bid = 0.0
        self.last_ask = 0.0
        self.bid_only = 0
        self.ask_only = 0
        self.both = 0
        self.bin_count = [0] * BINS
        self.bin_last_mid = [0.0] * BINS
        self.bin_seen = [False] * BINS

    def add(self, time_utc, bid, ask, pip):
        mid = (bid + ask) * .5
        spread = max(0.0, ask - bid)
        if not (math.isfinite(mid) and math.isfinite(spread)):
            return
        if self.count == 0:
            self.first_time = time_utc
            self.last_time = time_utc
            self.last_bid = bid
            self.last_ask = ask
            self.first_mid = mid
            self.last_mid = mid
            self.min_mid = mid
            self.max_mid = mid
        else:
            dtime = max(0.0, (time_utc - self.last_time).total_seconds())
            self.sum_dt += dtime
            self.sum_dt_sq += dtime * dtime
            self.max_dt = max(self.max_dt, dtime)
            move = mid - self.last_mid
            self.path += abs(move)
            self.sq_move += move * move
            eps = max(pip * .01, 1e-12)
            direction = 1 if move > eps else (-1 if move < -eps else 0)
            if direction > 0:
                self.up += 1
            elif direction < 0:
                self.down += 1
            else:
                self.flat += 1
            if direction != 0:
                if self.last_direction != 0 and direction != self.last_direction:
                    self.reversals += 1
                if direction == self.last_direction:
                    self.current_run += 1
                else:
                    self.current_run = 1
                if direction > 0:
                    self.max_up_run = max(self.max_up_run, self.current_run)
                else:
                    self.max_down_run = max(self.max_down_run, self.current_run)
                self.last_direction = direction
            bid_changed = abs(bid - self.last_bid) > eps
            ask_changed = abs(ask - self.last_ask) > eps
            if bid_changed and ask_changed:
                self.both += 1
            elif bid_changed:
                self.bid_only += 1
            elif ask_changed:
                self.ask_only += 1
            self.last_time = time_utc
            self.last_bid = bid
            self.last_ask = ask
            self.last_mid = mid
            self.min_mid = min(self.min_mid, mid)
            self.max_mid = max(self.max_mid, mid)
        self.sum_spread += spread
        self.sum_spread_sq += spread * spread
        self.max_spread = max(self.max_spread, spread)
        sec = (time_utc - self.open).total_seconds()
        index = max(0, min(BINS - 1, int(math.floor(sec / (60.0 / BINS)))))
        self.bin_count[index] += 1
        self.bin_last_mid[index] = mid
        self.bin_seen[index] = True
        self.count += 1

    def filled_bin_mid(self):
        x = [0.0] * BINS
        first = self.first_mid
        for i in range(BINS):
            if self.bin_seen[i]:
                first = self.bin_last_mid[i]
                x[i] = first
            else:
                x[i] = first
        for i in range(BINS - 2, -1, -1):
            if not self.bin_seen[i] and i == 0:
                x[i] = self.first_mid
        return x

    def features(self, atr, pip):
        atr = max(pip, atr)
        moves = max(1, self.count - 1)
        mean_dt = self.sum_dt / moves if moves > 0 else 0.0
        var_dt = max(0.0, self.sum_dt_sq / moves - mean_dt * mean_dt) if moves > 1 else 0.0
        spread_mean = self.sum_spread / self.count if self.count > 0 else 0.0
        spread_var = max(0.0, self.sum_spread_sq / self.count - spread_mean * spread_mean) if self.count > 1 else 0.0
        directional = max(1, self.up + self.down)
        imbalance = (self.up - self.down) / directional
        bin_mean = sum(self.bin_count) / BINS
        bin_var = sum((v - bin_mean) * (v - bin_mean) for v in self.bin_count) / BINS
        early = self.bin_count[0] + self.bin_count[1]
        late = self.bin_count[BINS - 2] + self.bin_count[BINS - 1]
        activity_tilt = (late - early) / max(1, late + early)
        bins = self.filled_bin_mid()
        f = [
            math.log(1.0 + self.count),
            mean_dt / 60.0,
            (math.sqrt(var_dt) / max(.05, mean_dt)) if max(.05, mean_dt) > 0 else 0.0,
            self.max_dt / 60.0,
            (self.last_mid - self.first_mid) / atr,
            (self.max_mid - self.min_mid) / atr,
            self.path / atr,
            (self.last_mid - self.first_mid) / max(pip, self.path),
            math.sqrt(max(0.0, self.sq_move)) / atr,
            imbalance,
            self.reversals / directional,
            self.max_up_run / max(1, self.count),
            self.max_down_run / max(1, self.count),
            spread_mean / atr,
            self.max_spread / atr,
            math.sqrt(spread_var) / max(pip, spread_mean),
            self.bid_only / max(1, self.count),
            self.ask_only / max(1, self.count),
            math.sqrt(bin_var) / max(1.0, bin_mean),
            activity_tilt,
        ]
        for i in range(BINS):
            f.append((bins[i] - self.first_mid) / atr)
        if len(f) != CHANNELS or not all(math.isfinite(v) for v in f):
            raise ValueError('R17_TICK_FEATURE_CONTRACT')
        return f


def accumulate(series, open_utc, pip, order=TICK_ORDER_FORWARD):
    """series: iterable of (seconds_after_open, bid, ask)."""
    if order not in (TICK_ORDER_FORWARD, TICK_ORDER_LEGACY):
        raise ValueError('R17 unknown tick order')
    items = list(series)
    if order == TICK_ORDER_LEGACY:
        items = list(reversed(items))
    minute = TickMinute(open_utc)
    for sec, bid, ask in items:
        minute.add(open_utc + dt.timedelta(seconds=sec), bid, ask, pip)
    return minute


def forward_window(ticks, open_utc, end_utc, pip):
    """ticks: ascending list of (datetime_utc, bid, ask); selects [open,end)."""
    minute = TickMinute(open_utc)
    previous = None
    for t, bid, ask in ticks:
        if t < open_utc:
            continue
        if t >= end_utc:
            break
        if previous is not None and t < previous:
            raise ValueError('R17_TICK_TIME_DIRECTION')
        previous = t
        minute.add(t, bid, ask, pip)
    return minute
