branch: for-fable-and-opus/swarm-27
folder: forge-combo29/swarm/27/
area: 7 (READING THE CODE for faults)
seed: 2701

# FINAL STATE — all findings, raw files and patches are on this branch

## THE TWO THINGS A MERGER NEEDS (both at the top of PATCHES.md)
1. **Composition order and paths**: seat 12's `two_doors_mate.patch.txt` FIRST with `-p1` from the directory
   that CONTAINS `forge-combo29/`; then my `job1/drawn_root_reporting.patch.txt` with `-p1` from INSIDE
   `forge-combo29/`. The two patch files have different path roots — that is the trap. Reverse order fails.
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
