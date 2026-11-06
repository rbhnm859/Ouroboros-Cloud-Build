using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyBot.XauUsd.Core;

var cases = new List<(string Name, Action Test)>();
void Test(string name, Action action) => cases.Add((name, action));
void True(bool value, string reason) { if (!value) throw new Exception(reason); }
void Equal<T>(T expected, T actual) { if (!EqualityComparer<T>.Default.Equals(expected, actual))
    throw new Exception("Expected " + expected + ", got " + actual); }
void Fails(Action action)
{
    bool thrown = false;
    try { action(); } catch (ArgumentException) { thrown = true; }
    catch (InvalidOperationException) { thrown = true; }
    if (!thrown) throw new Exception("Expected failure");
}
var time = new DateTimeOffset(2020, 1, 2, 12, 0, 0, TimeSpan.Zero);
BrokerSnapshot Broker() => new(true, true, true, true, 1m, 100m, .5m,
    .01m, .01m, .1m, 1m, 1m, time);
PortfolioSnapshot Portfolio() => new(1000m, 1000m, 500m, 0, 0, true, true, false);
ProposedTrade Trade() => new("BUY|test|1", Side.Buy, 2000m, 1990m, 2030m,
    1m, 0m, 5m, .2m, time);
List<ConfirmedPivot> Pivots() {
    decimal[] prices = {100m, 200m, 138m, 168m, 121.4m};
    var r = new List<ConfirmedPivot>();
    for(int i = 0; i < 5; ++i)
        r.Add(new(i, i + 2, i % 2 == 0 ? PivotKind.Low : PivotKind.High,
            prices[i], time.AddMinutes(i * 10), time.AddMinutes(i * 10 + 5)));
    return r;
}

Test("contract version", () => True(Contract.Version.StartsWith("HBXAU"), "version"));
Test("invalid bar OHLC rejected", () =>
    Fails(() => new CompletedBar(time, time.AddMinutes(1), 10m, 9m, 8m, 10m).Validate()));
Test("not completed rejected", () =>
    Fails(() => new CompletedBar(time, time, 10m, 11m, 9m, 10m).Validate()));
Test("non-UTC bar rejected", () =>
    Fails(() => new CompletedBar(time.ToOffset(TimeSpan.FromHours(8)), time.AddMinutes(1),
        10m, 11m, 9m, 10m).Validate()));
Test("causal pivot right-bar lag", () => {
    var d = new CausalPivotDetector(2, 2);
    decimal[] highs = {10,11,12,16,13,12};
    for(int i = 0; i < 5; i++) Equal(0, d.AppendCompleted(new CompletedBar(
        time.AddMinutes(i), time.AddMinutes(i+1), highs[i]-1, highs[i],
        highs[i]-2, highs[i]-1)).Count);
    var pivots = d.AppendCompleted(new CompletedBar(time.AddMinutes(5),time.AddMinutes(6),
        11m, 12m, 10m, 11m));
    Equal(1, pivots.Count); Equal(PivotKind.High, pivots[0].Kind);
    Equal(3L,pivots[0].SourceBarIndex); Equal(5L,pivots[0].ConfirmationBarIndex);
    Equal(time.AddMinutes(6),pivots[0].AvailableAtUtc);
});
Test("pivot tie cannot repaint", () => {
    var d = new CausalPivotDetector(1, 1);
    for(int i = 0; i < 6; i++) {
        var result = d.AppendCompleted(new CompletedBar(time.AddMinutes(i),
            time.AddMinutes(i+1), 15m,16m,14m,15m));
        Equal(0, result.Count);
    }
});
Test("pivot duplicate/out-of-order bar rejected", () => {
    var d = new CausalPivotDetector(1,1);
    var bar = new CompletedBar(time,time.AddMinutes(1),10m,11m,9m,10m);
    d.AppendCompleted(bar); Fails(() => d.AppendCompleted(bar));
});
Test("ratios are price-derived", () => {
    var r=HarmonicRatios.Calculate(Pivots());
    Equal(.62m,r.Xab); Equal(30m/62m,r.Abc);
    Equal(46.6m/30m,r.Bcd); Equal(.786m,r.Xad);
});
Test("ten distinct pattern research profiles", () => {
    Equal(10,PatternCatalog.ResearchOnly.Count);
    Equal(10,PatternCatalog.ResearchOnly.Select(x=>x.Family).Distinct().Count());
});
Test("no unverified source can enter trading", () => True(
    PatternCatalog.ResearchOnly.All(x=>!x.SourceVerified && !x.TradingApproved),
    "Any certified trading pattern would violate V1 freeze"));
