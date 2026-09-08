#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil
from pathlib import Path

BASE_VERSION="Fibonacci-v0.12.0-btc-round10-funnel"
TARGET_VERSION="Fibonacci-v0.13.0-btc-round15-portfolio"
SOURCE_FILE="FibonacciHarmonicSniperUltimate.cs"

def ro(s,o,n,label):
    c=s.count(o)
    if c!=1: raise RuntimeError(f"{label}: expected 1 match, found {c}")
    return s.replace(o,n,1)

def build(root:Path, force=False):
    base=root/BASE_VERSION; target=root/TARGET_VERSION
    if not (base/SOURCE_FILE).is_file(): raise FileNotFoundError(base/SOURCE_FILE)
    if target.exists():
        if not force: raise FileExistsError(target)
        shutil.rmtree(target)
    shutil.copytree(base,target)
    p=target/SOURCE_FILE; s=p.read_text(encoding='utf-8')

    s=ro(s,'Print("VERSION v0.12.0-btc-round10-funnel");','Print("VERSION v0.13.0-btc-round15-portfolio");','version')

    pa='''        [Parameter("R10 Log Rejection Funnel", DefaultValue = true, Group = "BTC Round10 Funnel")]
        public bool Round10LogFunnel { get; set; }
'''
    pb=pa+'''
        [Parameter("R15 Enable M30 Frequency Engine", DefaultValue = true, Group = "BTC Round15 Portfolio")]
        public bool Round15EnableM30Engine { get; set; }
'''
    s=ro(s,pa,pb,'r15 parameter')

    fa='''        private readonly Dictionary<string, long> _round10Funnel = new Dictionary<string, long>(StringComparer.OrdinalIgnoreCase);
'''
    fb=fa+'''        private AverageTrueRange _r15M30Atr;
        private ExponentialMovingAverage _r15M30Ema;
        private DateTime _r15LastSeenM30OpenTime = DateTime.MinValue;
        private int _r15LastM30TradeClosedIndex = -1000000;
        private int _r15LastM30BullishDIndex = -1;
        private int _r15LastM30BearishDIndex = -1;
        private readonly HashSet<string> _r15M30ConsumedSignals = new HashSet<string>(StringComparer.Ordinal);
        private int _r15M30Opened;
        private int _r15M30BlockedOpenPosition;
        private int _r15M30BlockedLimits;
'''
    s=ro(s,fa,fb,'r15 fields')

    ta='''        protected override void OnTick()
        {
            if (Round9ShadowTpContinuation)
'''
    tb='''        protected override void OnTick()
        {
            Round15ProcessM30ClosedBar();

            if (Round9ShadowTpContinuation)
'''
    s=ro(s,ta,tb,'r15 tick hook')

    sa='''            Print("BTC Round10 Funnel | enabled={0} | diagnostics only; trading logic unchanged", Round10LogFunnel);
'''
    sb='''            _r15M30Atr = Indicators.AverageTrueRange(_barsM30, AtrPeriod, MovingAverageType.Exponential);
            _r15M30Ema = Indicators.ExponentialMovingAverage(_barsM30.ClosePrices, EmaPeriod);
            if (_barsM30 != null && _barsM30.Count > 0)
                _r15LastSeenM30OpenTime = _barsM30.OpenTimes.LastValue;
''' + sa + '''            Print("BTC Round15 Portfolio | H1 primary + M30 Reciprocal ABCD frequency engine={0} | shared equity/risk/MaxOpenPositions | H1 priority", Round15EnableM30Engine);
'''
    s=ro(s,sa,sb,'r15 startup')

    ma='''        private void UpdateRound9Shadows()
'''
    methods=r'''        private void Round15ProcessM30ClosedBar()
        {
            if (!Round15EnableM30Engine || !TradingEnabled || _barsM30 == null || _r15M30Atr == null || _r15M30Ema == null)
                return;
            if (_barsM30.Count < 110)
                return;

            DateTime currentOpen = _barsM30.OpenTimes.LastValue;
            if (currentOpen == _r15LastSeenM30OpenTime)
                return;

            // H1 owns exact hourly boundaries. Defer M30 one tick/minute so H1 cannot be displaced.
            if (Server.Time.Minute == 0)
                return;

            _r15LastSeenM30OpenTime = currentOpen;
            int lastClosed = _barsM30.Count - 2;
            if (lastClosed < 100)
                return;

            if (Server.Time.Date != _day)
                ResetDay();

            if (!Round15PassSharedLimits(lastClosed))
            {
                _r15M30BlockedLimits++;
                return;
            }

            PatternMatch best = Round15FindM30Pattern(lastClosed);
            if (best == null)
                return;
            if (!Round15PassM30Confirmation(best, lastClosed))
                return;

            Round15ExecuteM30(best, lastClosed);
        }

        private bool Round15PassSharedLimits(int lastClosed)
        {
            if (_tradesToday >= MaxTradesPerDay)
                return false;
            if (lastClosed - _r15LastM30TradeClosedIndex < 4)
                return false;

            int ownOpen = 0;
            foreach (var p in Positions)
                if (p.SymbolName == SymbolName && p.Label == BotLabel)
                    ownOpen++;
            if (ownOpen >= MaxOpenPositions)
            {
                _r15M30BlockedOpenPosition++;
                return false;
            }

            if (MaxDailyLossPercent > 0 && _dayStartEquity > 0)
            {
                double dd = 100.0 * (_dayStartEquity - Account.Equity) / _dayStartEquity;
                if (dd >= MaxDailyLossPercent)
                    return false;
            }

            double spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            if (MaxSpreadPips > 0 && spreadPips > MaxSpreadPips)
                return false;

            double atr = _r15M30Atr.Result[lastClosed];
            double atrPips = atr / Symbol.PipSize;
            if (MinAtrPips > 0 && atrPips < MinAtrPips)
                return false;
            return atr > 0;
        }

        private List<PivotPoint> Round15BuildM30Pivots(int lastClosed)
        {
            const int left = 2;
            const int right = 2;
            const int lookback = 500;
            var pivots = new List<PivotPoint>();
            int latestConfirmed = lastClosed - right;
            int first = Math.Max(left, lastClosed + 1 - lookback);
            for (int i = first; i <= latestConfirmed; i++)
            {
                bool isHigh = true, isLow = true;
                for (int j = 1; j <= left; j++)
                {
                    if (_barsM30.HighPrices[i] <= _barsM30.HighPrices[i-j]) isHigh = false;
                    if (_barsM30.LowPrices[i] >= _barsM30.LowPrices[i-j]) isLow = false;
                }
                for (int j = 1; j <= right; j++)
                {
                    if (_barsM30.HighPrices[i] <= _barsM30.HighPrices[i+j]) isHigh = false;
                    if (_barsM30.LowPrices[i] >= _barsM30.LowPrices[i+j]) isLow = false;
                }
                if (isHigh && !isLow)
                    AddAlternatingPivot(pivots, new PivotPoint(i, _barsM30.HighPrices[i], PivotKind.High));
                else if (isLow && !isHigh)
                    AddAlternatingPivot(pivots, new PivotPoint(i, _barsM30.LowPrices[i], PivotKind.Low));
            }
            const int maxPivots=80;
            if (pivots.Count>maxPivots) pivots=pivots.GetRange(pivots.Count-maxPivots,maxPivots);
            return pivots;
        }

        private PatternMatch Round15FindM30Pattern(int lastClosed)
        {
            var pivots = Round15BuildM30Pivots(lastClosed);
            if (pivots.Count < 5)
                return null;
            var candidates = new List<PatternMatch>();
            int firstWindow = Math.Max(0, pivots.Count - 20);
            for (int i=firstWindow; i<=pivots.Count-5; i++)
            {
                var x=pivots[i]; var a=pivots[i+1]; var b=pivots[i+2]; var c=pivots[i+3]; var d=pivots[i+4];
                TradeType? direction=GetDirection(x,a,b,c,d);
                if (!direction.HasValue) continue;
                int age=lastClosed-d.Index;
                if (age<0 || age>32) continue;
                if (direction==TradeType.Buy && d.Index==_r15LastM30BullishDIndex) continue;
                if (direction==TradeType.Sell && d.Index==_r15LastM30BearishDIndex) continue;

                double xa=Math.Abs(a.Price-x.Price), ab=Math.Abs(b.Price-a.Price), bc=Math.Abs(c.Price-b.Price), cd=Math.Abs(d.Price-c.Price);
                if (xa<=0 || ab<=0 || bc<=0 || cd<=0) continue;
                if (MinXaPips>0 && xa/Symbol.PipSize<MinXaPips) continue;
                double xb=ab/xa, ac=bc/ab, bd=cd/bc, xd=Math.Abs(a.Price-d.Price)/xa, cdAb=cd/ab;
                foreach (var def in _patterns)
                {
                    if (!def.Name.Equals("Reciprocal ABCD", StringComparison.OrdinalIgnoreCase)) continue;
                    double score=def.Score(xb,ac,bd,xd,cdAb,6.0);
                    if (score<84.0) continue;
                    var match=new PatternMatch(def,direction.Value,x,a,b,c,d,score,xb,ac,bd,xd,cdAb);
                    match.TrendAligned=Round15M30TrendAligned(match.Direction,lastClosed);
                    match.FinalScore=Math.Min(100.0,match.Score+(match.TrendAligned?5.0:0.0));
                    string key="M30|"+match.SignalKey;
                    if (_r15M30ConsumedSignals.Contains(key)) continue;
                    candidates.Add(match);
                }
            }
            if (candidates.Count==0) return null;
            var ordered=candidates.OrderByDescending(m=>m.FinalScore).ThenByDescending(m=>m.D.Index).ToList();
            PatternMatch best=ordered[0];
            PatternMatch opposite=ordered.FirstOrDefault(m=>m.Direction!=best.Direction && Math.Abs(m.D.Index-best.D.Index)<=32);
            if (opposite!=null && best.FinalScore-opposite.FinalScore<MinScoreAdvantage) return null;
            return best;
        }

        private bool Round15M30TrendAligned(TradeType direction, int lastClosed)
        {
            if (lastClosed < 1) return false;
            double close=_barsM30.ClosePrices[lastClosed];
            double ema=_r15M30Ema.Result[lastClosed];
            double prev=_r15M30Ema.Result[lastClosed-1];
            bool slopeUp=ema>prev, slopeDown=ema<prev;
            if (direction==TradeType.Buy) return close>ema && (!RequireEmaSlope || slopeUp);
            return close<ema && (!RequireEmaSlope || slopeDown);
        }

        private bool Round15PassM30Confirmation(PatternMatch m, int lastClosed)
        {
            double close=_barsM30.ClosePrices[lastClosed];
            double open=_barsM30.OpenPrices[lastClosed];
            double atr=_r15M30Atr.Result[lastClosed];
            if (atr<=0) return false;
            if (Math.Abs(close-m.D.Price)>atr*1.80) return false;
            if (m.Direction==TradeType.Buy)
            {
                if (close<m.D.Price+atr*0.05) return false;
                if (close<=open) return false;
            }
            else
            {
                if (close>m.D.Price-atr*0.05) return false;
                if (close>=open) return false;
            }
            return true;
        }

        private void Round15ExecuteM30(PatternMatch m, int lastClosed)
        {
            // Re-check position immediately before market order; both engines share the same label/account.
            foreach (var p in Positions)
                if (p.SymbolName==SymbolName && p.Label==BotLabel)
                {
                    _r15M30BlockedOpenPosition++;
                    return;
                }

            double atr=_r15M30Atr.Result[lastClosed];
            double entry=m.Direction==TradeType.Buy?Symbol.Ask:Symbol.Bid;
            double slPrice=m.Direction==TradeType.Buy?m.D.Price-atr*SlAtrBuffer:m.D.Price+atr*SlAtrBuffer;
            double slPips=Math.Abs(entry-slPrice)/Symbol.PipSize;
            if (slPips<MinStopPips) slPips=MinStopPips;
            if (MaxStopPips>0 && slPips>MaxStopPips) return;

            double tpPips=CalculateTakeProfitPips(m,entry,slPips);
            if (tpPips<slPips*MinimumRiskReward) tpPips=slPips*FallbackRiskReward;
            if (tpPips<slPips*MinimumRiskReward) return;
            double volume=CalculateVolume(slPips);
            if (volume<Symbol.VolumeInUnitsMin) return;

            string patternName="M30|"+m.Definition.Name;
            var result=ExecuteMarketOrder(m.Direction,SymbolName,volume,BotLabel,slPips,tpPips,patternName,false);
            if (!result.IsSuccessful || result.Position==null)
            {
                Print("[R15 M30 ORDER FAIL] {0} {1} error={2}",m.Definition.Name,m.Direction,result.Error);
                return;
            }
            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                Print("[R15 M30 PROTECTION FAIL] closing unprotected position");
                ClosePosition(result.Position);
                return;
            }

            _tradesToday++;
            _r15LastM30TradeClosedIndex=lastClosed;
            if (m.Direction==TradeType.Buy) _r15LastM30BullishDIndex=m.D.Index; else _r15LastM30BearishDIndex=m.D.Index;
            _r15M30ConsumedSignals.Add("M30|"+m.SignalKey);
            _positionPattern[result.Position.Id]=patternName;
            _round8InitialRiskPips[result.Position.Id]=slPips;
            _round8InitialTpPips[result.Position.Id]=tpPips;
            _round8MfePips[result.Position.Id]=0.0;
            _round8MaePips[result.Position.Id]=0.0;
            if (!_stats.ContainsKey(patternName)) _stats[patternName]=new PatternStats();
            _stats[patternName].Trades++;
            _r15M30Opened++;
            Print("[R15 M30 OPEN] {0} {1} score={2:F1}% volume={3} SL={4:F1}p TP={5:F1}p RR={6:F2}",m.Definition.Name,m.Direction,m.Score,volume,slPips,tpPips,tpPips/slPips);
        }

        private void UpdateRound9Shadows()
'''
    s=ro(s,ma,methods,'r15 methods')

    stop_anchor='''            foreach (var kv in _round10Funnel.OrderByDescending(k => k.Value).ThenBy(k => k.Key))
                Print("[R10 FUNNEL] {0}={1}", kv.Key, kv.Value);
'''
    stop_block=stop_anchor+'''            Print("[R15 STATS] m30Opened={0} m30BlockedOpenPosition={1} m30BlockedLimits={2}", _r15M30Opened, _r15M30BlockedOpenPosition, _r15M30BlockedLimits);
'''
    s=ro(s,stop_anchor,stop_block,'r15 stop')

    p.write_text(s,encoding='utf-8')
    cs=target/'FibonacciHarmonicSniperUltimate.csproj'
    if cs.is_file():
        t=cs.read_text(encoding='utf-8').replace('<Version>0.12.0-btc-round10-funnel</Version>','<Version>0.13.0-btc-round15-portfolio</Version>')
        cs.write_text(t,encoding='utf-8')
    return target

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path.cwd()); ap.add_argument('--force',action='store_true'); a=ap.parse_args(); print(build(a.repo_root.resolve(),a.force)); return 0
if __name__=='__main__': raise SystemExit(main())
