from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

param_anchor = '''        [Parameter("V29.4 Allow Sell", DefaultValue = true)]
        public bool V294AllowSell { get; set; }

        private long _v294DirectionBlocked;
'''
param_new = '''        [Parameter("V29.4 Allow Sell", DefaultValue = true)]
        public bool V294AllowSell { get; set; }

        // V29.5 minimum architecture patch: one coherent thesis-validity engine.
        // It does not alter risk sizing, broker protection, margin, min-volume,
        // anti-hedge, duplicate-entry or fail-closed engineering modules.
        [Parameter("V29.5 Thesis Guard", DefaultValue = true)]
        public bool V295ThesisGuard { get; set; }

        [Parameter("V29.5 No-MFE Kill R", DefaultValue = 0.85, MinValue = 0.50, MaxValue = 1.20)]
        public double V295NoMfeKillR { get; set; }

        [Parameter("V29.5 Min Favorable Proof R", DefaultValue = 0.15, MinValue = 0.05, MaxValue = 0.50)]
        public double V295MinFavorableProofR { get; set; }

        [Parameter("V29.5 Min Invalidation Age Min", DefaultValue = 2.0, MinValue = 0.0, MaxValue = 30.0)]
        public double V295MinInvalidationAgeMinutes { get; set; }

        private long _v294DirectionBlocked;
        private long _v295ThesisInvalidations;
        private long _v295GridProofBlocked;
'''
if s.count(param_anchor) != 1:
    raise SystemExit(f'V29.5 parameter anchor count={s.count(param_anchor)}; expected 1')
s = s.replace(param_anchor, param_new, 1)

created_anchor = '''                LevelsOpened = 0,
                LastAddTime = Server.Time,
                WeightedEntry = p.EntryPrice,
'''
created_new = '''                LevelsOpened = 0,
                CreatedTime = Server.Time,
                LastAddTime = Server.Time,
                WeightedEntry = p.EntryPrice,
'''
if s.count(created_anchor) != 1:
    raise SystemExit(f'V29.5 basket creation anchor count={s.count(created_anchor)}; expected 1')
s = s.replace(created_anchor, created_new, 1)

manage_anchor = '''                UpdateBasketProtection(b, cur, money, r, positions);

                if (GridScaleOutEnabled && !b.ScaledOut && r >= GridScaleOutR)
'''
manage_new = '''                UpdateBasketProtection(b, cur, money, r, positions);

                // V29.5 THESIS-VALIDITY: the Development evidence shows that the
                // dominant tail baskets never proved favorable excursion before
                // consuming nearly the full initial risk budget. Fail closed only
                // after a short observation window and only while MFE remains below
                // the same proof threshold used by the Grid-add guard.
                if (V295ThesisGuard && ShouldV295InvalidateBasket(b, cur))
                {
                    double favR = V295PeakFavorableR(b);
                    double advR = V295AdverseR(b, cur);
                    _v295ThesisInvalidations++;
                    CloseBasket(id, b, "V295ThesisInvalidation", positions);
                    Print("[V295-THESIS-INVALIDATE] Basket #{0} pattern={1} favR={2:F3} advR={3:F3} ageMin={4:F1}",
                        id, b.PatternName, favR, advR, (Server.Time - b.CreatedTime).TotalMinutes);
                    continue;
                }

                if (GridScaleOutEnabled && !b.ScaledOut && r >= GridScaleOutR)
'''
if s.count(manage_anchor) != 1:
    raise SystemExit(f'V29.5 manage anchor count={s.count(manage_anchor)}; expected 1')
s = s.replace(manage_anchor, manage_new, 1)

helper_anchor = '''        private void TryAddGridLevel(GridBasket b, Position[] positions)
'''
helper_new = '''        private double V295PeakFavorableR(GridBasket b)
        {
            if (b == null || b.BaseRisk <= 0) return 0;
            double favorable = b.Direction == TradeDirection.Buy
                ? b.PeakPrice - b.BaseEntry
                : b.BaseEntry - b.PeakPrice;
            return Math.Max(0.0, favorable / Math.Max(b.BaseRisk, _symbol.PipSize));
        }

        private double V295AdverseR(GridBasket b, double cur)
        {
            if (b == null || b.BaseRisk <= 0) return 0;
            double adverse = b.Direction == TradeDirection.Buy
                ? b.BaseEntry - cur
                : cur - b.BaseEntry;
            return Math.Max(0.0, adverse / Math.Max(b.BaseRisk, _symbol.PipSize));
        }

        private bool ShouldV295InvalidateBasket(GridBasket b, double cur)
        {
            if (b == null) return false;
            if ((Server.Time - b.CreatedTime).TotalMinutes < V295MinInvalidationAgeMinutes) return false;
            return V295PeakFavorableR(b) < V295MinFavorableProofR
                && V295AdverseR(b, cur) >= V295NoMfeKillR;
        }

        private void TryAddGridLevel(GridBasket b, Position[] positions)
'''
if s.count(helper_anchor) != 1:
    raise SystemExit(f'V29.5 helper anchor count={s.count(helper_anchor)}; expected 1')
