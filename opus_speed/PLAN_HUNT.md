# Plan - bit-exact speed hunt vs the live lock trial_w6 (2026-11-05 evening, Opus 5.5, effort max)

## Context
QA published trial_w6 (sha256 4181A589..., six speed switches ON) as the live lock. This session hunts the NEXT
bit-exact speed win on top of it: one new switch per idea, proven node-identical (net on + net off, perft, 12k L3),
then timed against trial_w6 by wall nps. Screening only: no lock, no publish, QA re-times. Branch
`opus-speed-20261105`, tip 3ca407b3 (checked, clean), clone `F:\ospd\wt`, commits only via `commit_push.sh` (no
trailer, vendor lint). Checked in orientation: live lock exe = 4181a589 at both paths; session process Idle / 0x3;
load: CPUs 0-1 ~26 %, CPU 2 ~39 % (Idle trainer), CPUs 4-15 ~100 % (crew); F: 53.9 GB free, F:\ospd 6.3 / 8 GB,
C: 117 GB free; the account holds SeLockMemoryPrivilege (disabled until a process enables it in its own token).

## Rules I apply (from the brief + skills forge-pc-rules / forge-speed-lock-path)
- CPUs 0-3 only: builds / checks / profiling at 0x3 Idle, timing on CPU 2 BelowNormal, CPU 3 never used by me.
- Decision ABBAs run ALONE (nothing of mine on CPUs 0-1 meanwhile; coding/reading is fine). PS 5.1 tools start from
  Git Bash (`powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...`), long steps in the background.
- No agents (the brief overrides the plan-mode template), no kills, no deletes, nothing on D:, no STOP/PAUSE files,
  no CURRENT_LOCK / gates / queue / trainer / self-play, no L3b / Threads soak / QA ABBA, no KING_LINES / bundles a-d,
  no MovePicker bad_captures_ fix, no GPL/AGPL code copied (ideas only; own code).
- Disk (user: "c disk has space"): new scratch root `C:\ospd_hunt\` (abba\, builds\, ctl\, prof\, harness\), C: kept
  >= 50 GB free (planned use <= 3 GB). ABBA output goes there via `abba.ps1 -Out` (no tool change); identity builds
  via `build_variants -Work C:\ospd_hunt\builds`. speed_pack keeps its fixed `F:\ospd\packs` / `F:\ospd\builds`
  (~70-90 MB per idea without ABBA -> ~15 ideas of headroom under the 8 GB cap). If F:\ospd reaches ~7.4 GB or F:
  free nears 50 GB: add a `-ScratchRoot` parameter (default F:\ospd, so nothing existing changes) and move packs there.
- `date` read right before every time written into a record; push <= every 10 min (WIP ok), STATUS / FINAL_REPORT /
  RESUME updated on every push; FINAL_REPORT gets a new dated hunt section, earlier verdicts stay as written.

## Verdict rules (unchanged from the skill)
Wall nps of one run decides: WIN = 95 % t-interval low end > 1.000 and median >= 1.010 (d20, 10 rounds ABBA/BAAB,
fresh copies, CPU 2). A wall WIN with a CPU-time NO-WIN is a contradiction, not a lock-style WIN. CPU time never turns
a wall NO-WIN into a WIN. `--pool` is information only. Borderline (median >= +1 % or cpu WIN, wall NO-WIN): exactly
one 16-round re-time; both runs reported with their own verdicts. Session A/A trial_w6 vs itself must be sane
(median within ~+-1.0 %, per-round range <= 4.0 %); if not, re-run it before any decision.

## Session start (right after approval, in this order)
1. `date`; re-check tip / clean tree / exe sha256; create `C:\ospd_hunt\...`; copy this plan to
   `opus_speed/PLAN_HUNT.md`; STATUS / RESUME / FINAL_REPORT hunt headers; first push (WIP).
2. A/A (background, alone): `abba.ps1 -A <lock> -B <lock> -Out C:\ospd_hunt\abba\aa_w6_d20_s1 -Depth 20 -Rounds 10`
   -> this session's `-AaCsv`. While it runs: write the profiler (no CPU).
3. Profile (time-box 45 min): new `opus_speed/tools/rip_sampler.py` (venv python `-I -B`, pins itself 0x3 Idle, engine
   inherits): `bench 20` on the live exe, samples the busy thread's RIP ~1 kHz (Suspend / GetThreadContext /
   Resume), rebases by the runtime module base (DYNAMIC_BASE: rip - base + 0x140000000), maps with `nm -n` (the exe
   keeps its symbols: search, qsearch, evaluate_position, MovePicker::next, make_move, see_ge, has_legal_move,
   is_legal, generate_pseudo_legal, nnue::*). Validity: >= 95 % of samples inside .text, a second run ranks the same
   top 8. Output `C:\ospd_hunt\prof\` + a table in the report. If it drags: fall back to R7's ranking (HCE 14.4 %,
   picker 10.9 %, TT probe 10.7 %, nnue::update 8.3 %, ...) minus what the six switches removed.

## Per-idea pipeline (repeat until usage is almost out)
1. Write the change in a dev copy of `F:\ospd\src\trial_w6` behind `FORGE_SPD_<X>` (`#ifndef` guard, `#define 0` in
   source, new code under `#if`, the lock text verbatim under `#else`); quick o3 build with `-Define` + pins while
   developing. Where the change rewrites logic (not just layout), a differential C++ harness in `opus_speed/tests/`
   compares old vs new on perft walks + the 12k FENs + special positions, with a planted mutant that must fail.
