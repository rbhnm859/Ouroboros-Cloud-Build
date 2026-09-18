from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

param_anchor = '''        [Parameter("V29.5 Min Invalidation Age Min", DefaultValue = 2.0, MinValue = 0.0, MaxValue = 30.0)]
        public double V295MinInvalidationAgeMinutes { get; set; }

        private long _v294DirectionBlocked;
        private long _v295ThesisInvalidations;
        private long _v295GridProofBlocked;
'''
param_new = '''        [Parameter("V29.5 Min Invalidation Age Min", DefaultValue = 2.0, MinValue = 0.0, MaxValue = 30.0)]
        public double V295MinInvalidationAgeMinutes { get; set; }

        // Architecture Redesign RC. Harmonic patterns remain the sole setup generator.
        // This layer can only admit/reject an existing harmonic setup and manage an
        // already-open basket. Frozen engineering/risk modules are not modified.
        [Parameter("Architecture Redesign Mode", DefaultValue = 0, MinValue = 0, MaxValue = 3)]
        public int ArchitectureRedesignMode { get; set; }

        [Parameter("Architecture ATR Baseline Bars", DefaultValue = 240, MinValue = 60, MaxValue = 2880)]
        public int ArchitectureAtrBaselineBars { get; set; }

        [Parameter("Architecture Min Context Score", DefaultValue = 0.56, MinValue = 0.0, MaxValue = 1.0)]
        public double ArchitectureMinContextScore { get; set; }

        [Parameter("Architecture Min Confirmation Score", DefaultValue = 0.60, MinValue = 0.0, MaxValue = 1.0)]
        public double ArchitectureMinConfirmationScore { get; set; }

        [Parameter("Architecture Giveback Activate R", DefaultValue = 0.65, MinValue = 0.20, MaxValue = 3.0)]
        public double ArchitectureGivebackActivateR { get; set; }

        [Parameter("Architecture Max Giveback R", DefaultValue = 0.35, MinValue = 0.10, MaxValue = 2.0)]
        public double ArchitectureMaxGivebackR { get; set; }

        private long _v294DirectionBlocked;
        private long _v295ThesisInvalidations;
        private long _v295GridProofBlocked;
        private long _archAdmissionSeen;
        private long _archContextBlocked;
        private long _archConfirmationBlocked;
        private long _archGivebackExits;
        private long _archLifecycleSamples;
'''
if s.count(param_anchor) != 1:
    raise SystemExit(f'architecture parameter anchor count={s.count(param_anchor)}; expected 1')
s = s.replace(param_anchor, param_new, 1)

gate_anchor = '''                if (!PassMtfFilter(signal))
'''
gate_new = '''                // ARCHITECTURE REDESIGN ADMISSION: all inputs are signal-time causal.
                if (ArchitectureRedesignMode > 0)
                {
                    double archBaseline, archAtrRatio, archH1, archH4, archM15, archVol;
                    double archContext = ArchitectureContextScore(signal, signalIndex, atrNow,
                        out archBaseline, out archAtrRatio, out archH1, out archH4, out archM15, out archVol);
                    double archConfirm = ArchitectureConfirmationScore(signal, signalIndex, atrNow);
                    _archAdmissionSeen++;

                    string archDecision = "ALLOW";
                    if (archContext + 1e-12 < ArchitectureMinContextScore)
                    {
                        _archContextBlocked++;
                        archDecision = "BLOCK_CONTEXT";
                    }
                    else if (ArchitectureRedesignMode >= 2 && archConfirm + 1e-12 < ArchitectureMinConfirmationScore)
                    {
                        _archConfirmationBlocked++;
                        archDecision = "BLOCK_CONFIRMATION";
                    }

                    Print("[ARCH-ADMISSION] mode={0} decision={1} pattern={2} dir={3} idx={4} atr={5:F4} baseline={6:F4} ratio={7:F3} h1={8:F3} h4={9:F3} m15={10:F3} vol={11:F3} geometry={12:F3} prz={13:F3} time={14:F3} pivot={15:F3} conf={16:F3} context={17:F3} confirmation={18:F3}",
                        ArchitectureRedesignMode, archDecision, signal.PatternName ?? "NA", signal.Direction, signalIndex,
                        atrNow, archBaseline, archAtrRatio, archH1, archH4, archM15, archVol,
                        signal.GeometryQuality, signal.PrzConfluence, signal.TimeSymmetry, signal.PivotQuality,
                        signal.Confidence, archContext, archConfirm);

                    if (archDecision != "ALLOW")
                    {
                        if (v29FromPending) V29RemovePending(signal, archDecision, false);
                        return;
                    }
                }

                if (!PassMtfFilter(signal))
'''
if s.count(gate_anchor) != 1:
    raise SystemExit(f'architecture admission anchor count={s.count(gate_anchor)}; expected 1')
