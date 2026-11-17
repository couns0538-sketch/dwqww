
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

// ---- verbatim extraction from the engine source -------------------------
constexpr int MaxPly = 128;
constexpr int Infinite = 32001;
constexpr int MateValue = 32000;
constexpr int MateInMaxPly = MateValue - MaxPly;
constexpr int ValueNone = 32002;

[[nodiscard]] int score_to_tt(int score, int ply) {
    if (score >= MateInMaxPly) return score + ply;
    if (score <= -MateInMaxPly) return score - ply;
    return score;
}

[[nodiscard]] int score_from_tt(int score, int ply) {
    if (score == ValueNone) return ValueNone;
    if (score >= MateInMaxPly) {
        const int adjusted = score - ply;
        return adjusted >= MateInMaxPly ? adjusted : ValueNone;
    }
    if (score <= -MateInMaxPly) {
        const int adjusted = score + ply;
        return adjusted <= -MateInMaxPly ? adjusted : ValueNone;
    }
    return score;
}

// ------------------------------------------------------------------------

// A planted-wrong pair, shaped like real defects seen in engines.
// PLANT=noadjust:  store does not add ply (the classic missing adjustment).
// PLANT=invert:    the sign of the adjustment is inverted.
static int bad_to_tt(int score, int ply) {
    if (score >= MateInMaxPly) return score;      // no adjustment on store
    if (score <= -MateInMaxPly) return score;
    return score;
}
static int bad_from_tt(int score, int ply) {
    if (score == ValueNone) return ValueNone;
    if (score >= MateInMaxPly) return score - ply;
    if (score <= -MateInMaxPly) return score + ply;
    return score;
}
static int inv_to_tt(int score, int ply) {
    if (score >= MateInMaxPly) return score - ply;
    if (score <= -MateInMaxPly) return score + ply;
    return score;
}

struct Fail { const char* what; int p, q, rem, got, want; };