Test("specialized native patterns do not use XABCD shortcut", () => True(
    PatternCatalog.ResearchOnly.Where(x=>x.Mode==GeometryMode.Specialized)
        .All(x=>!x.ResearchMatches(new HarmonicRatios(1m,1m,1m,1m,1m))), "shortcut"));
Test("completed Gartley is research-only", () => {
    var o=HarmonicAnalyzer.Analyze(Pivots(),time.AddHours(2),.01m);
    Equal(Side.Buy,o.Direction); True(o.ResearchMatches.Contains(PatternFamily.Gartley),"Gartley");
    True(!o.ReadyForTrading,"Trading disabled");
});
Test("projected D cannot masquerade as confirmed", () => {
    var p=Pivots(); p[4]=p[4] with { AvailableAtUtc=time.AddDays(1) };
    Fails(()=>HarmonicAnalyzer.Analyze(p,time.AddHours(2),.01m));
});
Test("repeated pivot index rejected", () => {
    var p=Pivots(); p[4]=p[4] with { SourceBarIndex=p[3].SourceBarIndex };
    Fails(()=>HarmonicAnalyzer.Analyze(p,time.AddHours(2),.01m));
});
Test("non-alternating pivot rejected", () => {
    var p=Pivots(); p[4]=p[4] with { Kind=PivotKind.High };
    Fails(()=>HarmonicAnalyzer.Analyze(p,time.AddHours(2),.01m));
});
Test("event identity aliases family overlap", () => {
    var d=Pivots()[4]; Equal(EventIdentity.Create(Side.Buy,d,.01m),
        EventIdentity.Create(Side.Buy,d,.01m));
    True(EventIdentity.Create(Side.Buy,d,.01m)!=EventIdentity.Create(Side.Sell,d,.01m),
        "direction must matter");
});
Test("event price normalized to tick", () => {
    var d=Pivots()[4];
    var alternate=d with {Price=d.Price+.001m};
    Equal(EventIdentity.Create(Side.Buy,d,.01m),EventIdentity.Create(Side.Buy,alternate,.01m));
});
Test("PRZ intersects", () => {
    var z=PriceInterval.Intersect(new[]{new PriceInterval(100m,110m),new PriceInterval(105m,112m)});
    Equal(new PriceInterval(105m,110m),z);
});
Test("non-intersecting PRZ rejected", () => True(
    PriceInterval.Intersect(new[]{new PriceInterval(100m,102m),new PriceInterval(103m,105m)}) is null,
    "PRZ must intersect"));
Test("causal feature available at decision", () => {
    var f = new TimeStampedFeature("ATR",2m,time.AddMinutes(-5),
        time.AddMinutes(-4),time.AddMinutes(-1));
    True(TemporalGate.CanUse(f,time),"causal");
    True(!TemporalGate.CanUse(f,time.AddMinutes(-2)),"future leak");
});
Test("timestamp inversion rejected", () => {
    var f = new TimeStampedFeature("ATR",2m,time,time.AddMinutes(-1),time);
    True(!TemporalGate.CanUse(f,time),"inversion");
});
Test("valid research allocation risk bounded", () => {
    var v=RiskGate.Evaluate(Trade(),Broker(),Portfolio());
    True(v.Approved,"risk should be approved: "+v.Reason);
    True(v.Allocation!.VolumeInUnits>=1m && v.Allocation.VolumeInUnits<=100m,"volume");
    True(v.Allocation.InitialRiskUsd<=50m,"risk cap");
    True(v.Allocation.NetRewardRisk>=2m,"net RR");
});
Test("risk above five percent rejected", () =>
    Equal("RISK_PERCENT_LIMIT",RiskGate.Evaluate(Trade() with {RequestedRiskPercent=5.01m},
        Broker(),Portfolio()).Reason));
