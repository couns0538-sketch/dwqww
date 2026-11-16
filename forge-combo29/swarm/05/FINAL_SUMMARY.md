# SEAT 05 — final summary (area 5: principal variations and scores)

Branch `for-fable-and-opus/swarm-05`, folder `forge-combo29/swarm/05/`.
Base commit 6b98f217. Build: plain Release, GCC 13.3.0, sha256 `e06310ec...a83`, **honesty 4/4**
(bench 11 = 312866, 13 = 862329, 16 = 3024920, perft 5 = 4865609), re-verified after seat 19's 19-F12 warning.

## The one thing worth reading
**A `mate N` score is sometimes reported with a PV far too short to deliver that mate, and the score itself is
often not yet stable.** Found on G/192 in job1, then reproduced on a completely fresh 200-position random set in
job1b (R/120), where it self-corrects with depth exactly the same way. Two independent instances, two different
position sets. That is S-F1 + S-F9.

## Findings
| id | one line |
|---|---|
| S-F1 | depth 12 on G/192: `mate -12` but an 18-ply PV that does not end in mate; deeper searches give -9, -6, -4, so the depth-12 score is wrong, and mate in 6 is provable by hand |
| S-F2 | 553/553 last-PV lines replay legally; 9 of 10 mate PVs exactly match 2N-1 |
| S-F3 | the fifty-move draw fires ~9 plies early: K+R vs K scores cp 472 up to halfmove 75, cp 314 at 90, **cp 0 from 91** (same for K+Q), and H=91 costs 126.7 M nodes to decide |
| S-F4 | 20 K+Q/K+R boards are +470…+1259 cp at counter 0 but cp 0 in all 20 at counter 98 and 99 |
| S-F5 | repetition detection is CORRECT: 20 genuine 3-folds answer cp 0 / 0 nodes, and the same board as a plain FEN answers `mate -11` |
| S-F6 | K v K / KN v K / KB v K are cp 0 with 0 nodes 20/20; KNN v K is non-zero 20/20 (correct — mate exists there) |
| S-F7 | at a terminal root `go nodes 100` and `go movetime 50` iterate to depth 64 instead of stopping at the limit |
| S-F8 | `go infinite` at a terminal root produced no bestmove within 25 s (one observation, needs repeating) |
| S-F9 | the S-F1 truncation reproduces on the fresh R set (R/120: `mate -13`, 14-ply PV, self-corrects -10 at d16, -8 at d18) |
| S-F10 | R-set baseline: 200/200 bestmove+PV, 0 illegal PV moves, 18 mate scores (17 exact), 12,230,484 nodes, median 46,976 |
| S-F11 | the S-F3 cliff is not a fixed counter: the boundary tracks counter+depth at 100–101, which reconciles my "9 plies early" with seat 25's "1 ply early" — same rule, different mate distances |
| S-F12 | `DeadMaterial true` is a pure material key for exactly two knights: 8/8 KNNk positions across eight placements go cp 216..326 -> cp 0, and 0/3 KNNNk are touched (three knights can mate) |
| S-F13 | that boundary pattern holds across FOUR bare endgames (K+R, K+Q, K+B+B, K+N+N vs K): counter+depth = 100-101 at d6/d8/d10/d12, the counter just below scoring +33..+390 cp |
| S-F14 | **CORRECTION of my own S-F11/S-F13**: the boundary is POSITION-dependent, not one law. Seat 25's 21-piece middlegame is flat at 99; the same board pawnless is flat at 100. My "counter+depth" claim is scoped to bare endgames only |
| S-F15 | ONE black pawn flips it: bare K+R tracks depth (95/93/91/89), the same board with a pawn is flat at 98 — though stripping pawns from a middlegame does NOT restore tracking, so I claim no mechanism |

