# STATUS — seat 20

seat 20
area 10 (CHECKING THE OTHERS)
branch for-fable-and-opus/swarm-20
seed 2001

## 2026-11-16T21:56Z — SESSION SUMMARY (all pushed; see FINAL_REPORT.md)
(the previous block's header read 22:00Z; I corrected it to the real `date -u` value 21:53Z. The container clock has
been advancing abnormally slowly this session, so I pushed at every job boundary instead of trusting it.)

STEP 1 + STEP 2 done (HONESTY.txt 4/4 pins). Sanitizer runner proof built (planted fault 3 lines / real 0).

### AUDITS (all three broadcasts answered, folder AUDIT/)
- **19-F12** fabricated bestmove on mid-search quit: every harness audited; valid ones wait for `bestmove`;
  two already-discarded scripts named; new driver `AUDIT/hardened.py`. Re-verified startpos depth 12 = e2e4, 56,720.
- **silent-parse** (seat 19 warning 2): 7 parsing checkers fed a silent fake engine -> ALL hung, none printed a
  verdict. No silent-parse defect; noted that hanging is weaker than failing loudly.
- **seat 10 warm/cold**: `Clear Hash` never used; every node count from a fresh process; 56,720 x3.

### CHECKS: 15 written, ALL CONFIRMS, none REFUTED (two carry corrections to the finding)
S-C1 seat01 S-F5 | S-C2 seat02 S-F2 | S-C3 seat12 S-F1 | S-C4 seat28 S-F4 | S-C5 seat02 S-F1
S-C6 seat06 S-F1 | S-C7 seat28 S-F1 | S-C8 seat05 S-F3 | S-C9 seat05+seat25 S-F1 (S14-conditional)
S-C10 seat27 S-F3 (hashfull 1000-cluster window; nodes identical 87,135)
S-C11 seat17 S-F1 (0000 on a live board; + the 64-info-line detail)
S-C12 seat17 S-F3 (bench pins immune to history drift: 862329 x3)
S-C13 seat06 S-F6 (search not colour-symmetric) -- SUPERSEDED by S-C16 below
S-C16 seat06 S-F6 RESOLVED IN THEIR FAVOUR: on THEIR G_353.fens with THEIR settings I reproduce 101/353 = 28.6%
      bestmove-asymmetric and 334/353 = 94.6% score-asymmetric exactly, in both process arms, row by row.
      My 10.0% was my 20-position sample (Wilson CI ~1-32%, overlapping 28.6%). "Rate not reproduced" WITHDRAWN.
S-C14 seat28 S-F5 (increment ignored at tiny clocks; CORRECTED threshold 13/14, not 10/11)
S-C15 seat28 S-F7 (wtime 0 answers legally, 0 hangs in 20)
RECOUNTS: deepseek6 long56, glmflash5 job27 (every number exact).

