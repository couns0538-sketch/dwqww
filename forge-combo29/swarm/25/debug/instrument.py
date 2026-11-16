#!/usr/bin/env python3
"""instrument.py : builds the instrumented copy and emits a real unified diff.

Approach that cannot mis-count hunk lines: copy the PC tree to a scratch dir, EDIT the copy by exact string
replacement, then run `diff -u` on the single changed file and save the result as the EXPERIMENT patch. The
patch is therefore guaranteed to apply with `patch -p1` because it IS a diff of that file.

Instrumentation is stderr-only, behind FORGE_CLOCK99_DEBUG, so:
  * stdout `info` lines stay byte-identical (the harnesses keep working),
  * with the flag off the binary behaves exactly like the release build.
"""
import pathlib
import shutil
import subprocess
import sys

SRC = pathlib.Path("/agent/repos/pcsrc/forge-combo29")
WORK = pathlib.Path("/agent/repos/dbg")
OUTDIR = pathlib.Path("/agent/repos/dwqww/forge-combo29/swarm/25/debug")

if WORK.exists():
    shutil.rmtree(WORK)
shutil.copytree(SRC, WORK, ignore=shutil.ignore_patterns("tests_*", "docs", "*.zip"))

f = WORK / "src" / "search.cpp"
text = f.read_text()
orig = text

def sub(old, new, what):
    global text
    if old not in text:
        raise SystemExit(f"PATTERN NOT FOUND for {what}:\n{old[:200]}")
    if text.count(old) != 1:
        raise SystemExit(f"PATTERN NOT UNIQUE ({text.count(old)}x) for {what}")
    text = text.replace(old, new)
    print(f"instrumented: {what}")

# P5 + P6: instrument is_draw to say which sub-test fired
sub(
"""bool Worker::is_draw(const Board& board, int ply) const {
    (void)ply;
    if (board.halfmove_clock() >= 100) {""",
"""bool Worker::is_draw(const Board& board, int ply) const {
    (void)ply;
#ifdef FORGE_CLOCK99_DEBUG
    {
        // EXPERIMENT (swarm seat 25): report which sub-test decides "draw" at this node.
        static std::atomic<int> dbg_n{0};
        const int n = dbg_n.fetch_add(1, std::memory_order_relaxed);
        if (n < 300) {
            const bool fifty = board.halfmove_clock() >= 100;
            const bool rep = board.is_repetition(root_history_index_);
            const bool insuf = board.is_insufficient_material();
            const bool nomove = !board.in_check() && !board.has_legal_move();
            const bool verdict = fifty ? (!board.in_check() || board.has_legal_move())
                                       : (rep || insuf || nomove);
            if (verdict) {
                std::cerr << "[DBG is_draw TRUE #" << n << "] clock=" << board.halfmove_clock()
                          << " fifty=" << fifty << " rep=" << rep << " insuf=" << insuf
                          << " nomove=" << nomove << " fen=" << board.fen() << std::endl;
            }
        }
    }
#endif
    if (board.halfmove_clock() >= 100) {""",
    "is_draw sub-test reporter (P5)",
)

# P1/P2: the root_drawn decision and its early return
sub(
"""    const bool root_drawn = !legal.empty() && board.is_insufficient_material();""",
"""    const bool root_drawn = !legal.empty() && board.is_insufficient_material();
#ifdef FORGE_CLOCK99_DEBUG
    // EXPERIMENT (swarm seat 25): state of every root shortcut condition.
    std::cerr << "[DBG root] clock=" << board.halfmove_clock()
              << " legal=" << legal.size() << " cands=" << root_candidates.size()
              << " root_drawn=" << root_drawn
              << " insuf=" << board.is_insufficient_material()
              << " rep=" << board.is_repetition()
              << " cands_empty=" << root_candidates.empty()
              << " fen=" << board.fen() << std::endl;
#endif""",
    "root_drawn state print (P1)",
)

sub(
"""    if (root_candidates.empty() || root_drawn) {
        int score = 0;""",
"""    if (root_candidates.empty() || root_drawn) {
#ifdef FORGE_CLOCK99_DEBUG
        std::cerr << "[DBG ROOT-SHORTCUT PATH TAKEN] clock=" << board.halfmove_clock()
                  << " legal=" << legal.size() << " cands=" << root_candidates.size()
                  << " root_drawn=" << root_drawn
                  << " -> search is SKIPPED, score hardcoded 0" << std::endl;
#endif
        int score = 0;""",
    "ROOT-SHORTCUT path taken (P2)",
)

# P3: emergency / hard-limit path
sub(
"""    if (!waiting_to_ponder && (clock_reserve_empty_ || hard_limit_passed) && !root_candidates.empty()) {
        Move hashed = Move::none();""",
"""    if (!waiting_to_ponder && (clock_reserve_empty_ || hard_limit_passed) && !root_candidates.empty()) {
#ifdef FORGE_CLOCK99_DEBUG
        std::cerr << "[DBG EMERGENCY/HARDLIMIT PATH] clock=" << board.halfmove_clock()
                  << " reserve_empty=" << clock_reserve_empty_
                  << " hard_limit_passed=" << hard_limit_passed << std::endl;
#endif
        Move hashed = Move::none();""",
    "emergency/hard-limit path (P3)",
)

# P4: the finished root iteration, so a real-search 0 is distinguishable from a shortcut
sub(
"""        score = iteration_score;
        result.score = score;
        result.depth = depth;""",
"""        score = iteration_score;
#ifdef FORGE_CLOCK99_DEBUG
        std::cerr << "[DBG ROOT ITER SEARCHED] depth=" << depth << " score=" << score
                  << " pv_len=" << ss->pv_length << " clock=" << board.halfmove_clock() << std::endl;
#endif
        result.score = score;
        result.depth = depth;""",
    "finished root iteration (P4)",
)

f.write_text(text)

# produce a real unified diff against the PC source
diff = subprocess.run(
    ["diff", "-u", "--label", "a/src/search.cpp", "--label", "b/src/search.cpp",
     str(SRC / "src" / "search.cpp"), str(f)],
    capture_output=True, text=True)
OUTDIR.mkdir(parents=True, exist_ok=True)
patch = OUTDIR / "FORGE_EXPERIMENT_clock99_debug.patch.txt"
patch.write_text(diff.stdout)
print(f"\nwrote {patch}  ({diff.stdout.count(chr(10))} lines)")
