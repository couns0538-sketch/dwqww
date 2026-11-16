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

## Checks of other seats
| id | verdict |
|---|---|
| S-C1 | CONFIRMS seat 06's S-F9 (both mirror pairs exact) **and goes beyond it**: both mate-side PVs are themselves truncated |
| S-C2 | CONFIRMS seat 19's 19-F12 (piped quit ⇒ `bestmove a2a3`, 0 info lines) and shows my job1 numbers are unaffected — they reproduce the brief's node sums exactly |
| S-C3 | honesty re-verified after that audit: 4/4, so HONESTY.txt stands |
| S-C4 | after seat 19's parse warning I found and fixed a real false-verdict path in my own `job1/mate_check.py` (a missing parse fell through to MISMATCH, i.e. an invented REFUTES); proven by control, published numbers unchanged |

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

## Not done / open
- No cause is claimed for S-F1/S-F9: I did not read `search.cpp` (area 7's job).
- I could not establish whether the mate *scores* are the correct distance, only whether the PV matches the score.
- S-F3's cause (which constant produces the 91 boundary) is not established, and Stockfish also returns 0 early
  there, so I do not claim engine-specific guilt.