s = s.replace(gate_anchor, gate_new, 1)

helper_anchor = '''        private double V295PeakFavorableR(GridBasket b)
'''
helpers = '''        private double ArchitectureClamp01(double x)
        {
            return Math.Max(0.0, Math.Min(1.0, x));
        }

        private double ArchitectureRollingTrueRangeBaseline(int endIndex)
        {
            if (_signalBars == null || endIndex < 1) return 0;
            int lookback = Math.Max(60, Math.Min(2880, ArchitectureAtrBaselineBars));
            int end = Math.Min(endIndex, _signalBars.Count - 1);
            int start = Math.Max(1, end - lookback + 1);
            double sum = 0;
            int count = 0;
            for (int i = start; i <= end; i++)
            {
                double high = _signalBars.HighPrices[i];
                double low = _signalBars.LowPrices[i];
                double prevClose = _signalBars.ClosePrices[i - 1];
                double tr = Math.Max(high - low, Math.Max(Math.Abs(high - prevClose), Math.Abs(low - prevClose)));
                sum += tr;
                count++;
            }
            return count > 0 ? sum / count : 0;
        }

        private double ArchitectureAlignmentScore(TradeDirection direction, double fast, double slow)
        {
            if (fast <= 0 || slow <= 0) return 0.50;
            bool aligned = direction == TradeDirection.Buy ? fast > slow : fast < slow;
            return aligned ? 1.0 : 0.0;
        }

        private double ArchitectureM15MomentumScore(Signal signal, int signalIndex, double atrNow)
        {
            if (signal == null || _signalBars == null || atrNow <= 0) return 0.50;
            int i = Math.Min(signalIndex, _signalBars.Count - 2);
            if (i < 2) return 0.50;
            int j = Math.Max(0, i - 15);
            double delta = _signalBars.ClosePrices[i] - _signalBars.ClosePrices[j];
            if (signal.Direction == TradeDirection.Sell) delta = -delta;
            double normalized = delta / Math.Max(atrNow, 1e-9);
            return ArchitectureClamp01(0.50 + 0.35 * normalized);
        }

        private double ArchitectureVolatilityScore(double ratio)
        {
            if (ratio <= 0) return 0.50;
            if (ratio <= 1.15) return 1.0;
            if (ratio >= 2.0) return 0.25;
            return 1.0 - 0.75 * ((ratio - 1.15) / 0.85);
        }

        private double ArchitectureContextScore(Signal signal, int signalIndex, double atrNow,
            out double baseline, out double ratio, out double h1, out double h4, out double m15, out double vol)
        {
            baseline = ArchitectureRollingTrueRangeBaseline(signalIndex);
            ratio = baseline > 0 ? atrNow / baseline : 0;
            h1 = ArchitectureAlignmentScore(signal.Direction, _cacheH1Ema50, _cacheH1Ema200);
            h4 = ArchitectureAlignmentScore(signal.Direction, _cacheH4Ema50, _cacheH4Ema200);
            m15 = ArchitectureM15MomentumScore(signal, signalIndex, atrNow);
            vol = ArchitectureVolatilityScore(ratio);

            double geometry = ArchitectureClamp01(signal.GeometryQuality);
            double prz = ArchitectureClamp01(signal.PrzConfluence);
            double time = ArchitectureClamp01(signal.TimeSymmetry);
            double pivot = ArchitectureClamp01(signal.PivotQuality);
            double confidence = ArchitectureClamp01(signal.Confidence);

            // Preregistered continuous compatibility score. No date/hour/window lookup.
            return ArchitectureClamp01(
                0.24 * geometry +
                0.16 * prz +
                0.08 * time +
                0.06 * pivot +
                0.14 * confidence +
                0.12 * m15 +
                0.08 * h1 +
                0.06 * h4 +
                0.06 * vol);
        }

        private double ArchitectureConfirmationScore(Signal signal, int signalIndex, double atrNow)
        {
            if (signal == null || _signalBars == null || atrNow <= 0) return 0;
            int i = Math.Min(signalIndex, _signalBars.Count - 2);
            if (i < 1) return 0;

            double open = _signalBars.OpenPrices[i];
            double close = _signalBars.ClosePrices[i];
            double high = _signalBars.HighPrices[i];
            double low = _signalBars.LowPrices[i];
            double prevClose = _signalBars.ClosePrices[i - 1];
            double body = Math.Abs(close - open);
            double safeBody = Math.Max(body, atrNow * 0.005);

            bool directional;
            bool reclaim;
            bool rejection;
            if (signal.Direction == TradeDirection.Buy)
            {
                directional = close > open;
                reclaim = close >= prevClose;
                double lowerWick = Math.Max(0.0, Math.Min(open, close) - low);
                rejection = lowerWick >= safeBody * 0.50;
            }
            else
            {
                directional = close < open;
                reclaim = close <= prevClose;
                double upperWick = Math.Max(0.0, high - Math.Max(open, close));
                rejection = upperWick >= safeBody * 0.50;
            }

            double score = (directional ? 0.40 : 0.0) + (reclaim ? 0.30 : 0.0) + (rejection ? 0.30 : 0.0);
            return ArchitectureClamp01(score);
        }

        private double ArchitectureCurrentFavorableR(GridBasket b, double cur)
        {
            if (b == null || b.BaseRisk <= 0) return 0;
            double favorable = b.Direction == TradeDirection.Buy ? cur - b.BaseEntry : b.BaseEntry - cur;
            return Math.Max(0.0, favorable / Math.Max(b.BaseRisk, _symbol.PipSize));
        }

'''
if s.count(helper_anchor) != 1:
    raise SystemExit(f'architecture helper anchor count={s.count(helper_anchor)}; expected 1')
