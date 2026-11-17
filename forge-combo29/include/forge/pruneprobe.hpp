// Passive prune instrumentation for the mate-safety audit (swarm/pruning).
//
// Every macro below is a no-op unless -DFORGE_PRUNE_PROBE=1, so a build without
// that flag is byte-for-byte the audit base. With the flag on and no ablation
// option set, the counters are *passive*: they read state and add nothing to it,
// so node counts must still match the pins. `scripts/check_probe_identity.py`
// proves that; a probe that changed the search would make every count suspect.
//
// The counters exist to answer one question the brief calls the kill condition:
// did the corpus ever REACH a pruning path in a mate-relevant position? A null
// from a corpus that never fires these is not evidence about mate safety.
#pragma once

#include <cstdint>

#if defined(FORGE_PRUNE_PROBE) && FORGE_PRUNE_PROBE

namespace forge::probe {

struct Counts {
    // --- null move ---
    std::uint64_t null_try = 0;             // entered the null-move branch
    std::uint64_t null_cutoff = 0;          // accepted a null score >= beta
    std::uint64_t null_cutoff_verified = 0; // cutoff only after a verification search
    std::uint64_t null_score_mate_clamped = 0; // null_score was a mate score, clamped to beta
    std::uint64_t null_skipped_in_check = 0;   // would not apply anyway; sanity only
    std::uint64_t null_skipped_mate_beta = 0;  // beta was already a mate score

    // --- reverse futility / razor ---
    std::uint64_t razor_entered = 0;
    std::uint64_t razor_cutoff = 0;         // qsearch confirmed < alpha, returned
    std::uint64_t razor_fell_through = 0;   // qsearch did not confirm
    std::uint64_t rfp_cutoff = 0;

    // --- move-loop pruning ---
    std::uint64_t futility_quiet_skip = 0;
    std::uint64_t futility_capture_skip = 0;
    std::uint64_t lmp_skipped_moves = 0;
    std::uint64_t see_quiet_skip = 0;
    std::uint64_t hist_quiet_skip = 0;
    std::uint64_t see_noisy_skip = 0;
    std::uint64_t block_skips = 0;          // one per node whose move-loop block ran

    // --- LMR ---
    std::uint64_t lmr_reduced = 0;
    std::uint64_t lmr_reescalated = 0;      // reduced search beat alpha, full re-search ran
    std::uint64_t lmr_mate_on_reduced = 0;  // reduced search returned a mate score

    // --- singular extension ---
    std::uint64_t singular_search = 0;
    std::uint64_t singular_extension1 = 0;
    std::uint64_t singular_extension2 = 0;
    std::uint64_t singular_multicut = 0;    // singular_beta >= beta, returned

    // --- QuietExtinction ---
    std::uint64_t quiet_tail_closed = 0;    // close_quiet_tail() fired: remaining quiets skipped
    std::uint64_t futility_tight_set = 0;   // one wide quiet miss halved the futility slack
    std::uint64_t extinguish_futility_skip = 0; // the tightened futility arm skipped a quiet

    // --- mate bookkeeping ---
    std::uint64_t nodes = 0;
    std::uint64_t nodes_with_mate_alpha = 0;
    std::uint64_t nodes_with_mate_beta = 0;
    std::uint64_t cutoff_with_mate_score = 0; // a cutoff stored/returned a mate
    std::uint64_t bestmove_mate = 0;
};

inline Counts counts{};

// Ablation switches. OFF (default) = the real engine. Turning one on REMOVES
// that pruning class from the search, which is how a failure is attributed to a
// class rather than merely observed. These are not controls and are not used to
// produce any headline number; scripts/ablate.py labels every row with them.
struct Ablate {
    bool null_move = false;
    bool razor = false;
    bool rfp = false;
    // Removes the WHOLE shallow move-loop pruning block: LMP, futility (quiet
    // and capture), history prune and both SEE gates. It is deliberately coarse
    // -- one switch for "the move loop prunes nothing at shallow depth" -- because
    // the classes inside the block share a single guard and cannot be separated
    // without changing the guard, which would make the control a patch. Named
    // `futility` on the UCI command for brevity; `probestats` reports it as
    // `futility` too, and every row that used it says "move-loop block".
    bool futility = false;
    bool lmr = false;
    bool singular = false;
    // QuietExtinction is off by default like SoundMatePruning, so it is tested
    // by ENABLING it rather than ablating it. This field is unused by the
    // search; it records intent for the UCI `ablate` handler, which rejects
    // `quiet_extinction` with a message pointing at `setoption`.
    bool quiet_extinction = false;
};
inline Ablate ablate{};

inline bool on() { return true; }

} // namespace forge::probe

#define FORGE_PROBE_COUNTER(field) (++::forge::probe::counts.field)
#define FORGE_PROBE_ADD(field, n) (::forge::probe::counts.field += static_cast<std::uint64_t>(n))
#define FORGE_PROBE_ABLATED(name) (::forge::probe::ablate.name)
#define FORGE_PROBE_RESET() (::forge::probe::counts = ::forge::probe::Counts{})

#else

#define FORGE_PROBE_COUNTER(field) ((void)0)
#define FORGE_PROBE_ADD(field, n) ((void)0)
#define FORGE_PROBE_ABLATED(name) (false)
#define FORGE_PROBE_RESET() ((void)0)

#endif
