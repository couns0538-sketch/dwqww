// forge6.5 play build: see include/forge/forge65.hpp. Empty unless the build sets -DFORGE65=1.
#if FORGE65

#include "forge/forge65.hpp"

#include <iterator>

namespace forge::forge65 {
namespace {

// The loop's best net (round 67, sha256 737f1978...), byte for byte. The file lies beside this one.
const std::uint8_t NetBytes[] = {
#embed "forge65_net.fnn3"
};

// ALL 24 options the loop sends for that net (pipeline/config.forge.toml, [engine] uci_options and v3_uci_options,
// on 23 November 2026), in the loop's order, as the lines the loop sends; only the net's path names the built-in
// net. The lines go through the engine's own option handlers (uci.cpp), exactly as when the loop sends them.
// The listing in uci.cpp shows the same Hash value: change both together (the checks compare them).
constexpr const char* StartupLines[] = {
    "setoption name Threads value 1",
    "setoption name Hash value 16",
    "setoption name OwnBook value false",
    "setoption name MateAlphaGuard value true",
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
    "setoption name CuckooRep value true",
    "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true",
    "setoption name CorrHistV2 value true",
    "setoption name NNUEArchFile value <forge65>",
    "setoption name NNUEArch value true",
};

}  // namespace

const std::uint8_t* net_data() { return NetBytes; }

std::size_t net_size() { return sizeof(NetBytes); }

bool startup_line(std::size_t& index, std::string& line) {
    if (index >= std::size(StartupLines)) return false;
    line = StartupLines[index++];
    return true;
}

}  // namespace forge::forge65

#endif
