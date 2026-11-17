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

## 2026-11-16T22:32:17Z queue: 6 of 8 short-list entries confirmed at Threads 1
- **S-C21** seat 21 21-F9 — the halfmove counter test is `>= 100` with NO upper bound (fails identically at 100,
  101, 150, 9999 and 65536 on the base tree); the PC build answers the mate correctly at all of them.
- **S-C22** seat 01 S-F22 + S-F23 — both confirmed, and this pair gives the cleanest statement of the whole defect:
  on `8/8/8/8/2K4Q/8/8/1k6 w - - 100 1` the fifty-move claim IS available and no mating line resets the counter,
  so `cp 0` is correct chess — the base tree reaches it with **0 nodes** (shortcut) and the PC build with **135
  nodes** (searched). On seat 01's discriminating board `8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1` a forced mate exists
  and the base tree still says `cp 0 / 0 nodes`, while the PC build finds **`mate 2`**. Node count, not score,
  separates "shortcut" from "correct draw".
Remaining: seat 27's S-F8 chain, seat 28's S-F21/S-F19 (competing patches).
Counts: 64 FINDINGS lines (22 checks), tree clean, every push includes this file.

## 2026-11-16T22:33:15Z queue: 7 of 8 done + a swarm-wide labelling audit
- **S-C23** seat 27 S-F8/S-F8b: substance CONFIRMED (a `searchmoves` restriction changes the reported score on both
  builds at Threads 1) — but their quoted `cp 30 / 56720` labelled "S14" is the **default-settings** answer; real S14
  is `d2d4 / cp 24 / 22459`. NEW: on the PC build under PC20 the two-move restriction nearly closes the effect.