Test("open exposure blocks duplicate/hedge", () =>
    Equal("XAUUSD_EXPOSURE_ALREADY_EXISTS",RiskGate.Evaluate(Trade(),Broker(),
        Portfolio() with {OpenXauPositions=1}).Reason));
Test("pending exposure blocks duplicate/hedge", () =>
    Equal("XAUUSD_EXPOSURE_ALREADY_EXISTS",RiskGate.Evaluate(Trade(),Broker(),
        Portfolio() with {PendingXauOrders=1}).Reason));
Test("unknown order result blocks retry", () =>
    Equal("EXECUTION_CUSTODY_UNVERIFIED",RiskGate.Evaluate(Trade(),Broker(),
        Portfolio() with {UnknownOrderOutcome=true}).Reason));
Test("missing exclusive lease blocks", () =>
    Equal("EXECUTION_CUSTODY_UNVERIFIED",RiskGate.Evaluate(Trade(),Broker(),
        Portfolio() with {ExclusiveExecutionLeaseHeld=false}).Reason));
Test("stale quote blocks", () =>
    Equal("STALE_BROKER_SNAPSHOT",RiskGate.Evaluate(Trade(),
        Broker() with {ObservedAtUtc=time.AddMinutes(-5)},Portfolio()).Reason));
Test("max drawdown 10% blocks", () =>
    Equal("MAX_DRAWDOWN_LIMIT",RiskGate.Evaluate(Trade(),Broker(),
        Portfolio() with {EquityUsd=900m,PeakEquityUsd=1000m}).Reason));
Test("net RR uses spread/fees stress", () =>
    Equal("NET_RR_BELOW_2",RiskGate.Evaluate(Trade() with {
        RoundTripFeesPerVolumeUnit=9m, StressedSlippagePerVolumeUnit=4m },
        Broker(),Portfolio()).Reason));
Test("small account may be unaffordable", () =>
    Equal("MINIMUM_VOLUME_UNAFFORDABLE",RiskGate.Evaluate(Trade(),Broker(),
        Portfolio() with {EquityUsd=100m,PeakEquityUsd=100m,FreeMarginUsd=100m}).Reason));
Test("unknown conversion fails closed", () =>
    Equal("BROKER_CAPABILITY_UNVERIFIED",RiskGate.Evaluate(Trade(),
        Broker() with {CurrencyConversionVerified=false},Portfolio()).Reason));
Test("invalid buy stop geometry fails closed", () =>
    Equal("INVALID_STOP_TARGET_GEOMETRY",RiskGate.Evaluate(Trade() with {Stop=2001m},
        Broker(),Portfolio()).Reason));
Test("buy grid cannot widen stop", () => {
    Equal(1999m,VirtualProfitGrid.TightenStop(Side.Buy,1990m,1995m,1999m));
    Fails(()=>VirtualProfitGrid.TightenStop(Side.Buy,1990m,1995m,1994m));
});
Test("sell grid cannot widen stop", () => {
    Equal(2001m,VirtualProfitGrid.TightenStop(Side.Sell,2010m,2005m,2001m));
    Fails(()=>VirtualProfitGrid.TightenStop(Side.Sell,2010m,2005m,2006m));
});
Test("partial close never adds volume", () => {
    Equal(4m, VirtualProfitGrid.PartialClose(5m,1m));
    Fails(()=>VirtualProfitGrid.PartialClose(5m,6m));
});
Test("each thesis reserved once", () => {
    var ledger=new ResearchIntentLedger();
    True(ledger.TryReserve("BUY|time|ticks"),"initial intent");
    True(!ledger.TryReserve("BUY|time|ticks"),"duplicate");
});
Test("R uses approved initial risk", () =>
    Equal(2m,ResearchStatistics.RealizedR(50m,25m)));
Test("NY/London winter session", () => True(
    InstitutionalSession.IsOpen(DateTimeOffset.Parse("2026-01-15T09:00:00+00:00"),true,true),
    "winter"));
Test("NY/London summer session", () => True(
    InstitutionalSession.IsOpen(DateTimeOffset.Parse("2026-07-15T07:30:00+00:00"),true,true),
    "summer"));