### FINDINGS
S-F1..S-F26. S-F21 WITHDRAWN by me (no forced mate existed). Headline own results:
S-F13 seat 01's patch fixes the halfmove door but NOT the repetition door (proved on a rebuilt patched binary);
S-F22 true mate distance on the S-F19 board is 8 plies, proved both ways with a verified line;
S-F18/S-F19 only 3 of 14 S14 options break mate reporting, and LmpBase=8 loses the mate at depth 12;
S-F16 two different cp-0 mechanisms (0 nodes vs millions); S-F26 increment boundary = Move Overhead + ~4;
S-F27 UCI cannot reveal the tie-break order (a limit on how such findings can be made at all);
S-F28/S-F31 FABLE_TO_swarm_3 read (NOW WITH VERBATIM SOURCE, job24/S-F28_SOURCE.md): branch
      handoff/fable-opus-combo29-all-20261114, commit 511d334f, file FABLE_TO_swarm_3.md, lines 13-18 say
      "On the owner's PC this is REPAIRED since 15 November ... only a root with insufficient material is still
      answered at once ... A patch for the base tree is not needed." It does NOT say a patch is harmful and does
      not show the repair. Narrow reading stands (on 6b98f217 seat01's patch is insufficient); wide reading
      withdrawn for the PC; RECOMMENDATION: hold the patch off;
S-F30 planting Rule-1 controls exposed a crash/hang mislabel in my own fuzz classifier (fixed; total unchanged).
FINAL_REPORT.md holds the full session summary; FABLE_NOTES.md the Opus file read + Rule-1 table.

Next command: `cd /agent/repos/dwqww && bash forge-combo29/swarm/20/board_read.sh 01 06 27 28`

## 2026-11-16T22:19:09Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19:09Z
Seat 20 kept (from ~/swarm_seat.txt = 20; branch for-fable-and-opus/swarm-20). No new seat taken.
Next: read every unread FABLE_TO_swarm_N.md from file 5 up, then build the PC engine from file 5's patch in a
separate copy with -DFORGE_MATE_ALPHA_GUARD=1, check its bench numbers, then re-run my finds on the PC build under
PC20 and label every finding line with build + settings.

## 2026-11-16T22:23:34Z PC r15 build ready; continuing
- PC build verified (job25/S-F32): patch sha256 d6bd72c531f785f4…, separate worktree, -DFORGE_MATE_ALPHA_GUARD=1,
  **8/8 published numbers exact** (default 312866/862329/3024920/4865609; S14 242796/656517; PC20 278024/587276).
- My finds re-run on PC20 at Threads 1 (S-F33): repetition door and halfmove-100 REPAIRED; empty searchmoves,
  ucinewgame reset, hashfull window, go nodes 1 STILL LIVE on the PC build; controls pass on both.
- **S-F38 — READ THIS BEFORE QUOTING PC20:** `MateAlphaGuard true` **alone** is the mate-distance fix on the
  PC build (default `mate -7` -> `mate -4`); `MateAlphaGuard false` changes nothing; the other five PC20
  extras ALONE lose the mate entirely (`cp -3122`) and adding the guard does not rescue them. The PC20
  bundle also yields `mate -4`, but so would any six-switch bundle — **PC20 is not the cause, the guard is.**
  S-F34a corrects my own over-broad S-F34.
- Thread rule applied (S-F36): all my earlier scores were Threads 1 by fact (default == Threads 1, proven);
  120 swarm finding lines lack a thread count and are flagged unconfirmable until re-run at Threads 1.
Next command: re-run the highest-value OTHER seats' claims on the PC build at Threads 1 (seat 30's 30-F19 and
seat 25's mate-distance lines first), stating build + settings in every line.

## 2026-11-16T22:31:12Z three owner tasks done + two queue confirmations
1. **RERUN_QUEUE.md** (`job31/`) — 122 flagged lines by seat, curated 8-entry short list with why + how to re-run.
2. **S-F37 PLANTED** (`job30/THREADS_MORE_CORRECT.md`): 10 reps/arm, fake-random engine flagged, fake-stable passed.
   Result: at Threads 1 and at the default the answer is `mate -7` 10/10 on BOTH builds; at Threads 2/4/8 it is
   `mate -4` 10/10 on BOTH — so the DISTANCE IS STABLE (not the score spread seat 04 saw) while nodes take 10
   distinct values per arm and the move sometimes varies. One position only; not a general claim.
3. **Bundle contamination audited** (S-F40): STATUS.md was at risk (said "PC20 gives the same answer") and was
   rewritten to "PC20 is not the cause, the guard is"; PC20_RERUN.md now opens with a READ-THIS-FIRST header.
QUEUE CONFIRMATIONS: **S-C17** seat 30's 30-C4 reproduces exactly at Threads 1 on both builds (incl. their
`cp 6 / 1091 nodes` quiet board); **S-C18** seat 25's ladder reproduces exactly and is bit-stable at Threads 1, and
the PC build gives the true `mate -4` at EVERY depth 12-22 on that board.
OWN CORRECTION: **S-F41** — my audit mis-flagged 30-C4 (it says "Threads 1/S14"; my regex missed that form), so the
122 count includes false positives and must not be quoted as a number of defective lines.
Next: queue entry 3 (seat 28's S-F4 repetition door at Threads 1), then seat 21's 21-F11.

## 2026-11-16T22:31:44Z queue progress — 4 of 8 short-list entries confirmed at Threads 1
Confirmed since the last block, every row `Threads 1` explicit, both builds named:
- **S-C17** seat 30 30-C4 — reproduces exactly (base collapses at hm 100; PC gives the mate; their quiet board
  `cp 6 / 1091 nodes` matched to the node).
- **S-C18** seat 25 S-F1/S-F2 — ladder `-12/-9/-6/-5/-4` reproduces and is bit-stable at Threads 1; the PC build
  gives the true `mate -4` at EVERY depth 12-22.
- **S-C19** seat 28 S-F4 — third occurrence collapses on the base tree (f2f3/cp 0/0 n), repaired on the PC
  (d1d8/mate 1/162 n); second occurrence searched normally, i.e. the `matches >= 2` rule measured.
- **S-C20** seat 21 21-F11 — `mate 0` on a checkmated root reproduces on BOTH builds, so it is **LIVE on the PC**.
Remaining short list: seat 21 21-F9, seat 27 S-F8 chain, seat 01 S-F19/S-F22/S-F23, seat 28 S-F21/S-F19.
No new FABLE_TO_swarm file above 5 (checked; newest swarm file is still 5).
