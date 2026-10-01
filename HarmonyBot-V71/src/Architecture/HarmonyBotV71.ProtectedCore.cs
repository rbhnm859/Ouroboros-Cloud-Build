using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    // Protected V51 runtime/capital kernel.
    // This partial owns lifecycle/orchestration but shares state with the composition root.
    // Any change here requires 2021/2022/2023 exact replay before acceptance.
    public partial class HarmonyBotV71
    {
        protected override void OnStart()
        {
            _symbol = Symbols.GetSymbol(SymbolName);
            if (_symbol == null)
            {
                Print("[V51-FATAL] SYMBOL_NOT_FOUND {0}", SymbolName);
                Stop();
                return;
            }

            _h4Bars = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
            _h1Bars = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            _m15Bars = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _m1Bars = MarketData.GetBars(TimeFrame.Minute, SymbolName);

            if (!BarsObjectsReady())
            {
                Print("[V51-FATAL] TIMEFRAME_OBJECT_LOAD_FAILED");
                Stop();
                return;
            }

            WarmupBars(_h4Bars, 230, "H4");
            WarmupBars(_h1Bars, 230, "H1");
            WarmupBars(_m15Bars, 360, "M15");
            WarmupBars(_m1Bars, 120, "M1");

            if (!BarsReady())
                Print("[V51-WARMUP-PENDING] H4={0} H1={1} M15={2} M1={3}",
                    Count(_h4Bars), Count(_h1Bars), Count(_m15Bars), Count(_m1Bars));

            _londonTz = ResolveTimeZone("Europe/London", "GMT Standard Time");
            _newYorkTz = ResolveTimeZone("America/New_York", "Eastern Standard Time");
            if (_londonTz == null || _newYorkTz == null)
            {
                Print("[V51-FATAL] DST_TIMEZONE_UNAVAILABLE");
                Stop();
                return;
            }

            if (!string.IsNullOrWhiteSpace(EvaluationStartUtcIso))
            {
                DateTime parsed;
                if (DateTime.TryParse(EvaluationStartUtcIso, CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal, out parsed))
                    _evaluationStartUtc = parsed;
            }

            BuildPatternProfiles();
            _initialEquity = Account.Equity;
            _initialCapitalEligible = _initialEquity + 1e-8 >= MinimumSupportedEquity;
            _equityPeak = Account.Equity;
            ResetDaily(true);

            Positions.Closed += OnPositionClosed;
            Positions.Opened += OnPositionOpened;
            PendingOrders.Filled += OnPendingOrderFilled;

            PrintBrokerCapabilityProfile();

            Print("[V51-START] version={0} symbol={1} H4={2} H1={3} M15={4} M1={5} profiles={6}",
                Version, SymbolName, Count(_h4Bars), Count(_h1Bars), Count(_m15Bars), Count(_m1Bars), _profiles.Count);
            Print("[V51-TIMEFRAME-AUDIT] primaryPattern=M15 execution=M1 macro=H4 intermediate=H1 allCompletedBars=true");
            Print("[V51-SESSION-AUDIT] london={0} newYork={1} dstAware=true", _londonTz.Id, _newYorkTz.Id);
            Print("[V51-ALPHA-CONFIG] qualityObservation={0} legacyRegime={1} legacyEnhancedM1={2} capitalFeasibility={3} transitionVeto={4} exhaustionVeto={5} routeM1Veto={6}",
                EnableHarmonicRobustnessGate, EnableRegimeContextGate, EnableEnhancedM1Confirmation, EnableCapitalFeasibilityGate,
                EnableTransitionStateVeto, EnableExhaustionEvidenceVeto, EnableRouteSpecificM1Veto);
            Print("[V51-FREQUENCY-CONFIG] deferredRetention={0} agingPriority={1} ageBoost={2:F3} structuredRecall={3} recallGeometry={4:F3} recallPrz={5:F3} recallConfidence={6:F3}",
                EnableDeferredCandidateRetention, EnableFrequencyAgingPriority, CandidateAgeRankBoost, EnableStructuredRecallExpansion,
                RecallMinGeometry, RecallMinPrz, RecallMinConfidence);
            Print("[V51-RESTORED-KERNEL] canonicalSetup={0} canonicalStandard={1} independentPivotGraph={2} transitionProof={3} m1Rescue={4} rescueBars={5} diversityScheduler={6} executionClock=M1 projectedD=false",
                EnableCanonicalSetupIdentity, EnableCanonicalStandardCoordinates, EnableIndependentPivotGraph,
                EnableTransitionProofGate, EnableM1RescueLane, M1RescueMaxBars, EnableDiversityScheduler);
            Print("[V51-CONVERSION-ARCH] scaleRouteAdmission={0} temporalRescue={1} armedGrace={2} graceMinutes={3} preExecutionRevalidation={4}",
                EnableScaleRouteAdmission, EnableM1TemporalRescue, EnableArmedExecutionGrace, ArmedGraceMinutes,
                EnablePreExecutionGridRevalidation);
            Print("[V51-FAMILY-NATIVE] conversion={0} observation={1} principle=PATTERN_IDENTITY_NEQ_EXECUTION_IDENTITY", EnableFamilyNativeConversion, EnableFamilyNativeObservation);
            Print("[V51-COMPLETION-CONTRACT] canonicalContracts={0} familyCompletion={1} windowBars={2} provenLane=ABCD_SHARK_CYPHER_FROZEN",
                EnableCanonicalFamilyContracts, EnableFamilyCompletionContract, FamilyConfirmationWindowBars);
            Print("[V51-STRUCTURAL-GRID-CONTRACT] gridSpanV2={0} structuralInvalidationV2={1} rule=PRZ_LEGALITY_PLUS_RISK_RR_NOT_LEGACY_XA_MINSPAN",
                EnableGridSpanSemanticV2, EnableStructuralInvalidationV2);
            Print("[V51-MATH-GEOMETRY] jointGeometry={0} executionCorridor={1} entryAnchorForensics={2} rule=FAMILY_NATIVE_GEOMETRY_WITHOUT_RISK_RELAXATION",
                EnableFamilyNativeJointGeometry, EnableFamilyNativeExecutionCorridor, EnableEntryAnchorForensics);
            Print("[V51-THROUGHPUT-ARCH] persistentQueue={0} serialHandoff={1} nativeM1={2} nativeBars={3} decayRanking={4} hardLifetimeMinutes={5} alphaKernel=V46_SCALE_CONVERSION_FROZEN",
                EnablePersistentArmedQueue, EnableEventDrivenSerialHandoff, EnablePatternNativeM1Expansion,
                PatternNativeM1MaxBars, EnableOpportunityDecayRanking, ParkedHardLifetimeMinutes);
            Print("[V71-PROTECTED-CORE] trustedParent={0} expansionShadow={1} expansionExecution={2} expansionRiskCap={3:F2} bifurcationResearch={4} familyNativeCausal={5}",
                V51TrustedParent, EnableV71ExpansionShadow, EnableV71ExpansionExecution,
                Math.Min(5.0, V71ExpansionRiskPercent), EnableV72BifurcationAlpha, EnableV72FamilyNativeCausalAlpha);
            Print("[V71-INCREMENTAL-POLICY] corePreemption=true familyBalancedCensus={0} perFamilyCap={1} abcdSharePct={2} fullPivotLattice={3} familyNativeConfirmation={4} selectorModel=NONE overlapShadowVisible=true overlapCapitalBlocked=true",
                EnableV71FamilyBalancedCensus, Math.Max(2, Math.Min(12, V71PerFamilyCensusCap)),
                Math.Max(0, Math.Min(25, V71AbcdCensusSharePercent)), EnableV71FullFamilyPivotLattice,
                EnableV71FamilyNativeConfirmation);
        }

        protected override void OnStop()
        {
            V72HcogFinalizeAndPrint();
            V71FinalizeExpansionShadows();
            CancelAllOwnPending("BOT_STOP");
            EnsureServerProtection();
            Positions.Closed -= OnPositionClosed;
            Positions.Opened -= OnPositionOpened;
            PendingOrders.Filled -= OnPendingOrderFilled;
            foreach (var kv in _pipeline.OrderBy(k => k.Key))
            {
                var x = kv.Value;
                Print("[V51-PIPELINE] pattern={0} detected={1} validated={2} routed={3} prz={4} confirming={5} nativeTemporalPass={6} armed={7} slotBlocked={8} parked={9} revalidated={10} revalidationRejected={11} basketPlanned={12} leg0={13} leg1={14} leg2={15} leg3={16} basketClosed={17} executed={18} expired={19} rejected={20} invalidated={21}",
                    kv.Key, x.Detected, x.Validated, x.Routed, x.PrzWaiting, x.Confirming, x.NativeTemporalPass, x.Armed,
                    x.SlotBlocked, x.Parked, x.Revalidated, x.RevalidationRejected, x.BasketPlanned,
                    x.Leg0Executed, x.Leg1Filled, x.Leg2Filled, x.Leg3Filled, x.BasketClosed, x.Executed, x.Expired, x.Rejected, x.Invalidated);
            }
            if (EnableEntryAnchorForensics)
            {
                foreach (var c in _candidates.Values.Where(x => x.Signal != null && x.CompletionAnchorPrice > 0).OrderBy(x => x.CandidateId))
                {
                    Print("[V51-ENTRY-ANCHOR-FORENSICS] cid={0} setup={1} pattern={2} route={3} scale={4} completion={5} confirm={6} retest={7} completionMfeR={8:F3} completionMaeR={9:F3} confirmMfeR={10:F3} confirmMaeR={11:F3} retestMfeR={12:F3} retestMaeR={13:F3}",
                        c.CandidateId, c.SetupKey, c.Signal.PatternName, c.Route, c.Signal.PivotScale,
                        c.CompletionAnchorPrice, c.NativeConfirmAnchorPrice, c.NativeRetestAnchorPrice,
                        c.CompletionAnchorMfeR, c.CompletionAnchorMaeR, c.NativeConfirmMfeR, c.NativeConfirmMaeR,
                        c.NativeRetestMfeR, c.NativeRetestMaeR);
                }
            }
            Print("[V51-SUMMARY] candidates={0} baskets={1} openLedgers={2} executionErrors={3} gridRiskViolations={4} duplicateGridLegs={5} orphanPendingOrders={6} stopWideningViolations={7} gapThroughInvalidations={8} gapThroughSurvivors={9} unprotectedSurvivors={10} postFillProtectionFailures={11} actualBasketRiskViolations={12} executionStateViolations={13} virtualGridFills={14} microModeBaskets={15} capitalRejectedBaskets={16} marginRiskViolations={17}",
                _candidateSeq, _baskets.Count, _positions.Count, _executionErrors, _gridRiskViolations, _duplicateGridLegs, _orphanPendingOrders, _stopWideningViolations,
                _gapThroughInvalidations, _gapThroughSurvivors, _unprotectedSurvivors, _postFillProtectionFailures, _actualBasketRiskViolations, _executionStateViolations,
                _virtualGridFills, _microModeBaskets, _capitalRejectedBaskets, _marginRiskViolations);
            Print("[V51-ALPHA-SUMMARY] qualityRejected={0} regimeRejected={1} confirmationRejected={2} capitalInfeasible={3} alphaPassed={4}",
                _alphaQualityRejected, _regimeRejected, _confirmationRejected, _capitalInfeasibleCandidates, _alphaPassed);
            Print("[V71-EXPANSION-SUMMARY] detected={0} armed={1} executed={2} coreBlocked={3} eligibilityRejected={4} shadowClosed={5} riskScaled={6} active={7} selectorModel=NONE",
                _v71ExpansionDetected, _v71ExpansionArmed, _v71ExpansionExecuted, _v71ExpansionCoreBlocked,
                _v71ExpansionEligibilityRejected, _v71ExpansionShadowClosed,
                _v71ExpansionRiskScaled, _v71Expansion.Values.Count(x => x.IsActive));
            foreach (var kv in _v72PayoffCensus.OrderBy(x => x.Key))
            {
                string[] parts = kv.Key.Split('|');
                string lane = parts.Length > 0 ? parts[0] : "UNKNOWN";
                string family = parts.Length > 1 ? parts[1] : "UNKNOWN";
                var z = kv.Value;
                Print("[V72-PAYOFF-CENSUS] lane={0} family={1} n={2} sumR={3:F9} sumSqR={4:F9} gpR={5:F9} glR={6:F9} wins={7}",
                    lane, family, z.N, z.SumR, z.SumSqR, z.GrossProfitR, z.GrossLossR, z.Wins);
            }
            foreach (var fam in _profiles.Select(x => V71FamilyKey(x.Name)).Distinct().OrderBy(x => x))
            {
                int tracked = _v71FamilyTracked.ContainsKey(fam) ? _v71FamilyTracked[fam] : 0;
                int armed = _v71FamilyArmed.ContainsKey(fam) ? _v71FamilyArmed[fam] : 0;
                int overlap = _v71FamilyCoreOverlap.ContainsKey(fam) ? _v71FamilyCoreOverlap[fam] : 0;
                int closed = _v71FamilyShadowClosed.ContainsKey(fam) ? _v71FamilyShadowClosed[fam] : 0;
                Print("[V71-FAMILY-CENSUS] family={0} tracked={1} armed={2} coreOverlap={3} shadowClosed={4}",
                    fam, tracked, armed, overlap, closed);

                int expected = _v71OracleExpected.ContainsKey(fam) ? _v71OracleExpected[fam] : 0;
                int matched = _v71OracleMatched.ContainsKey(fam) ? _v71OracleMatched[fam] : 0;
                int missed = _v71OracleMissed.ContainsKey(fam) ? _v71OracleMissed[fam] : 0;
                double recall = expected > 0 ? (double)matched / expected : 1.0;
                Print("[V71-ORACLE-CENSUS] family={0} expected={1} matched={2} missed={3} recall={4:F6}",
                    fam, expected, matched, missed, recall);
            }
            foreach (var kv in _v71ExpansionRejectAttribution.OrderBy(x => x.Key))
            {
                string[] parts = kv.Key.Split('|');
                string fam = parts.Length > 0 ? parts[0] : "UNKNOWN";
                string reason = parts.Length > 1 ? parts[1] : "UNKNOWN";
                Print("[V71-EXP-REJECT-SUMMARY] family={0} reason={1} count={2}", fam, reason, kv.Value);
            }
            int oracleExpected = _v71OracleExpected.Values.Sum();
            int oracleMatched = _v71OracleMatched.Values.Sum();
            int oracleMissed = _v71OracleMissed.Values.Sum();
            Print("[V71-ORACLE-SUMMARY] expected={0} matched={1} missed={2} perfectRecall={3}",
                oracleExpected, oracleMatched, oracleMissed, oracleMissed == 0);
            Print("[V71-CORE-PRESERVATION] executed={0} fnv64={1:X16}", _v71CoreExecutionCount, _v71CoreExecutionFnv);
            Print("[V71-PROTECTED-RISK-SUMMARY] expansionNet={0:F2} reserveBlocked={1} riskCapped={2} coreRiskPct={3:F2}",
                V71ExpansionContributionNet(), _v71ExpansionRiskReserveBlocked, _v71ExpansionRiskCapped, BasketRiskPercent);
            Print("[V51-FREQUENCY-SUMMARY] schedulerDeferred={0} schedulerRecoveredExecutions={1} structuredRecallAdmitted={2} activeDeferred={3}",
                _schedulerDeferred, _schedulerRecoveredExecutions, _structuredRecallAdmitted, _deferredCandidates.Count);
            Print("[V51-INDEPENDENT-SETUP-SUMMARY] duplicateSuppressed={0} uniqueExecuted={1} rescueAdmissions={2} transitionProofRejected={3} independentScaleCandidates={4}",
                _canonicalDuplicateSuppressed, _executedSetupKeys.Count, _m1RescueAdmissions, _transitionProofRejected, _independentScaleCandidates);
            Print("[V51-CONVERSION-SUMMARY] scaleRouteRejected={0} temporalRescueAdmissions={1} armedGraceExtended={2} preExecutionRevalidationRejected={3}",
                _scaleRouteRejected, _temporalRescueAdmissions, _armedGraceExtended, _preExecutionRevalidationRejected);
            double avgWait = _slotWaitMinutes.Count > 0 ? _slotWaitMinutes.Average() : 0;
            double medWait = Percentile(_slotWaitMinutes, .50);
            double p90Wait = Percentile(_slotWaitMinutes, .90);
            double avgOccupancy = _basketOccupancyMinutes.Count > 0 ? _basketOccupancyMinutes.Average() : 0;
            Print("[V51-THROUGHPUT-SUMMARY] slotBlocked={0} parked={1} revalidated={2} revalidationRejected={3} recoveredExecutions={4} nativeTemporalPass={5} hardLifetimeExpired={6} decayRejected={7} avgSlotWaitMin={8:F2} medianSlotWaitMin={9:F2} p90SlotWaitMin={10:F2} avgBasketOccupancyMin={11:F2} missedPositive={12} avoidedNegative={13}",
                _slotBlocked, _parkedCount, _parkedRevalidated, _parkedRevalidationRejected, _parkedRecoveredExecutions,
                _nativeTemporalPass, _hardLifetimeExpired, _opportunityDecayRejected, avgWait, medWait, p90Wait, avgOccupancy,
                _missedPositiveSetups, _avoidedNegativeSetups);
            foreach (var p in _profiles.Select(x => x.Name).Distinct().OrderBy(x => x))
            {
                int pass = _familyContractPass.ContainsKey(p) ? _familyContractPass[p] : 0;
                int reject = _familyContractWindowReject.ContainsKey(p) ? _familyContractWindowReject[p] : 0;
                Print("[V51-FAMILY-CONTRACT-SUMMARY] pattern={0} pass={1} windowReject={2}", p, pass, reject);
            }
            foreach (var kv in _gridPlanRejectReasons.OrderBy(k => k.Key))
                Print("[V51-GRID-REJECT-SUMMARY] reason={0} count={1}", kv.Key, kv.Value);
            foreach (var kv in _executionErrorReasons.OrderBy(k => k.Key))
                Print("[V51-EXECUTION-ERROR-SUMMARY] code={0} count={1}", kv.Key, kv.Value);
        }

        protected override void OnBar()
        {
            try
            {
                if (!BarsReady()) return;
                ResetDaily(false);
                UpdateRiskLocks();

                ProcessNewM15Close();
                ProcessNewM1Close();
            }
            catch (Exception ex)
            {
                RecordExecutionError("EXCEPTION_ONBAR", ex.GetType().Name + ":" + ex.Message);
            }
        }

        protected override void OnTick()
        {
            try
            {
                ResetDaily(false);
                UpdateRiskLocks();
                ReconcileAndManageBaskets();
            }
            catch (Exception ex)
            {
                RecordExecutionError("EXCEPTION_ONTICK", ex.GetType().Name + ":" + ex.Message);
            }
        }

        private void ProcessNewM15Close()
        {
            int i = LastClosedIndex(_m15Bars);
            if (i < 50) return;
            DateTime t = _m15Bars.OpenTimes[i];
            if (t <= _lastM15Closed) return;
            _lastM15Closed = t;

            double atr = Atr(_m15Bars, 14, i);
            if (atr <= 0) return;

            var h4State = GetActiveHarmonicState(_h4Bars, H4SwingDepth, 220, 3);
            var h1State = GetActiveHarmonicState(_h1Bars, H1SwingDepth, 260, 4);
            var regime = BuildRegimeSnapshot();
            var detected = DetectPatternCandidates(_m15Bars, i, M15SwingDepth, M15SwingLookback, PortfolioMaxCandidates, "M15");

            foreach (var signal in detected)
            {
                string setupKey = BuildSetupGeometryKey(signal);
                if (EnableCanonicalSetupIdentity)
                {
                    if (_executedSetupKeys.Contains(setupKey))
                    {
                        _canonicalDuplicateSuppressed++;
                        continue;
                    }
                    string owner;
                    if (_activeSetupOwners.TryGetValue(setupKey, out owner))
                    {
                        CandidateRecord existing;
                        if (_candidates.TryGetValue(owner, out existing) && existing.IsActive)
                        {
                            _canonicalDuplicateSuppressed++;
                            continue;
                        }
                        _activeSetupOwners.Remove(setupKey);
                    }
                }

                string id = NewCandidateId(signal);
                if (_candidates.ContainsKey(id)) continue;

                var record = new CandidateRecord
                {
                    CandidateId = id,
                    SetupKey = setupKey,
                    Signal = signal,
                    State = CandidateState.DETECTED,
                    DetectedUtc = Server.Time.ToUniversalTime(),
                    ExpiryUtc = Server.Time.ToUniversalTime().AddMinutes(15.0 * Math.Max(2, Math.Min(CandidateTtlM15Bars, signal.Profile.MaxAgeM15Bars))),
                    LastReason = "PATTERN_DETECTED"
                };
                _candidates[id] = record;
                if (EnableCanonicalSetupIdentity) _activeSetupOwners[setupKey] = id;
                CountPipeline(signal.PatternName).Detected++;
                Ledger(record, CandidateState.DETECTED, "PATTERN_DETECTED");

                if (signal.GeometryQuality < Math.Max(MinGeometryQuality, signal.Profile.MinGeometry) ||
                    signal.PrzConfluence < Math.Max(MinPrzConfluence, signal.Profile.MinPrz))
                {
                    Reject(record, "PATTERN_QUALITY");
                    continue;
                }

                record.AlphaQualityScore = HarmonicRobustnessScore(signal);
                if (EnableHarmonicRobustnessGate && !HarmonicRobustnessEligible(signal, record.AlphaQualityScore))
                {
                    _alphaQualityRejected++;
                    Event(record, "HARMONIC_ROBUSTNESS_OBSERVATION_ONLY");
                }

                Transition(record, CandidateState.VALIDATED, "PATTERN_VALIDATED");
                CountPipeline(signal.PatternName).Validated++;

                record.Conflict = ClassifyMtfConflict(signal.Direction, h4State, h1State);
                record.Regime = regime;
                record.RegimeScore = RegimeContextScore(signal, record.Conflict, regime);
                record.Route = RouteSignal(signal, record.Conflict, regime);

                if (record.Route == HarmonicRoute.NO_TRADE)
                {
                    if (EnableRegimeContextGate) _regimeRejected++;
                    Reject(record, "ROUTER_NO_TRADE");
                    continue;
                }

                // V47 expands only genuinely independent secondary-scale setups.
                // V45 DEV showed secondary-scale AB=CD exhaustion positive in A/B/C,
                // while secondary-scale trend-aligned AB=CD was negative overall.
                if (EnableScaleRouteAdmission && signal.PivotScale != M15SwingDepth &&
                    signal.PatternName == "AB=CD" && record.Route != HarmonicRoute.EXHAUSTION_REVERSAL)
                {
                    _scaleRouteRejected++;
                    Reject(record, "SECONDARY_SCALE_ABCD_ROUTE_REJECT");
                    continue;
                }

                if (EnableCapitalFeasibilityGate)
                {
                    double minL0Risk, minL0Margin;
                    record.CapitalFeasible = CapitalFeasibilityEligible(record, out minL0Risk, out minL0Margin);
                    record.CapitalMinL0Risk = minL0Risk;
                    record.CapitalMinL0Margin = minL0Margin;
                    if (!record.CapitalFeasible)
                    {
                        _capitalInfeasibleCandidates++;
                        Reject(record, "CAPITAL_INFEASIBLE_PRECHECK");
                        continue;
                    }
                }
                else record.CapitalFeasible = true;

                Print("[V51-ALPHA-CANDIDATE] cid={0} pattern={1} quality={2:F3} regime={3:F3} conflict={4} route={5} adxH1={6:F2} adxH4={7:F2} adxSlope={8:F2} atrPct={9:F3} efficiency={10:F3} capitalFeasible={11} minL0Risk={12:F4}",
                    record.CandidateId, signal.PatternName, record.AlphaQualityScore, record.RegimeScore, record.Conflict, record.Route,
                    regime.AdxH1, regime.AdxH4, regime.AdxH1Slope, regime.AtrPercentile, regime.Efficiency,
                    record.CapitalFeasible, record.CapitalMinL0Risk);

                Transition(record, CandidateState.ROUTED, "ROUTE_" + record.Route);
                CountPipeline(signal.PatternName).Routed++;
                Transition(record, CandidateState.WAIT_PRZ, "WAIT_PRZ");
                CountPipeline(signal.PatternName).PrzWaiting++;
            }

            // V71 invariant: establish the exact V51 core candidate book first.
            // Expansion is discovered only after core ownership is known, so identical setups
            // can never enter the expansion book.
            V71PreemptExpansionForCore(Server.Time.ToUniversalTime());
            if (EnableV71ExpansionShadow || EnableV71ExpansionExecution || EnableV72HcogAlpha || EnableV72HcapAlpha)
            {
                int expansionLimit = Math.Max(8, Math.Min(32, V71ExpansionMaxCandidates));
                int expansionPoolLimit = (EnableV72HcogAlpha || EnableV72HcapAlpha) ? 128 :
                    (EnableV71FamilyBalancedCensus ? Math.Max(64, Math.Min(128, expansionLimit * 4)) : expansionLimit);
                var expansionPool = V71DetectExpansionPatternCandidates(_m15Bars, i, M15SwingDepth, M15SwingLookback, expansionPoolLimit, "M15");
                if (EnableV72HcogAlpha || EnableV72HcapAlpha) V72HcogTrackRawPool(expansionPool, h4State, h1State, regime);
                bool legacyResearch = EnableV71ExpansionShadow || EnableV72BifurcationAlpha || EnableV72FamilyNativeCausalAlpha || EnableV72FailureAuctionCausalAlpha;
                if (legacyResearch)
                {
                    var expansionDetected = V71SelectExpansionSignals(expansionPool, expansionLimit);
                    foreach (var expansionSignal in expansionDetected) V71TrackExpansionSignal(expansionSignal, h4State, h1State, regime);
                }
            }

            TrimCandidateBook();
        }

        private void ProcessNewM1Close()
        {
            int i = LastClosedIndex(_m1Bars);
            if (i < 10) return;
            DateTime t = _m1Bars.OpenTimes[i];
            if (t <= _lastM1Closed) return;
            _lastM1Closed = t;
            DateTime utc = DateTime.SpecifyKind(t, DateTimeKind.Utc);

            if (EnableV71ExpansionShadow || EnableV71ExpansionExecution)
                V71ProcessExpansionM1(i, utc);
            if (EnableV72HcogAlpha || EnableV72HcapAlpha)
                V72HcogProcessM1(i, utc);

            foreach (var c in _candidates.Values.Where(x => x.IsActive).ToList())
            {
                UpdateOpportunityShadow(c, i);
                if (EnableEntryAnchorForensics) UpdateEntryAnchorForensics(c, i);

                bool queuedState = c.State == CandidateState.SLOT_BLOCKED || c.State == CandidateState.PARKED ||
                                   c.State == CandidateState.REVALIDATING || c.State == CandidateState.EXECUTABLE;
                if (queuedState && EnablePersistentArmedQueue)
                {
                    if (c.ParkedHardExpiryUtc.HasValue && utc >= c.ParkedHardExpiryUtc.Value)
                    {
                        _hardLifetimeExpired++;
                        MarkOpportunityTerminal(c, "HARD_LIFETIME_EXPIRED");
                        Expire(c, "HARD_LIFETIME_EXPIRED");
                        continue;
                    }
                    if (!IsInstitutionalSession(utc))
                    {
                        MarkOpportunityTerminal(c, "SESSION_EXPIRED");
                        Expire(c, "SESSION_EXPIRED");
                        continue;
                    }
                }
                else if (utc >= c.ExpiryUtc)
                {
                    Expire(c, "TTL_EXPIRED");
                    continue;
                }

                if (PatternInvalidatedBeforeEntry(c.Signal))
                {
                    MarkOpportunityTerminal(c, "STRUCTURAL_INVALIDATION");
                    Invalidate(c, "STRUCTURAL_INVALIDATION");
                    continue;
                }

                if (c.State == CandidateState.WAIT_PRZ)
                {
                    if (BarTouchesPrz(i, c.Signal))
                    {
                        c.PrzTouchUtc = utc;
                        if (EnableEntryAnchorForensics && c.CompletionAnchorPrice <= 0)
                            c.CompletionAnchorPrice = c.Signal.D.Price;
                        Transition(c, CandidateState.CONFIRMING, "PRZ_RETEST");
                        CountPipeline(c.Signal.PatternName).Confirming++;
                    }
                    continue;
                }

                if (c.State == CandidateState.CONFIRMING)
                {
                    if (!c.PrzTouchUtc.HasValue || utc <= c.PrzTouchUtc.Value) continue;

                    double legacyScore = M1ConfirmationScore(i, c.Signal);
                    c.ConfirmationScore = legacyScore;
                    double legacyRequired = c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 0.75 : 0.60;
                    bool familyContractLane = EnableFamilyCompletionContract && IsFamilyCompletionLane(c.Signal.PatternName);
                    bool confirmationPass = false;

                    if (familyContractLane)
                    {
                        c.FamilyConfirmationBarsObserved++;
                        double familyScore;
                        confirmationPass = UpdateFamilyCompletionEvidence(i, c, out familyScore);
                        c.ConfirmationScore = Math.Max(c.ConfirmationScore, familyScore);
                        if (EnableEntryAnchorForensics && c.FamilyRetest && c.NativeRetestAnchorPrice <= 0)
                            c.NativeRetestAnchorPrice = _m1Bars.ClosePrices[i];
                        if (confirmationPass)
                        {
                            IncrementCounter(_familyContractPass, c.Signal.PatternName);
                            Event(c, "FAMILY_COMPLETION_CONTRACT_PASS_" + familyScore.ToString("F2", CultureInfo.InvariantCulture));
                        }
                        else if (c.FamilyConfirmationBarsObserved >= Math.Max(6, FamilyConfirmationWindowBars))
                        {
                            IncrementCounter(_familyContractWindowReject, c.Signal.PatternName);
                            Reject(c, "FAMILY_COMPLETION_WINDOW_EXHAUSTED");
                            continue;
                        }
                    }
                    else confirmationPass = legacyScore >= legacyRequired;

                    if (!familyContractLane && !confirmationPass && EnablePatternNativeM1Expansion)
                    {
                        c.NativeM1BarsObserved++;
                        double nativeScore;
                        if (c.NativeM1BarsObserved <= Math.Max(3, Math.Min(4, PatternNativeM1MaxBars)) &&
                            UpdatePatternNativeM1State(i, c, out nativeScore))
                        {
                            c.ConfirmationScore = Math.Max(c.ConfirmationScore, nativeScore);
                            confirmationPass = true;
                            _nativeTemporalPass++;
                            CountPipeline(c.Signal.PatternName).NativeTemporalPass++;
                            Event(c, "PATTERN_NATIVE_M1_PASS_" + nativeScore.ToString("F2", CultureInfo.InvariantCulture));
                        }
                    }

                    if (!confirmationPass && EnableM1RescueLane)
                    {
                        c.RescueBarsObserved++;
                        double enhanced = EnhancedM1ConfirmationScore(i, c.Signal, c.Route, c.Regime);
                        c.RescueBestScore = Math.Max(c.RescueBestScore, enhanced);
                        bool evidencePass = RouteSpecificM1EvidencePass(i, c.Signal, c.Route);
                        double rescueThreshold = EnhancedM1Threshold(c.Route);
                        confirmationPass = c.RescueBarsObserved <= Math.Max(1, M1RescueMaxBars) &&
                                           enhanced >= rescueThreshold && evidencePass;
                        if (confirmationPass)
                        {
                            c.ConfirmationScore = enhanced;
                            _m1RescueAdmissions++;
                            Event(c, "M1_RESCUE_ADMITTED_" + enhanced.ToString("F2", CultureInfo.InvariantCulture));
                        }

                        if (!confirmationPass && EnableM1TemporalRescue &&
                            c.RescueBarsObserved <= Math.Max(1, M1RescueMaxBars))
                        {
                            double temporalScore;
                            if (UpdateM1TemporalEvidence(i, c, out temporalScore))
                            {
                                c.ConfirmationScore = Math.Max(c.ConfirmationScore, temporalScore);
                                confirmationPass = true;
                                _temporalRescueAdmissions++;
                                Event(c, "M1_TEMPORAL_RESCUE_ADMITTED_" + temporalScore.ToString("F2", CultureInfo.InvariantCulture));
                            }
                        }
                    }

                    if (!confirmationPass)
                    {
                        Event(c, "LEGACY_CONFIRMATION_FAILED_" + legacyScore.ToString("F2", CultureInfo.InvariantCulture));
                        continue;
                    }

                    if (EnableEntryAnchorForensics && c.NativeConfirmAnchorPrice <= 0)
                        c.NativeConfirmAnchorPrice = _m1Bars.ClosePrices[i];

                    if (EnableRouteSpecificM1Veto && !RouteSpecificM1EvidencePass(i, c.Signal, c.Route))
                    {
                        _confirmationRejected++;
                        Event(c, "ROUTE_SPECIFIC_M1_VETO");
                        continue;
                    }

                    if (!TryBuildFibonacciGridPlan(c))
                    {
                        Reject(c, "FIB_GRID_PLAN_REJECTED");
                        continue;
                    }

                    c.Rank = CandidateRank(c);
                    _alphaPassed++;
                    c.ArmedUtc = utc;
                    if (EnableArmedExecutionGrace)
                    {
                        DateTime graceExpiry = utc.AddMinutes(Math.Max(15, ArmedGraceMinutes));
                        if (graceExpiry > c.ExpiryUtc)
                        {
                            c.ExpiryUtc = graceExpiry;
                            c.ArmedGraceApplied = true;
                            _armedGraceExtended++;
                        }
                    }
                    Transition(c, CandidateState.ARMED, "CONFIRMATION_PASSED_GRID_PREPLANNED");
                    CountPipeline(c.Signal.PatternName).Armed++;
                }
            }

            TryScheduleAndExecute();
        }

        private void TryScheduleAndExecute()
        {
            if (!TradingEnabled) return;
            if (!_initialCapitalEligible) return;
            DateTime now = Server.Time.ToUniversalTime();
            if (_evaluationStartUtc.HasValue && now < _evaluationStartUtc.Value) return;

            // Core ownership must be asserted before a shared account risk lock can return.
            // This lets a newly-detected V51 thesis remove an expansion basket immediately;
            // the normal V51 risk lock still governs whether the core may then execute.
            V71PreemptExpansionForCore(now);
            if (_dailyLocked || PeakDrawdownExceeded()) return;

            bool slotBusy = OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive);
            if (slotBusy)
            {
                if (EnablePersistentArmedQueue) ParkArmedCandidates(now);
                return;
            }

            if (!IsInstitutionalSession(now) || !SpreadValid())
            {
                if (EnablePersistentArmedQueue) SweepParkedHardValidity(now);
                return;
            }

            if (EnablePersistentArmedQueue)
                RevalidateParkedQueue(now);

            var executableStates = EnablePersistentArmedQueue
                ? new[] { CandidateState.ARMED, CandidateState.EXECUTABLE }
                : new[] { CandidateState.ARMED };

            var armedQuery = _candidates.Values
                .Where(c => executableStates.Contains(c.State) && c.IsActive && c.GridPlan != null &&
                            (!EnableCanonicalSetupIdentity || !_executedSetupKeys.Contains(c.SetupKey)));

            if (EnableDiversityScheduler)
                armedQuery = armedQuery.GroupBy(c => string.IsNullOrWhiteSpace(c.SetupKey) ? c.CandidateId : c.SetupKey)
                    .Select(g => g.OrderByDescending(c => EnableOpportunityDecayRanking ? OpportunityScore(c, now) : c.Rank).First());

            var armed = armedQuery
                .OrderByDescending(c => EnableOpportunityDecayRanking ? OpportunityScore(c, now) : c.Rank)
                .ToList();
            if (armed.Count == 0)
            {
                V71TryExecuteExpansion(now);
                return;
            }

            var winner = armed[0];

            if (EnablePreExecutionGridRevalidation || (EnablePersistentArmedQueue && winner.WasParked))
            {
                winner.GridPlan = null;
                Transition(winner, CandidateState.REVALIDATING, "PRE_EXECUTION_REVALIDATION");
                if (!RevalidateCandidateForExecution(winner, now, true))
                {
                    _preExecutionRevalidationRejected++;
                    _parkedRevalidationRejected += winner.WasParked ? 1 : 0;
                    CountPipeline(winner.Signal.PatternName).RevalidationRejected++;
                    MarkOpportunityTerminal(winner, "PRE_EXECUTION_REVALIDATION_FAILED");
                    Reject(winner, "PRE_EXECUTION_REVALIDATION_FAILED");
                    return;
                }
                CountPipeline(winner.Signal.PatternName).Revalidated++;
                Transition(winner, CandidateState.EXECUTABLE, "REVALIDATED_EXECUTABLE");
                winner.Rank = CandidateRank(winner);
            }

            ExecuteFibonacciGridPlan(winner);

            if (winner.State == CandidateState.EXECUTED)
            {
                if (winner.WasParked && winner.ParkedUtc.HasValue)
                {
                    double wait = Math.Max(0, (now - winner.ParkedUtc.Value).TotalMinutes);
                    _slotWaitMinutes.Add(wait);
                    _parkedRecoveredExecutions++;
                    Event(winner, "PARKED_RECOVERED_EXECUTION_WAIT_" + wait.ToString("F1", CultureInfo.InvariantCulture));
                }
                _parkedCandidateIds.Remove(winner.CandidateId);
                if (_deferredCandidates.Remove(winner.CandidateId))
                    _schedulerRecoveredExecutions++;

                foreach (var other in armed.Skip(1))
                {
                    if (EnablePersistentArmedQueue)
                    {
                        ParkCandidate(other, now, "SERIAL_SLOT_DEFERRED");
                    }
                    else if (EnableDeferredCandidateRetention)
                    {
                        if (_deferredCandidates.Add(other.CandidateId))
                            _schedulerDeferred++;
                        Event(other, "SCHEDULER_DEFERRED_KEEP_ALIVE");
                    }
                    else
                    {
                        Reject(other, "SINGLE_BASKET_SCHEDULER");
                    }
                }
            }
        }

        private void ParkArmedCandidates(DateTime now)
        {
            foreach (var c in _candidates.Values.Where(x => x.IsActive && x.State == CandidateState.ARMED).ToList())
                ParkCandidate(c, now, "SLOT_BLOCKED");
        }

        private void ParkCandidate(CandidateRecord c, DateTime now, string reason)
        {
            if (c == null || !c.IsActive || c.State == CandidateState.EXECUTED) return;
            if (!c.ParkedUtc.HasValue)
            {
                c.ParkedUtc = now;
                c.ParkedHardExpiryUtc = c.ArmedUtc.HasValue
                    ? c.ArmedUtc.Value.AddMinutes(Math.Max(180, ParkedHardLifetimeMinutes))
                    : now.AddMinutes(Math.Max(180, ParkedHardLifetimeMinutes));
                c.OriginalRank = c.Rank;
                c.OriginalGeometry = c.Signal.GeometryQuality;
                c.OriginalPrzConfluence = c.Signal.PrzConfluence;
                c.OriginalM1Evidence = c.ConfirmationScore;
                c.OriginalEntryAnchor = c.GridPlan != null ? c.GridPlan.EntryAnchor : (c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid);
                c.ShadowRiskDistance = Math.Max(Math.Abs(c.OriginalEntryAnchor - c.Signal.StructuralInvalidation), _symbol.PipSize);
                c.WasParked = true;
                _parkedCount++;
                CountPipeline(c.Signal.PatternName).Parked++;
            }
            _slotBlocked++;
            CountPipeline(c.Signal.PatternName).SlotBlocked++;
            c.GridPlan = null;
            _parkedCandidateIds.Add(c.CandidateId);
            Transition(c, CandidateState.SLOT_BLOCKED, reason);
            Transition(c, CandidateState.PARKED, "PARKED_NO_BROKER_ORDER_NO_RESERVED_RISK");
        }

        private void SweepParkedHardValidity(DateTime now)
        {
            foreach (var c in _candidates.Values.Where(x => x.IsActive && (x.State == CandidateState.PARKED || x.State == CandidateState.SLOT_BLOCKED)).ToList())
            {
                if (!HardThesisValid(c, now, false, out string reason))
                {
                    MarkOpportunityTerminal(c, reason);
                    if (reason == "STRUCTURAL_INVALIDATION" || reason == "MTF_HARD_CONFLICT") Invalidate(c, reason);
                    else Expire(c, reason);
                }
            }
        }

        private void RevalidateParkedQueue(DateTime now)
        {
            foreach (var c in _candidates.Values
                .Where(x => x.IsActive && (x.State == CandidateState.PARKED || x.State == CandidateState.SLOT_BLOCKED))
                .OrderByDescending(x => EnableOpportunityDecayRanking ? OpportunityScore(x, now) : x.Rank)
                .ToList())
            {
                Transition(c, CandidateState.REVALIDATING, "SLOT_RELEASE_REVALIDATION");
                if (!RevalidateCandidateForExecution(c, now, false))
                {
                    _parkedRevalidationRejected++;
                    CountPipeline(c.Signal.PatternName).RevalidationRejected++;
                    MarkOpportunityTerminal(c, "PARKED_REVALIDATION_REJECTED");
                    Reject(c, "PARKED_REVALIDATION_REJECTED");
                    continue;
                }
                _parkedRevalidated++;
                CountPipeline(c.Signal.PatternName).Revalidated++;
                c.Rank = CandidateRank(c);
                Transition(c, CandidateState.EXECUTABLE, "PARKED_REVALIDATED");
            }
        }

        private bool RevalidateCandidateForExecution(CandidateRecord c, DateTime now, bool finalCheck)
        {
            if (!HardThesisValid(c, now, true, out string reason))
            {
                Event(c, "REVALIDATION_HARD_FAIL_" + reason);
                return false;
            }
            c.GridPlan = null;
            if (!TryBuildFibonacciGridPlan(c)) return false;
            if (c.NetRR < MinimumNetRR) return false;
            if (c.GridPlan == null || c.GridPlan.WorstCaseRisk > c.GridPlan.BasketRiskAmount + 1e-8) return false;
            if (Account.FreeMargin < c.GridPlan.BasketRiskAmount * MinFreeMarginRiskMultiple) return false;
            if (finalCheck && !SpreadValid()) return false;
            return true;
        }

        private bool HardThesisValid(CandidateRecord c, DateTime now, bool requireTradableSession, out string reason)
        {
            reason = "";
            if (c == null || c.Signal == null || !c.IsActive) { reason = "INACTIVE"; return false; }
            if (EnableCanonicalSetupIdentity && _executedSetupKeys.Contains(c.SetupKey)) { reason = "SETUP_ALREADY_EXECUTED"; return false; }
            if (c.ParkedHardExpiryUtc.HasValue && now >= c.ParkedHardExpiryUtc.Value) { reason = "HARD_LIFETIME_EXPIRED"; return false; }
            if (requireTradableSession && !IsInstitutionalSession(now)) { reason = "SESSION_EXPIRED"; return false; }
            if (PatternInvalidatedBeforeEntry(c.Signal)) { reason = "STRUCTURAL_INVALIDATION"; return false; }
            double px = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            if (c.Signal.Direction == TradeDirection.Buy && px >= c.Signal.CanonicalTarget1) { reason = "TARGET_ALREADY_REACHED"; return false; }
            if (c.Signal.Direction == TradeDirection.Sell && px <= c.Signal.CanonicalTarget1) { reason = "TARGET_ALREADY_REACHED"; return false; }
            var h4 = GetActiveHarmonicState(_h4Bars, H4SwingDepth, 220, 3);
            var h1 = GetActiveHarmonicState(_h1Bars, H1SwingDepth, 260, 4);
            if (ClassifyMtfConflict(c.Signal.Direction, h4, h1) == MtfConflict.CONFLICT &&
                c.Route != HarmonicRoute.EXHAUSTION_REVERSAL) { reason = "MTF_HARD_CONFLICT"; return false; }
            if (_dailyLocked || PeakDrawdownExceeded()) { reason = "RISK_LOCK"; return false; }
            if (!SpreadValid()) { reason = "SPREAD_INVALID"; return false; }
            return true;
        }

        private void UpdateEntryAnchorForensics(CandidateRecord c, int i)
        {
            if (c == null || c.Signal == null || i < 0 || i >= _m1Bars.Count) return;
            UpdateAnchorExcursion(c.Signal.Direction, c.Signal.StructuralInvalidation, c.CompletionAnchorPrice, i, ref c.CompletionAnchorMfeR, ref c.CompletionAnchorMaeR);
            UpdateAnchorExcursion(c.Signal.Direction, c.Signal.StructuralInvalidation, c.NativeConfirmAnchorPrice, i, ref c.NativeConfirmMfeR, ref c.NativeConfirmMaeR);
            UpdateAnchorExcursion(c.Signal.Direction, c.Signal.StructuralInvalidation, c.NativeRetestAnchorPrice, i, ref c.NativeRetestMfeR, ref c.NativeRetestMaeR);
        }

        private void UpdateAnchorExcursion(TradeDirection direction, double stop, double anchor, int i, ref double mfeR, ref double maeR)
        {
            if (anchor <= 0) return;
            double risk = Math.Abs(anchor - stop);
            if (risk <= _symbol.PipSize) return;
            double fav, adv;
            if (direction == TradeDirection.Buy)
            {
                fav = (_m1Bars.HighPrices[i] - anchor) / risk;
                adv = (anchor - _m1Bars.LowPrices[i]) / risk;
            }
            else
            {
                fav = (anchor - _m1Bars.LowPrices[i]) / risk;
                adv = (_m1Bars.HighPrices[i] - anchor) / risk;
            }
            mfeR = Math.Max(mfeR, fav);
            maeR = Math.Max(maeR, adv);
        }

        private double OpportunityScore(CandidateRecord c, DateTime now)
        {
            if (c == null || c.Signal == null) return -999;
            double conservativeAlpha = VClamp(.35 * c.AlphaQualityScore + .25 * c.Signal.GeometryQuality +
                                              .20 * c.Signal.PrzConfluence + .20 * c.ConfirmationScore);
            double remainingRr = VClamp(c.NetRR / 3.0);
            double ageMin = c.ParkedUtc.HasValue ? Math.Max(0, (now - c.ParkedUtc.Value).TotalMinutes) : 0;
            double freshness = Math.Exp(-ageMin / 120.0);
            double evidence = VClamp(c.ConfirmationScore);
            double routeReliability = c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? .88 :
                                      c.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? .90 : .82;
            double expectedSlotMinutes = c.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? 90.0 :
                                         c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 120.0 : 75.0;
            double drift = c.OriginalEntryAnchor > 0 ? Math.Abs((c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid) - c.OriginalEntryAnchor) /
                           Math.Max(c.ShadowRiskDistance, _symbol.PipSize) : 0;
            double priceDriftPenalty = Math.Min(.35, drift * .18);
            double thesisAgePenalty = Math.Min(.30, ageMin / Math.Max(180.0, ParkedHardLifetimeMinutes) * .30);
            double structuralDistancePenalty = Math.Min(.25, Math.Abs((c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid) - c.Signal.D.Price) /
                                                     Math.Max(c.ShadowRiskDistance, _symbol.PipSize) * .10);
            double spreadPenalty = Math.Min(.20, CurrentSpreadPips() / Math.Max(1.0, MaxSpreadPips) * .20);
            double marginBurdenPenalty = Account.FreeMargin > 0 && c.GridPlan != null
                ? Math.Min(.20, c.GridPlan.EstimatedPhysicalMargin / Math.Max(Account.FreeMargin, 1.0) * .20) : 0;
            double density = conservativeAlpha * Math.Max(.10, remainingRr) * Math.Max(.10, freshness) *
                             Math.Max(.10, evidence) * routeReliability / Math.Max(1.0, expectedSlotMinutes / 60.0);
            return density - priceDriftPenalty - thesisAgePenalty - structuralDistancePenalty - spreadPenalty - marginBurdenPenalty;
        }

        private void UpdateOpportunityShadow(CandidateRecord c, int i)
        {
            if (c == null || !c.WasParked || c.ShadowRiskDistance <= 0 || i < 0 || i >= _m1Bars.Count) return;
            double fav, adv;
            if (c.Signal.Direction == TradeDirection.Buy)
            {
                fav = (_m1Bars.HighPrices[i] - c.OriginalEntryAnchor) / c.ShadowRiskDistance;
                adv = (c.OriginalEntryAnchor - _m1Bars.LowPrices[i]) / c.ShadowRiskDistance;
            }
            else
            {
                fav = (c.OriginalEntryAnchor - _m1Bars.LowPrices[i]) / c.ShadowRiskDistance;
                adv = (_m1Bars.HighPrices[i] - c.OriginalEntryAnchor) / c.ShadowRiskDistance;
            }
            c.ShadowMfeR = Math.Max(c.ShadowMfeR, fav);
            c.ShadowMaeR = Math.Max(c.ShadowMaeR, adv);
        }

        private void MarkOpportunityTerminal(CandidateRecord c, string reason)
        {
            if (c == null || !c.WasParked || c.OpportunityTerminalLogged) return;
            c.OpportunityTerminalLogged = true;
            bool missedPositive = c.ShadowMfeR >= 1.0 && c.ShadowMfeR > c.ShadowMaeR;
            bool avoidedNegative = c.ShadowMaeR >= 1.0 && c.ShadowMaeR > c.ShadowMfeR;
            if (missedPositive) _missedPositiveSetups++;
            if (avoidedNegative) _avoidedNegativeSetups++;
            Print("[V51-OPPORTUNITY-LOSS] cid={0} setup={1} pattern={2} route={3} scale={4} reason={5} shadowMfeR={6:F3} shadowMaeR={7:F3} missedPositive={8} avoidedNegative={9}",
                c.CandidateId, c.SetupKey, c.Signal.PatternName, c.Route, c.Signal.PivotScale, reason,
                c.ShadowMfeR, c.ShadowMaeR, missedPositive, avoidedNegative);
        }

        private double Percentile(List<double> values, double p)
        {
            if (values == null || values.Count == 0) return 0;
            var x = values.OrderBy(v => v).ToList();
            double pos = (x.Count - 1) * VClamp(p);
            int lo = (int)Math.Floor(pos), hi = (int)Math.Ceiling(pos);
            if (lo == hi) return x[lo];
            return x[lo] + (x[hi] - x[lo]) * (pos - lo);
        }

        private bool GridPlanReject(CandidateRecord c, string reason)
        {
            if (string.IsNullOrWhiteSpace(reason)) reason = "UNKNOWN";
            int n; _gridPlanRejectReasons.TryGetValue(reason, out n); _gridPlanRejectReasons[reason] = n + 1;
            if (c != null) Event(c, "GRID_PLAN_REJECT_" + reason);
            return false;
        }

        private bool TryBuildFibonacciGridPlan(CandidateRecord c)
        {
            var p = c.Signal.Profile;
            if (p == null || !p.GridEnabled) return GridPlanReject(c, "PROFILE_DISABLED");
            if (!_initialCapitalEligible) return GridPlanReject(c, "INITIAL_CAPITAL");

            double anchor = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double stop = c.Signal.StructuralInvalidation;
            double distance = c.Signal.Direction == TradeDirection.Buy ? anchor - stop : stop - anchor;
            if (distance <= PipsToPrice(MinStopLossPips)) return GridPlanReject(c, "STOP_DISTANCE");

            double xa = Math.Abs(c.Signal.A.Price - c.Signal.X.Price);
            double spanXa = xa > 0 ? distance / xa : 999;
            double executionUnit = distance;
            if (EnableFamilyNativeExecutionCorridor)
            {
                executionUnit = Math.Abs(c.Signal.D.Price - stop);
                if (!double.IsFinite(executionUnit) || executionUnit <= PipsToPrice(MinStopLossPips))
                    return GridPlanReject(c, "INVALID_NATIVE_EXECUTION_CORRIDOR");
            }
            if (!EnableGridSpanSemanticV2 && (spanXa < p.MinimumGridSpanXa || spanXa > p.MaximumGridSpanXa)) return GridPlanReject(c, "LEGACY_XA_SPAN");
            if (EnableGridSpanSemanticV2 && (!double.IsFinite(spanXa) || spanXa <= 0)) return GridPlanReject(c, "INVALID_RISK_XA");

            int routeMax = c.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? 4 :
                           c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 2 :
                           c.Route == HarmonicRoute.TRANSITION_REVERSAL ? (c.Regime != null && c.Regime.Efficiency >= .28 ? 3 : 2) : 0;
            int maxLegs = Math.Min(Math.Min(routeMax, p.MaximumGridLegs), p.GridFractions.Length);
            if (maxLegs <= 0) return GridPlanReject(c, "ROUTE_LEGS");

            var plan = new FibonacciGridPlan
            {
                CandidateId = c.CandidateId,
                Pattern = c.Signal.PatternName,
                Direction = c.Signal.Direction,
                Route = c.Route,
                EntryAnchor = anchor,
                StructuralStop = stop,
                GridDistance = executionUnit,
                BasketRiskAmount = Account.Equity * V71CandidateRiskPercent(c) / 100.0,
                CreatedUtc = Server.Time.ToUniversalTime(),
                ExpirationUtc = MinDate(c.ExpiryUtc, Server.Time.ToUniversalTime().AddMinutes(p.PendingTtlMinutes)),
                MicroCapitalMode = AdaptiveCapitalMode && Account.Equity <= MicroCapitalThreshold
            };
            if (plan.BasketRiskAmount <= 0) return GridPlanReject(c, "RISK_BUDGET");

            double przTol = Math.Max(c.Signal.PrzHigh - c.Signal.PrzLow, executionUnit * p.GridStructuralTolerance);
            double legalLow = c.Signal.PrzLow - przTol;
            double legalHigh = c.Signal.PrzHigh + przTol;

            for (int leg = 0; leg < maxLegs; leg++)
            {
                double fraction = p.GridFractions[leg];
                if (fraction < -1e-9 || fraction > .6180001) continue;
                double price = c.Signal.Direction == TradeDirection.Buy ? anchor - fraction * executionUnit : anchor + fraction * executionUnit;
                if (price < legalLow || price > legalHigh) continue;

                double riskWeight = leg < p.GridRiskWeights.Length ? p.GridRiskWeights[leg] : 0;
                double slPips = PriceToPips(Math.Abs(price - stop));
                if (slPips < MinStopLossPips || riskWeight <= 0) continue;

                double minVolume = _symbol.VolumeInUnitsMin;
                double minRisk = minVolume * _symbol.PipValue * (slPips + ModeledCostPips());
                plan.Legs.Add(new FibonacciGridLeg
                {
                    Index = leg,
                    Fraction = fraction,
                    PlannedPrice = price,
                    RiskWeight = riskWeight,
                    RiskBudget = plan.BasketRiskAmount * riskWeight,
                    MinBrokerRisk = minRisk,
                    Volume = 0,
                    PlannedRisk = 0,
                    ModeledCost = 0,
                    Physical = false,
                    State = GridLegState.VIRTUAL_ONLY
                });
            }

            if (plan.Legs.Count == 0 || plan.Legs[0].Index != 0) return GridPlanReject(c, "NO_LEGAL_L0_IN_PRZ");
            plan.LogicalLegCount = plan.Legs.Count;

            if (!ConfigureCapitalExecution(plan))
            {
                _capitalRejectedBaskets++;
                return GridPlanReject(c, "CAPITAL_EXECUTION");
            }

            var physical = plan.Legs.Where(x => x.Physical && x.Volume > 0).ToList();
            if (physical.Count == 0 || physical[0].Index != 0) return GridPlanReject(c, "NO_PHYSICAL_L0");

            double totalVolume = physical.Sum(l => l.Volume);
            plan.ExpectedWeightedEntry = physical.Sum(l => l.PlannedPrice * l.Volume) / totalVolume;

            double virtualDen = plan.Legs.Sum(l => l.RiskWeight / Math.Max(PriceToPips(Math.Abs(l.PlannedPrice - stop)), 1e-9));
            plan.VirtualWeightedEntry = virtualDen > 0
                ? plan.Legs.Sum(l => l.PlannedPrice * (l.RiskWeight / Math.Max(PriceToPips(Math.Abs(l.PlannedPrice - stop)), 1e-9))) / virtualDen
                : plan.ExpectedWeightedEntry;

            double target, netRr;
            if (!SelectCanonicalBasketTarget(c.Signal, plan.ExpectedWeightedEntry, plan.StructuralStop, out target, out netRr))
                return GridPlanReject(c, "TARGET_RR");

            plan.CanonicalTarget = target;
            plan.ExpectedNetRR = netRr;
            c.GridPlan = plan;
            c.SelectedTarget = target;
            c.NetRR = netRr;

            Print("[V51-GRID-PLAN] cid={0} pattern={1} route={2} logicalLegs={3} physicalDepth={4} micro={5} anchor={6} weighted={7} virtualWeighted={8} stop={9} target={10} budget={11:F2} worst={12:F2} margin={13:F2} netRR={14:F3}",
                c.CandidateId, c.Signal.PatternName, c.Route, plan.LogicalLegCount, plan.PhysicalDepth, plan.MicroCapitalMode,
                anchor, plan.ExpectedWeightedEntry, plan.VirtualWeightedEntry, stop, target, plan.BasketRiskAmount,
                plan.WorstCaseRisk, plan.EstimatedPhysicalMargin, plan.ExpectedNetRR);
            foreach (var leg in plan.Legs)
                Print("[V51-GRID-LEG-PLAN] cid={0} leg=L{1} fraction={2:F3} price={3} weight={4:F6} physical={5} volume={6} budget={7:F2} risk={8:F2} minBrokerRisk={9:F2} state={10}",
                    c.CandidateId, leg.Index, leg.Fraction, leg.PlannedPrice, leg.RiskWeight, leg.Physical, leg.Volume,
                    leg.RiskBudget, leg.PlannedRisk, leg.MinBrokerRisk, leg.State);

            PrintCapitalCompatibilityMatrix(plan);
            return true;
        }

        private bool ConfigureCapitalExecution(FibonacciGridPlan plan)
        {
            foreach (var l in plan.Legs)
            {
                l.Physical = false;
                l.Volume = 0;
                l.PlannedRisk = 0;
                l.ModeledCost = 0;
                l.State = GridLegState.VIRTUAL_ONLY;
            }

            if (plan.MicroCapitalMode)
            {
                for (int depth = plan.Legs.Count; depth >= 1; depth--)
                {
                    var prefix = plan.Legs.Take(depth).ToList();
                    double weightSum = prefix.Sum(x => x.RiskWeight);
                    if (weightSum <= 0) continue;
                    double worst = 0, margin = 0;
                    var vols = new Dictionary<int, double>();
                    bool feasible = true;

                    foreach (var l in prefix)
                    {
                        double slPips = PriceToPips(Math.Abs(l.PlannedPrice - plan.StructuralStop));
                        double budget = plan.BasketRiskAmount * l.RiskWeight / weightSum;
                        double volume = VolumeForRiskBudget(budget, slPips);
                        if (volume <= 0) { feasible = false; break; }

                        double risk = volume * _symbol.PipValue * slPips;
                        double cost = volume * _symbol.PipValue * ModeledCostPips();
                        worst += risk + cost;
                        margin += EstimatedMargin(plan.Direction, volume);
                        vols[l.Index] = volume;
                    }

                    if (!feasible || worst > plan.BasketRiskAmount + 1e-8) continue;
                    if (Account.FreeMargin - margin < plan.BasketRiskAmount * MinFreeMarginRiskMultiple) continue;

                    foreach (var l in prefix)
                    {
                        double slPips = PriceToPips(Math.Abs(l.PlannedPrice - plan.StructuralStop));
                        l.RiskBudget = plan.BasketRiskAmount * l.RiskWeight / weightSum;
                        l.Volume = vols[l.Index];
                        l.PlannedRisk = l.Volume * _symbol.PipValue * slPips;
                        l.ModeledCost = l.Volume * _symbol.PipValue * ModeledCostPips();
                        l.Physical = true;
                        l.State = GridLegState.PLANNED;
                    }
                    plan.PhysicalDepth = depth;
                    plan.WorstCaseRisk = worst;
                    plan.EstimatedPhysicalMargin = margin;
                    _microModeBaskets++;
                    return true;
                }
                return false;
            }

            double cumulative = 0, totalMargin = 0;
            int physicalDepth = 0;
            foreach (var l in plan.Legs)
            {
                double slPips = PriceToPips(Math.Abs(l.PlannedPrice - plan.StructuralStop));
                l.RiskBudget = plan.BasketRiskAmount * l.RiskWeight;
                double volume = VolumeForRiskBudget(l.RiskBudget, slPips);
                if (volume <= 0) continue;

                double risk = volume * _symbol.PipValue * slPips;
                double cost = volume * _symbol.PipValue * ModeledCostPips();
                if (cumulative + risk + cost > plan.BasketRiskAmount + 1e-8) continue;

                l.Volume = volume;
                l.PlannedRisk = risk;
                l.ModeledCost = cost;
                l.Physical = true;
                l.State = GridLegState.PLANNED;
                cumulative += risk + cost;
                totalMargin += EstimatedMargin(plan.Direction, volume);
                if (l.Index == physicalDepth) physicalDepth++;
            }

            plan.PhysicalDepth = physicalDepth;
            plan.WorstCaseRisk = cumulative;
            plan.EstimatedPhysicalMargin = totalMargin;
            return plan.Legs[0].Physical && plan.WorstCaseRisk <= plan.BasketRiskAmount + 1e-8 &&
                   Account.FreeMargin - totalMargin >= plan.BasketRiskAmount * MinFreeMarginRiskMultiple;
        }

        private double EstimatedMargin(TradeDirection direction, double volume)
        {
            try
            {
                return _symbol.GetEstimatedMargin(direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell, volume);
            }
            catch { return 0; }
        }

        private int EstimateRiskOnlyPhysicalDepth(FibonacciGridPlan plan, double equity)
        {
            double effectivePct = Account.Equity > 0 && plan.BasketRiskAmount > 0
                ? Math.Min(5.0, Math.Max(.1, plan.BasketRiskAmount / Account.Equity * 100.0))
                : Math.Min(5.0, Math.Max(.1, BasketRiskPercent));
            double budget = equity * effectivePct / 100.0;
            if (budget <= 0) return 0;
            for (int depth = plan.Legs.Count; depth >= 1; depth--)
            {
                var prefix = plan.Legs.Take(depth).ToList();
                double ws = prefix.Sum(x => x.RiskWeight);
                if (ws <= 0) continue;
                double worst = 0;
                bool ok = true;
                foreach (var l in prefix)
                {
                    double slPips = PriceToPips(Math.Abs(l.PlannedPrice - plan.StructuralStop));
                    double legBudget = budget * l.RiskWeight / ws;
                    double v = VolumeForRiskBudget(legBudget, slPips);
                    if (v <= 0) { ok = false; break; }
                    worst += v * _symbol.PipValue * (slPips + ModeledCostPips());
                }
                if (ok && worst <= budget + 1e-8) return depth;
            }
            return 0;
        }

        private void PrintCapitalCompatibilityMatrix(FibonacciGridPlan plan)
        {
            double[] equities = { 100, 150, 200, 300, 500, 1000 };
            string matrix = string.Join(",", equities.Select(e =>
                e.ToString("F0", CultureInfo.InvariantCulture) + ":" + EstimateRiskOnlyPhysicalDepth(plan, e)));
            Print("[V51-CAPITAL-COMPAT] cid={0} logicalLegs={1} riskOnlyPhysicalDepths={2}", plan.CandidateId, plan.LogicalLegCount, matrix);
        }

        private void ExecuteFibonacciGridPlan(CandidateRecord c)
        {
            var plan = c.GridPlan;
            if (plan == null || plan.Legs.Count == 0) { Reject(c, "GRID_PLAN_MISSING"); return; }
            if (Account.FreeMargin < plan.BasketRiskAmount * MinFreeMarginRiskMultiple) { Reject(c, "MARGIN_HEADROOM"); return; }
            if (plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8)
            {
                _gridRiskViolations++;
                Reject(c, "WORST_CASE_BASKET_RISK");
                return;
            }

            string basketId = NewBasketId();
            plan.BasketId = basketId;
            var basket = new FibonacciBasket
            {
                BasketId = basketId,
                CandidateId = c.CandidateId,
                Pattern = c.Signal.PatternName,
                Direction = c.Signal.Direction,
                Route = c.Route,
                State = FibonacciBasketState.PLANNED,
                CreatedUtc = Server.Time.ToUniversalTime(),
                ExpirationUtc = plan.ExpirationUtc,
                EntryAnchor = plan.EntryAnchor,
                StructuralStop = plan.StructuralStop,
                CanonicalTarget = plan.CanonicalTarget,
                InitialBasketRisk = plan.BasketRiskAmount,
                PlannedWorstCaseRisk = plan.WorstCaseRisk,
                ProtectionFrontier = plan.StructuralStop,
                Plan = plan,
                Candidate = c,
                IsActive = true
            };
            _baskets[basketId] = basket;
            CountPipeline(c.Signal.PatternName).BasketPlanned++;
            BasketEvent(basket, "BASKET_PLANNED");

            var l0 = plan.Legs.First(x => x.Index == 0);
            string l0Label = GridLabel(basketId, 0);
            if (LegAlreadyExists(l0Label))
            {
                _duplicateGridLegs++;
                basket.State = FibonacciBasketState.CANCELLED;
                basket.IsActive = false;
                Reject(c, "DUPLICATE_L0");
                return;
            }

            double marketEntry = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double slPips = PriceToPips(Math.Abs(marketEntry - plan.StructuralStop));
            double tpPips = PriceToPips(Math.Abs(plan.CanonicalTarget - marketEntry));
            if (!BrokerProtectionDistancesValid(c.Signal.Direction, marketEntry, plan.StructuralStop, plan.CanonicalTarget))
            {
                basket.State = FibonacciBasketState.RISK_REJECTED;
                basket.IsActive = false;
                Reject(c, "L0_BROKER_MIN_DISTANCE");
                return;
            }

            double volume = VolumeForRiskBudget(l0.RiskBudget, slPips);
            if (volume <= 0)
            {
                basket.State = FibonacciBasketState.RISK_REJECTED;
                basket.IsActive = false;
                Reject(c, "L0_RISK_VOLUME");
                return;
            }

            double otherWorst = plan.Legs.Where(x => x.Index != 0 && x.Physical).Sum(x => x.PlannedRisk + x.ModeledCost);
            double l0Worst = volume * _symbol.PipValue * (slPips + ModeledCostPips());
            if (otherWorst + l0Worst > plan.BasketRiskAmount + 1e-8)
            {
                _gridRiskViolations++;
                basket.State = FibonacciBasketState.RISK_REJECTED;
                basket.IsActive = false;
                Reject(c, "L0_SLIPPAGE_RISK_RECHECK");
                return;
            }

            TransitionLegState(basket, l0, GridLegState.SUBMITTING, "L0_SUBMITTING");
            TradeType tt = c.Signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;
            var tr = ExecuteMarketOrder(tt, SymbolName, volume, l0Label, slPips, tpPips);
            if (tr == null || !tr.IsSuccessful || tr.Position == null)
            {
                string code = "L0_ORDER_" + (tr == null ? "NULL" : tr.Error.ToString());
                RecordExecutionError(code, "basket=" + basket.BasketId);
                basket.State = FibonacciBasketState.RISK_REJECTED;
                basket.IsActive = false;
                Reject(c, code);
                return;
            }

            l0.Volume = volume;
            l0.PositionId = tr.Position.Id;
            if (!PositionStillExists(tr.Position.Id))
            {
                basket.State = FibonacciBasketState.INVALIDATED;
                basket.IsActive = false;
                Invalidate(c, "L0_FAIL_CLOSED_POST_FILL");
                return;
            }
            if (!_postFillValidated.Contains(tr.Position.Id))
                PostFillSafetyKernel(tr.Position, "L0_RESULT");
            if (!_postFillValidated.Contains(tr.Position.Id))
            {
                basket.ExitOverride = "L0_POST_FILL_NOT_VALIDATED";
                CancelBasketPending(basket, basket.ExitOverride);
                if (PositionStillExists(tr.Position.Id))
                    FailClosePosition(tr.Position, basket, basket.ExitOverride);
                if (PositionStillExists(tr.Position.Id))
                    _unprotectedSurvivors++;
                basket.State = FibonacciBasketState.INVALIDATED;
                basket.IsActive = false;
                Invalidate(c, "L0_FAIL_CLOSED_POST_FILL");
                return;
            }
            if (!PositionStillExists(tr.Position.Id))
            {
                basket.State = FibonacciBasketState.INVALIDATED;
                basket.IsActive = false;
                Invalidate(c, "L0_FAIL_CLOSED_POST_FILL");
                return;
            }
            basket.State = FibonacciBasketState.LEG0_EXECUTED;
            if (!_positions.ContainsKey(tr.Position.Id)) RegisterFilledPosition(basket, l0, tr.Position);
            RecordLegFillTelemetry(basket, l0);
            CountPipeline(c.Signal.PatternName).Leg0Executed++;
            BasketEvent(basket, "LEG0_EXECUTED");
            Transition(c, CandidateState.EXECUTED, "FIB_GRID_LEG0_FILLED");
            V71RecordCoreExecution(c);
            if (EnableCanonicalSetupIdentity && !c.V71Expansion && !string.IsNullOrWhiteSpace(c.SetupKey))
            {
                _executedSetupKeys.Add(c.SetupKey);
                _activeSetupOwners.Remove(c.SetupKey);
            }
            else if (c.V71Expansion && !string.IsNullOrWhiteSpace(c.SetupKey))
            {
                _v71ExpansionExecutedSetupKeys.Add(c.SetupKey);
            }
            CountPipeline(c.Signal.PatternName).Executed++;

            foreach (var leg in plan.Legs.Where(x => x.Index > 0))
            {
                if (!leg.Physical) continue;
                if (!DeeperLegThesisEligible(basket, leg))
                {
                    TransitionLegState(basket, leg, GridLegState.CANCELLED, "DEEPER_LEG_THESIS_REJECT");
                    continue;
                }
                if (PlaceGridLimit(basket, leg))
                    basket.State = FibonacciBasketState.GRID_PENDING;
            }
        }

        private bool PlaceGridLimit(FibonacciBasket basket, FibonacciGridLeg leg)
        {
            if (!leg.Physical || leg.Volume <= 0) return false;
            string label = GridLabel(basket.BasketId, leg.Index);
            if (LegAlreadyExists(label))
            {
                _duplicateGridLegs++;
                TransitionLegState(basket, leg, GridLegState.REJECTED, "GRID_LEG_DUPLICATE");
                BasketEvent(basket, "GRID_LEG_DUPLICATE_L" + leg.Index);
                return false;
            }

            if ((basket.Direction == TradeDirection.Buy && leg.PlannedPrice >= _symbol.Ask) ||
                (basket.Direction == TradeDirection.Sell && leg.PlannedPrice <= _symbol.Bid))
            {
                TransitionLegState(basket, leg, GridLegState.CANCELLED, "GRID_LEG_PRICE_CROSSED_BEFORE_SUBMIT");
                BasketEvent(basket, "GRID_LEG_PRICE_CROSSED_BEFORE_SUBMIT_L" + leg.Index);
                return false;
            }

            double slPips = PriceToPips(Math.Abs(leg.PlannedPrice - basket.StructuralStop));
            double tpPips = PriceToPips(Math.Abs(basket.CanonicalTarget - leg.PlannedPrice));
            if (slPips < MinStopLossPips || tpPips <= 0)
            {
                TransitionLegState(basket, leg, GridLegState.REJECTED, "GRID_LEG_GEOMETRY_REJECT");
                BasketEvent(basket, "GRID_LEG_GEOMETRY_REJECT_L" + leg.Index);
                return false;
            }

            if (!BrokerProtectionDistancesValid(basket.Direction, leg.PlannedPrice, basket.StructuralStop, basket.CanonicalTarget))
            {
                TransitionLegState(basket, leg, GridLegState.REJECTED, "GRID_LEG_BROKER_MIN_DISTANCE");
                BasketEvent(basket, "GRID_LEG_BROKER_MIN_DISTANCE_L" + leg.Index);
                return false;
            }

            double liveFilledRisk = CurrentFilledStructuralRisk(basket);
            double livePendingRisk = CurrentPendingStructuralRisk(basket);
            double nextWorst = liveFilledRisk + livePendingRisk + leg.PlannedRisk + leg.ModeledCost;
            if (nextWorst > basket.InitialBasketRisk + 1e-8)
            {
                TransitionLegState(basket, leg, GridLegState.RISK_REJECTED, "LIVE_FILLED_RISK_REJECT");
                BasketEvent(basket, "LIVE_FILLED_RISK_REJECT_L" + leg.Index);
                return false;
            }

            DateTime nowUtc = Server.Time.ToUniversalTime();
            if (basket.ExpirationUtc <= nowUtc.AddSeconds(1))
            {
                TransitionLegState(basket, leg, GridLegState.EXPIRED, "PENDING_TTL_NOT_STRICTLY_FUTURE");
                return false;
            }

            TransitionLegState(basket, leg, GridLegState.SUBMITTING, "LIMIT_SUBMITTING");
            TradeType tt = basket.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;
            var tr = PlaceLimitOrder(tt, SymbolName, leg.Volume, leg.PlannedPrice, label,
                basket.StructuralStop, basket.CanonicalTarget, ProtectionType.Absolute, basket.ExpirationUtc,
                GridComment(basket, leg.Index), false);
            if (tr == null || !tr.IsSuccessful || tr.PendingOrder == null)
            {
                string code = "GRID_LEG_ORDER_" + (tr == null ? "NULL" : tr.Error.ToString());
                RecordExecutionError(code, "basket=" + basket.BasketId + ";leg=L" + leg.Index);
                TransitionLegState(basket, leg, GridLegState.REJECTED, "GRID_LEG_SUBMIT_FAILED_" + code);
                BasketEvent(basket, "GRID_LEG_SUBMIT_FAILED_L" + leg.Index + "_" + code);
                return false;
            }

            leg.PendingOrderId = tr.PendingOrder.Id;
            if (leg.State == GridLegState.SUBMITTING)
                TransitionLegState(basket, leg, GridLegState.SUBMITTED, "GRID_LEG_SUBMITTED");
            else
                BasketEvent(basket, "LIMIT_SUBMIT_RETURN_AFTER_EVENT_L" + leg.Index + "_STATE_" + leg.State);
            return leg.State == GridLegState.SUBMITTED || leg.State == GridLegState.FILLED_UNVERIFIED || leg.State == GridLegState.PROTECTED;
        }

        private bool SelectCanonicalBasketTarget(PatternSignal s, double weightedEntry, double stop, out double target, out double netRr)
        {
            target = 0; netRr = 0;
            double riskPips = PriceToPips(Math.Abs(weightedEntry - stop));
            if (riskPips < MinStopLossPips) return false;

            double[] targets = s.Profile != null && s.Profile.CanonicalTargetPolicy == "T2_PREFERRED"
                ? new[] { s.CanonicalTarget2, s.CanonicalTarget1 }
                : new[] { s.CanonicalTarget1, s.CanonicalTarget2 };

            foreach (double t in targets)
            {
                if (!GeometryValid(s.Direction, weightedEntry, stop, t)) continue;
                double rewardPips = PriceToPips(Math.Abs(t - weightedEntry)) - ModeledCostPips();
                double rr = riskPips > 0 ? rewardPips / riskPips : 0;
                if (rr >= MinimumNetRR)
                {
                    target = t;
                    netRr = rr;
                    return true;
                }
            }
            return false;
        }

        private double VolumeForRiskBudget(double riskBudget, double slPips)
        {
            if (riskBudget <= 0 || slPips <= 0 || _symbol.PipValue <= 0) return 0;
            double raw = riskBudget / (slPips * _symbol.PipValue);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0) return 0;
            double v = _symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (v < _symbol.VolumeInUnitsMin) return 0;
            return Math.Min(v, _symbol.VolumeInUnitsMax);
        }

        private double ModeledCostPips()
        {
            return Math.Max(0, SpreadPips()) + Math.Max(0, RoundTurnCommissionPips) + Math.Max(0, SlippageStressPips);
        }

        private void ReconcileAndManageBaskets()
        {
            ReconcileGridFills();
            CancelInvalidPendingOrders();
            RevalidatePendingExposureGovernor();

            foreach (var basket in _baskets.Values.Where(b => b.IsActive).ToList())
            {
                UpdateVirtualGridState(basket);
                var positions = OwnPositions().Where(p => LabelBasketId(p.Label) == basket.BasketId).ToList();
                var pending = OwnPendingOrders().Where(o => LabelBasketId(o.Label) == basket.BasketId).ToList();

                if (positions.Count == 0)
                {
                    if (pending.Count == 0 && basket.State != FibonacciBasketState.PLANNED)
                        CloseBasketLedger(basket, "NO_OPEN_LEGS");
                    continue;
                }

                basket.State = pending.Count > 0 ? FibonacciBasketState.PARTIALLY_FILLED : FibonacciBasketState.BASKET_ACTIVE;
                basket.FilledLegs = Math.Max(basket.FilledLegs, positions.Count);
                basket.AverageEntry = WeightedAverageEntry(positions);

                foreach (var p in positions)
                {
                    PositionLedger legLedger;
                    if (!_positions.TryGetValue(p.Id, out legLedger) || legLedger.InitialRiskPips <= 0) continue;
                    double legR = p.Pips / legLedger.InitialRiskPips;
                    if (legR > legLedger.PeakR) legLedger.PeakR = legR;
                    if (-legR > legLedger.MaxAdverseR) legLedger.MaxAdverseR = -legR;
                }

                double currentNet = positions.Sum(p => p.NetProfit);
                double currentR = basket.InitialBasketRisk > 0 ? (basket.RealizedNet + currentNet) / basket.InitialBasketRisk : 0;
                if (currentR > basket.PeakR) basket.PeakR = currentR;
                if (-currentR > basket.MaxAdverseR) basket.MaxAdverseR = -currentR;

                if (basket.PeakR >= GridCancelMfeR && pending.Count > 0)
                    CancelBasketPending(basket, "MFE_GRID_CANCEL");

                double age = (Server.Time.ToUniversalTime() - basket.CreatedUtc).TotalMinutes;
                bool v72FixedPayoff = basket.Candidate != null &&
                    (basket.Candidate.V72BifurcationAlpha || basket.Candidate.V72FamilyNativeCausalAlpha ||
                     (basket.Candidate.CandidateId ?? "").StartsWith("V71EXP-HCOG-", StringComparison.Ordinal));
                if (!v72FixedPayoff && age >= NoMfeMinAgeMinutes && basket.PeakR < NoMfeProofR && currentR <= -Math.Abs(NoMfeKillR))
                {
                    basket.ExitOverride = "NO_MFE_THESIS_FAILURE";
                    CancelBasketPending(basket, basket.ExitOverride);
                    CloseBasketPositions(basket, basket.ExitOverride);
                    continue;
                }

                double protectTriggerR = BreakEvenTriggerR;
                double protectLockR = Math.Max(0, BreakEvenLockR);
                if (!v72FixedPayoff && basket.PeakR >= protectTriggerR)
                {
                    double span = Math.Abs(basket.AverageEntry - basket.StructuralStop);
                    double lockPrice = basket.Direction == TradeDirection.Buy
                        ? basket.AverageEntry + span * protectLockR
                        : basket.AverageEntry - span * protectLockR;
                    AdvanceBasketProtectionFrontier(basket, lockPrice, "COLLECTIVE_PROTECT");
                }

                if (!v72FixedPayoff && basket.PeakR >= TrailTriggerR)
                {
                    double trail = FibonacciStructureTrail(basket.Direction);
                    if (trail > 0) AdvanceBasketProtectionFrontier(basket, trail, "FIB_382_STRUCTURE_TRAIL");
                }
            }
        }

        private void ReconcileGridFills()
        {
            foreach (var p in OwnPositions().ToList())
            {
                string basketId = LabelBasketId(p.Label);
                int legIndex = LabelLegIndex(p.Label);
                FibonacciBasket basket;
                if (string.IsNullOrWhiteSpace(basketId) || !_baskets.TryGetValue(basketId, out basket))
                {
                    _orphanPendingOrders++;
                    continue;
                }

                var leg = basket.Plan.Legs.FirstOrDefault(x => x.Index == legIndex);
                if (leg == null)
                {
                    _orphanPendingOrders++;
                    continue;
                }

                if (!_postFillValidated.Contains(p.Id))
                    PostFillSafetyKernel(p, "RECONCILE");
                if (!_postFillValidated.Contains(p.Id))
                {
                    if (PositionStillExists(p.Id))
                    {
                        basket.ExitOverride = "RECONCILE_POST_FILL_NOT_VALIDATED";
                        FailClosePosition(p, basket, basket.ExitOverride);
                        if (PositionStillExists(p.Id)) _unprotectedSurvivors++;
                    }
                    continue;
                }
                if (!PositionStillExists(p.Id)) continue;

                if (!_positions.ContainsKey(p.Id))
                    RegisterFilledPosition(basket, leg, p);
                RecordLegFillTelemetry(basket, leg);
            }

            foreach (var o in OwnPendingOrders().ToList())
            {
                string basketId = LabelBasketId(o.Label);
                if (string.IsNullOrWhiteSpace(basketId) || !_baskets.ContainsKey(basketId))
                {
                    _orphanPendingOrders++;
                    var r = CancelPendingOrder(o);
                    if ((r == null || !r.IsSuccessful) && PendingOrderStillExists(o.Id))
                        RecordExecutionError("ORPHAN_CANCEL_FAILED_" + (r == null ? "NULL" : r.Error.ToString()), "order=" + o.Id);
                }
            }
        }

        private void RegisterFilledPosition(FibonacciBasket basket, FibonacciGridLeg leg, Position p)
        {
            if (_positions.ContainsKey(p.Id)) return;
            double initialRiskPips = PriceToPips(Math.Abs(p.EntryPrice - basket.StructuralStop));
            _positions[p.Id] = new PositionLedger
            {
                PositionId = p.Id,
                CandidateId = basket.CandidateId,
                PatternName = basket.Pattern,
                Route = basket.Route,
                Direction = basket.Direction,
                EntryUtc = p.EntryTime.ToUniversalTime(),
                InitialRiskPips = initialRiskPips,
                RiskAmount = p.VolumeInUnits * _symbol.PipValue * initialRiskPips,
                PeakR = 0,
                MaxAdverseR = 0,
                BasketId = basket.BasketId,
                LegIndex = leg.Index
            };
        }

        private void CancelInvalidPendingOrders()
        {
            DateTime now = Server.Time.ToUniversalTime();
            foreach (var basket in _baskets.Values.Where(b => b.IsActive).ToList())
            {
                string reason = null;
                if (now >= basket.ExpirationUtc) reason = "CANDIDATE_TTL_EXPIRED";
                else if (_dailyLocked) reason = "DAILY_RISK_LOCK";
                else if (PeakDrawdownExceeded()) reason = "MAX_DRAWDOWN_LOCK";
                else if (!IsInstitutionalSession(now)) reason = "SESSION_EXPIRED";
                else if (BasketStructuralInvalidated(basket)) reason = "STRUCTURAL_INVALIDATION";
                else if (BasketHardConflict(basket)) reason = "MTF_HARD_CONFLICT";

                if (reason == null) continue;

                CancelBasketPending(basket, reason);

                if (!OwnPositions().Any(p => LabelBasketId(p.Label) == basket.BasketId))
                {
                    basket.State = reason == "SESSION_EXPIRED" ? FibonacciBasketState.SESSION_EXPIRED :
                                   reason == "STRUCTURAL_INVALIDATION" ? FibonacciBasketState.INVALIDATED :
                                   reason == "CANDIDATE_TTL_EXPIRED" ? FibonacciBasketState.EXPIRED : FibonacciBasketState.CANCELLED;
                    basket.IsActive = false;
                }
            }
        }

        private bool BasketStructuralInvalidated(FibonacciBasket basket)
        {
            return basket.Direction == TradeDirection.Buy ? _symbol.Bid <= basket.StructuralStop : _symbol.Ask >= basket.StructuralStop;
        }

        private bool BasketHardConflict(FibonacciBasket basket)
        {
            var h4 = GetActiveHarmonicState(_h4Bars, H4SwingDepth, 220, 3);
            var h1 = GetActiveHarmonicState(_h1Bars, H1SwingDepth, 260, 4);
            return ClassifyMtfConflict(basket.Direction, h4, h1) == MtfConflict.CONFLICT &&
                   basket.Route != HarmonicRoute.EXHAUSTION_REVERSAL;
        }

        private void CancelBasketPending(FibonacciBasket basket, string reason)
        {
            foreach (var o in OwnPendingOrders().Where(x => LabelBasketId(x.Label) == basket.BasketId).ToList())
            {
                var r = CancelPendingOrder(o);
                if (r == null || !r.IsSuccessful)
                {
                    if (PendingOrderStillExists(o.Id))
                        RecordExecutionError("GRID_CANCEL_FAILED_" + (r == null ? "NULL" : r.Error.ToString()),
                            "basket=" + basket.BasketId + ";order=" + o.Id + ";reason=" + reason);
                    else
                        BasketEvent(basket, "GRID_CANCEL_RACE_BENIGN_ORDER_" + o.Id);
                    continue;
                }

                var leg = basket.Plan.Legs.FirstOrDefault(x => x.Index == LabelLegIndex(o.Label));
                if (leg != null && (leg.State == GridLegState.SUBMITTED || leg.State == GridLegState.SUBMITTING)) TransitionLegState(basket, leg, GridLegState.CANCELLED, "PENDING_CANCELLED_" + reason);
                BasketEvent(basket, "GRID_LEG_CANCELLED_" + reason + "_L" + LabelLegIndex(o.Label));
            }
        }

        private void CancelAllOwnPending(string reason)
        {
            foreach (var o in OwnPendingOrders().ToList())
            {
                var r = CancelPendingOrder(o);
                if ((r == null || !r.IsSuccessful) && PendingOrderStillExists(o.Id))
                    RecordExecutionError("STOP_CANCEL_FAILED_" + (r == null ? "NULL" : r.Error.ToString()), "order=" + o.Id + ";reason=" + reason);
            }
            Print("[V51-PENDING-CANCEL-ALL] reason={0}", reason);
        }

        private void CloseBasketPositions(FibonacciBasket basket, string reason)
        {
            foreach (var p in OwnPositions().Where(x => LabelBasketId(x.Label) == basket.BasketId).ToList())
            {
                PositionLedger l;
                if (_positions.TryGetValue(p.Id, out l)) l.ExitOverride = reason;
                var r = ClosePosition(p);
                if ((r == null || !r.IsSuccessful) && PositionStillExists(p.Id))
                    RecordExecutionError("CLOSE_FAILED_" + (r == null ? "NULL" : r.Error.ToString()),
                        "basket=" + basket.BasketId + ";position=" + p.Id + ";reason=" + reason);
            }
        }

        private void AdvanceBasketProtectionFrontier(FibonacciBasket basket, double proposal, string reason)
        {
            if (proposal <= 0) return;
            double frontier = basket.ProtectionFrontier;
            double next = frontier <= 0 ? proposal :
                (basket.Direction == TradeDirection.Buy ? Math.Max(frontier, proposal) : Math.Min(frontier, proposal));

            // Never generate a widening proposal. Structural stop is the initial floor/ceiling.
            if (basket.Direction == TradeDirection.Buy)
                next = Math.Max(next, basket.StructuralStop);
            else
                next = Math.Min(next, basket.StructuralStop);

            bool advanced = frontier <= 0 || (basket.Direction == TradeDirection.Buy ? next > frontier + _symbol.TickSize : next < frontier - _symbol.TickSize);
            if (!advanced) return;

            basket.ProtectionFrontier = next;
            bool anyApplied = false;
            foreach (var p in OwnPositions().Where(x => LabelBasketId(x.Label) == basket.BasketId).ToList())
            {
                if (TargetTooCloseForProtectionUpdate(p))
                {
                    BasketEvent(basket, "FRONTIER_SKIP_TARGET_PROXIMITY_POS_" + p.Id);
                    continue;
                }

                double brokerSafe = BrokerSafeStop(p.TradeType, next);
                if (brokerSafe <= 0) continue;

                bool improves = !p.StopLoss.HasValue ||
                    (p.TradeType == TradeType.Buy ? brokerSafe > p.StopLoss.Value + _symbol.TickSize : brokerSafe < p.StopLoss.Value - _symbol.TickSize);
                if (!improves) continue;

                var r = p.ModifyStopLossPrice(brokerSafe);
                if (r == null || !r.IsSuccessful)
                {
                    if (!PositionStillExists(p.Id) || TargetTooCloseForProtectionUpdate(p))
                    {
                        BasketEvent(basket, "FRONTIER_MODIFY_RACE_BENIGN_POS_" + p.Id);
                        continue;
                    }

                    double retryStop = BrokerSafeStop(p.TradeType, next);
                    bool retryImproves = retryStop > 0 && (!p.StopLoss.HasValue ||
                        (p.TradeType == TradeType.Buy ? retryStop > p.StopLoss.Value + _symbol.TickSize : retryStop < p.StopLoss.Value - _symbol.TickSize));
                    TradeResult retry = retryImproves ? p.ModifyStopLossPrice(retryStop) : null;
                    if (retry != null && retry.IsSuccessful)
                    {
                        anyApplied = true;
                        BasketEvent(basket, "FRONTIER_RETRY_SUCCESS_POS_" + p.Id);
                        continue;
                    }

                    if (!PositionStillExists(p.Id) || TargetTooCloseForProtectionUpdate(p))
                    {
                        BasketEvent(basket, "FRONTIER_RETRY_RACE_BENIGN_POS_" + p.Id);
                        continue;
                    }

                    RecordExecutionError("FRONTIER_STOP_FAILED_" + (retry != null ? retry.Error.ToString() : (r == null ? "NULL" : r.Error.ToString())),
                        "basket=" + basket.BasketId + ";position=" + p.Id + ";reason=" + reason);
                    continue;
                }
                anyApplied = true;
            }

            if (anyApplied)
            {
                basket.State = FibonacciBasketState.BASKET_PROTECTED;
                BasketEvent(basket, "PROTECTION_FRONTIER_ADVANCED_" + reason);
            }
        }

        private double BrokerSafeStop(TradeType tradeType, double proposed)
        {
            double reference = tradeType == TradeType.Buy ? _symbol.Bid : _symbol.Ask;
            double minDistance = BrokerMinimumDistancePrice(reference, true);
            double spreadPrice = Math.Max(0, _symbol.Ask - _symbol.Bid);
            double safety = Math.Max(_symbol.TickSize * 4.0, Math.Max(minDistance + _symbol.TickSize * 2.0, spreadPrice * 2.0 + _symbol.TickSize * 2.0));
            double safe = tradeType == TradeType.Buy
                ? Math.Min(proposed, reference - safety)
                : Math.Max(proposed, reference + safety);
            if (tradeType == TradeType.Buy && safe >= reference) return 0;
            if (tradeType == TradeType.Sell && safe <= reference) return 0;
            if (_symbol.Digits >= 0)
                return Math.Round(safe, _symbol.Digits, MidpointRounding.AwayFromZero);
            return safe;
        }

        private bool TargetTooCloseForProtectionUpdate(Position p)
        {
            if (p == null || !p.TakeProfit.HasValue) return false;
            double reference = p.TradeType == TradeType.Buy ? _symbol.Bid : _symbol.Ask;
            double gap = p.TradeType == TradeType.Buy ? p.TakeProfit.Value - reference : reference - p.TakeProfit.Value;
            if (gap <= 0) return true;
            double spreadPrice = Math.Max(0, _symbol.Ask - _symbol.Bid);
            double minTp = BrokerMinimumDistancePrice(reference, false);
            double raceBuffer = Math.Max(_symbol.TickSize * 4.0, Math.Max(minTp + _symbol.TickSize * 2.0, spreadPrice * 2.0 + _symbol.TickSize * 2.0));
            return gap <= raceBuffer;
        }

        private bool DeeperLegThesisEligible(FibonacciBasket basket, FibonacciGridLeg leg)
        {
            if (leg.Index <= 0) return true;
            if (BasketStructuralInvalidated(basket) || BasketHardConflict(basket)) return false;
            if (_dailyLocked || PeakDrawdownExceeded() || !IsInstitutionalSession(Server.Time.ToUniversalTime())) return false;

            // Causal eligibility only: no historical PF/hour/date lookup and no new Fibonacci levels.
            int i = LastClosedIndex(_m1Bars);
            if (i < 3) return false;
            double close = _m1Bars.ClosePrices[i];
            double prev = _m1Bars.ClosePrices[i - 1];
            double impulse = basket.Direction == TradeDirection.Buy ? close - prev : prev - close;
            bool notAcceleratingAgainst = impulse >= -PipsToPrice(Math.Max(1.0, SpreadPips()));
            return notAcceleratingAgainst;
        }

        private double CurrentFilledStructuralRisk(FibonacciBasket basket)
        {
            double risk = 0;
            foreach (var p in OwnPositions().Where(x => LabelBasketId(x.Label) == basket.BasketId))
            {
                double d = PriceToPips(Math.Abs(p.EntryPrice - basket.StructuralStop));
                risk += p.VolumeInUnits * _symbol.PipValue * d;
            }
            return risk;
        }

        private double CurrentPendingStructuralRisk(FibonacciBasket basket)
        {
            double risk = 0;
            foreach (var o in OwnPendingOrders().Where(x => LabelBasketId(x.Label) == basket.BasketId))
            {
                double d = PriceToPips(Math.Abs(o.TargetPrice - basket.StructuralStop));
                risk += o.VolumeInUnits * _symbol.PipValue * d + o.VolumeInUnits * _symbol.PipValue * ModeledCostPips();
            }
            return risk;
        }

        private double FibonacciStructureTrail(TradeDirection direction)
        {
            int end = LastClosedIndex(_m1Bars);
            if (end < 20) return 0;
            int start = Math.Max(1, end - 20);
            double hi = double.MinValue, lo = double.MaxValue;

            for (int i = start; i <= end; i++)
            {
                hi = Math.Max(hi, _m1Bars.HighPrices[i]);
                lo = Math.Min(lo, _m1Bars.LowPrices[i]);
            }

            if (hi <= lo) return 0;
            return direction == TradeDirection.Buy
                ? hi - .382 * (hi - lo)
                : lo + .382 * (hi - lo);
        }

        private void OnPositionOpened(PositionOpenedEventArgs args)
        {
            if (args == null || args.Position == null) return;
            PostFillSafetyKernel(args.Position, "POSITIONS_OPENED");
        }

        private void OnPendingOrderFilled(PendingOrderFilledEventArgs args)
        {
            if (args == null || args.Position == null) return;
            PostFillSafetyKernel(args.Position, "PENDING_FILLED");
        }

        private void PostFillSafetyKernel(Position p, string source)
        {
            if (p == null || p.SymbolName != SymbolName || string.IsNullOrWhiteSpace(p.Label) ||
                !p.Label.StartsWith(BotPrefix + "|", StringComparison.Ordinal)) return;
            if (_postFillValidated.Contains(p.Id)) return;
            if (!_postFillInProgress.Add(p.Id))
            {
                Print("[V51-POST-FILL-DEDUPE] pos={0} source={1}", p.Id, source);
                return;
            }

            try
            {
                PostFillSafetyKernelCore(p, source);
            }
            finally
            {
                _postFillInProgress.Remove(p.Id);
            }
        }

        private void PostFillSafetyKernelCore(Position p, string source)
        {
            string basketId = LabelBasketId(p.Label);
            int legIndex = LabelLegIndex(p.Label);
            FibonacciBasket basket;
            if (string.IsNullOrWhiteSpace(basketId) || !_baskets.TryGetValue(basketId, out basket))
            {
                _orphanPendingOrders++;
                return;
            }
            var leg = basket.Plan.Legs.FirstOrDefault(x => x.Index == legIndex);
            if (leg == null)
            {
                _orphanPendingOrders++;
                return;
            }

            if (leg.State == GridLegState.FAIL_CLOSED)
            {
                FailClosePosition(p, basket, "REPEAT_POST_FILL_AFTER_FAIL_CLOSED");
                return;
            }

            if (leg.State == GridLegState.CANCELLED || leg.State == GridLegState.EXPIRED ||
                leg.State == GridLegState.REJECTED || leg.State == GridLegState.RISK_REJECTED)
            {
                _executionStateViolations++;
                basket.ExitOverride = "LATE_FILL_AFTER_TERMINAL_STATE_" + leg.State;
                Print("[V51-STATE-VIOLATION] basket={0} leg=L{1} prior={2} next=FILLED_UNVERIFIED reason=LATE_FILL_AFTER_TERMINAL_STATE",
                    basket.BasketId, leg.Index, leg.State);
                CancelBasketPending(basket, basket.ExitOverride);
                FailClosePosition(p, basket, basket.ExitOverride);
                return;
            }

            TransitionLegState(basket, leg, GridLegState.FILLED_UNVERIFIED, "POST_FILL_" + source);
            leg.PositionId = p.Id;
            if (!_positions.ContainsKey(p.Id)) RegisterFilledPosition(basket, leg, p);

            bool entryCross = basket.Direction == TradeDirection.Buy
                ? p.EntryPrice <= basket.StructuralStop
                : p.EntryPrice >= basket.StructuralStop;
            bool marketCross = BasketStructuralInvalidated(basket);
            if (entryCross || marketCross)
            {
                _gapThroughInvalidations++;
                basket.ExitOverride = "GAP_THROUGH_STRUCTURAL_INVALIDATION";
                TransitionLegState(basket, leg, GridLegState.FAIL_CLOSED, basket.ExitOverride);
                CancelBasketPending(basket, basket.ExitOverride);
                FailClosePosition(p, basket, basket.ExitOverride);
                if (PositionStillExists(p.Id)) _gapThroughSurvivors++;
                else _positions.Remove(p.Id);
                return;
            }

            double actualWorst = ActualBasketWorstRisk(basket);
            if (actualWorst > basket.InitialBasketRisk + 1e-8)
            {
                _actualBasketRiskViolations++;
                basket.ExitOverride = "ACTUAL_FILL_RISK_BUDGET_BREACH";
                CancelBasketPending(basket, basket.ExitOverride);
                TransitionLegState(basket, leg, GridLegState.FAIL_CLOSED, basket.ExitOverride);
                FailClosePosition(p, basket, basket.ExitOverride);
                if (!PositionStillExists(p.Id)) _positions.Remove(p.Id);
                return;
            }

            if (!EnsurePostFillProtection(p, basket))
            {
                basket.ExitOverride = "POST_FILL_PROTECTION_FAIL_CLOSED";
                CancelBasketPending(basket, basket.ExitOverride);
                TransitionLegState(basket, leg, GridLegState.FAIL_CLOSED, basket.ExitOverride);
                FailClosePosition(p, basket, basket.ExitOverride);
                if (PositionStillExists(p.Id)) _unprotectedSurvivors++;
                else _positions.Remove(p.Id);
                return;
            }

            if (Account.FreeMargin < basket.InitialBasketRisk * MinFreeMarginRiskMultiple)
            {
                _marginRiskViolations++;
                basket.ExitOverride = "POST_FILL_MARGIN_HEADROOM";
                CancelBasketPending(basket, basket.ExitOverride);
                TransitionLegState(basket, leg, GridLegState.FAIL_CLOSED, basket.ExitOverride);
                FailClosePosition(p, basket, basket.ExitOverride);
                if (!PositionStillExists(p.Id)) _positions.Remove(p.Id);
                return;
            }

            _postFillValidated.Add(p.Id);
            TransitionLegState(basket, leg, GridLegState.PROTECTED, "POST_FILL_PROTECTED");
            Print("[V51-POST-FILL-AUDIT] basket={0} leg=L{1} pos={2} source={3} entry={4} stop={5} target={6} actualWorst={7:F4} budget={8:F4} protected=true",
                basket.BasketId, leg.Index, p.Id, source, p.EntryPrice, basket.StructuralStop, basket.CanonicalTarget, actualWorst, basket.InitialBasketRisk);
        }

        private bool EnsurePostFillProtection(Position p, FibonacciBasket basket)
        {
            bool stopAcceptable = p.StopLoss.HasValue &&
                (p.TradeType == TradeType.Buy ? p.StopLoss.Value + _symbol.TickSize >= basket.StructuralStop
                                              : p.StopLoss.Value - _symbol.TickSize <= basket.StructuralStop);
            bool tpAcceptable = p.TakeProfit.HasValue &&
                (p.TradeType == TradeType.Buy ? p.TakeProfit.Value > p.EntryPrice : p.TakeProfit.Value < p.EntryPrice);

            if (!stopAcceptable)
            {
                if (!BrokerStopDistanceValid(p.TradeType, basket.StructuralStop))
                {
                    _postFillProtectionFailures++;
                    return false;
                }
                var rs = p.ModifyStopLossPrice(basket.StructuralStop);
                if (rs == null || !rs.IsSuccessful)
                {
                    _postFillProtectionFailures++;
                    RecordExecutionError("POST_FILL_SL_" + (rs == null ? "NULL" : rs.Error.ToString()),
                        "basket=" + basket.BasketId + ";position=" + p.Id);
                    return false;
                }
            }

            var live = Positions.FirstOrDefault(x => x.Id == p.Id);
            if (live == null || !live.StopLoss.HasValue)
            {
                _postFillProtectionFailures++;
                return false;
            }

            if (!tpAcceptable)
            {
                if (!BrokerTargetDistanceValid(p.TradeType, basket.CanonicalTarget))
                {
                    _postFillProtectionFailures++;
                    return false;
                }
                var rt = live.ModifyTakeProfitPrice(basket.CanonicalTarget);
                if (rt == null || !rt.IsSuccessful)
                {
                    _postFillProtectionFailures++;
                    RecordExecutionError("POST_FILL_TP_" + (rt == null ? "NULL" : rt.Error.ToString()),
                        "basket=" + basket.BasketId + ";position=" + p.Id);
                    return false;
                }
            }

            live = Positions.FirstOrDefault(x => x.Id == p.Id);
            return live != null && live.StopLoss.HasValue && live.TakeProfit.HasValue;
        }

        private bool BrokerTargetDistanceValid(TradeType tradeType, double target)
        {
            double reference = tradeType == TradeType.Buy ? _symbol.Ask : _symbol.Bid;
            double minTp = BrokerMinimumDistancePrice(reference, false);
            return tradeType == TradeType.Buy
                ? target > reference && target - reference + 1e-12 >= minTp
                : target < reference && reference - target + 1e-12 >= minTp;
        }

        private void FailClosePosition(Position p, FibonacciBasket basket, string reason)
        {
            var r = ClosePosition(p);
            if ((r == null || !r.IsSuccessful) && PositionStillExists(p.Id))
                RecordExecutionError("FAIL_CLOSE_" + (r == null ? "NULL" : r.Error.ToString()),
                    "basket=" + basket.BasketId + ";position=" + p.Id + ";reason=" + reason);
        }

        private double ActualBasketWorstRisk(FibonacciBasket basket)
        {
            double risk = 0;
            foreach (var p in OwnPositions().Where(x => LabelBasketId(x.Label) == basket.BasketId))
            {
                bool validSide = basket.Direction == TradeDirection.Buy ? p.EntryPrice > basket.StructuralStop : p.EntryPrice < basket.StructuralStop;
                if (!validSide) return double.MaxValue;
                double d = PriceToPips(Math.Abs(p.EntryPrice - basket.StructuralStop));
                risk += p.VolumeInUnits * _symbol.PipValue * (d + ModeledCostPips());
            }
            foreach (var o in OwnPendingOrders().Where(x => LabelBasketId(x.Label) == basket.BasketId))
            {
                double d = PriceToPips(Math.Abs(o.TargetPrice - basket.StructuralStop));
                risk += o.VolumeInUnits * _symbol.PipValue * (d + ModeledCostPips());
            }
            return risk;
        }

        private void RecordLegFillTelemetry(FibonacciBasket basket, FibonacciGridLeg leg)
        {
            if (leg.FillCounted) return;
            if (leg.State != GridLegState.PROTECTED || leg.PositionId <= 0 || !_postFillValidated.Contains(leg.PositionId))
            {
                _executionStateViolations++;
                BasketEvent(basket, "FILL_TELEMETRY_WITHOUT_PROTECTION_L" + leg.Index);
                return;
            }
            leg.FillCounted = true;
            basket.FilledLegs = Math.Max(basket.FilledLegs, basket.Plan.Legs.Count(x => x.FillCounted));
            if (leg.Index == 1) CountPipeline(basket.Pattern).Leg1Filled++;
            if (leg.Index == 2) CountPipeline(basket.Pattern).Leg2Filled++;
            if (leg.Index == 3) CountPipeline(basket.Pattern).Leg3Filled++;
            BasketEvent(basket, "GRID_LEG_FILLED_L" + leg.Index);
        }

        private void UpdateVirtualGridState(FibonacciBasket basket)
        {
            if (basket == null || !basket.IsActive || BasketStructuralInvalidated(basket)) return;
            foreach (var leg in basket.Plan.Legs.Where(x => !x.Physical && x.State == GridLegState.VIRTUAL_ONLY).ToList())
            {
                bool touched = basket.Direction == TradeDirection.Buy ? _symbol.Ask <= leg.PlannedPrice : _symbol.Bid >= leg.PlannedPrice;
                if (!touched) continue;
                if (!DeeperLegThesisEligible(basket, leg))
                {
                    TransitionLegState(basket, leg, GridLegState.CANCELLED, "VIRTUAL_THESIS_REJECT");
                    continue;
                }
                _virtualGridFills++;
                TransitionLegState(basket, leg, GridLegState.VIRTUAL_FILLED, "VIRTUAL_GRID_FILLED");
            }
        }

        private void RevalidatePendingExposureGovernor()
        {
            foreach (var basket in _baskets.Values.Where(b => b.IsActive).ToList())
            {
                foreach (var o in OwnPendingOrders().Where(x => LabelBasketId(x.Label) == basket.BasketId).ToList())
                {
                    int index = LabelLegIndex(o.Label);
                    var leg = basket.Plan.Legs.FirstOrDefault(x => x.Index == index);
                    if (leg == null || !leg.Physical) continue;
                    if (DeeperLegThesisEligible(basket, leg)) continue;

                    var r = CancelPendingOrder(o);
                    if (r == null || !r.IsSuccessful)
                    {
                        if (PendingOrderStillExists(o.Id))
                            RecordExecutionError("EXPOSURE_GOVERNOR_CANCEL_" + (r == null ? "NULL" : r.Error.ToString()),
                                "basket=" + basket.BasketId + ";order=" + o.Id);
                        continue;
                    }
                    TransitionLegState(basket, leg, GridLegState.CANCELLED, "EXPOSURE_GOVERNOR");
                }
            }
        }

        private void TransitionLegState(FibonacciBasket basket, FibonacciGridLeg leg, GridLegState next, string reason)
        {
            GridLegState prior = leg.State;
            bool allowed =
                prior == next ||
                (prior == GridLegState.PLANNED && (next == GridLegState.SUBMITTING || next == GridLegState.CANCELLED ||
                    next == GridLegState.EXPIRED || next == GridLegState.REJECTED || next == GridLegState.RISK_REJECTED ||
                    next == GridLegState.VIRTUAL_ONLY)) ||
                (prior == GridLegState.SUBMITTING && (next == GridLegState.SUBMITTED || next == GridLegState.FILLED_UNVERIFIED ||
                    next == GridLegState.REJECTED || next == GridLegState.FAIL_CLOSED || next == GridLegState.CANCELLED ||
                    next == GridLegState.EXPIRED)) ||
                (prior == GridLegState.SUBMITTED && (next == GridLegState.FILLED_UNVERIFIED || next == GridLegState.CANCELLED ||
                    next == GridLegState.EXPIRED || next == GridLegState.FAIL_CLOSED)) ||
                (prior == GridLegState.FILLED_UNVERIFIED && (next == GridLegState.PROTECTED || next == GridLegState.FAIL_CLOSED)) ||
                (prior == GridLegState.PROTECTED && next == GridLegState.FAIL_CLOSED) ||
                (prior == GridLegState.VIRTUAL_ONLY && (next == GridLegState.VIRTUAL_FILLED || next == GridLegState.CANCELLED ||
                    next == GridLegState.EXPIRED));
            if (!allowed)
            {
                _executionStateViolations++;
                Print("[V51-STATE-VIOLATION] basket={0} leg=L{1} prior={2} next={3} reason={4}", basket == null ? "" : basket.BasketId, leg.Index, prior, next, reason);
            }
            leg.State = next;
            if (basket != null) BasketEvent(basket, "LEG_STATE_L" + leg.Index + "_" + prior + "_TO_" + next + "_" + reason);
        }

        private void PrintBrokerCapabilityProfile()
        {
            double min = _symbol.VolumeInUnitsMin;
            double marginBuy = EstimatedMargin(TradeDirection.Buy, min);
            double marginSell = EstimatedMargin(TradeDirection.Sell, min);
            Print("[V51-BROKER-PROFILE] symbol={0} equity={1:F2} freeMargin={2:F2} minVolume={3} step={4} maxVolume={5} pipValue={6} tickValue={7} minSL={8} minTP={9} minDistanceType={10} minMarginBuy={11:F2} minMarginSell={12:F2} minimumSupportedEquity={13:F2} adaptiveCapital={14} microThreshold={15:F2} initialCapitalEligible={16}",
                SymbolName, Account.Equity, Account.FreeMargin, _symbol.VolumeInUnitsMin, _symbol.VolumeInUnitsStep, _symbol.VolumeInUnitsMax,
                _symbol.PipValue, _symbol.TickValue, _symbol.MinStopLossDistance, _symbol.MinTakeProfitDistance, _symbol.MinDistanceType,
                marginBuy, marginSell, MinimumSupportedEquity, AdaptiveCapitalMode, MicroCapitalThreshold, _initialCapitalEligible);
        }

        private double WeightedAverageEntry(List<Position> positions)
        {
            double volume = positions.Sum(p => p.VolumeInUnits);
            return volume > 0 ? positions.Sum(p => p.EntryPrice * p.VolumeInUnits) / volume : 0;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p == null || p.SymbolName != SymbolName || string.IsNullOrWhiteSpace(p.Label) || !p.Label.StartsWith(BotPrefix + "|", StringComparison.Ordinal))
                return;

            PositionLedger l;
            if (!_positions.TryGetValue(p.Id, out l))
            {
                Print("[V51-LEG-CLOSED] pos={0} basket=UNKNOWN net={1:F2} reason={2}", p.Id, p.NetProfit, args.Reason);
                return;
            }

            FibonacciBasket basket = null;
            if (_baskets.TryGetValue(l.BasketId, out basket))
            {
                if (!string.IsNullOrWhiteSpace(basket.CandidateId) &&
                    basket.CandidateId.StartsWith("V71EXP-", StringComparison.Ordinal))
                    _v71ExpansionRealizedNet += p.NetProfit;
                basket.RealizedNet += p.NetProfit;
                basket.ClosedLegs++;
                double legRealizedR = l.InitialRiskPips > 0 ? p.Pips / l.InitialRiskPips : 0;
                Print("[V51-LEG-CLOSED] basket={0} cid={1} leg=L{2} pos={3} pattern={4} route={5} dir={6} mfeR={7:F3} maeR={8:F3} realizedR={9:F3} net={10:F2} reason={11}",
                    basket.BasketId, basket.CandidateId, l.LegIndex, p.Id, basket.Pattern, basket.Route, basket.Direction,
                    l.PeakR, l.MaxAdverseR, legRealizedR, p.NetProfit, args.Reason);

                if (args.Reason.ToString().IndexOf("TakeProfit", StringComparison.OrdinalIgnoreCase) >= 0)
                    CancelBasketPending(basket, "CANONICAL_TARGET_REACHED");
            }

            _positions.Remove(p.Id);
            _postFillValidated.Remove(p.Id);

            if (basket != null &&
                !OwnPositions().Any(x => LabelBasketId(x.Label) == basket.BasketId) &&
                !OwnPendingOrders().Any(x => LabelBasketId(x.Label) == basket.BasketId))
                CloseBasketLedger(basket, string.IsNullOrWhiteSpace(basket.ExitOverride) ? args.Reason.ToString() : basket.ExitOverride);
        }

        private void CloseBasketLedger(FibonacciBasket basket, string reason)
        {
            if (!basket.IsActive) return;
            basket.IsActive = false;
            basket.State = FibonacciBasketState.CLOSED;
            basket.ExitReason = reason;

            double realizedR = basket.InitialBasketRisk > 0 ? basket.RealizedNet / basket.InitialBasketRisk : 0;
            CountPipeline(basket.Pattern).BasketClosed++;
            BasketEvent(basket, "BASKET_CLOSED_" + reason);

            double entryImprovementPips = basket.AverageEntry > 0
                ? PriceToPips(basket.Direction == TradeDirection.Buy ? basket.EntryAnchor - basket.AverageEntry : basket.AverageEntry - basket.EntryAnchor)
                : 0;
            string setupKey = basket.Candidate != null ? basket.Candidate.SetupKey : "";
            string subtype = basket.Candidate != null && basket.Candidate.Signal != null ? basket.Candidate.Signal.HarmonicSubtype : basket.Pattern;
            Print("[V51-BASKET-CLOSED] basket={0} cid={1} setup={2} pattern={3} subtype={4} route={5} dir={6} plannedLegs={7} filledLegs={8} anchor={9} avgEntry={10} entryImprovePips={11:F3} stop={12} target={13} initialRisk={14:F2} worstRisk={15:F2} mfeR={16:F3} maeR={17:F3} realizedR={18:F3} net={19:F2} reason={20}",
                basket.BasketId, basket.CandidateId, setupKey, basket.Pattern, subtype, basket.Route, basket.Direction, basket.Plan.Legs.Count, basket.FilledLegs,
                basket.EntryAnchor, basket.AverageEntry, entryImprovementPips, basket.StructuralStop, basket.CanonicalTarget,
                basket.InitialBasketRisk, basket.PlannedWorstCaseRisk, basket.PeakR, basket.MaxAdverseR, realizedR, basket.RealizedNet, reason);

            double occupancyMin = Math.Max(0, (Server.Time.ToUniversalTime() - basket.CreatedUtc).TotalMinutes);
            _basketOccupancyMinutes.Add(occupancyMin);
            Print("[V51-SLOT-OCCUPANCY] basket={0} cid={1} pattern={2} route={3} occupancyMinutes={4:F2} realizedR={5:F3} net={6:F2}",
                basket.BasketId, basket.CandidateId, basket.Pattern, basket.Route, occupancyMin, realizedR, basket.RealizedNet);

            if (EnableEventDrivenSerialHandoff)
                TryScheduleAndExecute();
        }

        private IEnumerable<PendingOrder> OwnPendingOrders()
        {
            return PendingOrders.Where(o => o.SymbolName == SymbolName &&
                !string.IsNullOrWhiteSpace(o.Label) && o.Label.StartsWith(BotPrefix + "|", StringComparison.Ordinal));
        }

        private bool LegAlreadyExists(string label)
        {
            return OwnPositions().Any(p => p.Label == label) || OwnPendingOrders().Any(o => o.Label == label);
        }

        private string NewBasketId()
        {
            _basketSeq++;
            return BotPrefix + "-" + SymbolName + "-" + Server.Time.ToUniversalTime().ToString("yyyyMMdd", CultureInfo.InvariantCulture) + "-" +
                   _basketSeq.ToString("D6", CultureInfo.InvariantCulture);
        }

        private string GridLabel(string basketId, int legIndex)
        {
            return BotPrefix + "|" + basketId + "|L" + legIndex;
        }

        private string GridComment(FibonacciBasket basket, int legIndex)
        {
            return "cid=" + basket.CandidateId + ";basket=" + basket.BasketId + ";leg=L" + legIndex +
                   ";pattern=" + basket.Pattern + ";tf=M15;route=" + basket.Route;
        }

        private string LabelBasketId(string label)
        {
            if (string.IsNullOrWhiteSpace(label)) return null;
            var p = label.Split('|');
            return p.Length >= 3 && p[0] == BotPrefix ? p[1] : null;
        }

        private int LabelLegIndex(string label)
        {
            if (string.IsNullOrWhiteSpace(label)) return -1;
            var p = label.Split('|');
            if (p.Length < 3 || !p[2].StartsWith("L", StringComparison.Ordinal)) return -1;
            int x;
            return int.TryParse(p[2].Substring(1), out x) ? x : -1;
        }

        private void BasketEvent(FibonacciBasket basket, string reason)
        {
            Print("[V51-BASKET-EVENT] basket={0} cid={1} pattern={2} route={3} state={4} reason={5}",
                basket.BasketId, basket.CandidateId, basket.Pattern, basket.Route, basket.State, reason);
        }

        private DateTime MinDate(DateTime a, DateTime b) { return a <= b ? a : b; }

        // V71/V72 research-resolution implementation is isolated in
        // Architecture/HarmonyBotV71.Resolution.cs. This boundary is behavior-preserving:
        // frozen harmonic detection and protected V51 capital semantics remain authoritative.

    }
}
