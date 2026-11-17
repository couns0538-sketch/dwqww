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
