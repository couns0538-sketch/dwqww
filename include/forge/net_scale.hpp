#pragma once

#include <cstdint>

// S41 NetScale (UCI spin, percent; default 100 = OFF). With a network active, the static evaluation the search
// uses (residual network: hand-crafted evaluation + network correction; stand-alone network: its output) is
// multiplied by NetScale / 100 before the usual clamp, so a network whose evaluations are spread wider or
// narrower than h256_e12's -- the scale the search margins were tuned on -- can be mapped back to that scale.
// 100 returns the evaluation unchanged (the AL1 s198 search). The value is written only while no search runs
// (the UCI loop stops the search first) and the hash is cleared, because the TT stores static evaluations.
// The hand-crafted-only path (UseNNUE false) is never scaled.
namespace forge::net_scale {

inline constexpr int Default = 100;
inline constexpr int Minimum = 50;
inline constexpr int Maximum = 150;

extern int percent;

// eval * pct / 100 in 64-bit arithmetic, truncated toward zero (odd: apply(-e) == -apply(e)); pct == 100 is the
// identity. Callers clamp the result to the non-mate range.
[[nodiscard]] constexpr int apply(int eval, int pct) {
    if (pct == Default) return eval;
    return static_cast<int>(static_cast<std::int64_t>(eval) * pct / 100);
}

} // namespace forge::net_scale
