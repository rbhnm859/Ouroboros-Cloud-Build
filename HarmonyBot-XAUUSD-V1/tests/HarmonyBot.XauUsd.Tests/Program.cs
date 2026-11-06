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

int passed=0;
foreach(var (name,action) in cases)
{
    try { action(); Console.WriteLine("PASS "+name); ++passed; }
    catch(Exception e) { Console.Error.WriteLine("FAIL "+name+": "+e); }
}
Console.WriteLine("SUMMARY passed="+passed+" total="+cases.Count);
return passed==cases.Count ? 0 : 1;