Test("US/UK DST mismatch week", () => {
    True(!InstitutionalSession.IsOpen(
        DateTimeOffset.Parse("2026-03-16T07:30:00+00:00"),true,true),"London not open");
    True(InstitutionalSession.IsOpen(
        DateTimeOffset.Parse("2026-03-16T08:30:00+00:00"),true,true),"London open");
});
Test("broker holiday status is mandatory", () => True(
    !InstitutionalSession.IsOpen(DateTimeOffset.Parse("2026-07-15T07:30:00+00:00"),false,true),
    "unknown broker hours"));
Test("DST weekend not tradable", () => True(
    !InstitutionalSession.IsOpen(DateTimeOffset.Parse("2026-03-08T10:00:00+00:00"),true,true),
    "weekend"));
Test("non-validated pattern cannot ENTER", () => {
    var o=HarmonicAnalyzer.Analyze(Pivots(),time.AddHours(2),.01m);
    Equal(Decision.Reject,StrategyDecision.Evaluate(o,true,true).Action);
});
Test("missing causal proof cannot ENTER", () => {
    var o=HarmonicAnalyzer.Analyze(Pivots(),time.AddHours(2),.01m);
    Equal("NON_CAUSAL_FEATURE",StrategyDecision.Evaluate(o,false,true).Reason);
});


Test("five-pivot assembler emits research only at confirmed D", () => {
    var a=new CausalPatternAssembler(); var p=Pivots();
    for(int i=0;i<4;i++) True(a.Observe(p[i],time.AddHours(2),.01m) is null,"premature D");
    var o=a.Observe(p[4],time.AddHours(2),.01m);
    True(o is not null && !o.ReadyForTrading,"research only");
});
Test("assembler rejects duplicate confirmed source", () => {
    var a=new CausalPatternAssembler(); var p=Pivots();
    a.Observe(p[0],time.AddHours(2),.01m);
    Fails(()=>a.Observe(p[0],time.AddHours(2),.01m));
});
Test("assembler same-side pivots cannot fake alternating D", () => {
    var a=new CausalPatternAssembler();var p=Pivots();
    a.Observe(p[0],time.AddHours(2),.01m);
    var extra=p[0] with { SourceBarIndex=20, ConfirmationBarIndex=22, Price=99m };
    True(a.Observe(extra,time.AddHours(2),.01m) is null,"same-side pivot");
});
Test("partial closes remain exactly one trade", () => {
    var ledger=new WholeTradeAccounting("THESIS",5m,25m);
    ledger.RecordNetClose(2m,20m);
    Equal(0,ledger.WholeTradeCount);
    Fails(()=>{ var x=ledger.FinalNetR(); });
    ledger.RecordNetClose(3m,30m);
    Equal(1,ledger.WholeTradeCount);
    Equal(2,ledger.PartialCloseCount);
    Equal(2m,ledger.FinalNetR());
    Fails(()=>ledger.RecordNetClose(1m,1m));
});
Test("annual gate does not accept missing lineage", () => {
    var e=new AnnualOosEvidence(2025,true,true,false,true,
        new string('a',64),new string('b',64),new string('c',64),
        500,.9m,3.3m,.6m,2.3m,.01m);
    True(!CommercialResearchGate.Check(e).Passed,"lineage");
});
Test("annual gate checks lower bound separately", () => {
    var e=new AnnualOosEvidence(2025,true,true,true,true,
        new string('a',64),new string('b',64),new string('c',64),
        500,.9m,3.3m,.6m,2.3m,0m);
    Equal("LCB95_NONPOSITIVE",CommercialResearchGate.Check(e).Reason);
});
Test("annual gate cannot merge away failed years", () => {
    var e=new AnnualOosEvidence(2025,true,true,true,true,
        new string('a',64),new string('b',64),new string('c',64),
        500,.9m,3.3m,.6m,2.3m,.1m);
    True(CommercialResearchGate.Check(e).Passed,"synthetic contract should pass");
    True(!CommercialResearchGate.CheckAll(new[]{e,e with {Year=2026,WholeTrades=499}}),
        "year-2 must fail");
    True(!CommercialResearchGate.CheckAll(new[]{e,e}),"duplicate year");
});


