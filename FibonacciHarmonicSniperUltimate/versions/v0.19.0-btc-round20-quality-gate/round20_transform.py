from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: round20_transform.py <round19.cs> <round20.cs>')
s=Path(sys.argv[1]).read_text()
exp='c408a95259b791937a52490fe4472a1f1799edca53e87a4b4fedd08115484b98'
if hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()!=exp: raise SystemExit('Round19 SHA mismatch')
needle='''        [Parameter("R19 Aligned Buy Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Expansion")]
        public double Round19AlignedBuyRiskPercent { get; set; }
'''
insert=needle+'''
        [Parameter("R20 H1 Priority Handoff", DefaultValue = true, Group = "BTC Round20 Quality Gate")]
        public bool Round20H1PriorityHandoff { get; set; }

        [Parameter("R20 Max M30 Hold Minutes", DefaultValue = 60, MinValue = 30, MaxValue = 240, Step = 30, Group = "BTC Round20 Quality Gate")]
        public int Round20MaxM30HoldMinutes { get; set; }
'''
if needle not in s: raise SystemExit('param anchor missing')
s=s.replace(needle,insert,1)
s=s.replace('Print("VERSION v0.18.0-btc-round19-quality-expansion");','Print("VERSION v0.19.0-btc-round20-quality-gate");',1)
needle='''        protected override void OnTick()
        {
            Round15ProcessM30ClosedBar();
'''
repl='''        private void Round20EnforceH1PriorityHandoff()
        {
            if (!Round20H1PriorityHandoff)
                return;
            DateTime now = Server.Time;
            foreach (var p in Positions)
            {
                if (p.Label != BotLabel || p.SymbolName != SymbolName || string.IsNullOrEmpty(p.Comment) || !p.Comment.StartsWith("M30|", StringComparison.Ordinal))
                    continue;
                double heldMinutes = (now - p.EntryTime).TotalMinutes;
                bool maxHold = heldMinutes >= Round20MaxM30HoldMinutes;
                bool h1Boundary = now.Minute == 0 && heldMinutes >= 25.0;
                if (!maxHold && !h1Boundary)
                    continue;
                Print("[R20 H1 HANDOFF] pos={0} dir={1} heldMin={2:F1} boundary={3} maxHold={4}", p.Id, p.TradeType, heldMinutes, h1Boundary, maxHold);
                ClosePosition(p);
            }
        }

        protected override void OnTick()
        {
            Round20EnforceH1PriorityHandoff();
            Round15ProcessM30ClosedBar();
'''
if needle not in s: raise SystemExit('tick anchor missing')
s=s.replace(needle,repl,1)
out=Path(sys.argv[2]); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(s)
print(hashlib.sha256(out.read_bytes()).hexdigest())
