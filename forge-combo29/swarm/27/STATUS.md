branch: for-fable-and-opus/swarm-27
folder: forge-combo29/swarm/27/
area: 7 (READING THE CODE for faults)
seed: 2701

# FINAL STATE — all findings, raw files and patches are on this branch

## THE TWO THINGS A MERGER NEEDS (both at the top of PATCHES.md)
1. **Composition order and paths**: seat 12's `two_doors_mate.patch.txt` FIRST with `-p1` from the directory
   that CONTAINS `forge-combo29/`; then my `job1/drawn_root_reporting.patch.txt` with `-p1` from INSIDE
   `forge-combo29/`. The two patch files have different path roots — that is the trap. **CORRECTED by seat 12:
   ORDER DOES NOT MATTER** — both orders give a byte-identical `src/search.cpp`, sha256 `24912a43...` (I
   reproduced it both ways after their correction). What matters is the `-p` level per patch, and that you check
   every exit code. My earlier "reverse order fails" was the wrong `-p` level mistaken for an order dependency.
   Combined tree builds to sha256 `80b5e535fad4ea12305868198c4c4cc4994b9caec75113f617a59c95b5573507`.
2. **The assertion**: `bash forge-combo29/swarm/27/assert_composition.sh <your-forge>` searches
   `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60` (clock 100, White has Ra8#). PASS (exit 0) = bestmove `a1a8` and a
   `score mate 1` line. Verified three ways: base FAIL (`f2f3`), seat 27 alone FAIL (`f2f3`, 1 info line),
   seat 12 alone and seat 12+mine PASS (`a1a8`).

## Honesty gate (every build I used)
Base `e06310ec`, three-patch set `d3f1a40f` (rebuilt twice, identical sha256):
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four PASS, base and patched.
`HONESTY.txt` is generated from raw files by `make_honesty_txt.sh`.

## FINDINGS (see FINDINGS.md for the one-line form)
New: S-F1 drawn-root depth ladder · S-F2 `go nodes` under one iteration answers a2a3 silently ·
S-F3 hashfull is a 1000-cluster sample · S-F4 `Clear Hash` keeps the histories (9/20 bestmoves, 19/20
scores; ten-second repro S-F4a: cp -130/-130/**-100**) · S-F5 search order changes the answer
(14/40 bestmoves) · S-F7 the option surface is clean (81 options, 291 cases) · S-F8/S-F8a `searchmoves`
changes the SCORE (cp 23 vs cp 30) — **OPEN**, two causes pinned, one not · S-F9 a mid-search `setoption`
truncates the search · S-F10 `eval` is pure (8/8, total==clamp(hce+nnue) 26/26) · S-F11 my drawn-root patch
composes with seat 12's two-doors patch (their -p2 first, then mine -p1).
Confirmations: S-C1 11-F1 · S-C3 01-F5/01-F8.
Withdrawn: S-F6 (duplicate of 01-F5/01-F8 — I had not read their file when I wrote it).

## PATCHES — `patch -p1` from `forge-combo29/`, no fuzz, verified alone AND together (PATCHES.md)
1. `job1/drawn_root_reporting.patch.txt` — one info line at a drawn root instead of the depth ladder
2. `job2/clear_hash.patch.txt` — `Clear Hash` also clears the histories (makes a search reproducible)
3. `job3/halfmove_clock.patch.txt` — refuses a FEN clock above 100 (seat 01's finding; my patch)
   `job5/searchmoves_iir.PARTIAL.patch.txt` is PARTIAL ONLY — do not present it as a fix.

## INTEGRITY (both of seat 19's broadcasts applied to my own work)
- 19-F12: my pipelined runner hit it. `job1/HARNESS_AUDIT.md` lists every measurement and its status. The
  600-FEN sanitizer run was REDONE paced: 600 bestmoves, 1516 info lines, 0 sanitizer lines, 0 crashes.
  S-F2 re-verified paced and stands. Bench/perft are synchronous in the UCI loop, so honesty was never at risk.
- Parser integrity: every script raises on a missing line; `job3/pyperft.py` replaced a bare `except` that had
  turned python-chess's missing `Board.perft` into 12 fake "differences"; `job3/f2_harness_can_fail.py` proves
  the harness reports a difference, a missing line and a wrong expectation. `job4/FALSE_ALARMS.md` records two
  more of my false alarms (shell quoting, not engine faults).

## NOT DONE / OPEN
- S-F8's third cause (unknown).
- The move generator's attack tables and the time manager as source-reading jobs.
- TSan (area 4 owns it).

## WARM-TABLE RULE CHECKED (seat 10: Clear Hash is NOT a cold baseline)
`job7/HARNESS_AUDIT_2.md` audits every committed script by reading its process handling. **One real error
found**: `job4/f1_options.py` ran the Threads 1 vs 2 comparison in ONE process, so Threads 2 = 30,356 nodes was
WARM. My first correction (14,883) was ALSO wrong: a parallel search has no single cold value. Measured 5 fresh
processes per setting: Threads 1 = 13,102 / d2d4 in **5 of 5**; Threads 2 = 18,993 / 25,249 / 27,138 / 27,508 /
34,983 with two different bestmoves. **Never used to argue scaling** (the row only showed the option takes
effect). Harness rule: node-count pins are only meaningful at Threads 1; Threads > 1 needs a range.
**REPOSITORY-WIDE: every pinned node total (bench 11/13/16, perft 5, and the brief's known sums O d12
9,500,069 / G d12 18,466,239 / O d14 21,812,100 / G d14 43,345,893) is a Threads 1 statement and must be
compared ONLY against Threads 1 runs.** `bench` and perft are immune by construction: bench builds its own
single-threaded `Searcher bench_searcher(16)` (uci.cpp:612) and ignores `Threads` — verified, bench 13 = 862,329
at both Threads 1 and Threads 8. I checked my own tables with git grep: none ever put a Threads > 1 number
against a known sum, and honesty.sh sets no Threads line, so all my honesty numbers are Threads 1. Everything else is a fresh
process per search; the S-F8 chain (job7/f1, f2, f3) is cold-measured and re-ran identical after the rule came
out. S-F4 is CORROBORATED by the rule: seat 10's third value (40,569) for Clear Hash is exactly what S-F4 predicts.

## S-F8 IS TWO DEFECTS (seat 10's split) — my partial patch covers A only
Seat 10 (branch `for-fable-and-opus/swarm-10`) settled it: **10-F17** defect A = the restricted root computes a
wrong score with an EMPTY table (Clear Hash changes no node, 21,640 both ways); **10-F15** defect B = a restricted
search pollutes the shared table for a later unrestricted search. **10-F14** = restricting to ALL 20 legal moves
still differs (cp 23/d2d4 vs cp 30/e2e4). **10-F18** = minimal repro with `searchmoves e2e4`.
So `job5/searchmoves_iir.PARTIAL.patch.txt` addresses A only and does NOT touch B. Full write-up:
REPORT_job5.md §"CURRENT STATE OF S-F8" and job7/RESULT.md.

### Mechanism of the NO-OP restriction, named (job7/f3, committed script)
| build | unrestricted | all-20 restricted |
|---|---|---|
| base | cp 30 / 56720 / e2e4 | cp 23 / 21640 / d2d4 |
| IIR stopped at a restricted root | cp 30 / 56720 / e2e4 | cp 24 / 70142 / d2d4 |
| IIR stopped AND root TT store restored | cp 30 / 56720 / e2e4 | **cp 30 / 56720 / e2e4 — EQUALS** |
So for a restriction excluding nothing, the error is fully the extra reduced ply (IIR, no hash move) plus the
skipped root store; that also explains 10-F12's 21,640 -> 17,847 on a repeat. **Aspiration is RULED OUT**
(AspirationDelta 200 does not shrink the gap). **But the general case stays open** (`d2d4 e2e4` gives cp 26 vs
cp 30 on that same build), so S-F8 remains OPEN and I did not guess the remaining cause.

### CAUTION on 10-F18's depth sign flip (S-F8c)
At depths 8 and 10 the unrestricted search plays d2d4 and the restricted one plays e2e4, so those "gaps"
compare two DIFFERENT MOVES and are not errors. The clean like-for-like case is all-20 (10-F14).

## S-F8 earlier bound (IirDepth sweep) — superseded by the table above, kept for the record
With `IirDepth 20` (IIR cannot fire at depth 12) the restricted search still reports cp 26 vs cp 34
unrestricted: **8 cp gap with IIR provably inactive**, so IIR is not the whole cause. At `IirDepth 2` (S14) the
restricted score is 4 cp HIGHER and the plain search plays d2d4 while both restricted variants play e2e4 — the
sign is unstable, which is worse for move-quality reasoning than a consistent bias. Third cause unidentified;
stated, not guessed. Raw: `job7/f1/`. Detail: store `internal/swarm/seat-27-sf8-bound.md`.

## CORRECTION to my own job-5 report
The S-F8 table in REPORT_job5.md was labelled "S14" and was measured with **default tuning**. Numbers stand
(re-verified: cp 30 / cp 23), label fixed in both REPORT_job5.md and job5/f3/README.txt. The S14 numbers are the
IirDepth-2 row in job7 (cp 24 vs cp 28 — smaller and opposite sign). This mislabel is exactly what hid the sign
flip the first time.

Next command:
  git -C /agent/repos/dwqww show for-fable-and-opus/swarm-27:forge-combo29/swarm/27/PATCHES.md | head -60

## STALE-CLAIM SWEEP: DONE OVER THE WHOLE FOLDER (2026-11-16T22:11Z)
I grepped every file in `forge-combo29/swarm/27/` for the wrong patch instruction rather than trusting memory:
`git grep -n -B2 -A2 "1 out of 1 hunk ignored"` and `git grep` for "one order only", "Reverse order fails",
"seat 12 first, always". **Result: the sweep found one file the earlier pass missed** — `job6/INTEGRATION_s12.md`
still said seat 12's patch takes "`-p2` from the repository root", which is wrong (it is `-p1` from the root, or
`-p2` from inside `forge-combo29/`; measured again on a clean archive: `-p2` from the root gives "1 out of 1 hunk
ignored"). Both of its blocks are fixed — the "What I ran" comment is annotated as the original mistake rather
than silently rewritten, because that file is the record of a mistake.

What remains in the folder mentioning the old claim are only the deliberate "my earlier statement was wrong"
sentences: FINDINGS S-F11 (tagged CORRECTED-by-seat-12), PATCHES.md's correction section, this STATUS block, and
the INTEGRATION note. `PATCHES.md` line 16 was checked and was already correct.

`verify_patch_order.sh` is now named in the first three lines of PATCHES.md, and the script was hardened after
the sweep: it resolves its arguments to absolute paths before any `cd`, and it fails (exit 1) if any patch did
not apply. The first version silently printed PASS while seat 12's patch had skipped, because relative paths
broke after the `cd` and its exit codes were never checked — the exact mistake the script exists to warn about.
Four self-tests are recorded in its header and in `job6/order_verify/` (positive run, negative run).

## HARNESS RULE worth carrying past this seat: read exit codes without a pipeline
`cmd | tail`, `| head`, `| grep` all report the EXIT CODE OF THE LAST STAGE, not of `cmd`. Twice in this
seat's work a pipeline masked the thing being tested:
  - my first negative test of `verify_patch_order.sh` printed "SCRIPT RC=0" and I nearly accepted it; the 0
    was `tail`'s. Run without the pipe it was genuinely 1.
  - the same script printed PASS while seat 12's patch had silently skipped, because the patch calls were
    `patch ... > /dev/null 2>&1` followed by an echo that captured nothing.
What to do instead: capture the code on its own line (`cmd > log 2>&1; rc=$?`) or use `set -o pipefail`, and
when a check exists to detect a failure, write a test that MAKES it fail and confirm the nonzero code.
A check that has only ever passed has not been tested.

## 2026-11-16T22:18Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18Z
Seat 27 kept (no new seat taken). Branch `for-fable-and-opus/swarm-27`.
Order of work: (1) read every unread `FABLE_TO_swarm_N.md` from the lowest N up; (2) build the owner's PC
engine from file 5 as it says, in a SEPARATE copy with `-DFORGE_MATE_ALPHA_GUARD=1`, and check its known bench
numbers; (3) THE CYCLE with BOTH builds, re-running my own finds on the PC build under the settings PC20 and
naming build + settings in every finding line. Push STATUS at least every 25 minutes, mid-job if needed.
Earlier rules all stand: my branch and folder only, no PR, no engine source in the repository, text only.

## 2026-11-16T22:26Z PC BUILD BUILT AND PINS VERIFIED; Threads-1 rule adopted
Read files 3, 4, 5 of FABLE_TO_swarm (1 and 2 were already read). File 5 = the owner's PC engine (r15) as a
patch against 6b98f217. Patch sha256 `d6bd72c5...` matches the stated prefix; `patch -p1` applied to a separate
copy (`/tmp/pcbuild`), 11 files, no fuzz; built with `-DFORGE_MATE_ALPHA_GUARD=1` as instructed.
exe `/agent/repos/base/build-pc/forge` sha256 `068f0927...`, 92 advertised options, MateAlphaGuard present.
**All seven file-5 pins match exactly**, fresh process per line, Threads 1, 0 bad option lines:
  none: 312866 / 862329 / 3024920 / perft 4865609
  S14 : 242796 / 656517
  PC20: 278024 / 587276
Detail: `pc/PC_BUILD.md`, raw in `pc/pins/`, regenerated by `pc/pc_pins.sh`.
Also from file 3: my S-F1 (drawn root) is REPAIRED on the PC (`FORGE_FIX_ROOT_DRAWN`), so that patch is not
needed there — recorded in the finding line.
**THREADS-1 RULE adopted** (coordinator): every score I report is Threads 1 unless the job is about threading.
Audited my entire record: everything I ever reported was Threads 1; the only Threads>1 runs are already
labelled non-deterministic in job4/f2_threads and the withdrawn REPORT_job4 row. Nothing of mine needs a
provisional caveat. Seat 04's Threads 4 five-run spread (+2576 / mate 13 / mate 18 / mate 16) is the same
phenomenon as my S-F7a, now with scores.
From now on every finding line names build + settings + Threads 1.

## 2026-11-16T22:27Z cycle 1 done on BOTH builds
Re-ran my own findings on PC r15 under PC20 (Threads 1) against the base build under S14, same harness:
  S-F1 drawn root        **REPAIRED on PC** (threefold root now searches: cp 23 / 13,424 nodes; clock-100 mate
                         returns mate 1 / a1a8 / 210 nodes; base: 0 nodes, a2a3 / f2f3). My patch not needed there.
  S-F2 `go nodes <26`    **SURVIVES on PC**: nodes 20 -> a2a3, 0 info lines; nodes 26 -> d2d4 with 26 nodes.
  S-F3 hashfull sample   **SURVIVES on PC**: 15 at Hash 16 vs 0 at Hash 1024, same 28,565-node search.
  S-F4 Clear Hash warm   **SURVIVES on PC**: cp -143 / -113 / -108 and 33,643 / 28,568 / 21,580 nodes.
  S-F9 mid-search setopt **SURVIVES on PC**: 20 info lines alone, 16 with a setoption 100 ms in.
  S-F8 all-20 restriction **SURVIVES on PC and reproduces exactly**: cp 29 / 21,410 vs cp 25 / 21,600,
                         identical in 3 of 3 fresh processes each. S-F8 stays OPEN on both builds.
New check: **S-C6 CONFIRMS 07-F1 on the PC build** (nothing else has checked it there) with a control through
the same harness (legal restriction: 344 nodes, real pv).
Next: continue the cycle — look for other seats' unconfirmed finds relevant to area 7 and check them on the PC
build; keep every score at Threads 1.
Next command:
  bash forge-combo29/swarm/27/pc/check_07f1_pc.sh /agent/repos/base/build-pc/forge PC20

## 2026-11-16T22:31Z cycle 2: two cross-seat checks on the PC build
S-C6 CONFIRMS 07-F1 on the PC build (first seat to check it there): `searchmoves` naming no legal root move
gives `score cp 0 nodes 0` with empty pv and `bestmove 0000`; control through the SAME harness and PC20 block
gives 344 nodes and a real pv. Not repaired by the PC build.
S-C7 CONFIRMS 20-F11 on the PC build: (a) `go nodes 0/1` answers the first legal move with 0 info lines 6/6,
(b) `stop` at 0 ms the same 3/3 with the 1 ms control searching 971/497/930 nodes, (c) `quit` with no delay
the same 3/3.
**Two harness errors of mine, both found and fixed in this cycle:**
  1. my S-F11 re-run script guessed the "first legal move" constants (e2e4/e1g1/b5b6) instead of measuring
     them; `go perft 1` shows they are a2a3/a2a3/e2e3, so I fixed the harness, not the engine;
  2. I first recorded 20-F11 (c) as "partially refuted" because my quit arrived 50 ms in and the search had
     already published 12-14 info lines. Re-tested at 0 ms: the defect is there, their finding was right and
     my "refutation" was my own harness being slow. Corrected in FINDINGS rather than left standing.
Next: continue checking other seats' unconfirmed finds on the PC build; area 7 jobs still open are the move
generator and the time manager as source-reading jobs.

## 2026-11-16T22:33Z cycle 3: 30-F9 checked on both builds
S-C8 CONFIRMS 30-F9 with a correction. One quiet middlegame, only the half-move counter changed, `go depth 10`,
fresh process per row, Threads 1:
  PC r15 / PC20 : peak 177,829 nodes at counter **90** (84x the counter-99 figure of 2,111)
  base / S14    : peak 227,597 nodes at counter **92** (108x the counter-99 figure of 2,101), and counter 100
                  short-circuits to **0 nodes** where the PC build searches 2,111
So the horizon spike is real on both builds, its peak sits at a different counter value per build, and the
clock-100 row is a direct sighting of the PC's `FORGE_FIX_ROOT_DRAWN` repair in the cost curve.
My first attempt used a position with mate-in-one available, so every clock returned mate 1 / 210 nodes and the
sweep tested nothing — caught by reading the numbers instead of trusting that it ran; template replaced.

## 2026-11-16T22:36Z the two paragraphs the coordinator asked for
**Fifty-move band merged with seat 08's 08-F22** (S-C8 rewritten): three positions, three peaks - PC r15/PC20 at
counter **90** (177,829 nodes, cp 35), base/S14 at **92** (227,597, cp 22), seat 08's won K+R vs K at **91**
(7,251,835). Each peak sits at its own value-crossing, so it is a boundary effect, not a fixed cost; the cost is
a SPIKE (then cheaper than normal at 94-98), not a band. **Verdict: the spike is the normal cost of not
short-circuiting** - at my peak the engine scores cp 35 / cp 22, i.e. real analysis of a WINNING position, not
draw-proving. **Two neighbours are genuine defects:** the base build's counter-100 row returns **0 nodes**
(adjudicates on sight - S-F1, repaired on PC which searches 2,111 and gets cp 0 honestly), and seat 08's chronic
SCORE band (exactly cp 0 from 91 to 99 on a won board) is correctness with game consequences, a different thing
from the node spike.
**`go nodes` below one iteration given the full treatment** (S-P2 rewritten): what such a budget should do
(mark the reply unsearched, or wait for one iteration, or return the previous COMPLETED move - never a move with
no score) and what a dataset recorded (a2a3 = the generator's first entry, with a null score that biases a
trainer's filter, or a default 0 that teaches "equal, play a2a3"). The 26-node threshold is not guessable, so
such rows cannot be repaired by inspection. I did NOT measure what fraction of any dataset falls in that band.
Both paragraphs also in the store note `internal/swarm/seat-27-fifty-move-band-and-nodes.md`.

## 2026-11-16T22:38Z cycle 4: 29-F3 confirmed on the PC build by a different method
S-C9: fitting reported `time` against reported `nodes` over depths 10-14 (PC r15/PC20, Threads 1, fresh process
per bench, two rounds) gives intercepts **+14.84 ms** and **+18.53 ms** with r2 0.994 / 0.996, slope 585-586
ms per M-node. A timer containing only search work fits through the origin; this one does not, and the intercept
is the fixed cost by construction. Seat 29 found ~14 ms by timing; I found ~16.7 ms by the shape of the curve -
two methods, same conclusion. Consequence: the fixed part is 3-4 % of a bench 13 report, under 2 % of bench 16,
so shallow-bench nps is understated. **Node totals are unaffected**, which is why the pins stay comparable.

## 2026-11-16T22:44Z the go-nodes band counted against the repository (S-P7)
Asked to measure rather than warn, so I searched the repository for the owner's training/tuning data.
**There is none here**, and I say that plainly: `*.jsonl` = 1 file (my own mutation list), `*.csv` = 0, the only
"train" path is `windows_build/frozen_train_cmds.txt` (bench commands, 0 position lines, 0 info-depth lines).
So the fraction of DATASET rows in the band cannot be counted from this repository; the owner's data is on his PC.
**What I could count, over all 12,058 tracked text files: 709,727 `go nodes N` occurrences, 61 below the 26-node
threshold = 0.0086 %.** Distribution 0:32, 1:17, 10:4, 20:5, 26:16, then 2,000:138,776 / 20,000:365,901 /
50,000:204,857. Of the 61, **37 are in `swarm/` probe scripts (mine included) and 5 are deliberate unit tests**
that assert the small-budget behaviour; **not one is training data**. Every budget the repo commits is 77x-1,900x
above the threshold, so nothing committed here is at risk.
Re-runnable: `bash forge-combo29/swarm/27/census_go_nodes.sh`; raw output `pc/rerun/census_go_nodes.txt`.
Store note updated with an addendum: `internal/swarm/seat-27-fifty-move-band-and-nodes.md`.
Next: continue confirmations.

## 2026-11-16T22:48Z cycle 5: 16-F6 confirmed on the PC build, with the control it needed
S-C10: PC r15, Threads 1, Book Depth 100 so the book can fire at all.
  analysis limits, OwnBook true vs false -> bit-identical and 0 book lines: `go depth 10` d2d4/13,102 both ways,
  `go nodes 20000` d2d4/13,102 both ways, `go infinite`+3 s+stop d2d4/30,606,312 both ways.
  clocked limits -> the book DOES fire: `go movetime 300` 1 book line (c2c4) vs 0 (e2e4); `go wtime 10000` 1 book
  line (e2e4) vs 0 (d2d4).
That second half is the control seat 16's own check could not show: a book that never fires looks exactly like a
book correctly excluded from analysis searches. With it, their claim holds on the PC build.

## 2026-11-16T22:56Z File 6 read: TWO of my verdicts changed, new area started
**S-V1 (verdict change).** File 6's rule: a cp 0 at a high counter is a defect ONLY if a forced mate exists with
`2N-1 <= 100-counter` AND the real-counter search still scores cp 0. Measured on the PC build (PC20, Threads 1,
`go depth 20`, fresh process per row): **seat 08's K+R vs K board `1K6/8/8/3R4/8/8/8/k7 w` is `mate 8` at counter
0, so 2N-1 = 15**, while at counter 91 only `100-91 = 9` half-moves remain -> 15 <= 9 is FALSE, the mate cannot
land before the match program ends the game, and cp 0 is CORRECT. My quiet middlegame does not even score cp 0 at
high counters (90 -> cp 17, 91 -> cp 17, 99 -> cp 21). **So the "band" I recorded in S-C8 is NOT a defect on
either board**, and the "genuine defect" sentence in S-C8 is superseded. The node spike stays a performance note.
**S-V2 (verdict change).** My Threads-2 non-determinism observation is NOT a defect: File 6 confirms shared-table
multi-thread variation is by design, and a real multi-thread defect is only a hang/crash/illegal move/sanitizer
line/out-of-spread score that does not shrink with depth. I saw none of those. S-F7a stands only as a HARNESS rule
(pin at Threads 1, use a range above it).
**S-N1 (new area, softnodes).** PC r15/PC20/Threads 1, 4 real-game-family positions, N = 2,000 and 20,000, 3
fresh processes per cell: **deterministic 8 of 8 cells** (bestmove, score and final node count identical across
all three runs), **finished depth 8 of 8** (every reply carried a pv), and **overshoot 1.02x-1.95x N, median 1.20x**.
So the self-play contract holds exactly and its labels are reproducible.
**S-P8.** The census script is now generic (git mode inside a repo, `find` outside) and self-tested on a synthetic
300-row directory where it correctly found 153 band rows — which also caught a field-order bug in my own regex.

## 2026-11-16T23:16Z still working — next: the negative-sum clock and the softnodes boundary
Not idle: the last push was the File-6 verdict pass at 22:56Z. Taking the coordinator's first suggestion next,
the 6s+0.06 clock with a median search near 105 ms against a 60 ms increment, on the PC build under PC20 at
Threads 1, then the `go nodes` boundary on real-game positions. STATUS cadence stays at 25 minutes.

## 2026-11-16T23:24Z S-C11: the negative-sum clock, direction right, magnitude and forfeit ply refuted
Tested seat 15's 15-F35 (no prior confirmation) with my own harness: self-play from startpos on the PC build,
PC20, **Threads 1**, Hash 16, a real per-side clock decremented by measured wall time and incremented 60 ms per
move, forfeit at zero, 3 games to a 200-ply cap (600 moves).
  **6 s + 0.06 (owner's control): median 78.6 ms/move vs the 60 ms increment = 18.6 ms net drain**, p99 557 ms,
  max 920 ms. Zero point at the median: about **322 plies**, not their ~165. All three games reached the 200-ply
  cap alive but thin (418/158, 116/117, 551/465 ms left) - their "narrow margin", without their forfeit.
  Their 105 ms median / 73 ms drain / ~82 moves is about 4x my measured drain; on this build, at 200 plies,
  nothing forfeits.
  **Control (6 s + 0.5 s): median 419 ms, net -80.6 ms/move (positive sum)**, two of three games ended with
  10-19 s left - so the harness can see a clock that does NOT drain, and the drain above is measured rather than
  inferred. The control also shows the engine really does spend more when the clock is healthy (419 vs 79 ms).
Raw: pc/rerun/check_15f35.json. Next: 19-F46's `go nodes` undershoot table lacks a second confirmation and is on
the owner's path -- checking it next.

## 2026-11-16T23:26Z S-C12: 19-F46/F47 confirmed in structure, two figures corrected
Independent harness (my own), PC r15, PC20, Threads 1, Hash 16, 6 real-game FENs x N in {20000, 50000}, 3 fresh
processes per cell, all deterministic.
  **Structure holds exactly**: hard `go nodes` undershoots, `go softnodes` overshoots, and softnodes is exactly
  one ply deeper in **12 of 12** cells.
  hard nodes/N median **0.728** (0.467-0.993); soft nodes/N median **1.151** (1.037-3.464) - both close to their
  -32 % and +21.9 %.
  **Cliff reproduces in shape**: pos 0 `go depth 12` = 21,812 nodes; `go nodes 21812` -> depth 12 / 21,812;
  `go nodes 21811` -> depth 11 / **9,330** nodes, a 57 % drop for ONE node of budget.
  **Two corrections**: their "bestmove identical in all 18 cells" is not universal - 2 of my 12 differ (pos 3
  N=20000 and pos 5 N=50000); and my cliff uses my own position's count, not their 31,779.
Owner consequence, now measured twice: a match labelled "node 50000" typically spends median 73 % of it and is
one ply shallower than softnodes at the same budget. Next: the deep-mate score boards (base centipawns vs PC mate).

## 2026-11-16T23:45Z reconciliation for seat 15, and a withdrawal of my own
**Reconciliation (no channel to another seat, so it is on my branch and going to you to relay):** my drain is
78.6 ms median from startpos and 81.7 ms from seat 15's own four opening FENs, against their 105 ms. Matching
their positions did NOT close the gap, so position weight is not the explanation. My machine: Intel Xeon, 4 vCPU
2.4 GHz, 15 GB, AVX-512F + BMI2, g++ 13.3, load 0.42-0.64. **The one number that would settle it is their median
NODES per move** - nodes are machine-independent, milliseconds are not. Full note (also in the store as
`internal/swarm/seat-27-reconcile-seat15-clock.md`): `pc/RECONCILE_seat15.md`.
**And I have to withdraw my own S-F12.** I briefly believed the engine swapped the white and black clocks,
published it, then checked: **it does not.** Correct control (book OFF, 3 reps): startpos White `wtime 100 btime
5000` -> 9,653 nodes vs `wtime 100000 btime 5000` -> 13,616,554; startpos Black `btime 100` -> 10,713 vs
`btime 100000` -> 4,163,373. Each side is timed by its OWN clock, as uci.cpp:121-124 says. My "swap" rows had
`OwnBook` left ON on a 2-move opening position, and the book answers instantly and independently of the clock.
`check_clock_swap.txt` now opens with a warning that its conclusion is wrong; S-F12 is WITHDRAWN in FINDINGS.
**One real thing did come out of it:** a game of mine FORFEITED at ply 106 (White spent 200.7 ms holding 3 ms),
which means seat 15's forfeit prediction is right and my earlier "no forfeit at 200 plies" was too strong.

## 2026-11-16T23:54Z S-C11b: the process-policy exchange is DONE
Both policies on the same four start FENs (seat 15's own), 6 s + 0.06, PC20, Threads 1, Hash 16, OwnBook false
hard-coded, PC r15. WARM = one process per game; COLD = a fresh process per move.
  median nodes/move, warm vs cold: start0 190,877 / 245,809 (-22 %), start1 197,987 / 210,961 (-6 %),
  start2 261,829 / 256,991 (+2 %), start3 192,465 / 212,022 (-9 %). median wall 120.8/137.2, 129.1/112.4,
  157.0/132.9, 117.5/122.2 ms.
  **Verdict: table warmth is real but small (median about -9 % nodes), and it does NOT explain my earlier 45 %
  gap.** With both policies on the same positions BOTH of my arms land at 190-262k, i.e. at seat 15's 263,746.
  My original 145,432 came from a different sampling: 4 games to a 200-ply cap (2 of 4 capped), per-game medians
  101,572 / 145,890 / 150,497 / 205,472, where long endgame-heavy games drag the median down.
  **Forfeits reproduced in BOTH policies on start2** (144-178 plies), so the forfeit belongs to that opening at
  this control, not to either process policy - which is the "narrow margin, both true" framing.
Also: Move Overhead is now reported BOTH ways in every clock table (raw and raw-10 ms), so no figure of mine can
be mistaken about the convention again.

## 2026-11-16T23:58Z S-C13: the deep-mate premise does NOT reproduce on verified lone-king boards
Checked the claim "base reports centipawns where the PC reports mate" on boards VERIFIED with python-chess first
(legality + exact plies), PC r15/PC20 and base/S14, Threads 1, Hash 16, OwnBook false hard-coded, depths 8/12/16:
  KR vs lone K (mate in 1): **both builds `mate 1`**, bm h4h8, nodes 170/254/338 on BOTH.
  KQ vs lone K (mate in 1): **both `mate 1`**, bm c7b7, nodes 198/294/390 on both.
  KQ vs lone K (mate in 2 moves / 3 plies): **both `mate 2`**, nodes 570/816/1063 vs 593/853/1111; same score,
  same distance, different first move (base c6c7, PC f4f7), both mating.
  Controls (quiet middlegame, startpos): `cp` at every depth on both builds, never a mate score.
**So there is no cp-vs-mate split on lone-king mates at depths 8-16** - the claim I was asked to check does not
reproduce, and seat 23's 23-F46 already showed the lone-king failures were a DEPTH effect. Depth is stated beside
every row per that caution.
**Two of my own errors caught in this job, both before any result was recorded:** my first hand-written mate set
had two ILLEGAL FENs, and one board I labelled "mate in 3" was 3 PLIES = mate in 2 MOVES, so the engine's
`mate 2` looked wrong when it was right. The script now verifies every board and refuses to run if one fails.

## 2026-11-17T00:00Z method notes written down; S-C13 names what would overturn it
**`METHOD_NOTES.md`** now collects the traps that each cost a near-miss, with the predictable symptom for each:
  - **plies vs moves**: UCI `mate N` counts MOVES, so a board labelled by its PLY count returns `mate (plies+1)/2`
    and looks off by one -- a mate score consistently about half the expectation, always rounded up, is that
    signature and NOT a search defect. Boards store plies; the label is derived, never typed.
  - **verify every position before measuring**: two illegal FENs and one wrong distance in my first mate set; the
    harness now asserts legality and exact distance and REFUSES TO RUN if either fails.
  - **Move Overhead is part of the wall convention**: every clock table prints wall raw AND wall-10 ms.
  - **OwnBook false unconditionally**: leaving it on produced a false "0 info lines" reading AND the withdrawn
    clock-swap claim.
  - **a pipeline hides the exit code**; write a test that makes the check fail.
  - **a repository grep always "finds" data rows**; three passes before the go-nodes census was right.
**S-C13 now names its overturning condition**: a FEN where base reports `cp` and PC reports `mate` at the SAME
depth with Threads 1 / Hash 16 / OwnBook false. I did not have that FEN, so the request stays OPEN rather than
the question being closed -- a refutation on verified boards is the result, and the counter-example is the next
thing to look for.

## 2026-11-17T00:02Z S-C12 extended to the owner's third budget (250,000)
Re-ran the `go nodes` vs `go softnodes` comparison over **all three of the owner's match budgets** {20,000 /
50,000 / 250,000} x 6 real-game FENs = 18 cells, 2 fresh processes each, **18 of 18 deterministic**:
  hard nodes/N **median 0.740** (0.467-0.993); soft nodes/N **median 1.232** (1.037-3.464);
  **soft is exactly one ply deeper in 18 of 18 cells**; same bestmove in **16 of 18** (NOT all 18 as seat 19
  reported - pos 3 N=20000 and pos 5 N=50000 differ, which is a correction to their line).
  At the largest budget: `go nodes 250000` spends 167,506 of it on one board (0.67x) while `go softnodes 250000`
  spends 1.05x-1.25x and is a ply deeper.
  Cliff unchanged: `go depth 12` = 21,812; `go nodes 21812` -> depth 12 / 21,812; `go nodes 21811` -> depth 11 /
  9,330 (57 % drop for one node).
**Owner consequence, now at every budget he uses: a match labelled "nodes N" spends median 74 % of it and lands
one ply shallower than `go softnodes N` on the same position.**

## 2026-11-17T00:05Z S-N2: softnodes combined with a clock - safe, and now measured
The PC's self-play uses `go softnodes 2000`; its strength matches use 6 s + 0.06. Nobody had crossed the two
limits. PC r15/PC20/Threads 1/Hash 16/OwnBook false, 3 positions x 4 commands x 2 fresh processes,
**12 of 12 deterministic**:
  **the smaller limit wins** - `go softnodes 2000` alone gives 2,474/2,303/2,341 nodes; with a 6 s clock added it
  gives the SAME numbers, so the clock never binds;
  **an empty clock overrides a huge budget** - `go softnodes 400000 wtime 10 btime 10` gives 25/76/394 nodes at
  depth 1 in 0.8-1.3 ms, so the 10 ms clock is honoured and the budget is not spent;
  the `info string softnodes nodes K` line matches the last info line whenever a soft budget was given.
**So a self-play loop that sends both is safe and reproducible.** Recorded because "safe" is only a claim once
somebody has crossed the limits and checked - and no defect here.

## 2026-11-17T00:07Z the practical rule for crossing limits, and both bestmove numbers kept
**S-N2 carries the rule now, stated so it can be acted on:** when both a budget and a clock are sent, the
SMALLER limit decides the search and the other is inert. A node budget survives an added clock unchanged
(`softnodes 2000` -> the same 2,474 / 2,303 / 2,341 nodes with or without a 6 s clock), and a clock with nothing
left overrides any budget (`softnodes 400000 wtime 10` -> 25 / 76 / 394 nodes at depth 1). So a self-play loop
that sends both gets exactly the cap it asked for, with the clock as a pure safety net - the configuration to use
when labels must stay reproducible but a slow position still must not overrun.
**S-C12 keeps both numbers side by side**: seat 19's "bestmove identical in all 18 cells" and my measured
**16 of 18** (pos 3 N=20,000 hard c1e3 vs soft e1g1; pos 5 N=50,000 hard g1f3 vs soft f2f4). A reader can see the
claim and the correction in one line rather than only my version.

## 2026-11-16T00:10Z S-C14: seat 24's 348-second warm stall does not exist on the release build
24-F3 reports position 90 of G taking **348,278 ms (T2) / 376,680 ms (T4) inside a long-lived TSan process**. Their
own control already said the cost "comes from accumulated search state, not the position". I measured the build the
owner actually plays: PC r15 `068f0927`, Threads 1, Hash 16, OwnBook false, `go depth 12`:
  **fresh process: 25 ms / 79,980 nodes / f3f8 / cp 2197.**
  **same position six times in ONE process: 26.1, 3.4, 3.0, 1.8, 0.6, 0.5 ms**, nodes 79,980 -> 1,324.
**Warm state makes it 50x FASTER on release, the opposite direction from their stall.** So on the owner's build
there is no warm-state outlier at this position; the 348-second figure exists only under TSan. **This does not
contradict their TSan measurement - it bounds it:** 24-F3 is a property of the instrumented build and must not be
carried to the release engine or a match. Overturning condition recorded: the same 6-repeat warm loop producing a
run more than 10x the first, or any run over a second.

## 2026-11-17T00:12Z S-N3: a training label at the match budgets is bit-reproducible (48/48)
The question a label pipeline actually needs, which I had not answered at the match budgets on a broad sample:
8 real-game FENs x 6 limits {`go nodes` and `go softnodes` at 20,000 / 50,000 / 250,000} = **48 cells, 3 fresh
processes each** -> **(bestmove, score, depth, nodes) identical in every rep of every cell: 48/48, zero
variants.** PC r15/PC20/Threads 1/Hash 16/OwnBook false, `ucinewgame`+`isready` before every `go`.
**So the label is not the fragile part of the pipeline** - the same four fields come back tomorrow. Explicitly
NOT claimed: the label is not thereby *good* (that is S-C12's 74 % undershoot), and none of this holds at
Threads > 1 (not reproducible by design) or for a clock-driven search (seat 25's S-C15: move stable,
score/nodes/depth variable). It holds specifically for budget-limited searches at Threads 1.

## 2026-11-17T00:14Z the budget-label sentence is in the finding; labelling side closed
**S-N3 now carries the sentence to keep: a node-budget label is HONEST ABOUT REPETITION AND MISLEADING ABOUT
EFFORT.** Repetition because 48 of 48 cells return identical four fields on a second and third run; effort because
the same label spends a median 74 % of the budget and reaches a ply less than `go softnodes` at the same number.
Anyone reading "node 50000" in a dataset should read it as "a repeatable search of about 37,000 nodes".
**Labelling side closed** - reproducibility (48/48), cross-mode structure (18/18 one ply deeper), the undershoot
magnitude (median 74 %), and the limit-crossing rule are all measured. Nothing further owed there.
Next: another unconfirmed cross-seat finding on the PC path.

## 2026-11-17T00:16Z S-C15: seat 05's mate-PV truncation confirmed exactly, with a verified control
My own harness, PC r15/PC20/Threads 1/Hash 16/OwnBook false, 2 reps per row, all deterministic, on their
`r2r4/.../4K2R b - - 1 40` board. **Every number matches theirs:**
  `softnodes 2000` cp 3725 / 3,190 nodes / depth 8; `nodes 20000` cp 4056 / 10,515 / depth 10;
  **`nodes 50000` `mate 11` / 44,749 nodes / 18-ply PV where 2N-1 = 21 -> TRUNCATED by 3**;
  `nodes 250000` `mate 7` / 138,869 / 13-ply vs 13 needed -> consistent; `depth 20` `mate 7` / 13-of-13.
  **bestmove `b3c2` in every row**, so their S-F59 holds - the score and PV length are corrupted, the move is not.
**The control that makes it testable**: the same checker on a verified mate-in-1 (S-C13 board) reports `mate 1`,
1 ply, 2N-1 = 1, consistent - and the script ABORTS if the control fails, so "truncated" is not a default.
**This is also a second independent sighting of what my S-C12 measured**: a `go nodes` budget at a match value
stops mid-iteration, and here the consequence is a **score the engine's own PV cannot support** (`mate 11` in
18 plies).

## 2026-11-17T00:18Z the sentence to keep, and one recommendation now stated once
**S-C15 carries the sentence: at a long mate a `go nodes` budget can publish A SCORE THE ENGINE'S OWN PV CANNOT
SUPPORT** (`mate 11` in 18 plies where 2N-1 = 21). The harm is not a shortened line but a claim the engine does
not itself prove - and that is the concrete reason to prefer `go softnodes` on the labelling path, since it lands
on an iteration boundary so the reported score is always one the PV backs up, at the cost of the 2-95 % over-budget
S-N1 measured.
**One ordering note about my own work, recorded because it is the kind of thing that decides whether a number can
be trusted:** my first run of the S-C15 harness crashed on a formatting bug (`plies_needed` is None for a cp
score) - **after** the control had already passed. The control's result was still valid, the crash was in the
target-row printing, and I fixed it and re-ran before recording any target number. So the sequence was: control
verified, target formatting failed, target re-run on the fixed script, only then recorded.

## 2026-11-17T00:20Z S-C16: the base build plays a WRONG move at halfmove 100 - strongest base-vs-PC difference yet
Seat 17's decisive board `r7/1P6/8/8/8/8/8/k1K5 w - - 100 1`, verified with python-chess first: of 11 legal moves
**only `b7a8q` and `b7a8r` mate**; `b7b8q` - the engine's first generated promotion - is **not** mate.
  **base `e06310ec` at hm=100: `b7b8q`, `cp 0 nodes 0` - the WRONG move, from the drawn-root fallback.**
  base at hm=99: `b7a8q`, `mate 1`, 96 nodes.   **PC r15 at hm=100: `b7a8q`, `mate 1`, 96 nodes** (same as its
  own hm=99 row).
So the PC's root repair turns a lost win into the mate. **This matters for my own S-F1:** I recorded the fallback
as a reporting/score defect; on this board it **costs the game**, because the move it plays is not a mate while
the position has one. The luck cases are why this needed care - their earlier `8/P7/...` boards were NOT decisive
because `a7a8q` happens to be first in generation order there, so the base played the right move with a 0-node
score; I verified the mate set before running the engine, so this row cannot be a luck case.

## 2026-11-17T00:22Z S-C16 now states WHY the row is decisive, not just that it was checked
The argument, in the finding and the evidence file: **the mate set was computed with python-chess BEFORE the
engine ran** - all 11 legal moves scanned, only `b7a8q` and `b7a8r` mate, `b7b8q` does not - so the verdict does
not depend on where the generator places the promotions. **The excluded failure mode is precise: a board whose
first generated move happens to be mating cannot distinguish a fallback that picks a good move from one that
picks a lucky one.** Here first-in-order (`b7b8q`) and mating (`b7a8q`) are different moves, which is what makes
it decisive; their earlier `8/P7/...` boards fail exactly that test (`a7a8q` is both), so the base build passes
them while proving nothing.
**Softnodes reason stays stated once**, as asked: it lands on an iteration boundary, so the reported score is
always one the PV backs up, at the cost of the 2-95 % over-budget S-N1 measured.

## 2026-11-17T00:25Z S-C16a: the wrong-move band is every counter >= 100, not a one-off at 100
Same decisive board, base `e06310ec`, Threads 1, Hash 16, OwnBook false, `go depth 8`, fresh process each:
  **hm 95 / 98 / 99 -> `b7a8q`, `mate 1`** (searches, finds it)
  **hm 100 / 101 / 105 -> `b7b8q`, `cp 0`, 0 nodes** (the drawn-root shortcut returns the generator's first move)
So the failure starts exactly at the fifty-move threshold and **persists at every counter above it** - a reader
must not take S-C16 as "a bug at exactly 100". Below 100 the engine searches and mates; at 100 or above it hands
back a move that is not a mate while the position has one.
Also added the luck-case argument to S-C16 and its evidence file: the mate set was computed with python-chess
BEFORE the engine ran, and the excluded failure mode is precise - a board whose first generated move happens to
be mating cannot distinguish a fallback that picks a good move from one that picks a lucky one. Here first-in-order
(`b7b8q`) and mating (`b7a8q`) are different moves.

## 2026-11-17T00:28Z S-C17: 19-F59's structure confirmed, its numbers do NOT reproduce
On `6k1/8/5K2/8/6r1/8/8/8 w - - 0 1`, PC r15/PC20/Threads 1/Hash 16/OwnBook false, fresh process per depth:
  mine: depth 16 -> `f6e5` cp -391 (129,346); depth 20 -> `f6e5` cp -509 (1,915,526); **depth 24 -> `f6f5`
  `mate -25`** (4,224,962).
  theirs: depth 16/20 -> `f6e7` cp -490; depth 24 -> `f6f5` `mate -15`.
**Structure CONFIRMED**: below depth 24 a centipawn-scored king move, at depth 24 the longest-defence move with a
losing MATE score - so "depth limit, not a preference for dying quickly" holds and the position is a calibration
case, not a bug. **Numbers differ in all three fields** (move at 16/20, cp, and the mate distance: mine -25 = 49
plies vs their -15 = 29 plies). I have their sentence, not their raw output, so I cannot say whether the cause is
a setting, a different FEN, or a real difference between runs.
**What I did NOT do: adjust my numbers toward theirs or re-run until they matched.** These are the first runs on
that board, unpicked. Resolving it needs their exact command line and raw `info depth 24` line.

## 2026-11-17T00:30Z my exact inputs for S-C17 are on record, plus an observation about my own row
**FEN:** `6k1/8/5K2/8/6r1/8/8/8 w - - 0 1` (halfmove 0, fullmove 1), sent as ONE-LINE `position fen`, never built
from a move list. **stdin** (committed as `pc/rerun/input_19f59_depth24.uci`): option block, then `ucinewgame` +
`isready`, **then** `position`, `isready`, `go depth 24` - that order matters because seat 10's 10-F11 showed
`ucinewgame` after a `position` silently resets to startpos. **Driver** `paced_session.py` (waits for bestmove each
line). **exe** `068f0927...`. Full write-up with the raw depth-24 line: `pc/rerun/S-C17_inputs.md`.
**And something about my own row that matters: my depth-24 PV is 24 plies while `mate -25` needs 2|N| = 50, so my
own line is TRUNCATED like 05-F58** - all 24 plies legal, final position not check, the line stops long before the
mate it claims. The move `f6f5` is still the longest-defence choice, but **the score is unproven by its own PV** -
the S-C15 phenomenon on a second board, at depth 24 instead of at a node budget.
**Kept as first runs, unpicked.** If seat 19's raw line matches my FEN and settings, the two builds genuinely
differ at depth 24 here - and that is the more interesting outcome, recorded rather than reconciled away.

## 2026-11-17T00:18Z guards everywhere, the anti-pattern is grep-able, and the S-C11 residual is now a range
**The grep-able anti-pattern is in METHOD_NOTES** with the exact command to find it, because grepping my own folder
showed the fix was incomplete: `grep -rn 'infos\[-1\] if infos else' .` found **five files still carrying the
pattern**, two of which I had listed as "pre-existing guard" (the guard raised first, so they were safe, but the
dead line is a trap for the next editor), and **four more with NO guard at all** - including `job2/f2_history_drift.py`
and `job2/f3_tt_vs_histories.py`, behind my published S-F5 and S-F4. All are now guarded, and the only remaining
instance is `check_20f11_pc.py`'s `summarise()`, where 0 info lines is the EXPECTED answer for control rows.
**Checked whether those two findings were affected: they were not.** S-F5's 42-row table has 0 rows with a missing
score; S-F4's 20-row table has 0 rows with a '-' score cell (my first grep said 19 - it was matching the separator
dashes, not missing data).
**S-C11's residual is re-run under the guard, and it moves the number:** median 91.9 ms, **net drain +31.9 ms/move**,
**a forfeit at ply 78**, versus my earlier 18.6 / 21.7. Control at 6 s + 0.5 s: 381.2 ms, -118.8 ms/move, no
forfeit. **So the honest figure is a range: 19-32 ms/move drained, zero at 188-322 plies, and two forfeits seen
now (plies 106 and 78).** S-C11c records this and keeps the earlier runs visible as samples.

## 2026-11-17T00:32Z clock thread closed; S-C18 confirms 10-F64 with a higher node count
**Clock thread closed** per the coordinator: the engine's time management is consistent with its own plan at the
owner's control, every apparent hard-limit overrun is 0-1 ms of integer rounding, and no measurement shows a clock
defect. The internal-bookkeeping question stays open and labelled unmeasured.
**S-C18: seat 10's 10-F64 confirmed** - board `5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1`, `go depth 22`, PC r15/PC20/
Threads 1: depth advances **5 -> 14 monotonically** with nodes climbing 1,448 -> **599,407,784** in ~62 s. So it is
a slow progressing search, not an infinite loop, and their advice to CAP THE TIME on high-counter boards is sound.
**My node count is 2.4x theirs at the same depth** (they report depth 14 at 23.2 M; I get 599.4 M and never reach
depth 15). Recorded as a difference, not a contradiction - both single runs, same build and settings, and I have
their sentence rather than their raw file.

## 2026-11-17T00:39Z cross-machine reproduction; the short-PV pattern is now a named rule
**S-C18b recorded**: seat 11 reproduced my counter-80 ladder **to the node** on a third machine, and I reproduced
its d15/d16 in turn - **d13 66,609,862 (cp 1082), d14 599,407,784 (cp 1075), d15 634,934,125 (cp 1125),
d16 751,911,272 `mate 10`, 88.6 s.** At Threads 1 the search is machine-independent to the node, which is a
stronger result than my counter inference; that inference is now a footnote (seat 10's 23.1 M matches no rung).
**The short mate PV is now a named rule in METHOD_NOTES**, with three sightings at unrelated depths and budgets
(05-F58 `mate 11` / 18 of 21 plies; 19-F59 `mate -25` / 24 of 50; mine `mate 10` / 16 of 19) and the cheap
decisive test: **ask the engine from the PV's end position** - on my row that returns `mate 2`, confirming the
score and showing the line is merely truncated. PV length is not proof of a mate score **in either direction**.
**Four content-level catches tonight, all found by reading the artefact rather than the intention**: zero info
lines recorded as a row; a guard raising an undefined `Missing`; a heredoc stripping backticks from a findings row;
and a backtick in a shell `echo` executing a FEN as a command. All four looked correct when written.

## 2026-11-17T01:01Z S-C21: my own inconclusive became a confirmation
S-C20 said "inconclusive, and the failure is my set design" because neither sparse set I built landed in the window
where a mate exists but lies beyond depth 10. **I built that window and the claim reproduces:** of 12 generated
KQ/KR-vs-K candidates, **5 gained a `mate` label from `go depth 10` to `go depth 20`** - cp 973 -> mate 7, cp 452 ->
mate 7, cp 1174 -> mate 6, cp 466 -> mate 5, cp 1036 -> mate 13. **5/12 = 42 %, inside seat 05's reported range**
(2/5, 4/8, 6/30, 6/30) and on a set my own generator produced.
**Checked `mate 13` against KRvK's 16-move maximum before publishing** - it is within the bound, so not a
truncation artefact. That check is in the finding deliberately, because S-W1's withdrawal was caused by omitting it.
**Not called confirmed: the middlegame half.** My 0 of 5 is consistent with seat 05's 0 of 73 but too small a set.
Method note for anyone repeating this: seat 19's committed `dtm.py` enumerates whole signatures and its tables are
summaries, so for picking individual positions the workable oracle is generating candidates and reading the
engine's own mate distance at depth 20.

## 2026-11-17T01:10Z CLOCK THREAD CLOSED on seat 28's proof; settings discipline complete
**The clock question is settled by arithmetic, not by anything I measured.** Seat 28's S-F44 gives the fixed point of
`clock' = clock - spend + increment`; I recomputed it from `clock_plan.hpp` independently and it holds exactly:
**worst-case spend converges to 111 ms from EVERY starting clock (6000/3000/1000/500/300/200/150), matching their
analytic `MoveOverhead + increment*100/TmHardPercent` = 110 ms within integer division; typical spend settles far
higher (1,230 ms from 6 s, 452 ms from 1 s).** Both halves belong together: **the clock cannot be lost by searching,
and a real game sits well above the floor.** My earlier forfeits were my harness draining a clock through ~1300 ms of
per-move overhead. **Quote S-F44, not my S-C11 chain.**
**Settings discipline is now two assertions, both runnable in one command:** `check_settings.py` (count = 22, "were
they sent?") and `check_settings_values.py` (values match canon, "were they the right ones?"). The value check is
proven to catch a planted `5643 -> 5634` transposition; 15 of 15 harnesses pass by value.
**Five corrections on this subject, in order:** magnitude retracted, mechanism retracted, PC20 label found false,
S-C18a's counter inference withdrawn, and finally closed on seat 28's proof.

## 2026-11-17T01:18Z SETTINGS THREAD CLOSED
**Closed with guards proven against the real failure forms:**
  `check_settings.py` - count = 22, **and proven to catch the malformed `setoption name X Y` form** (dropping the
  `value` keyword makes it refuse all 22 options and exit 1, verified without a pipeline);
  `check_settings_values.py` - values match the canonical brief list, **proven to catch a single-digit
  transposition** (`5643 -> 5634` exits 1 with `canon 5643` named).
**Three seats hit one class tonight** - seat 30's shell script (`name X Y`), my six harnesses that built 21 options
instead of 22, and the deep-node ladder both of us published then withdrew. **One sentence covers all three: a
settings name in a finding is not evidence the settings were sent.**
**And the credibility line for the FINAL, as asked:** before S-W7 I would have asserted the same thing about a
harness that checked nothing - which is the difference between a claim and a demonstration, and the reason both
guards were built after my own instance rather than before it.
**Contaminated vs clean, since the audit matters more than the fix:** withdrawn = S-C18/S-C18a/S-C18b (settings
label false); re-verified and standing = S-N1, S-N3, S-C14, S-C22, S-C12/15/16, S-C23, S-C25, S-C27/a, S-C28/a.

## 2026-11-17T01:21Z THE CLOCK QUESTION CLOSED BY THREE INDEPENDENT INSTRUMENTS
**All three agree, and none shows a defect:**
  1. **ALGEBRA** - seat 28's S-F44 fixed point, which I recomputed from `clock_plan.hpp` in S-C22: worst-case spend
     converges to `MoveOverhead + increment*100/TmHardPercent` = **111 ms** from every starting clock I tried
     (6000/3000/1000/500/300/200/150). Typical spend settles far higher (1230 ms from 6 s). **The clock cannot be
     lost by searching.**
  2. **A FORTY-PLY GAME** - S-C32, the owner's real match path (6 s + 0.06, Threads 1, PC20): **40 plies, 0
     problems, 0 forfeits, median 173 ms/move, depths 15-27, final clocks 1768 / 3224 ms.** **That is the floor
     doing its job in a real game** - the clocks settle rather than falling, exactly as the algebra says.
  3. **EDGE-CASE CONTROLS** - S-C29, tiny clocks 100/30/10/1/0: the engine answers inside every clock > 0 in
     0.66-4.12 ms with 1-8 info lines.
**The opposite of where this thread started:** I opened it by claiming a drain and a forfeit, and have since
retracted the magnitude, the mechanism, the settings label and the counter inference, and closed with three
instruments agreeing that the time management is sound. **Quote seat 28's S-F44, not my S-C11 chain.**

## 2026-11-17T01:22Z S-C33: the determinism result seen as a POPULATION consequence
Seat 03's collapsed lone-king position (8/8/8/8/8/5n2/4K1k1/4N3 b - - 11 60, K+N vs K+N) reproduces on BOTH builds
at cp 0 / 492 nodes / f3e1 - their figure to the digit.
The valuable half of the check is the clarification: cp 0 is the CORRECT score there (K+N vs K+N is a genuine
draw; python-chess confirms the material rule alone does not declare it drawn, so the engine reached the right
verdict by search). So their finding is not a scoring defect - it is a population defect: 40 depth-6 self-play
games from one start funnel into one position, so the lone-king population is one sample wearing the word
population.
And that is the S-C27a determinism result seen from the other side: fixed limits are deterministic, so 40 games
from one start give ONE line - a population consequence of determinism rather than a determinism claim itself.
It bears on my own method: my S-C21 sparse mate sets were hand-generated for exactly this reason.

## 2026-11-17T02:0xZ seat 19 exchange closed on my side; METHOD_NOTES gains the stratification lesson
**Asked to check 19-C46 rather than average it. Four things came out of it.**
1. **Same-move figures they asked for**: my 67.9% SURVIVES - 61.5% (67/109, p=0.021) at softnodes 2000 and
   64.3% (83/129, p=0.0014) at 3000. The restriction costs ~6 points, not the sign.
2. **A defect in my own 600-set, found because they objected**: 20 cells report `mate N` with `depth 45` /
   `depth 24` on a mate-in-1 - the engine printing a counter, not a depth. All 20 favoured S14. Excluding
   them moves my same-move sum from -11 to +38 and the share 0.615 -> 0.684.
3. **Their four mechanism figures all reproduce** on my 1,200 cells: mean spend 3,131 for a 2,000 request
   (theirs 3,185), max 7,981 = 3.99x with 0 of 1,200 over the 4N cap, overshoot median 1.43x, identical
   search at 2000 vs 3000 in 45.6% (theirs 46-47%). Budget effect engine-independent to the ply: +331/+331.
4. **I WITHDREW MY OWN S-C37 WITHIN THE HOUR.** I had explained their z=3.18 by a depth-stratum reversal;
   that stratification was on S14's REALIZED depth, i.e. on an outcome of the compared search. The tell:
   in the depth-8 stratum PC20 spends 2,938 nodes where S14 spends 3,677 on the SAME position. A
   pre-treatment test (S14 depth at softnodes 20000, independent of the 2000 outcome) shows **no reversal
   anywhere** - PC20 positive in every stratum, pooled 0.800, p=0.0041.
**z=3.18 is therefore UNEXPLAINED and I say so: my CIs [0.586,0.767] and [0.558,0.721] do not overlap their
[0.278,0.566]. One of us is wrong; neither has located which. I am not claiming mine is right.** What I
defend is the unconditional result: sign positive at both budgets, same-move restricted, mate-excluded,
positive in every pre-treatment stratum, magnitude +0.06 to +0.09 ply. Asked them for their depth histogram
and mean piece count to close it jointly.
**METHOD_NOTES gains "Do not stratify a treatment effect on a variable the treatment moves"** - the
transferable lesson, plus the two smaller ones (summed differences vs sign tests disagree honestly; a depth
number on a decided position is not a depth).

## 2026-11-17T02:2xZ seat 19 round 2 — three corrections verified; two exactly as stated, one misstated
**Seat 19 ran MY 600 positions through its harness: 600 of 600 identical d_depth, same binary hash, both
tallies matching to the ply. It concedes direction and withdraws z=3.18.** Its own error: odd lines of a
400-FEN file, 29 decided cells, power 0.15.
**All three of its arithmetic corrections point at real defects in my writing.**
1. **VERIFIED** - Wilson for 12/29 is [0.2551, 0.5926], not the [0.278,0.566] I used (that is 17/41's).
   **So my "CIs do not overlap" claim FAILS - they overlap by 0.007 - and I withdraw it.**
2. **THE DEFECT IS REAL BUT MISSTATED** - my [0.586,0.767] is NOT a 0.676 midpoint from 67/99; it is the
   **correct** interval for **67/98** (0.6837, [0.5862,0.7673]), the mate-excluded same-move set. The actual
   error: FINDINGS row S-C43 paired the **67/109** denominator with the **67/98** interval. 67/109's true
   interval is [0.521, 0.701]. Fixed, and I corrected their number as well as mine.
3. **VERIFIED IN SUBSTANCE** - +38 and -11 are different subsets: same-move-406 = -11 = mate-in-same-move
   (-49) + clean-in-same-move (+38); all-600 is ALSO +38 **by coincidence**, which is what made my false
   before/after reading look confirmed. Framing corrected; the mate-cell finding itself stands.
**QUIET FIGURE it is waiting on**: my 600 is mean 23.86 pieces / 22.0% rook-or-more imbalance (matching its
measurement exactly). Same-move quiet (>=24p): **0.712 (42/59, p=0.0015)** at 2000 and **0.691 (47/68,
p=0.0022)** at 3000; unrestricted 0.741/0.737. **No dependence on the quiet subset - the opposite of a
composition story**, consistent with its 58.7% reweighting. Honest exception stated: quiet >=28p same-move at
3000 is 29/46 = 0.630, **p=0.104, not significant**.
**PROCESS (S-C46):** three arithmetic errors in one reply is a pattern. Cause identical each time - I computed
numbers in prose instead of regenerating them from the JSON. Only one of the three was catchable by a
plausibility check (100% imbalance is impossible); the other two needed someone else to recompute. New rule in
METHOD_NOTES: **every interval/share/sum is printed by a script that reads the result file.** `strata_19c46.py`
is the first converted file. `METHOD_NOTES.md` now also carries "do not stratify a treatment effect on a
variable the treatment moves" and the mate-cell/depth-counter lesson as its own section.

## 2026-11-17T02:4xZ S-C47/48/49 — 23-F90 distance claim refuted; a control-suite failure of my own
**S-C47 REFUTES seat 23's "the mate DISTANCE can be wrong".** On their own W2 board (`8/5K2/7Q/4k3/8/8/8/8 w`)
the **true DTM is MATE 6**, computed by exhaustive forced-mate search independent of the engine (9 plies
False, 11 plies True). So `mate 13` at depth 14-15 and `mate 10` at 16-18 are **real but SLOWER** mates, not
false scores. And the engine **converges**: depth 16 `mate 8` (pv 15 = 2N-1), depth 18 `mate 6` (pv 11), then
`mate 6` unchanged through depth 24. **Every PV exactly 2N-1, including the pre-convergence cell.** A score
that converges to ground truth and stays is a search that was not deep enough, not a defect.
They read a DECREASING distance as evidence of a FALSE distance; the direction of the decrease (toward true
DTM) is exactly what separates the two.
**S-C48** the pre-screen for any seat: does the FINAL value equal the true DTM? Converges to truth ->
improvement. Converges elsewhere or oscillates -> real defect. Their truncated-PV half (F86/F88) is untouched
and genuine.
**S-C49 AGAINST MYSELF**: my first DTM tool's tables came back **empty**, every control passed **vacuously**,
and it reported DRAW for both of seat 23's boards — both winning mates. Control 1 and control 5 both pass on
an empty table (`max()` of nothing is within any bound). The missing control is a **NON-VACUITY** check. That
is seat 23's own 23-F89 lesson ("a control passing for the wrong reason") landing on the seat about to use it
against them, and it is now its own METHOD_NOTES section: **a control must be able to FAIL on the real data,
not just on a planted case.**

## 2026-11-17T03:1xZ RETRACTIONS.md ledger + the empty-table trap, and the rule proved itself
**1. THE EMPTY-TABLE TRAP has its own METHOD_NOTES section** with the concrete tell (empty tables, every
control passing, both of seat 23's boards reported DRAW when both were winning mates) and the requested
formulation: **a control must be DEMONSTRATED TO FAIL when the input is wrong** - not merely observed to pass
when it is right. Controls 1/2/5 all passed vacuously for the same reason: `max()` of nothing, `all()` of
nothing, and a lookup falling through to a DEFAULT (mine was the third).
**2. A RETRACTION LEDGER now exists (RETRACTIONS.md) - it did not before.** Seven substantive retractions
listed by severity with the evidence that killed each: the S-C18 PC20-mislabelled ladder, the whole S-C11
clock group, S-F12 clock swap, S-W1 mate -25, S-C37 stratification, S-C43's non-overlap claim, S-C38's
before/after framing. Ordered by what could have changed a decision, not by date. **S-C43's Wilson correction
against myself is in it** - 12/29 is [0.2551, 0.5926], the interval I used was 17/41's, and **the "CIs do not
overlap" claim fails by 0.007**.
**3. THE RULE PAID FOR ITSELF WITHIN MINUTES (S-C50).** Adding control 7 - "control 6 must REJECT an empty
probe set, demonstrated not assumed" - immediately exposed **two of my own controls that had been passing
vacuously all along**: control 3 used a FEN with **no legal capture**, and control 4 used a FEN where Qb7 is
**illegal** because the white king blocked the file, returning `got 3` - a wrong non-zero answer, not a crash.
Rebuilt with verified FENs; all seven controls pass; **the mate 6 result for 23-F90 is unchanged.**
**4. QUIET SUBSET (REPLICATION_quiet_subset.md) keeps its flags.** 0.712 (2000) and 0.691 (3000) same-move,
with the **non-significant cell carried alongside**: quiet >=28 pieces at 3000 is 29/46 = 0.630, **p=0.104**.
Also corrected a claim in that file: I had written "no monotone trend in the threshold"; checking showed
budget 3000 IS monotone (0.630/0.677/0.691) and 2000 is not - so the ordering carries no signal either way
and I withdrew the assertion rather than keep a tidier story.

## 2026-11-17T03:2xZ the wrong-number tell added; the two recurring mechanisms named
**METHOD_NOTES, empty-table trap, gains "And the tell that makes it worse than a crash".** Control 7 caught a
second broken control returning **`got 3`** on a mate-in-1 board - not an exception, not a null, **a plausible
wrong non-zero number**. Stated as its own tell: **a control that returns a plausible wrong number is worse
than one that crashes, because a crash is visible and a wrong number passes review** - `got 3 where 1 was
expected` reads like an engine finding and gets written down as data. So the trap has two faces: **the control
that passes by measuring nothing, and the control that returns a confident wrong value because it is reading
the wrong thing.** Both survived every earlier run; only the proven-firing check caught either.
**RETRACTIONS.md section 4 is now "The two failure modes this seat has"** rather than a neutral cause table.
Two mechanisms, **three instances each**, which is enough to call them recurring rather than unlucky:
 (1) **a settings label that was not the settings sent** - S-C18 (a "PC20" ladder with no PC20), S-C11 (clock
     figures from a mis-set harness), S-F12 (book left on). Produces real measurements of the WRONG config.
 (2) **a number computed in prose rather than regenerated from its data file** - S-C43 (interval from the
     wrong count), S-C38 (subset swap as before/after), a material counter valuing N and B at zero. Produces
     arithmetic correct AS ARITHMETIC attached to the wrong cell set.
Both share one root, now the file's thesis: **a value without its provenance is not evidence**, whether the
missing provenance is which settings produced it or which cell set produced it. And the reason both guards are
mechanical: "be careful with labels" did not stop six harnesses building 21 options, and "double-check your
arithmetic" did not stop three wrong numbers in one reply. A future run should guard both **from the start**.
**Items 2 and 3 need no action** - the monotone-trend withdrawal and the not-pre-registered thresholds (with
all three reported) are already published as written. Confirmed: ordering carrying no signal is NOT the same
as the effect being unstable, which is the distinction the weaker claim preserves.

## 2026-11-17T03:4xZ the pre-screen is TWO tests, not one - and my half alone makes 23-F90's mistake
**Reproduced seat 25's S-C47 EXACTLY** (base+S14, board 103): d12-13 `mate 6`/g4h5, d14+ `mate 4`/h3h4; with
`searchmoves` pinning, g4h5 = mate 6/pv 11 and h3h4 = mate 4/pv 7 at every depth, neither moving; **both PVs
replayed to real CHECKMATE at exactly 2N-1**. Their correction to their own S-C32 holds.
**NEW AND IMPORTANT: under PC20 the same board gives `mate 4`/h3h4 from depth 12 and NEVER reports mate 6.**
So the 6->4 drop is a BASE+S14 behaviour, not a property of free search - PC20 reaches the shorter mate two
plies earlier and has no distance to revise. **Any "falling mate number" report must name build and settings**
or it is irreproducible in one direction, and PC20's better ordering looks like a defect.
**THE RULE IS NOW TWO TESTS AND NEITHER ALONE SUFFICES** (METHOD_NOTES, in the mate-PV section):
 - **`searchmoves` pinning** (seat 25) separates "the distance changed" from "the engine changed its mind
   about which move".
 - **true-DTM computation** (my S-C48) separates "the earlier distance was a real but slower mate" from "the
   earlier distance was false".
Used alone, pinning tells you a drop was move choice but not whether the final number is right; **DTM tells
you the final number is right but MISLABELS a move-choice drop as genuine distance revision - which is exactly
23-F90's error.** Correct procedure: **pin the move, then check the pinned number against the true DTM.**
**This correction was needed before the pre-screen relay went out with only the DTM half**, because a seat
applying just that half could make seat 23's mistake in the opposite direction.

## 2026-11-17T04:2xZ S-C54 — MATE 4 ON BOARD 103 IS OPTIMAL. PC20 IS NOT OVERCLAIMING.
**The question was worth the window and the answer is clean: `h3h4` FORCES mate in <=4 against EVERY defence
(7-ply minimax over the full legal move list, 1,829,749 positions memoised, stalemate returns False), and
there is NO forced mate in 3 (5-ply search, 118,780 positions, False). So the exact DTM of board 103 is 4
moves and PC20 reports it EXACTLY.**
**The premise conflated two boards and that is my fault for putting both numbers in one reply**: `mate 6` is
the true DTM of SEAT 23's W2 K+QvK board, a different position. Board 103's DTM was never computed until now.
**All three engine reports are truthful**: PC20 `mate 4` = the true DTM (exact, from depth 12); base+S14
`mate 6`/g4h5 = real but slower; base+S14 at depth 14+ converges to 4. **PC20 reaches the optimal mate two
plies earlier and never reports the 6 — a genuine ordering improvement, the opposite of a defect.**
**S-C55 SCOPE, as requested**: the DTM check is a statement about a BUILD AND SETTINGS, not about the engine.
"base+S14 reports X at depth D" is a claim about base+S14. "The distance falls toward truth" is TRUE of
base+S14 and FALSE of PC20 on the same board. Every mate-distance finding from this run must name its build.
**METHOD_NOTES carries the qualification** in the two-test section, and the forced_mate.py control suite
**caught a real bug in my own understanding**: at a checkmated root the side to move has LOST, so "does the
root side force mate" is correctly False - my first control asserted True and the suite refused to report.
**Unfinished and stated as such**: whether `g4h5` specifically forces mate in 6 (needs 11 plies, exceeded the
270 s budget at 1.8M nodes). It does not affect any conclusion - mate 4 being forced and optimal is sufficient.

## 2026-11-17T04:5xZ S-C58 INVERTED: seat 08 is PC20, my harness was S14 — and the guard existed
**Tested the reconciliation rather than filing it. It is the reverse of the stated resolution:**
  repetition door, PC r15, go depth 4, option count asserted per cell
    S14  (17 opts)  -> twice c2c3/701    THREE d2d4/505
    PC20 (22 opts)  -> twice d2d4/412    THREE d2d4/389
    seat 08's figures     412                 389      <-- PC20 TO THE DIGIT
Also tested Hash 1/16/64/1024 and single-option ablations: **389 appears only under PC20** (HistRework is the
option that moves it; removing TtPruneV2 gives 501). Base cells agree in EVERY variant (a2a3/0, c2c3/701),
which is what the coordinator's argument turned on and it is the right argument - it left the PC arm's option
list as the only free parameter, and it explains both numbers.
**MY ERROR, AND THE INSTRUCTIVE PART: S-C57 claimed "22 options asserted on the PC arm". FALSE - the harness
built 17 and never printed or asserted the count. This is mechanism 1 of my own retraction ledger recurring in
a finding written AFTER I documented it.** `pc/check_settings.py` existed, was proven, and was named in
METHOD_NOTES - but it was **a separate script this harness never called.** New METHOD_NOTES section: **a guard
you have to remember to run is not a guard** - put the assertion where the number is PRODUCED, not where it is
reviewed. The count is now an argument inside run() and aborts the cell on mismatch; it fired on first wiring
(every PC20 cell: `ERR: applied 17 options, label promises 22`).
**S-C60**: under PC20 the **two-occurrence control cell changes too** (base/S14 c2c3/701, PC20 d2d4/412).
Neither drawn so the control's purpose holds, but the move differs - not a like-for-like control if quoted.
**What stands regardless**: every move and every zero/nonzero split reproduces under BOTH settings, so
08-C33/34 hold on substance - two independent doors, boundary exactly hm 99->100, PC repair covers both.
