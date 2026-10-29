#pragma once

#include <array>
#include <string_view>
#include <vector>

namespace forge {

// Search constants exposed for tuning. Every accepted constant is advertised as
// a UCI spin option in every build; defaults remain the tested values. The 20
// named in AdvertisedParameters are listed first for the existing SPSA workflow.
namespace tune {
struct Parameter {
    const char* name;
    int* value;
    int minimum;
    int maximum;
};
extern int LmrQuietBase;      // x0.01
extern int LmrQuietDivisor;   // x0.01
extern int LmrNoisyBase;      // x0.01
extern int LmrNoisyDivisor;   // x0.01
extern int NullMoveMinDepth;
extern int NullMoveBase;
extern int NullMoveDepthDivisor;
extern int NullMoveEvalDivisor;
// Null-move pruning is tried only when static_eval >= beta - NullMoveMarginDepth * depth + NullMoveMarginBase
// (R3-4: the AL1 s198 literals 24 and 180 as tunables, same defaults).
extern int NullMoveMarginDepth;
extern int NullMoveMarginBase;
extern int RfpDepth;
extern int RfpMargin;
extern int RfpImproving;
extern int RazorDepth;
extern int RazorBase;
extern int RazorMultiplier;
extern int FutilityDepth;
extern int FutilityBase;
extern int FutilityMultiplier;
extern int LmpBase;
extern int HistoryPruneDepth;
extern int HistoryPruneMultiplier;
extern int SeeQuietMultiplier;
extern int SeeNoisyMultiplier;
extern int SingularDepth;
extern int SingularMargin;
extern int IirDepth;
extern int ProbcutDepth;
extern int ProbcutMargin;
extern int QsFutilityMargin;
extern int QsSeeMargin;
extern int AspirationDelta;
extern int HistoryBonusQuadratic;
extern int HistoryBonusLinear;
extern int HistoryBonusMax;
extern int LmrHistoryDivisor;
extern int CheckExtensionDepth;
extern int LmrCutoffThreshold;    // child cutoff count above which late moves are reduced more (0 = off)
extern int MaterialCorrectionWeight; // 0 = off, 100 = same weight as the pawn correction
// Time management (sudden-death / increment controls).
extern int TmSoftDivisor;         // soft limit = remaining / divisor + increment share
extern int TmIncrementPercent;    // share of the increment added to the soft limit
extern int TmHardPercent;         // hard limit as a percentage of the remaining time
extern int TmHardSoftMultiple;    // hard limit cap as a multiple of the soft limit
extern int TmStableFactor;        // x0.01 soft scale after 6 stable iterations
extern int TmSemiStableFactor;    // x0.01 soft scale after 3 stable iterations
extern int TmUnstableFactor;      // x0.01 soft scale when the best move just changed
extern int TmEffortBase;          // x0.01: factor *= clamp(base - effort, 0.6, 1.4)
extern int TmFallingEvalPercent;  // extra percent of soft time per 100 cp of score drop since the previous iteration
extern int TmMinFactorPercent;    // lower bound of the combined soft-limit factor (x0.01)
extern int CaptureFutilityBase;   // futility pruning of captures: base margin (0 = off)
extern int CaptureFutilityMultiplier;
extern int CaptureFutilityDepth;
extern int FailLowContinuationBonus; // x0.01 of the history bonus given to the parent move on fail low (0 = off)
// CorrHistPlus (UCI option, default 0 = off): read weights of the extra correction keys (x0.01).
extern int CorrContWeight;        // bit 1: continuation correction (previous two moves)
extern int CorrMinorWeight;       // bit 2: minor-piece correction
extern int CorrNonPawnWeight;     // bit 4: each side's non-pawn correction
// UCI CorrMargins (forge/corr_margins.hpp): weights of |correction| (cp) in the
// pruning margins; read only by the CorrMargins search instance; 0 = no change.
extern int CorrRfpPct;            // reverse futility margin += |correction| * pct / 100
extern int CorrFutilityPct;       // quiet futility margin += |correction| * pct / 100
extern int CorrNullMovePct;       // null-move static-eval threshold += |correction| * pct / 100
extern int CorrLmrPct;            // LMR reduction -= reduction * pct% per 64 cp of |correction|
// UCI CorrExt (forge/corr_ext.hpp): correction-history extensions; read only by
// the CorrExt search instance.
extern int CorrExtDoublePct;      // double-extension margin 24 -= |correction| * pct / 100 (at least 0); 0 = AL1 s198
extern int CorrExtTripleCorr;     // |correction| (cp) from which a triple extension is possible; 0 = no triple
extern int CorrExtTripleMargin;   // triple when the singular score is this far below the singular beta
extern int CorrExtBudget;         // extra plies from double/triple extensions allowed per path (AL1 s198: 7)
[[nodiscard]] const std::vector<Parameter>& parameters();
// Call after changing LMR parameters.
void refresh();

// R3-4: the 20 search constants advertised as UCI spin options in every build
// (default = the current value, min/max = the range in parameters()), for SPSA
// tuning with tools/spsa/opus_spsa.py (tools/spsa/README.md has the reasons for
// the choice). Listed first in this order, grouped by mechanism; the remaining
// registered tunables are advertised afterwards in every build.
inline constexpr std::array<std::string_view, 20> AdvertisedParameters{
    // late-move reductions
    "LmrQuietBase", "LmrQuietDivisor", "LmrNoisyBase", "LmrNoisyDivisor", "LmrHistoryDivisor", "LmrCutoffThreshold",
    // null-move pruning
    "NullMoveBase", "NullMoveDepthDivisor", "NullMoveEvalDivisor", "NullMoveMarginDepth", "NullMoveMarginBase",
    // reverse futility pruning
    "RfpMargin", "RfpImproving", "RfpDepth",
    // futility pruning (main search and quiescence)
    "FutilityBase", "FutilityMultiplier", "QsFutilityMargin",
    // SEE pruning margins of the main search (QsSeeMargin is not here: SEE balances are multiples of 100, so
    // every value 0-99 searches the same tree and small SPSA steps would measure nothing)
    "SeeQuietMultiplier", "SeeNoisyMultiplier",
    // aspiration windows
    "AspirationDelta",
};
} // namespace tune

} // namespace forge