- **S-F42** (new, swarm-wide): audited every seat's FINDINGS for "S14" next to a node number. **Exactly one real
  mislabel (seat 27's), no others.** Ground truth measured: defaults = e2e4/cp 30/56720 on BOTH builds; S14 =
  d2d4/cp 24/22459; PC20 = d2d4/cp 25/21600. So the S14 labelling is otherwise sound, and the default answer being
  identical on both builds is why the four honesty pins stay comparable.
Remaining: seat 28's S-F21/S-F19 (three competing drawn-root patches — which one to advise).

## 2026-11-16T22:33:34Z QUEUE COMPLETE — all 8 short-list entries addressed at Threads 1
S-C17 (seat 30 30-C4) | S-C18 (seat 25 S-F1/S-F2) | S-C19 (seat 28 S-F4) | S-C20 (seat 21 21-F11)
S-C21 (seat 21 21-F9) | S-C22 (seat 01 S-F22+S-F23) | S-C23 (seat 27 S-F8) | S-C24 (seat 28 S-F21/S-F19)
Every row states build + settings and sends `Threads 1` explicitly.

**Most urgent result (S-C24):** at Threads 4 on PC r15/PC20 the engine plays **three different moves** across five
runs (e1g1, c2c3, d2d4) with five distinct scores and five distinct node counts, while Threads 1 is bit-identical
5/5. So above Threads 1 a MOVE and not just a score is unreproducible — every match/regression result taken above
one thread is unreproducible at the move level.

**The one-line summary of the drawn-root family (S-C22):** node count separates "shortcut" from "correct draw".
Base reaches `cp 0` on a drawn root with **0 nodes**; the PC build reaches the same `cp 0` with **135 nodes** by
searching. A checker comparing scores alone cannot tell these apart.

**S-F42:** the "S14" mislabel is exactly one line swarm-wide (seat 27's), not systemic.
Remaining work: nothing on the queue; continuing with new finds and checks on both builds.

## 2026-11-16T22:36:23Z both live PC defects confirmed with per-run data
- **S-C25 fifty-move band** (`job44/BAND_HM_CONFIRMED.md`): every halfmove 85..100, 3 runs each, both builds,
  Threads 1. Score falls from cp 231-349 (85-90) to EXACTLY cp 0 at **91** and stays 0 to 100 — all 32 cells
  identical across 3 runs. It is the in-tree horizon, not the root shortcut: at hm 91 the PC searches **7,251,835**
  nodes. Only cell where builds differ is hm 100: base 0 nodes, PC 200 nodes. Extra: PC reports `mate 8` at hm 85
  where the base says cp 349.
- **S-C26 `go nodes` band** (`job45/BAND_NODES_CONFIRMED.md`): every value 1..30, 3 runs each, both builds. **EVERY
  value 1..25 gives `a2a3` with 0 info lines and 0 nodes, identically on BOTH builds** — 60/60 cells stable. Boundary
  exactly **26**; 27..30 still report nodes 26, so no partial root iteration can be bought. **Live on the PC build**;
  no PC20 switch touches it (S-F43). Controls asserted: `go nodes 1000` gives real searched answers on both builds.
- **S-F44 regime ground truth** (`job43/GROUND_TRUTH.md`): defaults = `e2e4/cp 30/56720` on BOTH builds; S14 =
  `d2d4/cp 24/22459` on both; PC20 = `d2d4/cp 25/21600` (PC only). TRAP documented: the base build answers
  `unknown option` for all five PC20 names, so "PC20 on the base tree" silently = S14.

## 2026-11-16T22:48:10Z file 6 verdicts applied; PC's mate 8 proved real; softnodes area done
- **S-F45** fifty-move band RETIRED as a defect (Opus's inequality: measured mate = 15 plies, so `15 <= 100-c`
  holds only at counter 85; every `cp 0` from 86 to 100 was correct chess).
- **S-F46** thread variance is DESIGN, not a defect; S-C24 now documents shared-hash behaviour, and the defect test
  recorded is Opus's (hang / crash / illegal move / sanitizer line / score outside the one-thread spread).
- **S-F47** the PC's `mate 8` at halfmove 85 is **REAL**: exhaustive test gives False at 1,3,5,7,9,11,13 plies and
  **True at 15** = mate 8, so the PC build is right and the base tree misses it at every depth up to 14 (cp 330-372).
  The PC's PV is truncated at 10 plies — truncation, not a wrong score.
- **S-F48** `go softnodes N` on the PC path: **deterministic 12/12 cells 5/5 (incl. node count)**, only finished
  depths published, but the budget **overruns N by +5.4% to +106%** (startpos N=2000 -> 4,121 nodes). The hard
  `go nodes` limit does not overrun. So self-play is exactly replayable but "2000 nodes" under-counts up to 2x.
Next: the PC's real path — clock 6s+0.06, `go nodes` 20000/50000/250000, real-game positions; keep the
MultiPV/Hash collapse live.

## 2026-11-16T22:49:17Z both-signs caveat added; PC match path measured
- **S-F47 amended** per the owner: it now opens with SMALL SAMPLE, BOTH SIGNS and cites the counter-evidence by id —
  seat 08's 08-F23 (`CuckooRep true` ALONE makes the mate distance WORSE on its board: mate -13 vs baseline mate -9),
  and seat 01's S-F49/S-F49b (below the depth where a mate first becomes visible the guard changes NOTHING;
  identical node counts at depths 12-16 on their S-F48b board). One board for, one against, one null = a per-position
  effect, NOT a general strength claim.
- **S-F48 softnodes: area CLOSED** per the owner (deterministic 12/12, finished depths only, overruns N by +5..+106%).
- **S-F49 clock path** (the PC's match control, 6 s + 0.06, Threads 1): a move uses only **129-301 ms = 2-5% of the
  budget**, reaching **depth 17-18**; the MOVE never varied across 3 runs but the **DEPTH/NODE COUNT flipped 17 vs 18**
  (288,912 vs 314,239 nodes) because ~5 ms of wall-clock variation decides whether the 18th iteration finishes. So
  clock matches cannot be replayed exactly (node-limited ones can), and raising the clock buys almost nothing.
Next: keep confirming on the PC path — the `go nodes` 20000/50000/250000 ladder is done (all deterministic, 3/3);
remaining: MultiPV/Hash strength collapse (live per the owner) and any new seat claims on the PC build.

## 2026-11-16T22:50:07Z MultiPV x Hash collapse confirmed — and it changes the MOVE
- **S-C27** (seat 02's S-F7b/S-F7c): PC r15, Threads 1, `go wtime 5000`, 3 runs/cell. MultiPV 1 safe at Hash
  16/256/2048; Hash 16 safe at MultiPV 8 (d12); **Hash 256/MultiPV 3 -> depths 2,5,7**; **Hash 2048/MultiPV 3 and 8 ->
  depth 1, 3/3**, burning 1.1-1.3 s. **NEW: the collapsed cells change the MOVE** — healthy cells play `g7g6`,
  Hash 256/MultiPV 8 plays `f6d7` (3/3), Hash 2048/MultiPV 3,8 play `b8a8` (3/3). A reproducibly WORSE root move in
  analysis, not just a shallow one. Correction to their table: Hash 256/MultiPV 3 is not a clean d8 (I got 2,5,7 with
  a varying move — collapsed AND erratic). Advice: MultiPV 1 at any Hash, or Hash <= 16 MB with MultiPV > 1.
- **S-F49** clock path: 6s+0.06 uses only 2-5% of the budget (129-301 ms), depth 17-18, but depth/node count flips
  17 vs 18 across runs at Threads 1 — clock matches are not exactly replayable, `go nodes` matches are.
Next: continue confirming PC-path claims; MultiPV/Hash stays the live strength item.

## 2026-11-16T22:50:36Z MultiPV/Hash verdicts SPLIT per cell (the decisive measurement)
- **S-C28**: the two collapsed cells are NOT the same defect.
  - **Hash 256 + MultiPV >= 3 -> `f6d7` is MERELY DIFFERENT**: `f6d7` cp -293 vs healthy `g7g6` cp -297, i.e. **+4 cp
    (marginally better)**, well inside the ~24 cp restriction noise band. Wasted-budget defect only (searches ~5% of
    the depth, equally good move).
  - **Hash 2048 + MultiPV >= 3 -> `b8a8` is 46 cp WORSE**: cp -343 vs -297, ~2x the noise band, stable **5/5**. A real
    **QUALITY defect** — a reproducibly wrong recommendation at the same depth. Describe it that way.
  - Method A (MultiPV 4, healthy settings): g7g6 cp -273, e5e4 -311, f5e6 -327, b8b7 -328.
  - Avoided identically: **MultiPV 1 at any Hash, or Hash <= 16 MB with MultiPV > 1.** Analysis only (matches use MPV 1).
Next: continue confirming PC-path claims; nothing of mine awaits a decision.

## 2026-11-16T22:52:01Z class test done — split verdict, and a 0-node fallback answer found
- **S-C29** (6 G-set positions, Threads 1, pre-stated worse-than-noise-band rule): **NOT a move-quality class** —
  WORSE 2/6 (delta -203 vs band 31; -335 vs band 310), equal 1, **SAME MOVE 3**. So the move-quality warning stays
  MEASURED, not emphatic.
- **But the collapsed cell is UNRELIABLE, which is a class defect**: on position 1, six runs gave `d5d4` with **0
  NODES** then `b8a8` (nodes 67/67/143/220/220) — two moves, one a 0-node fallback answer. The per-line tt.clear()
  can consume the entire clock. Warning: measured on move quality, **emphatic on reliability** (0-node answers,
  varying depth and move). Load-sensitive: job51 saw b8a8 3/3 on an idle machine, so both readings are recorded.
- Advice unchanged: **MultiPV 1 at any Hash, or Hash <= 16 MB with MultiPV > 1.**
Next: continue confirmations on the PC path.

## 2026-11-16T22:56:38Z 0-node answer measured under load — the actionable reliability number
- **S-F50**: Hash 2048 + MultiPV 8, `go wtime 5000`, Threads 1, 10 fresh processes per arm:
  **1/10 zero-node answers IDLE -> 6/10 with three CPU hogs** (moves vary b8a8/d5d4, nodes 0/67/143), while the
  HEALTHY cell (Hash 16 + MultiPV 1) gives **0/10 in BOTH conditions** (single move g7g6, nodes 121k-289k).
- So the 0-node fallback is specific to the collapse and load turns it from rare to a majority.
- **Warning for the owner:** analysing on a busy PC with MultiPV 8 and Hash >= 256 MB can return a move with NO SEARCH
  behind it. Fix: MultiPV 1 at any Hash, or Hash <= 16 MB with MultiPV > 1. Matches use MultiPV 1, unaffected.
- Method note on record: my harness refused the first load attempt with `no readyok` after 20 s; the load arm uses a
  120 s isready timeout (printed in the output) because the engine was starved, not hung. The 19-F12 discipline is
  unchanged — we never continue without a readyok and never invent an answer.
Next: continue confirmations on the PC path.

## 2026-11-16T22:59:24Z warning page written, and the last number NARROWED it
- **`WARNING_multipv_hash.md`** (one screen, owner-facing): failing configuration, idle vs loaded failure rate,
  healthy control, the fix, and that the matches are unaffected.
- **S-C30 narrowed S-F50**: **MultiPV 3 + Hash 256 — the plausible GUI setting — gave 0/5 zero-node answers idle AND
  0/5 under load, on TWO positions.** So the no-search answer is demonstrated at **Hash 2048 + MultiPV 8** only
  (1/10 idle -> 6/10 loaded, one position). 256 MB + MultiPV 3 gets "slower and shallower" (nodes 5,395-47,818 vs
  288,912 healthy on P1; 1,132 vs 237,233 on P2), never a no-search move.
- The warning page now says exactly that, and I removed an unverified "second position reproduced it" sentence before
  measuring P2 — P2 did not reproduce a zero-node answer at 256/3.
Next: continue confirmations on the PC path.

## 2026-11-16T23:00:54Z FINAL
51 own findings, 31 checks, 2 of my own WITHDRAWN. Builds: base = 6b98f217; PC r15 = base + file 5 patch
(sha256 d6bd72c531f785f4…, -DFORGE_MATE_ALPHA_GUARD=1), verified 8/8 published numbers. Settings: none / S14 / PC20.
EVERY score is Threads 1 except rows that explicitly say >1 to show why that matters.

LIVE ON THE PC BUILD (what the owner's engine still does)
- S-F50/S-C31 (mine, open): Hash 2048 + MultiPV>1 can return a move with NO SEARCH — 1/10 idle -> 6/10 with three
  CPU hogs, and 5/5 at 2048/MultiPV 3; healthy control 0/10. Page: WARNING_multipv_hash.md (also carries the milder
  256 MB depth warning: 5,395-47,818 nodes vs 288,912, no zero-node failure).
- S-C27/S-C28 (confirms seat 02): MultiPV x Hash depth collapse; one cell's move 46 cp worse, 203-335 cp on 2 of 6
  positions. Advice: MultiPV 1 at any Hash, or Hash <= 16 MB with MultiPV > 1.
- S-F43 (mine): NO PC20 switch closes empty-searchmoves->0000, ucinewgame reset, hashfull window, go-nodes-1.
- S-C20 (21-F11): checkmated root scored `mate 0`, still live on the PC. S-C26: go nodes 1..25 -> first legal move,
  0 info lines, boundary exactly 26, live on the PC. S-C11: searchmoves -> 0000 on a 20-move board, 64 info lines
  at 0 nodes. S-C10: hashfull samples 1000 clusters. S-C3: ucinewgame resets the board.
- S-F49 (mine): clock path uses 2-5% of budget, depth flips 17<->18 run to run — clock matches not exactly replayable.
- S-F48 (mine, CLOSED as an area): go softnodes deterministic 12/12 incl. node count, finished depths only, overruns
  N by +5.4% to +106%.

REPAIRED ON THE PC / RECLASSIFIED (each with its state)
- S-F45: fifty-move band RETIRED as a defect — cp 0 from halfmove 91 is correct chess (Opus inequality: measured mate
  = 15 plies, fits only at 85). S-C25 now documents behaviour, not a fault.
- S-F46: thread variance is DESIGN, not a defect. Kept: above Threads 1 the MOVE varies (3 moves in 5 runs).
- S-C1/S-C4/S-F13: base-tree only (drawn-root doors closed on the PC); seat 01's patch is insufficient on 6b98f217 —
  a statement about that patch, NOT about the PC.
- S-F38/S-F34a (mine): `MateAlphaGuard true` ALONE is the mate-distance fix; PC20 gives the same answer but is not
  the cause; the other five extras alone LOSE the mate (cp -3122).
- S-F22/S-F47 (mine): mate distance 8 plies proved; the PC's `mate 8` at hm85 is REAL (False at 1..13 plies, True at
  15) — but one board for the PC, seat 08's 08-F23 and seat 01's S-F49 are against/null, so NO general strength claim.
- S-C18 (confirms seat 25): ladder reproduces bit-stable at Threads 1; PC correct at every depth 12-22.

INFRASTRUCTURE CONTRIBUTED
- S-F44 regime ground truth (defaults e2e4/cp30/56720 on BOTH builds; S14 d2d4/cp24/22459; PC20 d2d4/cp25/21600) with
  the trap that the BASE build answers `unknown option` for all five PC20 names, so "PC20 on the base tree" = S14.
- S-F42 the "S14" mislabel is ONE line swarm-wide. S-F36/S-F39/S-F41 thread audit + RERUN_QUEUE.md (S-F41 corrects my
  own 122-line count: it includes false positives). S-F30 planting controls exposed a crash/hang mislabel in MY OWN
  fuzz classifier. S-F23/S-F27/S-F14 three protocol limits. S-F32 PC build verified 8/8.

MY OWN ERRORS/WITHDRAWALS (on the record)
- S-F21 WITHDRAWN (claimed a missed mate on a board with no forced mate). S-C13's "rate not reproduced" WITHDRAWN
  (seat 06's 28.6% reproduces exactly, S-C16). Two job16 scripts discarded (line did not reach mate). S-F37 reported
  only after planting. A warning-page draft carried an unmeasured "second position reproduced it" sentence: removed,
  measured, and it did NOT reproduce — the page now says so.

NOT DONE: the three competing drawn-root patches were never built and compared (owner's decision); no GUI test after
0000; no Windows build; class-test generality rests on 6 positions, the load measurement on 1 position at 2048/8.

Branch for-fable-and-opus/swarm-20, tree clean, everything pushed. FINAL_REPORT.md holds the earlier detailed report.

## 2026-11-16T23:29:08Z window continues — MultiPV warning widened to 10 positions
- **S-C32** (10 G-set positions, 5 fresh processes/cell = 50 runs/cell, Threads 1, `go wtime 5000`):
  - **healthy (Hash 16 + MPV 1): 0/50 zero-node, 0/10 collapsed, depth 14-17 — perfectly clean.**
  - **Hash 2048 + MPV 2 / 3 / 8: the DEPTH COLLAPSE is UNIVERSAL — 10/10 positions at every MultiPV value, depth 1,
    nodes 22-595 vs a healthy 176,257-613,767 (about a thousandth of the search).**
  - **zero-node is RARER than I implied: 2/50 runs, 2/10 positions, only at MPV 2; 0/50 at MPV 3 and 8.**
- So the warning was **broader** on collapse and **narrower** on the no-search failure. The owner page
  (`WARNING_multipv_hash.md`) now leads with the collapse, demotes the 0-node answer to secondary with the load
  result (1/10 -> 6/10) as why it still matters, and states the healthy control is clean in the wider sample.
Next: continue within the window (to 2026-11-17T10:18Z) — next is the same ten-position method at Hash 256/512 to
find where the collapse begins, since 256 MB + MPV 3 showed only a partial collapse earlier.

## 2026-11-16T23:31:39Z collapse boundary measured — advice corrected to a two-tier recommendation
- **S-C33**: MultiPV 3, 10 positions per Hash, pre-stated rule, Threads 1. Healthy (Hash 16 + MPV 1) median depth 17.
  At MPV 3: **Hash 16 -> 13.5 usable, 64 -> 11.5, 128 -> 11.0 (largest SAFE), 256 -> 4.0 UNUSABLE, 512 -> 1.0
  UNUSABLE (all ten positions depth 1)**. So the collapse is a **CLIFF between 128 and 256 MB**, with a gentle
  gradient below it.
- **Advice corrected and now two-tier** (owner page updated): 1) **MultiPV 1 at any Hash** — unaffected at every size;
  2) **MultiPV > 1 only with Hash <= 128 MB** (I had been saying <= 16 MB — stricter than the evidence);
  3) **never Hash >= 256 MB with MultiPV > 1**. Caveat on the page: "safe" = usable, not equal to MultiPV 1 — MPV 3
  at Hash 16 still gives up ~3.5 plies.
Next: continue in the window; the warning page is now fully supported by 10-position data at both the catastrophic and
the boundary end.

## 2026-11-16T23:33:05Z safe limit is MultiPV-dependent — corrected again by measurement
- **S-C34**: the "128 MB" limit I reported an hour ago was measured at **MultiPV 3 only**. At **MultiPV 8**, same
  10-position method: Hash 16 -> median 11.0 SAFE, 64 -> 9.0 SAFE, **128 -> 6.0 UNSAFE**, 256 -> 2.0, 512 -> 1.0.
  **So the safe limit is 128 MB at MPV 3 but only 64 MB at MPV 8** — the cliff moves left as MultiPV rises.
- Owner page now: (a) opens with the actionable line — *multiple lines -> Hash 16 MB (least-lossy); big Hash ->
  MultiPV 1; never both*; (b) carries BOTH MultiPV columns in one table so "128 MB" cannot be read as applying to
  MPV 8.
- General rule that survives: **big Hash + multiple lines is the incompatible pair**; 256 MB+ with any MultiPV > 1 is
  unusable.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:37:00Z CAUSE FOUND AND REPAIR CONFIRMED — the MultiPV collapse is fixable
- **S-C35** (independent: my own build of seat 30's patch, 5 fresh processes/cell, Threads 1):
  - CAUSE verified by reading the source: `src/search.cpp:2879 alt_shared->tt.clear();` sits inside the per-line
    loop opened at **2851**, so a FULL-TABLE clear runs once per extra PV line **per depth**.
  - REPAIR reproduces seat 30's exact figures: Hash 256 MPV 3 shipped depths **[11,11,11,7,11]** nodes
    [47818/5395] (unstable) -> repaired **[13,13,13,13,13] / 106863** (stable); Hash 512 shipped **[1,1,1,1,1]/220**
    -> repaired **[12,12,12,12,12] / 71070**.
  - GATES: repaired build keeps **all four honesty pins** (312866/862329/3024920/4865609); the **MultiPV 1 path is
    byte-identical** on both builds (depth 17, 288912 nodes, 3/3 at Hash 16 and 512).
- Owner page now records the cause and repair, so the warning is no longer "avoid this setting" but "here is why and
  here is the fix". Adoption remains Opus's call. Did NOT re-run their 2.0-4.2x timing table.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:37:13Z page opening now states cause-known / unadopted / strength-unmeasured
- Owner page opens with: cause known (`src/search.cpp:2879 alt_shared->tt.clear()` inside the per-line loop at 2851),
  a patch exists that restores depth 12-13 at Hash 256-512 with pins unchanged and MultiPV 1 byte-identical, but it
  is **UNADOPTED** and its **strength effect is UNMEASURED** — "I did not measure whether it makes the engine
  stronger, only that it stops the collapse and is reproducible". Same sentence added to the later repair section so
  it cannot read as endorsing a strength gain.
- **No timing number added**: I did not re-run seat 30's 2.0-4.2x table; a weak timing claim on this shared box would
  be worse than none.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:38:48Z cross-check: clock-table DEPTH is warm/cold dependent by ~2 plies
- **S-C36** (seat 05's S-F51 inc-60 cell, 10 G-set positions, PC r15 + PC20, Threads 1, Hash 16):
  **wall time agrees** (my median 211 ms vs their 202 ms) but **depth does not** (my 18 vs their 22) — and the cause is
  measured: fresh process per position -> median **18**; ONE warm process -> median **20**. **Warm gains +2 plies at
  the same wall time.** Their note says runs were "SEQUENTIAL"; a warm run lands where their 22 sits.
- NOT calling their numbers wrong: the depth column of a clock-based table depends on process discipline, the same
  warm/cold class as seat 10's node rule — now shown to affect DEPTH.
- For the owner: his matches run many moves in ONE process, so **warm depth (~20) is the match-realistic figure**; my
  earlier fresh-process S-F49 (17-18) answers "how deep does a cold engine get" instead. Both stated in the file.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:39:07Z RULE added to the page: every clock-based table states cold/warm
- **S-F51**: the page now carries a titled rule — same cell (6 s + 0.06, MPV 1, Hash 16, 10 game positions): fresh
  process per position -> median depth **18**; one warm process -> median depth **20 (+2 plies, same wall time)**.
  Same class as the node-count warm/cold rule, now shown to affect **depth**. Therefore "depth N at clock T" is not a
  number unless it says cold or warm; the PC's matches are warm (one process, many moves), so **warm is
  match-realistic**.
- This reconciles seat 05's depth 22 with my 18 without either being wrong (theirs warm-style, mine cold), and I added
  **S-F49a** qualifying my own earlier clock finding so its depth column is not read as match behaviour.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:43:21Z leaked-process disclosure + collapse is load-INDEPENDENT + tie-break closed
- **FOUND A LEAKED `forge` PROCESS OF MINE** pinning a core at 97-99% for 3,400 s (~22:45Z-23:44Z), orphaned from an
  earlier backgrounded heredoc. It produced one bogus "warm escapes collapse, median 15.5" probe, which I did NOT
  report and have **WITHDRAWN**. Killed it and its parent; verified 0 forge processes and loadavg ~1.5 before
  re-measuring. **Numbers I took between ~22:45Z and ~23:44Z are suspect and I say so in the file.**
- **S-C37**: the MultiPV collapse is **load-INDEPENDENT** (quiet median depth **1.0**, under 3 hogs **1.0**), so the
  warning needs no "busy machine" qualifier and stands unqualified.
- **S-C36a**: my S-C36 warm/cold result fell inside that window, so I re-ran it clean: FRESH median **18**, WARM
  median **20 — +2 plies, unchanged.** It survives contamination.
- **S-C38**: another seat's matched pair (3 vs 5 legal moves) closes the tie-break half I could not test; recorded WITH
  its caveat — this shows the PROTOCOL cannot distinguish the two tie rules, NOT that they are identical.
- **LESSON in the record for every seat: check `ps | grep forge` and `/proc/loadavg` before and after any timing run.**
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:43:53Z this box is MINE ALONE — 'other seats affected' withdrawn (S-C37a)
- Evidence: hostname `cursor` (per-agent cloud VM); `/agent/repos/dwqww/forge-combo29/swarm/` contains ONLY `20`;
  box-wide `find` returns one swarm dir; one user, one agent session; no other seat's engines in the process list.
- So my S-C37 clause "including other seats' runs at the same wall-clock moment" was **WRONG and is WITHDRAWN** —
  the leak degraded only MY measurements. Original line annotated in place so the clause cannot be quoted.
- The hygiene lesson stands but is about **each seat's own box**: run `AUDIT/machine_clean.sh` (exit 0 = fit to
  measure; checks busy forge procs, any >50% CPU process, loadavg vs cores) before trusting a timing/depth number.
- S-C38 (tie-break) keeps its caveat as the lead: the PROTOCOL cannot distinguish the two tie rules, which is NOT the
  same as the rules being identical.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:47:21Z one-sided clock CONFIRMED with the qualifier that reconciles both seats
- **S-C39**: a one-sided `go` clock DOES hang (20,003 ms, 0 nodes) — but **only when the omitted clock belongs to the
  side TO MOVE**. White to move: `go wtime 2000` fine (86 ms/149,020) while **`go btime 2000` HANGS**. Black to move:
  `go btime 2000` fine (54 ms/91,990) while **`go wtime 2000` HANGS**. `go wtime 0 btime 0` answers in 4 ms.
  RULE: white needs `wtime`, black needs `btime`, both is always correct, only-the-opponent's always hangs.
- This reconciles seat 30's finding with my earlier non-reproduction (I had tested the SAFE direction), and explains
  why such a bug looks like a random hang: a per-side `go` builder forgets one clock and hangs on exactly one colour.
- **machine_clean.sh fixed**: it was flagging a DEFUNCT (zombie) engine as busy; zombies hold no CPU and are now
  excluded. Contract unchanged: **exit 0 = fit to measure**.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:48:25Z S-C20 withdrawn; the surviving reporting defect is now its own LIVE finding (S-F52)
- **S-C20 WITHDRAWN** (and its original line annotated in place with the wrong reasoning struck through, so it cannot
  be quoted as current): `score mate 0` on a mated root is CORRECT UCI — `mate y` is for the side to move, so y=0 means
  already mated. Seat 21's 21-F11 WITHDRAWN, seat 25's S-F6 superseded, seat 11's measurement credited. My own ladder
  re-measured: checkmated -> `0000`/`mate 0`/0n; mate in 1 -> `d1d8`/`mate 1`/140n; **stalemate -> `0000`/`cp 0`/0n**;
  KQvK -> `h6f8`/`cp 1131`/1836n. Checkmate and stalemate are reported DIFFERENTLY ON PURPOSE.
- **S-F52 (LIVE, kept separate on purpose)** — the reporting VOLUME is still wrong: on a terminal root the engine
  searches **0 nodes** but emits **one info-depth line per depth**, and with `nodes`/`movetime` there is no depth limit
  so it emits **64 identical lines** (`go depth 1/5/20` -> 1/5/20 lines; `go nodes 100` and `go movetime 50` -> 64).
  A GUI reads "depth 64"; the `nodes 0` is easy to miss. Stalemate behaves identically with `cp 0`, so it is the
  terminal-root path generally. Fix direction: emit ONE line there — a reporting change that cannot move a node count.
- **machine_clean.sh**: defunct (zombie) processes no longer fail the gate — a zombie holds no CPU. Exit 0 = fit.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:48:40Z the 64-line volume is ONE reporting habit across three zero-node paths (S-F53)
- **S-F53**: S-F52 is not a terminal-root quirk. **Any path that reports without searching emits one info-depth line
  per depth, capped at 64 when no depth is given.** Verified on BOTH builds, machine certified clean (exit 0):
  `go depth 2 searchmoves` -> 2 lines at 0 nodes (base and PC r15); **`go searchmoves` and `go nodes 100 searchmoves`
  -> 64 lines at 0 nodes on base AND PC r15**; terminal root behaves the same (`mate 0` / `cp 0`, 0 nodes).
- So the three known zero-node paths — terminal root, empty restriction, bare `go searchmoves` — share ONE cause and
  ONE fix direction: emit one line instead of one per depth. The PC r15 patch changes none of them.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:49:17Z S-F52 reconciles seat 25; two defects in my own FINDINGS file fixed
- **S-F52 reconciliation** (as requested, both readings true, neither supersedes): seat 25's point is the ANSWER is right
  at the requested depth, so nothing downstream breaks; mine is the LINE COUNT misreports how much search happened.
  **Cosmetic for a consumer of `bestmove`/`score`; NOT cosmetic for a consumer of `depth`.** Consumer cost kept as:
  **64 false progress reports, with the `nodes 0` easy to miss.**
- **Own-file defects found while consolidating, both fixed:** (a) a **duplicated S-F52 row** (an earlier heredoc appended
  the FINDINGS line then failed before writing the job file, so I re-appended) — dedup, 98 -> 97 rows; (b) a **stale
  status cell on the original S-C20 row** still saying "confirmed and STILL LIVE" — now leads with WITHDRAWN, and the
  withdrawal row's id cell reads `S-C20 WITHDRAWN` so a skimmer sees it in column one.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:49:53Z METHOD.md + findings_lint.py; the lint found a third defect on its first run
- **Rule recorded** (METHOD.md rule 1): write the finding row and its job file TOGETHER, or verify the row count after
  any append — one half-failed heredoc left the same finding twice plus a stale "STILL LIVE" status, both invisible to
  a normal read.
- **AUDIT/findings_lint.py** (exit 0 = clean): duplicate ids only as retraction pairs; no retracted id cell with a bare
  NEW/LIVE status; no malformed rows. **First run caught S-F28 had only 3 cells (no evidence, no status)** — fixed, now
  CLEAN. My first linter version wrongly flagged four innocent rows that merely MENTION a withdrawal; tightened, because
  a linter that cries wolf gets ignored.
- **AUDIT/METHOD.md**: 12 rules in three groups (writing / measuring / correcting myself) + the four tools with their
  exit-code contracts: hardened.py, machine_clean.sh, findings_lint.py, parse_audit.py & bundle_audit.py.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:52:57Z the repair costs nothing at safe Hash sizes and gains +2.5/+3.0 plies
- **S-C40**: shipped vs repaired, 10 G-set positions, `go wtime 5000`, MultiPV 3, Threads 1, pre-stated cost rule.
  Medians: Hash 16 **13.5 -> 14.0 (+0.5, neutral)**; Hash 64 **11.5 -> 14.0 (+2.5)**; Hash 128 **11.0 -> 14.0 (+3.0)**.
  **No cost at any safe Hash** — the missing number behind the page's "strength effect unmeasured" caveat.
- **New insight:** the repaired build is **FLAT at ~14 plies from Hash 16 to 128** while shipped decays 13.5 -> 11.5 ->
  11.0, so **the multi-PV gradient in my own S-C33 is mostly the per-line `clear()`, not the table size**.
- Page updated: "what IS measured (no cost, +depth at safe sizes)" vs "what is NOT (stronger in PLAY — depth at a fixed
  clock is not a match result)". Advice unchanged: **MultiPV 1 at any Hash** is least-lossy.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:55:28Z my own flat-14 explanation PARTLY REFUTED by its own prediction (S-C41)
- Prediction tested: "if the gradient is the per-line clear(), the REPAIRED build's depth should be FLAT in Hash."
  Repaired, MultiPV 3, `go wtime 5000`, Threads 1, 10 positions: Hash 16/64/128 -> **14.0 / 14.0 / 14.0 (flat)**,
  **256 -> 12.0, 512 -> 10.0 (declining)**.
- So **mostly** the clear — about 3 of the 4-5 plies at Hash 128 (shipped 13.5/11.5/11.0 becomes flat 14.0) — with a
  **residual table-size cost of ~2 plies per doubling above 256 MB** that the clear() removal does not touch
  (allocation, cache/TLB pressure on 4 cores). My S-C40 wording was right in direction and too absolute; corrected in
  both the finding and the owner page.
- Refined takeaway: the patch is still worth having (no cost at safe sizes, +2.5-3 plies at 64/128) but **does not make
  a 2 GB table as good as 16 MB**, so "huge Hash with MultiPV" stays a bad idea even repaired.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:56:58Z residual MPV cost is a SECOND FULL-SIZE TABLE, not cache pressure (S-F55, refutes my own guess)
- Control that settles it: on the REPAIRED build, **MultiPV 1 is FLAT in Hash — 17.0/17.0/17.0/16.5 at Hash
  16/128/512/2048** — so a 2 GB table costs a normal search nothing here. My "cache/TLB pressure" guess was refuted by
  its own control.
- Source `src/search.cpp:2726-2732`: `alt_shared = std::make_unique<SharedSearchState>(hash_mb)` — with MultiPV > 1 the
  engine allocates **a SECOND table the same size as the main one**. At Hash 2048 that is two 2 GB tables allocated and
  first-touched before the first line is searched — which is why **the repaired build still collapses at 2048**.
- Gradient has TWO causes: (1) per-line `tt.clear()` (~3 of 4-5 plies at Hash 128, removed by seat 30's patch);
  (2) the second-table allocation (residual above 128 MB, NOT removed). Further lever would be sizing/sharing that
  table, not another `clear()`.
- Owner takeaway kept: patch is worth having, but **does not make a huge Hash as good as a small one**.
- PROCESS: the missing-directory heredoc mistake recurred and duplicated the S-F55 row; **findings_lint.py caught it
  immediately** — the defect class the rule and tool exist for.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-16T23:58:32Z the lever WORKS — mechanism confirmed by intervention (S-C42); not proposed for adoption
- One change to the repaired tree: cap the alternate table at 64 MB instead of matching the main one.
  MultiPV 3, `go wtime 5000`, Threads 1, 10 positions — medians **repaired vs capped**:
  Hash 128 13.5 -> **14.0**; 256 12.0 -> **14.0**; 512 **6.5 -> 14.0**; **2048 1.0 -> 14.0**.
  Depth is **FLAT at 14.0 across a 16x Hash range**, including 2048 MB where repaired-uncapped collapses to depth 1.
- So S-F55 is confirmed BY INTERVENTION, not correlation: seat 30's patch is **necessary but not sufficient** (per-line
  `clear()`, ~3 plies at 128), and the alternate table's **SIZE** is a second independent cost. The lever is sizing that
  table, not another `clear()`.
- **CAVEAT relayed and recorded: this is a diagnostic experiment, NOT a patch I propose adopting.** Capping could
  degrade the ALTERNATE PV lines (smaller table for them), and I measured only the MAIN line's depth — not line
  quality. For a MultiPV analysis feature that is the wrong thing to ship untested.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-17T00:00:35Z line quality MEASURED — the cap is NOT a fix (S-F56); open requirement stated with an acceptance test
- Per-line scores, Hash 2048, MultiPV 3, 5 positions, repaired-uncapped vs capped: pos 3 improves **201->278** /
  **188->262**; pos 4 degrades **-528->-660** / **-536->-733**; pos 5 degrades **-241->-573** / **-278->-1029**.
  **Large differences in BOTH directions** — the cap changes exactly the output MultiPV exists to provide.
- **Honest counter-case recorded**: on pos 1 the UNCAPPED build published NO lines at all (depth 1) while capped reported
  three. So the cap is not uniformly worse — it is **unpredictable**, which is worse for a feature.
- **Open requirement, now precise with an acceptance test**: a real fix must restore main-line depth at large Hash
  **without moving the alternate lines' scores** (share one table with disjoint generations, or size the alt table
  adaptively). I have built and tested neither — handing over a requirement + its test, not a patch.
- Caveat is now a **column in the table row** (`⚠ is this a fix? | NO — diagnostic only`) plus a callout, so the flat
  14.0 cannot be skimmed as a fix.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-17T00:01:46Z I built the share-table fix — it restores depth and STILL fails the line-quality test (S-F57)
- Change: `SharedSearchState` borrows the MAIN table instead of allocating a second one. Hash 2048, MPV 3, 5 positions:
  **main-line depth 1 -> 11-15 (that half PASSES)**, but alternate-line scores still move by up to **~900 cp**
  (pos 5 line 3: -280 -> -1185), in both directions (pos 3 improves ~90 cp).
- WHY it fails and it is structural: a shared table makes the alternate line probe bounds computed for a **different
  root restriction**, so its tree changes by construction — the mechanism my own S-C23 measured for `searchmoves`.
- **Both named directions now fail**: fixed-64MB cap (lines <=775 cp, S-F56); share one table (lines <=900 cp, S-F57).
- **Narrowed requirement**: the alternate line needs its **OWN table that is cheap to allocate** — i.e. lazy/adaptive
  sizing (allocate small, grow if needed), NOT built; or accept the depth cost at very large Hash (status quo). The
  acceptance table remains the pass/fail criterion.
Next: continue in the window (ends 2026-11-17T10:18Z).

## 2026-11-17T00:03:16Z CORRECTION: own-8MB-table PASSES; my job-67 "fail" used the collapsed build as baseline (S-F58)
- Candidate: alternate line keeps its **OWN** table capped at **8 MB**. Correct reference = the **HEALTHY** build
  (Hash 16), NOT the collapsed Hash-2048 build. Hash 2048, MPV 3, 5 positions:
  alternate lines **identical to healthy on 4 of 5 positions (0 cp)**, **47 cp worst case**; main depth **1 -> 13-15**.
  Both halves of S-F56's acceptance test PASS (vs 775-988 cp for the two rejected variants).
- **MY ERROR**: job 67 compared the candidate to a build that had collapsed to depth 1 with no usable lines, so any
  working candidate "differed" by hundreds of cp. Same class as S-C20 — a comparison whose reference I had not checked.
  Lesson recorded: **before calling a candidate worse, check that the REFERENCE is working.**
- **S-F56's requirement IS satisfiable**: alternate line keeps its OWN table (independent bounds) but sized SMALL.
  Sharing fails (bounds from a different root restriction); own-and-small passes.
- Still NOT a proposal: 5 positions/one clock/MPV 3; 47 cp outlier shows invariance is not exact; **tolerance is an
  owner decision**; MPV 2/8 and 8 MB saturation untested. Next step = wider sample at a stated tolerance.
Next: continue in the window (ends 2026-11-17T10:18Z).
