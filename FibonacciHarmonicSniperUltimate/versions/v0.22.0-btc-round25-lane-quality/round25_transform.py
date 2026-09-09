from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3:
    raise SystemExit('usage: round25_transform.py <round22.cs> <round25.cs>')
src=Path(sys.argv[1]); out=Path(sys.argv[2]); data=src.read_bytes()
expected='d103dce25851d89bd51cb736c14ae91f416927dedfc692a441f28115a3343029'
actual=hashlib.sha256(data).hexdigest()
if actual!=expected:
    raise SystemExit(f'Round22 source SHA mismatch: {actual}')
s=data.decode()

param_anchor='''        [Parameter("R22 M30 Sell Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 1.0, Group = "BTC Round22 Capital Efficiency")]
        public double Round22M30SellRiskPercent { get; set; }
'''
param_insert=param_anchor+'''
        [Parameter("R25 Lane Quality", DefaultValue = true, Group = "BTC Round25 Lane Quality")]
        public bool Round25LaneQuality { get; set; }

        [Parameter("R25 Window Trades", DefaultValue = 6, MinValue = 3, MaxValue = 12, Group = "BTC Round25 Lane Quality")]
        public int Round25WindowTrades { get; set; }

        [Parameter("R25 Min Samples", DefaultValue = 4, MinValue = 2, MaxValue = 10, Group = "BTC Round25 Lane Quality")]
        public int Round25MinSamples { get; set; }

        [Parameter("R25 Weak Mean R", DefaultValue = -0.05, MinValue = -1.0, MaxValue = 0.5, Step = 0.05, Group = "BTC Round25 Lane Quality")]
        public double Round25WeakMeanR { get; set; }

        [Parameter("R25 Strong Mean R", DefaultValue = 0.25, MinValue = 0.0, MaxValue = 1.5, Step = 0.05, Group = "BTC Round25 Lane Quality")]
        public double Round25StrongMeanR { get; set; }

        [Parameter("R25 Weak Risk Mult", DefaultValue = 0.60, MinValue = 0.25, MaxValue = 1.0, Step = 0.05, Group = "BTC Round25 Lane Quality")]
        public double Round25WeakRiskMultiplier { get; set; }

        [Parameter("R25 Strong Risk Mult", DefaultValue = 1.08, MinValue = 1.0, MaxValue = 1.25, Step = 0.01, Group = "BTC Round25 Lane Quality")]
        public double Round25StrongRiskMultiplier { get; set; }
'''
if param_anchor not in s: raise SystemExit('parameter anchor missing')
s=s.replace(param_anchor,param_insert,1)

state_anchor='''        private readonly List<Round9ShadowState> _round9Shadows = new List<Round9ShadowState>();
        private readonly Dictionary<string, PatternStats> _stats = new Dictionary<string, PatternStats>(StringComparer.OrdinalIgnoreCase);

        protected override void OnStart()
'''
state_insert='''        private readonly List<Round9ShadowState> _round9Shadows = new List<Round9ShadowState>();
        private readonly Dictionary<string, PatternStats> _stats = new Dictionary<string, PatternStats>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, Queue<double>> _round25LaneRs = new Dictionary<string, Queue<double>>(StringComparer.OrdinalIgnoreCase);

        protected override void OnStart()
'''
if state_anchor not in s: raise SystemExit('state anchor missing')
s=s.replace(state_anchor,state_insert,1)

s=s.replace('Print("VERSION v0.21.0-btc-round22-capital-efficiency");','Print("VERSION v0.22.0-btc-round25-lane-quality");',1)
print_anchor='''            Print("BTC Round22 Capital Efficiency | H1 Buy={0:F2}% H1 Sell={1:F2}% M30 Buy={2:F2}% M30 Sell={3:F2}%", Round22H1BuyRiskPercent, Round22H1SellRiskPercent, Round22M30BuyRiskPercent, Round22M30SellRiskPercent);
'''
print_insert=print_anchor+'''            Print("BTC Round25 Lane Quality | enabled={0} window={1} minSamples={2} weakMeanR={3:F2} strongMeanR={4:F2} weakMult={5:F2} strongMult={6:F2}", Round25LaneQuality, Round25WindowTrades, Round25MinSamples, Round25WeakMeanR, Round25StrongMeanR, Round25WeakRiskMultiplier, Round25StrongRiskMultiplier);
'''
if print_anchor not in s: raise SystemExit('print anchor missing')
s=s.replace(print_anchor,print_insert,1)

m30_old='''            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);
'''
m30_new='''            string round25Lane = m.Direction == TradeType.Buy ? "M30_BUY" : "M30_SELL";
            double baseRiskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);
            double riskPercent = round21Bypass ? baseRiskPercent : baseRiskPercent * Round25LaneRiskMultiplier(round25Lane);
'''
if m30_old not in s: raise SystemExit('m30 risk anchor missing')
s=s.replace(m30_old,m30_new,1)