s = s.replace(helper_anchor, helpers + helper_anchor, 1)

created_anchor = '''                CreatedTime = Server.Time,
                LastAddTime = Server.Time,
'''
created_new = '''                CreatedTime = Server.Time,
                ArchMfeBucket = -1,
                ArchMaeBucket = -1,
                LastAddTime = Server.Time,
'''
if s.count(created_anchor) != 1:
    raise SystemExit(f'architecture basket creation anchor count={s.count(created_anchor)}; expected 1')
s = s.replace(created_anchor, created_new, 1)

basket_anchor = '''        public DateTime CreatedTime;
        public DateTime LastAddTime;
        public double WeightedEntry;
'''
basket_new = '''        public DateTime CreatedTime;
        public DateTime LastAddTime;
        public double WeightedEntry;
        public double ArchMaxFavorableR;
        public double ArchMaxAdverseR;
        public int ArchMfeBucket;
        public int ArchMaeBucket;
'''
if s.count(basket_anchor) != 1:
    raise SystemExit(f'architecture GridBasket anchor count={s.count(basket_anchor)}; expected 1')
s = s.replace(basket_anchor, basket_new, 1)

manage_anchor = '''                UpdateBasketProtection(b, cur, money, r, positions);

                // V29.5 THESIS-VALIDITY: the Development evidence shows that the
'''
manage_new = '''                UpdateBasketProtection(b, cur, money, r, positions);

                if (ArchitectureRedesignMode > 0)
                {
                    double archFav = V295PeakFavorableR(b);
                    double archAdv = V295AdverseR(b, cur);
                    if (archFav > b.ArchMaxFavorableR) b.ArchMaxFavorableR = archFav;
                    if (archAdv > b.ArchMaxAdverseR) b.ArchMaxAdverseR = archAdv;

                    int archMfeBucket = (int)Math.Floor(b.ArchMaxFavorableR * 10.0 + 1e-9);
                    int archMaeBucket = (int)Math.Floor(b.ArchMaxAdverseR * 10.0 + 1e-9);
                    if (archMfeBucket > b.ArchMfeBucket || archMaeBucket > b.ArchMaeBucket)
                    {
                        b.ArchMfeBucket = Math.Max(b.ArchMfeBucket, archMfeBucket);
                        b.ArchMaeBucket = Math.Max(b.ArchMaeBucket, archMaeBucket);
                        _archLifecycleSamples++;
                        Print("[ARCH-LIFECYCLE] basket={0} pattern={1} mfeR={2:F3} maeR={3:F3} ageMin={4:F1}",
                            id, b.PatternName ?? "NA", b.ArchMaxFavorableR, b.ArchMaxAdverseR,
                            (Server.Time - b.CreatedTime).TotalMinutes);
                    }

                    if (ArchitectureRedesignMode >= 3 && b.ArchMaxFavorableR >= ArchitectureGivebackActivateR)
                    {
                        double currentFavR = ArchitectureCurrentFavorableR(b, cur);
                        double givebackR = Math.Max(0.0, b.ArchMaxFavorableR - currentFavR);
                        if (givebackR + 1e-9 >= ArchitectureMaxGivebackR)
                        {
                            _archGivebackExits++;
                            CloseBasket(id, b, "ArchitectureWinnerGiveback", positions);
                            Print("[ARCH-GIVEBACK-EXIT] basket={0} pattern={1} mfeR={2:F3} maeR={3:F3} currentFavR={4:F3} givebackR={5:F3}",
                                id, b.PatternName ?? "NA", b.ArchMaxFavorableR, b.ArchMaxAdverseR, currentFavR, givebackR);
                            continue;
                        }
                    }
                }

                // V29.5 THESIS-VALIDITY: the Development evidence shows that the
'''
if s.count(manage_anchor) != 1:
    raise SystemExit(f'architecture lifecycle anchor count={s.count(manage_anchor)}; expected 1')
