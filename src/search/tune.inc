// Search module: tunable constants (forge/search_tune.hpp) and the late-move
// reduction / late-move pruning tables derived from them.
// Compiled as part of src/search.cpp (included exactly once).

namespace forge {

namespace tune {
int LmrQuietBase = 85;
int LmrQuietDivisor = 220;
int LmrNoisyBase = 10;
int LmrNoisyDivisor = 340;
int NullMoveMinDepth = 3;
int NullMoveBase = 3;
int NullMoveDepthDivisor = 3;
int NullMoveEvalDivisor = 200;
int RfpDepth = 8;
int RfpMargin = 72;
int RfpImproving = 40;
int RazorDepth = 2;
int RazorBase = 150;
int RazorMultiplier = 350;
int FutilityDepth = 7;
int FutilityBase = 100;
int FutilityMultiplier = 110;
int LmpBase = 4;
int HistoryPruneDepth = 3;
int HistoryPruneMultiplier = 2048;
int SeeQuietMultiplier = 24;
int SeeNoisyMultiplier = 150;
int SingularDepth = 7;
int SingularMargin = 2;
int IirDepth = 4;
int ProbcutDepth = 5;
int ProbcutMargin = 180;
int QsFutilityMargin = 160;
int QsSeeMargin = 40;
int AspirationDelta = 18;
int HistoryBonusQuadratic = 20;
int HistoryBonusLinear = 48;
int HistoryBonusMax = 2048;
int LmrHistoryDivisor = 6000;
int CheckExtensionDepth = 2;
int LmrCutoffThreshold = 3;
int MaterialCorrectionWeight = 100;
int TmSoftDivisor = 22;
int TmIncrementPercent = 75;
int TmHardPercent = 60;
int TmHardSoftMultiple = 5;
int TmStableFactor = 60;
int TmSemiStableFactor = 80;
int TmUnstableFactor = 140;
int TmEffortBase = 155;
int TmFallingEvalPercent = 100;
int TmMinFactorPercent = 45;
int CaptureFutilityBase = 0;
int CaptureFutilityMultiplier = 250;
int CaptureFutilityDepth = 6;
int FailLowContinuationBonus = 0;

const std::vector<Parameter>& parameters() {
    static const std::vector<Parameter> table{
        {"LmrQuietBase", &LmrQuietBase, 0, 300},         {"LmrQuietDivisor", &LmrQuietDivisor, 100, 500},
        {"LmrNoisyBase", &LmrNoisyBase, 0, 300},         {"LmrNoisyDivisor", &LmrNoisyDivisor, 100, 800},
        {"NullMoveMinDepth", &NullMoveMinDepth, 1, 10},  {"NullMoveBase", &NullMoveBase, 1, 6},
        {"NullMoveDepthDivisor", &NullMoveDepthDivisor, 1, 10},
        {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
        {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
        {"RfpImproving", &RfpImproving, 0, 200},         {"RazorDepth", &RazorDepth, 0, 6},
        {"RazorBase", &RazorBase, 0, 1000},              {"RazorMultiplier", &RazorMultiplier, 0, 1000},
        {"FutilityDepth", &FutilityDepth, 0, 15},        {"FutilityBase", &FutilityBase, 0, 500},
        {"FutilityMultiplier", &FutilityMultiplier, 0, 500},
        {"LmpBase", &LmpBase, 0, 20},                    {"HistoryPruneDepth", &HistoryPruneDepth, 0, 10},
        {"HistoryPruneMultiplier", &HistoryPruneMultiplier, 0, 20000},
        {"SeeQuietMultiplier", &SeeQuietMultiplier, 0, 200},
        {"SeeNoisyMultiplier", &SeeNoisyMultiplier, 0, 1000},
        {"SingularDepth", &SingularDepth, 2, 20},        {"SingularMargin", &SingularMargin, 0, 10},
        {"IirDepth", &IirDepth, 1, 20},                  {"ProbcutDepth", &ProbcutDepth, 1, 20},
        {"ProbcutMargin", &ProbcutMargin, 0, 1000},      {"QsFutilityMargin", &QsFutilityMargin, 0, 1000},
        {"QsSeeMargin", &QsSeeMargin, 0, 500},           {"AspirationDelta", &AspirationDelta, 4, 200},
        {"HistoryBonusQuadratic", &HistoryBonusQuadratic, 0, 100},
        {"HistoryBonusLinear", &HistoryBonusLinear, 0, 500},
        {"HistoryBonusMax", &HistoryBonusMax, 100, 10000},
        {"LmrHistoryDivisor", &LmrHistoryDivisor, 1000, 30000},
        {"CheckExtensionDepth", &CheckExtensionDepth, 1, 30},
        {"LmrCutoffThreshold", &LmrCutoffThreshold, 0, 20},
        {"MaterialCorrectionWeight", &MaterialCorrectionWeight, 0, 300},
        {"TmSoftDivisor", &TmSoftDivisor, 5, 80},            {"TmIncrementPercent", &TmIncrementPercent, 0, 150},
        {"TmHardPercent", &TmHardPercent, 10, 95},           {"TmHardSoftMultiple", &TmHardSoftMultiple, 1, 20},
        {"TmStableFactor", &TmStableFactor, 20, 150},        {"TmSemiStableFactor", &TmSemiStableFactor, 20, 150},
        {"TmUnstableFactor", &TmUnstableFactor, 50, 300},    {"TmEffortBase", &TmEffortBase, 100, 250},
        {"TmFallingEvalPercent", &TmFallingEvalPercent, 0, 400}, {"TmMinFactorPercent", &TmMinFactorPercent, 10, 100},
        {"CaptureFutilityBase", &CaptureFutilityBase, 0, 1000},  {"CaptureFutilityMultiplier", &CaptureFutilityMultiplier, 0, 1000},
        {"CaptureFutilityDepth", &CaptureFutilityDepth, 0, 15},  {"FailLowContinuationBonus", &FailLowContinuationBonus, 0, 300},
    };
    return table;
}
} // namespace tune

namespace {

struct ReductionTable {
    std::array<std::array<std::uint8_t, 64>, 64> quiet{};
    std::array<std::array<std::uint8_t, 64>, 64> noisy{};
    ReductionTable() { refresh(); }
    void refresh() {
        for (int depth = 1; depth < 64; ++depth) {
            for (int moves = 1; moves < 64; ++moves) {
                const double product = std::log(static_cast<double>(depth)) * std::log(static_cast<double>(moves));
                quiet[static_cast<std::size_t>(depth)][static_cast<std::size_t>(moves)] = static_cast<std::uint8_t>(
                    std::max(0.0, tune::LmrQuietBase / 100.0 + product / (tune::LmrQuietDivisor / 100.0)));
                noisy[static_cast<std::size_t>(depth)][static_cast<std::size_t>(moves)] = static_cast<std::uint8_t>(
                    std::max(0.0, tune::LmrNoisyBase / 100.0 + product / (tune::LmrNoisyDivisor / 100.0)));
            }
        }
    }
};
ReductionTable Reductions;

[[nodiscard]] int reduction(bool quiet, int depth, int moves) {
    const std::size_t d = static_cast<std::size_t>(std::min(depth, 63));
    const std::size_t m = static_cast<std::size_t>(std::min(moves, 63));
    return quiet ? Reductions.quiet[d][m] : Reductions.noisy[d][m];
}

[[nodiscard]] int lmp_threshold(int depth, bool improving) {
    return improving ? tune::LmpBase + depth * depth : (tune::LmpBase + depth * depth) / 2;
}

} // namespace

void tune::refresh() { Reductions.refresh(); }

} // namespace forge