int main() {
    std::vector<Fail> fails;
    int checked = 0;
    // rem = plies remaining below the node; p = storing ply; q = reading ply.
    // Legal search window: the mate is inside the horizon from the reading root,
    // i.e. q + rem <= MaxPly - 1, and 1 <= rem <= MaxPly - 1.
    const int rems[] = {1, 2, 3, 4, 7, 8, 15, 31, 64, 127};
    for (int rem : rems) {
        for (int p = 0; p + rem <= MaxPly - 1; ++p) {
            for (int q = 0; q + rem <= MaxPly - 1; ++q) {
                const int stored = score_to_tt(MateValue - (p + rem), p);
                // store must be position-relative and stay inside the band
                const int want_stored = MateValue - rem;
                if (stored != want_stored) {
                    fails.push_back({"store-not-position-relative", p, q, rem, stored, want_stored});
                }
                const int back = score_from_tt(stored, q);
                const int want_back = MateValue - (q + rem);
                if (back != want_back) {
                    fails.push_back({"probe-mismatch", p, q, rem, back, want_back});
                }
                // the recovered ROOT-RELATIVE distance must be q + rem:
                // the mate is rem plies below the node, and the node sits q plies
                // below the new root. (An earlier version of this check compared
                // against `rem` alone and fired on 117,304 of 118,327 cells --
                // a checker that rejects everything is as useless as one that
                // accepts everything.)
                if (back != ValueNone && MateValue - std::abs(back) != q + rem) {
                    fails.push_back({"distance-drift", p, q, rem, MateValue - std::abs(back), q + rem});
                }
                // negative side, same properties
                const int nstored = score_to_tt(-(MateValue - (p + rem)), p);
                const int want_n = -(MateValue - rem);
                if (nstored != want_n) {
                    fails.push_back({"store-neg", p, q, rem, nstored, want_n});
                }
                const int nback = score_from_tt(nstored, q);
                const int want_nb = -(MateValue - (q + rem));
                if (nback != want_nb) {
                    fails.push_back({"probe-neg", p, q, rem, nback, want_nb});
                }
                ++checked;
            }
        }
    }
    // non-mate scores must pass through untouched
    for (int s : {-3000, -1, 0, 1, 3000}) {
        if (score_to_tt(s, 40) != s || score_from_tt(s, 40) != s) {
            fails.push_back({"cp-passthrough", 40, 40, 0, 0, s});
        }
        ++checked;
    }
    // ValueNone must survive the probe path
    if (score_from_tt(ValueNone, 10) != ValueNone) fails.push_back({"valuenone", 10, 10, 0, 0, 0});

    // ---- the coordinator's named experiment, spelled out -----------------
    // "store a mate at ply 4 and probe at ply 8, compare against the DTM".
    // DTM here is `rem` plies below the node; the value stored must be the
    // position-relative MATE-rem, and reading it at ply 8 must give a
    // root-relative distance of 8+rem -- i.e. the same DTM, re-referenced.
    printf("named_case store_ply=4 probe_ply=8\n");
    for (int rem : {1, 3, 5, 7, 9}) {
        const int at_node = MateValue - (4 + rem);   // score seen at ply 4
        const int stored  = score_to_tt(at_node, 4); // what the table holds
        const int reread  = score_from_tt(stored, 8);
        const int dist_at_node = MateValue - std::abs(at_node);   // root-relative at ply 4
        const int dist_reread  = reread == ValueNone ? -1 : MateValue - std::abs(reread);
        // Three things must hold, and they are three separate claims:
        //  1. the root-relative distance at storage is 4 + rem;
        //  2. the root-relative distance at the re-probe is 8 + rem;
        //  3. the distance BELOW THE NODE -- dist minus its own ply -- is rem
        //     both times, i.e. the mate itself did not move.
        // Assertion 3 is the one that would fail on a wrong or absent
        // adjustment, and it is expressed without reference to either ply.
        const bool dtm_same = (dist_at_node == 4 + rem) && (dist_reread == 8 + rem)
                              && (dist_at_node - 4 == rem) && (dist_reread - 8 == rem);
        printf("  rem=%d node=%d stored=%d reread=%d dist@4=%d dist@8=%d below_node=%d %s\n",
               rem, at_node, stored, reread, dist_at_node, dist_reread,
               dist_reread - 8, dtm_same ? "OK" : "MISMATCH");
        if (!dtm_same) fails.push_back({"named_case", 4, 8, rem, dist_reread, 8 + rem});
        ++checked;
    }
    // Can a legitimate DTM reach the clamp? MateInMaxPly = MateValue - MaxPly,
    // so a mate score touches the clamp exactly at distance MaxPly. Report the
    // largest DTM the search can produce and whether it lands on the boundary.
    printf("clamp MateInMaxPly=%d MateValue=%d MaxPly=%d\n", MateInMaxPly, MateValue, MaxPly);
    printf("  max_legal_dtm_plies=%d  score_at_max=%d  is_mate_score=%d\n",
           MaxPly - 1, MateValue - (MaxPly - 1),
           (MateValue - (MaxPly - 1)) >= MateInMaxPly ? 1 : 0);
    printf("  score_at_exactly_MaxPly=%d  is_mate_score=%d\n",
           MateValue - MaxPly, (MateValue - MaxPly) >= MateInMaxPly ? 1 : 0);

    printf("cells_checked %d\n", checked);
    printf("failures %zu\n", fails.size());
    for (size_t i = 0; i < fails.size() && i < 12; ++i) {
        printf("  FAIL %s p=%d q=%d rem=%d got=%d want=%d\n",
               fails[i].what, fails[i].p, fails[i].q, fails[i].rem, fails[i].got, fails[i].want);
    }

    // ---- the same assertions against a PLANTED-WRONG pair ---------------
    std::vector<Fail> bad;
    int bad_checked = 0;
    for (int rem : rems) {
        for (int p = 0; p + rem <= MaxPly - 1; ++p) {
            for (int q = 0; q + rem <= MaxPly - 1; ++q) {
                const int stored_b = bad_to_tt(MateValue - (p + rem), p);
                const int back_b = bad_from_tt(stored_b, q);
                if (back_b != MateValue - (q + rem)) {
                    bad.push_back({"planted-noadjust", p, q, rem, back_b, MateValue - (q + rem)});
                }
                const int stored_i = inv_to_tt(MateValue - (p + rem), p);
                const int back_i = score_from_tt(stored_i, q);
                if (back_i != MateValue - (q + rem)) {
                    bad.push_back({"planted-invert", p, q, rem, back_i, MateValue - (q + rem)});
                }
                ++bad_checked;
            }
        }
    }
    printf("planted_cells_checked %d\n", bad_checked);
    printf("planted_failures %zu\n", bad.size());
    for (size_t i = 0; i < bad.size() && i < 6; ++i) {
        printf("  PLANT-FAIL %s p=%d q=%d rem=%d got=%d want=%d\n",
               bad[i].what, bad[i].p, bad[i].q, bad[i].rem, bad[i].got, bad[i].want);
    }
    printf("verdict %s\n", fails.empty() ? "PASS" : "FAIL");
    printf("planted_verdict %s\n", bad.empty() ? "PLANT-NOT-CAUGHT" : "PLANT-CAUGHT");
    return fails.empty() && !bad.empty() ? 0 : 1;
}