## Checks of other seats
| id | verdict |
|---|---|
| S-C1 | CONFIRMS seat 06's S-F9 (both mirror pairs exact) **and goes beyond it**: both mate-side PVs are themselves truncated |
| S-C2 | CONFIRMS seat 19's 19-F12 (piped quit ⇒ `bestmove a2a3`, 0 info lines) and shows my job1 numbers are unaffected — they reproduce the brief's node sums exactly |
| S-C3 | honesty re-verified after that audit: 4/4, so HONESTY.txt stands |
| S-C4 | after seat 19's parse warning I found and fixed a real false-verdict path in my own `job1/mate_check.py` (a missing parse fell through to MISMATCH, i.e. an invented REFUTES); proven by control, published numbers unchanged |
| S-C5 | CONFIRMS seat 15's 15-F3 on my own 20 KNN v K positions (20/20 non-zero off, 20/20 cp 0 on) + the correctness control: DeadMaterial true leaves K+Q/K+R wins at cp 472..1162 |
| S-C6 | CONFIRMS seat 15's 15-F4 (dead-draw roots emit an EMPTY pv with 0 nodes, one line per depth) and audits my own exposure: 600/600 empty pv lines in my job2 draw sets, but my cp 0 conclusions stand |
| S-C7 | CONFIRMS seat 25's S-F4 on their board (break at clock 99, 341 nodes) **and corrects my own S-F11** — their boundary is flat at 99, mine only tracked depth on bare endgames; also: no option (EvalRule50Damp, UseNNUE, Hash, Threads) or depth 1..20 escapes the clock-99 zero, while clock 0 searches normally (-164 cp, 19,621 nodes) |
| S-C8 | CONFIRMS seat 15's 15-F5 on 20 fresh seed-521 roots: 60/60 runs give mate 0 / cp 0 with 0 nodes and 0000, and the depth ladder runs to 64 for `go nodes`/`go movetime` vs 5 for `go depth 5` |

## Jobs
- `job1/` — PV legality + mate distances on O(200)+G(353) at depth 12. REPORT_job1.md
- `job2/` — draw scores: K v K / KN v K / KB v K / KNN v K, threefold, fifty-move. REPORT_job2.md
- `job3/` — checkmated/stalemated roots under ASan+UBSan, both sanitizer proofs. REPORT_job3.md
- `job1b/` — job 1 again, seed 511, fresh R set. REPORT_job1b.md
- `audit19f12/` — harness and parser integrity audits (19-F12 + the NaN/empty-parse warning). RESULT.md
- `check_s06f9/` — the check of seat 06's S-F9. RESULT.md

## Where I was wrong, plainly
- Job1b predictions #3 (expected 0–6 mate scores, got 18) and #6 (median 60k–130k, got 46,976) failed; my generator
  made a more tactical and more correlated set than I assumed. The engine conclusions did not depend on them.
- My first two distance-to-mate checkers were both buggy (a lazy `legal_moves` generator consumed while the board
  was mutated; an opponent's mating reply treated as an escape). The control caught the first; the second I caught
  by cross-checking two implementations. Both are documented in job1.
- My first hand-typed set of checkmated/stalemated roots was only 4/10 and 6/10 correct; I generated and asserted
  replacements.
- `resolve_192.py` never finished and its output file is empty — it proves nothing and I say so in REPORT_job1.md.
- In `check_15f3/deadmaterial_scope.py` I mislabelled several FENs (a "two knights" row that contained a black
  knight, a "three knights" row that was KNNk) and drew two claims from them; `raw/material_check.txt` disproved
  both and they are WITHDRAWN in `check_15f3/raw/scope_summary.txt` and RESULT.md. The controlled replacement
  (`knn_same_material.py`) asserts each FEN's material and gives the clean result.
- The first `cliff_vs_depth.py` scanned downward from 99 and therefore reported 99 at every depth; the corrected
  upward scan is what produced S-F11/S-F13.
- `honesty_safe.py` first waited for a `bestmove` that `bench` never prints and hung; it now waits for the
  `readyok` queued behind the command.
- I claimed (S-F11) that my "9 plies early" and seat 25's "1 ply early" were "the same rule". Testing their board
  showed their boundary is flat at 99 while mine only tracked depth on bare endgames; I scoped S-F11/S-F13 and wrote
  S-F14 as the correction. I then proposed a "reach the counter" mechanism and TESTED it — stripping all 12 pawns
  left the boundary flat at 100, so the hypothesis was withdrawn.
- One fifty-move test ran on the wrong FEN: `8/8/8/8/8/8/8/K1N4k` is K+N (a dead draw), not K+N+N, so every clock
  scored cp 0 and the scan measured nothing. Discarded, material asserted, re-run; both runs are recorded in
  `job2/out/cliff_vs_depth_KNN.txt`.

## Not done / open
- No cause is claimed for S-F1/S-F9: I did not read `search.cpp` (area 7's job).
- I could not establish whether the mate *scores* are the correct distance, only whether the PV matches the score.
- S-F3's cause (which constant produces the 91 boundary) is not established, and Stockfish also returns 0 early
  there, so I do not claim engine-specific guilt.
