# SEAT 15
- seat: 15
- branch: for-fable-and-opus/swarm-15
- area: 5 (PRINCIPAL VARIATIONS AND SCORES)
- seed: 1501

## 2026-11-16T22:23:47Z

PC BUILD PHASE. Build verified: patch from FABLE_TO_swarm_5.md, sha256 d6bd72c531f785f4…,
11 files, `patch -p1` clean, built with -DFORGE_MATE_ALPHA_GUARD=1. All nine known numbers match
(none / S14 / PC20). **Threads 1 in every run of mine; audited, none used more.**

DRAWN-ROOT THREAD (the priority question) — ANSWERED:
- mate-in-1 at halfmove 100: PC `mate 1` / 144 nodes / a1a8  |  base `cp 0` / 0 nodes / a1b1  -> REPAIRED
- pawn-move mate a7a8=Q# at halfmove 100: PC `mate 1` / 265 nodes  |  base `cp 0` / 0 nodes  -> REPAIRED
- **THE COMBINED PATCH IS NOT NEEDED FOR THE PC BUILD; it is base-tree-only.** (15-F12)

TERMINAL SCORES — I WAS WRONG, NOW RETRACTED (15-R1):
- `score mate 0` at a checkmated root is CORRECT. python-chess's own parser turns the engine's
  exact line into `PovScore(Mate(-0))`, `.mate()=0`, `.is_mate()=True`, converted **-100000** =
  the worst possible score, and its documented ordering is `Mate(-0) < Mate(-1) < … < MateGiven`.
- All three terminal cases are correct on BOTH builds: checkmate `mate 0`/`0000`, stalemate
  `cp 0`/`0000`, insufficient material `cp 0` + a real move. No inversion. 15-F13 WITHDRAWN.
- 15-F5 keeps only its real half: a terminal root walks the depth ladder to 64 with 0 nodes.

REPETITION (open, 15-F16): PC build SEARCHES a thrice-repeated root (`cp 23` / 13,424 nodes) and
four-times too, while the base tree declares the third occurrence drawn (`cp 0` / 0 nodes). Only the
history length varied; counts verified with python-chess. Two readings I cannot separate (check does
not fire vs it needs in-search repetition) — stated as such, not claimed.

ALSO CORRECTED MYSELF (15-F17): insufficient-material roots are SHORT-CIRCUITED at 0 nodes on both
builds. I had claimed they were searched, from counting info lines instead of nodes.

Next exact command:
  cd /agent/repos/dwqww/forge-combo29/swarm/15/job4 && python3 probe2.py 'k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1' 14 --opts s14   # then the same on the PC build under PC20
  -> re-run 15-F1 / 15-F9 (mate distance) on the PC build, which is the next thing the owner needs.

## 2026-11-16T22:18:36Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:36Z

Starting the 12-hour continuation on the same seat (15), branch for-fable-and-opus/swarm-15.
Order of work from here:
1. Read every unread forge-combo29/soak_all/FABLE_TO_swarm_N.md from the lowest N to the highest.
2. Apply the FABLE_TO_swarm_5.md patch to a SEPARATE copy, build with -DFORGE_MATE_ALPHA_GUARD=1,
   check the known bench numbers it states.
3. Re-run my own findings on the PC build under settings PC20 and state build+settings per finding.
4. THE CYCLE as before; STATUS every 25 minutes at most, even mid-job.

State at the start of the continuation: 13 findings + 4 checks pushed; all three area-5 jobs and a
job-1 repeat done with reports; harness fidelity proven at four (set,depth) points at diff 0.

## 2026-11-16T22:15:27Z — 22:30 checkpoint: 12 findings, 4 checks, 5 reports

DONE — every one pushed with raw files:
- STEP 1 seat 15. STEP 2 build 6b98f217, sha256 e06310ec…16a83, honesty 4/4 (HONESTY.txt, with the
  default-regime caveat added after 15-C3).
- **HARNESS FIDELITY, four exact matches** (15-F10): O d12 9,500,069 | G d12 18,466,239 |
  O d14 21,812,100 | G d14 43,345,893 — every difference 0.
- job 1  (REPORT_job1.md): 553 pos d12 — 0 illegal PV moves, 10 mate scores, 1 violation.
- job 1b (REPORT_job1b.md): 200 R pos seed 1511 — 8 mate scores, 0 violations, 3 truth-checked exact.
  My predictions P3/P4 were REFUTED there; recorded as such. Finding 15-F6.
- job 2  (REPORT_job2.md): 120 pos d10 — KvK/KNvK/KBvK/threefold all cp 0; KNN v K nonzero 19/20
  (15-F3); empty-pv dead draws (15-F4).
- job 3  (REPORT_job3.md): 20 terminal roots x 3 go kinds under ASan+UBSan, BOTH sanitizer proofs
  present; 60/60 bestmove 0000, 0 sanitizer lines; but 64 info lines with nodes 0 (15-F5).
- job 4  (REPORT_job4.md): O and G at depth 14 — sums exact; G gives 2 mate-fault violations, one a
  NEW position wrong by 6 moves (15-F9), and violations get more frequent with depth.

CHECKS written and pushed: 15-C1 CONFIRMS 05-F8 | 15-C2 CONFIRMS 07-F1 | 15-C3 CONFIRMS 10-F6 |
15-C4 CONFIRMS 05-F1. Two of my findings (15-F3, 15-F4) are confirmed by seat 05 (S-C5, S-C6).

Running now: nothing.

Next exact command:
  cd /agent/repos/dwqww/forge-combo29/swarm/15/job4 && python3 probe2.py 'k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1' 16 --opts s14 2>&1 | grep -E "^info depth 16 |^bestmove"

(after copying probe2.py from job1) — to see whether idx 69 self-corrects with depth as idx 192 did,
which would separate "deepening artefact" from "wrong at every depth".
