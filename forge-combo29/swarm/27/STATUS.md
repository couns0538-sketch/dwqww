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