s = s.replace(manage_anchor, manage_new, 1)

stop_anchor = '''            Print("[V295-THESIS-SUMMARY] invalidations={0} gridProofBlocked={1} guard={2} killR={3:F2} proofR={4:F2}",
                _v295ThesisInvalidations, _v295GridProofBlocked, V295ThesisGuard, V295NoMfeKillR, V295MinFavorableProofR);
            EnsureServerSideProtectionBeforeStop();
'''
stop_new = '''            Print("[V295-THESIS-SUMMARY] invalidations={0} gridProofBlocked={1} guard={2} killR={3:F2} proofR={4:F2}",
                _v295ThesisInvalidations, _v295GridProofBlocked, V295ThesisGuard, V295NoMfeKillR, V295MinFavorableProofR);
            Print("[ARCH-SUMMARY] mode={0} seen={1} contextBlocked={2} confirmationBlocked={3} givebackExits={4} lifecycleSamples={5} minContext={6:F2} minConfirmation={7:F2} givebackActivateR={8:F2} maxGivebackR={9:F2}",
                ArchitectureRedesignMode, _archAdmissionSeen, _archContextBlocked, _archConfirmationBlocked,
                _archGivebackExits, _archLifecycleSamples, ArchitectureMinContextScore, ArchitectureMinConfirmationScore,
                ArchitectureGivebackActivateR, ArchitectureMaxGivebackR);
            EnsureServerSideProtectionBeforeStop();
'''
if s.count(stop_anchor) != 1:
    raise SystemExit(f'architecture stop anchor count={s.count(stop_anchor)}; expected 1')
s = s.replace(stop_anchor, stop_new, 1)

old_version = 'V29.5-Thesis-Validity-Minimum-Patch-Dev'
if s.count(old_version) != 1:
    raise SystemExit(f'architecture version marker count={s.count(old_version)}; expected 1')
s = s.replace(old_version, 'Architecture-Redesign-One-Pass-RC', 1)

required = [
    'Architecture-Redesign-One-Pass-RC',
    'ArchitectureRedesignMode',
    'ArchitectureContextScore',
    'ArchitectureConfirmationScore',
    '[ARCH-ADMISSION]',
    '[ARCH-LIFECYCLE]',
    '[ARCH-GIVEBACK-EXIT]',
    '[ARCH-SUMMARY]',
    'V295ThesisGuard',
    'V29.3 GRID-RISK-CAP-HOTFIX'
]
for token in required:
    if token not in s:
        raise SystemExit('missing architecture token: ' + token)

p.write_text(s, encoding='utf-8')
print('Applied HarmonyBot Architecture Redesign One-Pass RC')
print('Scope: context compatibility + PRZ confirmation + lifecycle conversion; engineering core unchanged')