h1_old='''            double riskPercent = direction == TradeType.Buy ? Round22H1BuyRiskPercent : Round22H1SellRiskPercent;
'''
h1_new='''            double baseRiskPercent = direction == TradeType.Buy ? Round22H1BuyRiskPercent : Round22H1SellRiskPercent;
            string round25Lane = direction == TradeType.Buy ? "H1_BUY" : "H1_SELL";
            double riskPercent = baseRiskPercent * Round25LaneRiskMultiplier(round25Lane);
'''
if h1_old not in s: raise SystemExit('h1 risk anchor missing')
s=s.replace(h1_old,h1_new,1)

helper_anchor='''        private double Round22CalculateH1Volume(double slPips, TradeType direction)
        {
'''
helpers=r'''        private string Round25LaneForClosedPosition(string name, TradeType direction)
        {
            if (string.IsNullOrWhiteSpace(name))
                return null;
            if (name.StartsWith("R21M30|", StringComparison.OrdinalIgnoreCase))
                return null;
            if (name.StartsWith("M30|", StringComparison.OrdinalIgnoreCase))
                return direction == TradeType.Buy ? "M30_BUY" : "M30_SELL";
            return direction == TradeType.Buy ? "H1_BUY" : "H1_SELL";
        }

        private void Round25RecordLaneResult(string lane, double r)
        {
            if (string.IsNullOrWhiteSpace(lane) || double.IsNaN(r) || double.IsInfinity(r))
                return;
            double clipped = Math.Max(-1.0, Math.Min(2.0, r));
            Queue<double> q;
            if (!_round25LaneRs.TryGetValue(lane, out q))
            {
                q = new Queue<double>();
                _round25LaneRs[lane] = q;
            }
            q.Enqueue(clipped);
            while (q.Count > Math.Max(3, Round25WindowTrades))
                q.Dequeue();
            double sum = 0.0;
            int wins = 0;
            foreach (double x in q)
            {
                sum += x;
                if (x > 0) wins++;
            }
            Print("[R25 LANE CLOSE] lane={0} r={1:F3} samples={2} meanR={3:F3} wins={4}", lane, clipped, q.Count, q.Count > 0 ? sum / q.Count : 0.0, wins);
        }

        private double Round25LaneRiskMultiplier(string lane)
        {
            if (!Round25LaneQuality || string.IsNullOrWhiteSpace(lane))
                return 1.0;
            Queue<double> q;
            if (!_round25LaneRs.TryGetValue(lane, out q) || q.Count < Math.Max(2, Round25MinSamples))
                return 1.0;
            double sum = 0.0;
            foreach (double x in q) sum += x;
            double meanR = sum / q.Count;
            double mult = 1.0;
            if (meanR <= Round25WeakMeanR)
                mult = Math.Max(0.25, Math.Min(1.0, Round25WeakRiskMultiplier));
            else if (meanR >= Round25StrongMeanR)
                mult = Math.Max(1.0, Math.Min(1.25, Round25StrongRiskMultiplier));
            Print("[R25 LANE RISK] lane={0} samples={1} meanR={2:F3} mult={3:F2}", lane, q.Count, meanR, mult);
            return mult;
        }

'''+helper_anchor
if helper_anchor not in s: raise SystemExit('helper anchor missing')
s=s.replace(helper_anchor,helpers,1)

closed_anchor='''            _round8InitialRiskPips.TryGetValue(p.Id, out initialRiskPips);
            _round8InitialTpPips.TryGetValue(p.Id, out initialTpPips);
            _round8MfePips.TryGetValue(p.Id, out mfePips);
            _round8MaePips.TryGetValue(p.Id, out maePips);

            if (Round9ShadowTpContinuation && initialRiskPips > 0 && args.Reason.ToString() == "TakeProfit")
'''
closed_insert='''            _round8InitialRiskPips.TryGetValue(p.Id, out initialRiskPips);
            _round8InitialTpPips.TryGetValue(p.Id, out initialTpPips);
            _round8MfePips.TryGetValue(p.Id, out mfePips);
            _round8MaePips.TryGetValue(p.Id, out maePips);

            if (initialRiskPips > 0)
            {
                string round25Lane = Round25LaneForClosedPosition(name, p.TradeType);
                if (!string.IsNullOrWhiteSpace(round25Lane))
                    Round25RecordLaneResult(round25Lane, p.Pips / initialRiskPips);
            }

            if (Round9ShadowTpContinuation && initialRiskPips > 0 && args.Reason.ToString() == "TakeProfit")
'''
if closed_anchor not in s: raise SystemExit('closed anchor missing')
s=s.replace(closed_anchor,closed_insert,1)

out.write_text(s)
sha=hashlib.sha256(out.read_bytes()).hexdigest()
expected25='a68107129546992d2c4e27bf01c5583c12912767af916050c072d52e3d1e24ba'
if sha!=expected25:
    raise SystemExit(f'Round25 source SHA mismatch: {sha}')
print(f'Round25 source verified: {sha}')