Test("false directional harmonic price path rejected", () => {
    var p=Pivots();
    p[3]=p[3] with { Price=120m };
    Fails(()=>HarmonicAnalyzer.Analyze(p,time.AddHours(2),.01m));
});
Test("non-monotone pivot event time rejected", () => {
    var p=Pivots();
    p[4]=p[4] with { EventAtUtc=p[3].EventAtUtc };
    Fails(()=>HarmonicAnalyzer.Analyze(p,time.AddHours(2),.01m));
});


Test("bar receipt separates next-open boundary from observed tick", () => {
    var opened = time.AddMinutes(1);
    var observed = opened.AddSeconds(7);
    var receipt = CausalBarReceipt.CaptureOnBarOpened(time,opened,observed,
        10m,11m,9m,10m);
    Equal(opened,receipt.ClosedBar.CloseUtc);
    Equal(observed,receipt.AvailableAtUtc);
    Equal(observed,receipt.ObservedAtUtc);
});
Test("Friday last bar remains unavailable until Monday tick", () => {
    var friday = new DateTimeOffset(2026,11,6,21,59,0,TimeSpan.Zero);
    var monday = new DateTimeOffset(2026,11,9,0,0,0,TimeSpan.Zero);
    var firstTick = monday.AddSeconds(3);
    var receipt=CausalBarReceipt.CaptureOnBarOpened(friday,monday,firstTick,
        4000m,4002m,3998m,4001m);
    True(receipt.AvailableAtUtc>friday.AddDays(1),"weekend leak");
    Equal(firstTick,receipt.AvailableAtUtc);
});
Test("bar observation before next-open fails closed", () => Fails(() =>
    CausalBarReceipt.CaptureOnBarOpened(time,time.AddMinutes(1),
        time.AddSeconds(50),10m,11m,9m,10m)));
Test("non-UTC observation rejected", () => Fails(() =>
    CausalBarReceipt.CaptureOnBarOpened(time,time.AddMinutes(1),
        time.AddMinutes(2).ToOffset(TimeSpan.FromHours(8)),10m,11m,9m,10m)));
Test("bar observation must not predate completed boundary", () => {
    var d=new CausalPivotDetector(1,1);
    var bar=new CompletedBar(time,time.AddMinutes(1),10m,11m,9m,10m);
    Fails(()=>d.AppendCompleted(bar,time.AddSeconds(30)));
});
Test("pivot availability follows observed tick not nominal boundary", () => {
    var d=new CausalPivotDetector(1,1);
    decimal[] h={11m,15m,12m};
    for (int i=0;i<3;i++) {
        var bar=new CompletedBar(time.AddMinutes(i),time.AddMinutes(i+1),
            h[i]-1m,h[i],h[i]-2m,h[i]-1m);
        var pivots=d.AppendCompleted(bar,time.AddMinutes(i+1).AddSeconds(3));
        if(i==2) {
            Equal(1,pivots.Count);
            Equal(time.AddMinutes(3).AddSeconds(3),pivots[0].AvailableAtUtc);
            True(pivots[0].AvailableAtUtc > pivots[0].EventAtUtc,
                 "confirmation requires right-bar observation");
        }
    }
});
Test("time regression fails closed even for later bar open", () => {
    var d=new CausalPivotDetector(1,1);
    d.AppendCompleted(new CompletedBar(time,time.AddMinutes(1),10m,11m,9m,10m),
                      time.AddMinutes(5));
    Fails(()=>d.AppendCompleted(
        new CompletedBar(time.AddMinutes(1),time.AddMinutes(2),10m,11m,9m,10m),
        time.AddMinutes(4)));
});
Test("weekly bar boundaries cannot be mistaken for exact last tick", () => {
    var friday=new DateTimeOffset(2026,11,6,20,0,0,TimeSpan.Zero);
    var monday=new DateTimeOffset(2026,11,9,0,0,0,TimeSpan.Zero);
    var r=CausalBarReceipt.CaptureOnBarOpened(friday,monday,monday.AddMinutes(1),
        3000m,3003m,2998m,3001m);
    Equal(monday,r.NextBarOpenUtc);
    True(r.AvailableAtUtc>r.NextBarOpenUtc,"must model delayed observation");
});