2. Patches: `patches/h<N>_<x>_after_w6.patch` (trial_w6 -> tree) and the full `patches/h<N>_<x>.patch` (lock ->
   tree, what speed_pack verifies); the tree itself from `make_stack.sh h<N>_<x> trial_w6.patch h<N>_<x>_after_w6.patch`.
3. Two identity builds (lp_v1, `-Work C:\ospd_hunt\builds`): all switches 0 = **FD3A5190** byte for byte; six ON +
   new OFF (kit copy in `C:\ospd_hunt\ctl\`) = **4181A589** byte for byte. Either one differs -> stop and find out why.
4. Candidate: `speed_pack -SrcDir F:\ospd\src\h<N>_<x> -Name h<N>_<x> -Define <the six at their values>,FORGE_SPD_<X>=<v>
   -Quick -SkipAbba` -> pc1 = pc2, bitexact vs trial_w6: L1 bench d11-d22 net on AND net off, L2 perft5 + kiwipete,
   L3 2,000 FENs d13, L4 MSVC ASan + g++ UBSan (the first run fills `F:\ospd\ref\4181a589\`, allowed). Exit 3 =
   SEARCH-CHANGING: recorded as such, idea stopped, never tuned back.
5. ABBA alone vs the live lock exe: `abba.ps1 -A <lock> -B <pack exe> -Out C:\ospd_hunt\abba\h<N>_<x>_d20 -Depth 20
   -Rounds 10 -AaCsv C:\ospd_hunt\abba\aa_w6_d20_s1\runs.csv`; `abba_recheck.py` on it; borderline -> one 16-round re-time.
6. WIN (and cpu not contradicting) -> full 12k L3 vs trial_w6 (`bitexact_check` without -Quick; ~40 min the first
   time for the reference) -> pack complete: source, both patches + md5, exe sha256, pins net on/off, perft, ABBA CSV +
   log paths + md5, wall / cpu ratios, candidate file. Then the next idea; with >= 2 winners also ONE stack
   trial_w6 + winners only (own identity builds, pack, ABBA vs trial_w6). No kitchen sink, no publish.
7. Records per idea in STATUS (table row), FINAL_REPORT (hunt section), RESUME (next step): name, define, bit-exact net
   on / net off, wall (+ cpu) ratio vs trial_w6, exe sha256, verdict = screening WIN / NO-WIN / SEARCH-CHANGING.

## Idea queue (each: what it changes / why nodes cannot change; expectations UNPROVEN; the profile may reorder 2-5)
1. `FORGE_SPD_LARGEPAGES` (1 = TT, 2 = TT + per-worker tables arena + net weights): the TT (16 MB in bench = 4,096
   4 KB pages) is allocated in 2 MB pages after the engine enables SeLockMemoryPrivilege in its own token; same
   cluster count (computed from MB exactly as now; only the allocation is rounded up to 2 MB), zeroed and
   constructed as now, same index function -> every probe / store sees the same entries; only TLB misses change. Any
   failure falls back SILENTLY to the lock's allocation (no info string, no UCI option: transcripts stay identical);
   custom deleter / VirtualFree under the switch, `<windows.h>` with NOMINMAX + WIN32_LEAN_AND_MEAN (MSVC L4 builds it
   too). Bench allocates its Searcher(16) inside its timed window, so a slow large-page allocation counts against it
   - accepted as real. Mode 2 is the ablation by value (histories 1.67 MB, pawn cache 1.31 MB, w1 0.77 MB).
2. `FORGE_SPD_HASLEGAL_FAST`: is_draw calls has_legal_move at every non-check node; return true at once when a pawn
   push or a piece move starts on a square not on any queen line of the own king (not in check -> cannot be pinned ->
   legal); every other case (in check, aligned pieces, ep, castling) runs the lock's own code. The boolean is a
   property of the position, so the result is identical. Proof: differential harness incl. stalemates, in-check
   (halfmove >= 100 path), pawns pinned along their push file, ep-only and castling-only positions, planted mutant.
   Does not touch is_legal / gives_check (KING_LINES territory); a merge check is needed before any W9 stack.
3. `FORGE_SPD_PAWN_ENTRY32`: PawnEntry fields reordered to 32 bytes (key, score, valid, passed) in 32-B aligned
   storage (1.31 -> 1.0 MB, no cache-line splits); same index, contents and always-replace policy -> same evals.
4. `FORGE_SPD_HCE_REUSE`: evaluate_pieces / evaluate_king reuse slider attack sets they already computed (queen's
   bishop / rook parts for WeakQueen, rook rays for the passer terms) instead of recomputing the same lookups; same
   bitboards, same adds in the same order (differential eval harness).
5. `FORGE_SPD_SEE_HOIST`: see_ge computes each side's king-ray slider candidates once and masks them with `live`
   inside the loop as now; same sets per iteration -> same boolean (differential harness over all moves x thresholds).
Deprioritised / skipped: int16 w1 (research: -1..+1 % for this net, and it rewrites the NNUE_ZMM input), any sort or
picker change (std::sort tie order -> not bit-exact by construction), MATKEY, PICKBEST, CorrHistPrefetch, a second
AVX-512 net path, KING_LINES-style pin / check caching.

## Files
- New: `opus_speed/PLAN_HUNT.md`, `tools/rip_sampler.py`, `tests/<harness>.cpp` per logic change,
  `patches/h<N>_*.patch`, `candidates/h<N>_*.md` (speed_pack), skill rows (profiler, large pages, lessons) in
  `skills/forge-speed-lock-path/SKILL.md` + user-scope mirror.
- Updated every push: `opus_speed/STATUS.md`, `FINAL_REPORT.md` (new section 9 "Hunt vs trial_w6"), `RESUME.md`.
- Engine trees `F:\ospd\src\h<N>_*` (from trial_w6.patch + own patch); live lock and every earlier tree untouched.

## Verification (end to end, per idea)
Identity: all-0 build = FD3A5190, six-ON + new-OFF = 4181A589 (sha256). Proof: speed_pack pc1 = pc2 + bitexact L1-L4
vs trial_w6 (net on AND off pins 312866/862329/3024920/12389307/34048354 and 375354/907205/2448617/13573040/24506465,
perft 4865609 / 193690690), harness 0 mismatches + mutant caught; full 12k for a WIN. Timing: session A/A sane, ABBA
vs trial_w6 judged by the rules above, `abba_recheck.py` agrees. Final: records + push; one line with the new tip,
files changed, ideas tried and which were bit-exact wall WINs.
