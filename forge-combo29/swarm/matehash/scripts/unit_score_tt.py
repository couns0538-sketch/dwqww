"""Unit-level test of score_to_tt / score_from_tt.

The two functions live in an anonymous namespace inside src/search.cpp, so they
cannot be linked against. This harness EXTRACTS THEM BY TEXT from the audit-base
source and compiles that extraction, and records the sha256 of the extracted text
so a reader can confirm the code under test is the engine's code and not a
retyped copy.

The property under test is the one the engine relies on: a mate score stored at
one ply and read at another must describe the same distance FROM THE POSITION.
Concretely, for a mate with `rem` plies remaining below a node:

    score at ply p        = MATE - (p + rem)        (relative to the search root)
    score_to_tt(s, p)     = MATE - rem              (position-relative)
    score_from_tt(_, q)   = MATE - (q + rem)        (relative to the NEW root)

so the invariant is: from_tt(to_tt(MATE-(p+rem), p), q) == MATE-(q+rem), and in
particular the recovered distance rem = MATE - |value| + q is unchanged.

A planted-wrong pair is run through the SAME assertions to prove they can fail.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SEARCH_CPP = REPO / "src" / "search.cpp"
SEARCH_HPP = REPO / "include" / "forge" / "search.hpp"

NEEDED_CONSTANTS = re.compile(r"constexpr int (MaxPly|Infinite|MateValue|MateInMaxPly|ValueNone) = ([^;]+);")
FUNC_TO_TT = re.compile(r"\[\[nodiscard\]\] int score_to_tt\(int score, int ply\) \{.*?\n\}", re.S)
FUNC_FROM_TT = re.compile(r"\[\[nodiscard\]\] int score_from_tt\(int score, int ply\) \{.*?\n\}", re.S)


def extract():
    cpp = SEARCH_CPP.read_text()
    hpp = SEARCH_HPP.read_text()
    consts = NEEDED_CONSTANTS.findall(hpp)
    want = {"MaxPly", "Infinite", "MateValue", "MateInMaxPly", "ValueNone"}
    got = {name for name, _ in consts}
    if got != want:
        raise SystemExit(f"constant set changed: extracted {sorted(got)} want {sorted(want)}")
    to_tt = FUNC_TO_TT.search(cpp)
    from_tt = FUNC_FROM_TT.search(cpp)
    if not to_tt or not from_tt:
        raise SystemExit("could not extract the two functions by text")
    const_src = "\n".join(f"constexpr int {n} = {v};" for n, v in consts if n in want)
    body = const_src + "\n\n" + to_tt.group(0) + "\n\n" + from_tt.group(0) + "\n"
    digest = hashlib.sha256(body.encode()).hexdigest()
    return body, digest


HARNESS = r"""
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

// ---- verbatim extraction from the engine source -------------------------
@@BODY@@
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
"""


def main():
    body, digest = extract()
    src = REPO / "swarm" / "matehash" / "scripts" / "_unit_extract.cpp"
    src.write_text(HARNESS.replace("@@BODY@@", body))
    exe = src.with_suffix(".bin")
    cc = subprocess.run(
        ["/usr/bin/g++", "-std=c++20", "-O1", "-o", str(exe), str(src)],
        capture_output=True, text=True,
    )
    if cc.returncode != 0:
        print(cc.stderr[-3000:])
        raise SystemExit("compile failed")
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    print(f"extracted_sha256 {digest}")
    print(f"source {SEARCH_CPP}")
    print(run.stdout)
    (REPO / "swarm" / "matehash" / "evidence" / "unit_score_tt.json").write_text(json.dumps({
        "extracted_sha256": digest,
        "source_file": str(SEARCH_CPP),
        "extracted_source": body,
        "stdout": run.stdout,
        "returncode": run.returncode,
    }, indent=2))
    return run.returncode


if __name__ == "__main__":
    sys.exit(main())