Test("same candle double extreme is ambiguous and omitted", () => {
    var d=new CausalPivotDetector(1,1);
    d.AppendCompleted(new CompletedBar(time,time.AddMinutes(1),9.5m,10m,9m,9.5m));
    d.AppendCompleted(new CompletedBar(time.AddMinutes(1),time.AddMinutes(2),
        10m,16m,3m,10m));
    var result=d.AppendCompleted(new CompletedBar(time.AddMinutes(2),time.AddMinutes(3),
        10.5m,11m,10m,10.5m));
    Equal(0,result.Count);
    Equal(1L,d.AmbiguousOutsideBarCount);
});
Test("outside bar ambiguity cannot repeat when next candle arrives", () => {
    var d=new CausalPivotDetector(1,1);
    d.AppendCompleted(new CompletedBar(time,time.AddMinutes(1),9.5m,10m,9m,9.5m));
    d.AppendCompleted(new CompletedBar(time.AddMinutes(1),time.AddMinutes(2),
        10m,16m,3m,10m));
    d.AppendCompleted(new CompletedBar(time.AddMinutes(2),time.AddMinutes(3),
        10.5m,11m,10m,10.5m));
    d.AppendCompleted(new CompletedBar(time.AddMinutes(3),time.AddMinutes(4),
        10.5m,11m,10m,10.5m));
    Equal(1L,d.AmbiguousOutsideBarCount);
});
Test("negative pivot index cannot pass causal contract", () => {
    var p=Pivots()[0] with {SourceBarIndex=-1};
    Fails(()=>p.Validate(time.AddHours(2)));
});
Test("event ledger bounded with no eviction and no re-emission", () => {
    var l=new ResearchIntentLedger(2);
    True(l.TryReserve("A"),"A");
    True(l.TryReserve("B"),"B");
    True(!l.TryReserve("C"),"limit");
    True(l.Saturated,"saturated");
    Equal(2,l.Count);
    True(l.Contains("A"),"A retained");
    True(!l.TryReserve("A"),"reemit A forbidden");
});
Test("event ledger invalid capacity fails closed", () =>
    Fails(()=>{ var unused=new ResearchIntentLedger(0); }));
Test("event ledger oversize identifier rejected", () =>
    True(!new ResearchIntentLedger(1).TryReserve(new string('X',257)),
        "oversize thesis"));
Test("R allocator obeys remaining peak drawdown cushion", () => {
    var p=Portfolio() with {EquityUsd=925m,PeakEquityUsd=1000m};
    var r=RiskGate.Evaluate(Trade(),Broker(),p);
    True(r.Approved,"cushion permit: "+r.Reason);
    True(r.Allocation!.InitialRiskUsd<=25m,"risk would breach DD 10%");
});
Test("R allocator rejects trade when minimum size exceeds DD cushion", () => {
    var p=Portfolio() with {EquityUsd=910m,PeakEquityUsd=1000m};
    var r=RiskGate.Evaluate(Trade(),Broker(),p);
    Equal("MINIMUM_VOLUME_UNAFFORDABLE",r.Reason);
});
Test("negative broker exposure is unverified, not zero", () =>
    Equal("INVALID_EXPOSURE_COUNT",RiskGate.Evaluate(
        Trade(),Broker(),Portfolio() with {OpenXauPositions=-1}).Reason));
Test("invalid directional enum rejected", () =>
    Equal("INVALID_SIDE",RiskGate.Evaluate(
        Trade() with {Direction=(Side)250},Broker(),Portfolio()).Reason));
Test("off-grid stop rejected, never auto-rounded into looser risk", () =>
    Equal("PRICE_OFF_TICK_GRID",RiskGate.Evaluate(
        Trade() with {Stop=1990.005m},Broker(),Portfolio()).Reason));
Test("empty causal feature set is not proof of causality", () =>
    True(!TemporalGate.CanUseAll(Array.Empty<TimeStampedFeature>(),time),
        "empty temporal proof"));
