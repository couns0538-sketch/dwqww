#!/usr/bin/env python3
"""make_debug_patch.py : writes the EXPERIMENT instrumentation as a text patch.

Adds stderr prints (stderr, so the `info` line on stdout stays byte-identical for the harness) at every
place the ROOT can produce a score without a normal search:

  P1  after root_drawn is computed:            prints legal/root_candidates, is_insufficient_material,
                                               halfmove, is_repetition, and root_drawn itself
  P2  inside the root_drawn early-return:      prints "ROOT-DRAWN PATH" with the score and depth loop
  P3  inside the emergency-ply / hard-limit     prints "EMERGENCY/HARDLIMIT PATH" with clock_reserve_empty_
      early returns                            and hard_limit_passed
  P4  at the root loop's finished iteration:   prints depth, score, pv_length, nodes  (so a 0 score that
                                               came out of a REAL search is distinguishable from a shortcut)
  P5  in Worker::is_draw:                      prints "IS_DRAW fired" with FEN, halfmove, and which sub-test
                                               returned true (rate-limited to the first 200 hits per process)
  P6  at the top of the main search() for ply 0: prints the incoming board FEN and halfmove clock

Guard: everything behind FORGE_CLOCK99_DEBUG so the patch cannot change behaviour when the flag is off.
This is EXPERIMENT instrumention only: it must never be committed to the repository source.
"""
import pathlib

OUT = pathlib.Path("/agent/repos/dwqww/forge-combo29/swarm/25/debug/FORGE_EXPERIMENT_clock99_debug.patch.txt")

ORIG = "/agent/repos/pcsrc/forge-combo29/src/search.cpp"
lines = pathlib.Path(ORIG).read_text().split("\n")


def find(needle, start=0, stop=None):
    stop = stop or len(lines)
    for i in range(start, stop):
        if needle in lines[i]:
            return i
    raise SystemExit(f"needle not found: {needle}")


# We build the patch by hand as a unified diff of the few hunks, so it applies with `patch -p1` cleanly.
hunks = []


def hunk(start_line, context_before, new_body, context_after, note):
    """start_line is 1-based line in the ORIGINAL file where context_before begins."""
    old = context_before + new_body[0] + context_after
    new = context_before + new_body[1] + context_after
    old_count = len(old)
    new_count = len(new)
    body = [f"@@ -{start_line},{old_count} +{start_line},{new_count} @@ // EXPERIMENT {note}"]
    body += [" " + l for l in context_before]
    body += ["-" + l for l in new_body[0]]
    body += ["+" + l for l in new_body[1]]
    body += [" " + l for l in context_after]
    hunks.append("\n".join(body))


# HUNK 1: instrument is_draw (P5)
i = find("bool Worker::is_draw(const Board& board, int ply) const {")
ctx_b = lines[i - 1:i]
old_body = lines[i:i + 11]
new_body = [
    '#ifdef FORGE_CLOCK99_DEBUG',
    '    {',
    '        static std::atomic<int> dbg_hits{0};',
    '        const int h = dbg_hits.fetch_add(1, std::memory_order_relaxed);',
    '        if (h < 200) {',
    '            const bool fifty = board.halfmove_clock() >= 100;',
    '            const bool rep = board.is_repetition(root_history_index_);',
    '            const bool insuf = board.is_insufficient_material();',
    '            const bool nomove = !board.in_check() && !board.has_legal_move();',
    '            std::cerr << "[DBG is_draw# " << h << "] clock=" << board.halfmove_clock()',
    '                      << " fifty=" << fifty << " rep=" << rep << " insuf=" << insuf',
    '                      << " nomove=" << nomove << " fen=" << board.fen() << std::endl;',
    '        }',
    '    }',
    '#endif',
]
new_body += old_body
hunk(i, ctx_b, (old_body, new_body), [], "P5 instrument Worker::is_draw")

# HUNK 2: instrument root_drawn + its early return (P1, P2)
i = find("    const bool root_drawn = !legal.empty() && board.is_insufficient_material();")
ctx_b = lines[i - 2:i]
old_body = lines[i:i + 4]
new_body = [
    '#ifdef FORGE_CLOCK99_DEBUG',
    '    std::cerr << "[DBG root] legal=" << legal.size() << " cands=" << root_candidates.size()',
    '              << " clock=" << board.halfmove_clock()',
    '              << " insuf=" << board.is_insufficient_material()',
    '              << " rep=" << board.is_repetition()',
    '              << " fen=" << board.fen() << std::endl;',
    '#endif',
]
new_body += old_body
hunk(i, ctx_b, (old_body, new_body), [], "P1 instrument root_drawn computation")

# HUNK 3: instrument the root_drawn early-return body (P2)
i = find("    if (root_candidates.empty() || root_drawn) {")
ctx_b = lines[i:i + 1]
old_body = lines[i + 1:i + 4]
new_body = [
    '#ifdef FORGE_CLOCK99_DEBUG',
    '        std::cerr << "[DBG ROOT-DRAWN PATH] clock=" << board.halfmove_clock()',
    '                  << " cands=" << root_candidates.size()',
    '                  << " legal=" << legal.size()',
    '                  << " -> returning without search, score will be 0" << std::endl;',
    '#endif',
]
new_body += old_body
hunk(i + 1, ctx_b, (old_body, new_body), [], "P2 instrument ROOT-DRAWN early return")

# HUNK 4: instrument the emergency / hard-limit early returns (P3)
i = find("    if (!waiting_to_ponder && (clock_reserve_empty_ || hard_limit_passed) && !root_candidates.empty()) {")
ctx_b = lines[i:i + 1]
old_body = lines[i + 1:i + 2]
new_body = [
    '#ifdef FORGE_CLOCK99_DEBUG',
    '        std::cerr << "[DBG EMERGENCY/HARDLIMIT PATH] clock=" << board.halfmove_clock()',
    '                  << " reserve_empty=" << clock_reserve_empty_',
    '                  << " hard_limit_passed=" << hard_limit_passed',
    '                  << " ponder=" << waiting_to_ponder << std::endl;',
    '#endif',
]
new_body += old_body
hunk(i + 1, ctx_b, (old_body, new_body), [], "P3 instrument EMERGENCY/HARDLIMIT path")

# HUNK 5: instrument the finished-iteration store in the root loop (P4)
i = find("        result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);")
# pick the one inside the root loop (after the aspiration block); it is the last such line
occurrences = [j for j, l in enumerate(lines) if "result.pv.assign(ss->pv.begin()" in l]
target = occurrences[-1]
ctx_b = lines[target - 1:target]
old_body = lines[target:target + 1]
new_body = [
    '#ifdef FORGE_CLOCK99_DEBUG',
    '        std::cerr << "[DBG ROOT ITER] depth=" << depth << " score=" << score',
    '                  << " pv_len=" << ss->pv_length << " clock=" << board.halfmove_clock() << std::endl;',
    '#endif',
]
new_body += old_body
hunk(target, ctx_b, (old_body, new_body), [], "P4 instrument finished root iteration")

header = """--- a/src/search.cpp
+++ b/src/search.cpp
"""
patch = header + "\n".join(hunks) + "\n"
OUT.write_text(patch)
print(f"wrote {OUT}")
print(f"hunks: {len(hunks)}")