s = s.replace(helper_anchor, helper_new, 1)

grid_anchor = '''            if (b.DailyAdds >= GridMaxAddsPerDay) return;

            int nextLevel = b.LevelsOpened + 1;
'''
grid_new = '''            if (b.DailyAdds >= GridMaxAddsPerDay) return;

            // V29.5 CONTEXT-AWARE GRID: averaging is allowed only after the
            // original harmonic thesis has first demonstrated a minimum favorable
            // excursion. This preserves Grid recovery after proof, while blocking
            // the zero-MFE adverse adds identified in DEV-A.
            if (V295ThesisGuard && V295PeakFavorableR(b) < V295MinFavorableProofR)
            {
                _v295GridProofBlocked++;
                return;
            }

            int nextLevel = b.LevelsOpened + 1;
'''
if s.count(grid_anchor) != 1:
    raise SystemExit(f'V29.5 grid guard anchor count={s.count(grid_anchor)}; expected 1')
s = s.replace(grid_anchor, grid_new, 1)

basket_anchor = '''        public int LevelsOpened;
        public DateTime LastAddTime;
        public double WeightedEntry;
'''
basket_new = '''        public int LevelsOpened;
        public DateTime CreatedTime;
        public DateTime LastAddTime;
        public double WeightedEntry;
'''
if s.count(basket_anchor) != 1:
    raise SystemExit(f'V29.5 GridBasket anchor count={s.count(basket_anchor)}; expected 1')
s = s.replace(basket_anchor, basket_new, 1)

stop_anchor = '''            Print("[V294-EDGE-SUMMARY] directionBlocked={0} allowBuy={1} allowSell={2}", _v294DirectionBlocked, V294AllowBuy, V294AllowSell);
            EnsureServerSideProtectionBeforeStop();
'''
stop_new = '''            Print("[V294-EDGE-SUMMARY] directionBlocked={0} allowBuy={1} allowSell={2}", _v294DirectionBlocked, V294AllowBuy, V294AllowSell);
            Print("[V295-THESIS-SUMMARY] invalidations={0} gridProofBlocked={1} guard={2} killR={3:F2} proofR={4:F2}",
                _v295ThesisInvalidations, _v295GridProofBlocked, V295ThesisGuard, V295NoMfeKillR, V295MinFavorableProofR);
            EnsureServerSideProtectionBeforeStop();
'''
if s.count(stop_anchor) != 1:
    raise SystemExit(f'V29.5 stop anchor count={s.count(stop_anchor)}; expected 1')
s = s.replace(stop_anchor, stop_new, 1)

old_version = 'V29.4-Edge-Context-Gate-Dev'
if s.count(old_version) != 1:
    raise SystemExit(f'V29.5 version marker count={s.count(old_version)}; expected 1')
s = s.replace(old_version, 'V29.5-Thesis-Validity-Minimum-Patch-Dev', 1)

for token in [
    'V29.5-Thesis-Validity-Minimum-Patch-Dev',
    'V295ThesisGuard',
    'V295NoMfeKillR',
    'V295MinFavorableProofR',
    'ShouldV295InvalidateBasket',
    '[V295-THESIS-INVALIDATE]',
    '[V295-THESIS-SUMMARY]',
    'CreatedTime = Server.Time',
    'V29.3 GRID-RISK-CAP-HOTFIX',
    'V294AllowSell'
]:
    if token not in s:
        raise SystemExit('missing required V29.5 token: ' + token)

p.write_text(s, encoding='utf-8')
print('Applied V29.5 Thesis Validity Minimum Patch')
print('Scope: no-MFE thesis invalidation + proof-before-grid-add only; engineering core unchanged')