Test("valid causal feature set accepted", () =>
    True(TemporalGate.CanUseAll(new[]{
        new TimeStampedFeature("ATR",1m,time.AddMinutes(-3),
            time.AddMinutes(-2),time.AddMinutes(-1))},time),"feature"));
Test("research PRZ projected from XABC contains confirmed Gartley D", () => {
    var p=Pivots(); var zones=CausalPrzProjector.Project(p.Take(4).ToArray(),
        time.AddHours(1),.01m);
    var g=zones.Single(z=>z.Family==PatternFamily.Gartley);
    Equal(Side.Buy,g.Direction);
    True(g.TickAlignedZone.Low<=p[4].Price &&
         p[4].Price<=g.TickAlignedZone.High,"Gartley projection");
    True(!g.SourceVerified,"never certified");
});
Test("research PRZ does not use D input", () => {
    var p=Pivots();var z=CausalPrzProjector.Project(p.Take(4).ToArray(),
        time.AddHours(1),.01m);
    var changed=Pivots();changed[4]=changed[4] with {Price=115m};
    var z2=CausalPrzProjector.Project(changed.Take(4).ToArray(),
        time.AddHours(1),.01m);
    Equal(z.Count,z2.Count);
    for(int i=0;i<z.Count;i++) Equal(z[i],z2[i]);
});
Test("unavailable C pivot cannot project a past PRZ", () => {
    var p=Pivots().Take(4).ToArray();
    Fails(()=>CausalPrzProjector.Project(p,time.AddMinutes(30),.01m));
});
Test("inverted XABC price path fails projection", () => {
    var p=Pivots().Take(4).ToArray();
    p[3]=p[3] with {Price=120m};
    Fails(()=>CausalPrzProjector.Project(p,time.AddHours(1),.01m));
});
Test("specialized Shark and 5-0 never projected using generic XABCD", () => {
    var z=CausalPrzProjector.Project(Pivots().Take(4).ToArray(),
        time.AddHours(1),.01m);
    True(z.All(x=>x.Family!=PatternFamily.Shark &&
                   x.Family!=PatternFamily.FiveZero),"special grammar");
});
Test("research mirror projection handles bearish geometry", () => {
    var p=Pivots().Take(4).Select(x=>x with {
        Kind=x.Kind==PivotKind.Low?PivotKind.High:PivotKind.Low,
        Price=300m-x.Price}).ToArray();
    var zones=CausalPrzProjector.Project(p,time.AddHours(1),.01m);
    var g=zones.Single(x=>x.Family==PatternFamily.Gartley);
    Equal(Side.Sell,g.Direction);
    True(g.TickAlignedZone.Low<=178.6m && g.TickAlignedZone.High>=178.6m,
        "mirrored D");
});
Test("retrospective projected D is flagged when C unavailable beforehand", () => {
    var p=Pivots();
    p[3]=p[3] with {AvailableAtUtc=time.AddMinutes(41)};
    var o=HarmonicAnalyzer.Analyze(p,time.AddHours(2),.01m);
    True(!o.PrzProjectedBeforeD,"C was not known at D event");
    True(!o.ReadyForTrading,"retro fit cannot trade");
});
Test("causally projected D flag true only when C known first", () => {
    var o=HarmonicAnalyzer.Analyze(Pivots(),time.AddHours(2),.01m);
    True(o.PrzProjectedBeforeD,"C confirmation precedes D");
});
Test("off-grid PRZ intersection cannot invent a legal tick", () => {
    var p=Pivots().Take(4).ToArray();
    var zones=CausalPrzProjector.Project(p,time.AddHours(1),1000m);
    Equal(0,zones.Count);
});
Test("no D or future data can satisfy project signature", () =>
    Fails(()=>CausalPrzProjector.Project(Pivots(),time.AddHours(1),.01m)));

int passed=0;
foreach(var (name,action) in cases)
{
    try { action(); Console.WriteLine("PASS "+name); ++passed; }
    catch(Exception e) { Console.Error.WriteLine("FAIL "+name+": "+e); }
}
Console.WriteLine("SUMMARY passed="+passed+" total="+cases.Count);
return passed==cases.Count ? 0 : 1;
