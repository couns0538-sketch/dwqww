# seat 20 — FINAL REPORT (area 10: checking the others)

Branch `for-fable-and-opus/swarm-20`, tip committed with this file. Area 10, seed 2001.
Engine build: `/agent/repos/base` at 6b98f217, g++ 13.3.0, `-march=x86-64-v4`, sha256
`e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`; **honesty check 4/4**
(bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609). 4 cores.
ASan+UBSan build built and used, with the planted-fault runner proof (3 sanitizer lines on the fault copy,
0 on the real build).

## 1. What I did

Area 10's three jobs: reproduce other seats' NEW findings, recount the two helpers' reports, and check each other.
- **16 checks** written (S-C1 … S-C16), each with my own harness and a control.
- **2 helper reports recounted** from their own raw files (deepseek6 long56; glmflash5 job 27).
- **31 own findings** (S-F1 … S-F31), one **WITHDRAWN** by me (S-F21), and one of my own check readings
  **corrected in another seat's favour** (S-C16: seat 06's 28.6 % reproduces exactly on their own 353 positions).
- **3 broadcast audits** (19-F12 fabricated bestmove; silent-parse verdicts; seat 10's warm/cold node counts).

## 2. The findings that matter most for the PC

1. **The drawn-root shortcut skips the whole search.** `root_drawn` at `src/search.cpp:2250-2253` makes a position
   with `halfmove >= 100` (S-C1) or a repetition (S-C4) report `cp 0` with **0 nodes** and play its first legal
   move; at `halfmove >= 100` a mate-in-one is missed entirely. **Seat 01's patch fixes the halfmove door and does
   NOT fix the repetition door** (S-F13, proved on a rebuilt patched binary with pins unchanged).
2. **The true mate distance on the S-F19 board is 8 plies (`mate -4`), not the 14 plies the engine reports at
   depth 12** (S-F22). Proved both ways — an exact predicate (True at 8, False at 2..7) and an exhibited 8-ply line
   replayed to verified checkmate. The engine reaches `mate -4` at depth 16, so it is a depth-limited miss.
3. **Which S14 options break mate reporting** (S-F18): only three of the fourteen — `NullMoveBase=5`,
   `LmpBase=8`, `IirDepth=2`. The all-S14 `mate -12` is reached by no single option, no pair, not even the triple,
   and the effect is non-monotone (`NullMoveBase=5 + IirDepth=2` claims mate −15 in a 16-ply line, worse than the
   triple). Defaults are consistent at every depth I tried.
4. **`ucinewgame` silently resets the board to startpos** (S-C3), proved decisively on a black-to-move position
   where the engine answers a white move. This is why harnesses report false "illegal bestmoves".
5. **`bestmove 0000` on a board with 20 legal moves** for an empty or illegal `searchmoves` (S-C2, S-C11), and the
   unsearched root is dressed as a full-depth search — bare `go searchmoves` emits **64** `info depth` lines with
   `nodes 0`.
6. **`hashfull` samples only the first 1000 clusters** (S-C10): at depth 12 the node count is identical (87,135) at
   Hash 16/64/256/1024 while hashfull reads 44/12/3/1.
7. **The increment-ignored clock boundary** (S-C14, S-F26): the boundary is `Move Overhead + ~4` (first wtime where
   the increment matters: 5 at overhead 0, 14 at overhead 10, 35 at overhead 30), not the 10/11 seat 28 reported.
8. **`go movetime M` stops at M − 9.2 ms** (S-C7), a constant subtraction, exactly linear in `Move Overhead`.
9. **The fifty-move horizon reaches the root score ~10 plies early** (S-C8) with **millions of nodes and a full pv**
   — a different mechanism from the 0-node root shortcut (S-F16). A checker that tests only the score cannot tell
   them apart.
10. **`eval` is exactly colour-symmetric** (S-C6, 360/360 pairs, 0 difference) — but only if you know it is
    side-to-move relative (S-F14): a mirror must read the SAME number, not the negation. My first attempt negated
    and invented 120 false asymmetries.

## 3. What the helpers' reports were worth
- **deepseek6 long56**: 5 of 6 headline numbers match its raw file; `seqs: 0` contradicts "2,000 sequences"; its
  "ZERO illegal bestmoves" comes from a code path that cannot execute (S-F2), and it has none of the sanitizer
  proof the swarm rules require (S-F4); the run is not reproducible from the branch (S-F5). The named report
  `REPORT_deepseek6_longK.md` does not exist (S-F1).
- **glmflash5 job 27**: **every number reproduces exactly** — W-L-D, n5, Elo to 0.01, both pools, both intervals,
  all identities, and the openings are fully disjoint (S-F8, S-F9). Its hardcoded job-24 n5 arrays are truthful.
  The only note is that the brief's literal interval formula would be 2× too wide; the helper's formula is right.

## 4. My own mistakes, recorded not hidden
- **S-F21 WITHDRAWN**: I claimed the engine missed a mate in 3 on `6k1/6pp/8/8/8/8/5PPP/R5K1 w`. There is **no
  forced mate there** — black has 6 defences. I had counted white's free lines without checking whether black could
  avoid them.
- **Two job16 scripts discarded** (S-F23): their "mate distance" came with a line that did not end in checkmate.
- **A sign-convention error** produced 120 false asymmetries until I measured the convention first (S-F14).
- **My hypothesis that a shared process inflates search asymmetry is dead** (S-F25): 2/20 vs 1/20 vs 2/20.
- **A wrong timestamp** in one STATUS header (22:00Z written when the clock read 21:53Z), corrected.
- My bestmove-asymmetry rate (10.0 %) is below the 20–40 % I predicted, so **S-C13 carries my own killed
  prediction** and does not reproduce seat 06's 28.6 %.

## 5. Measurement integrity (all three broadcasts answered, folder AUDIT/)
- **19-F12** (fabricated bestmove on a mid-search `quit`): every harness of mine waits for `bestmove` before
  quitting. Two scripts were already discarded for this before the broadcast. Re-verified: startpos depth 12 =
  `e2e4`, 56,720 nodes. New driver `AUDIT/hardened.py`.
- **Silent-parse verdicts**: 7 parsing checkers fed a fake engine that answers `uciok` then nothing — **all hung,
  none printed a verdict**. No such defect, though hanging is weaker than failing loudly.
- **Warm/cold node counts**: `Clear Hash` is used nowhere in my work; every node count is from a fresh process;
  three runs of startpos depth 12 give 56,720 three times. And `bench` pins are immune to history drift
  (862,329 after 0/1/5 preceding searches, S-C12).

## 5b. Two late resolutions that the coordinator asked for (job24)

1. **S-F28 / S-F31 — the drawn-root repair, with verbatim source.** Branch
   `handoff/fable-opus-combo29-all-20261114`, commit `511d334f`, file `forge-combo29/soak_all/FABLE_TO_swarm_3.md`
   (blob `8b668cd5`, sha256 `cefd84fb…`), lines 13–18, quote: *"On the owner's PC this is REPAIRED since 15 November:
   the PC's engine searches such a root like any other (only a root with insufficient material is still answered at
   once) … Seat 20's 'the repetition door stays open' is covered by that repair. A patch for the base tree is not
   needed."* It does **not** say a patch is harmful, and it does not show the repair (no file or commit for it is in
   this repository). My **narrow** reading stands — on `6b98f217`, seat 01's patch is insufficient (measured,
   `job7/`); my **wide** reading (a live PC defect) is withdrawn. **Recommendation: hold the patch off.**
   Details: `job24/S-F28_SOURCE.md`.
2. **S-C16 — the 10.0 % vs 28.6 % conflict is resolved in seat 06's favour.** I ran *their* `G_353.fens` with
   *their* settings (depth 10, S14, Threads 1, Hash 16, OwnBook false) and reproduced **101/353 = 28.6 %** and
   **334/353 = 94.6 %** exactly, in two process arms that agreed in 353/353 rows. My 10.0 % was my 20-position
   sample; its Wilson interval (~1–32 %) overlaps their figure, so it was never evidence against them. The
   "rate not reproduced" reading of my S-C13 is withdrawn. Details: `job24/RESOLUTION_s06f6.md`.

## 6. What I did NOT do
- I did run seat 06's 353-position G set (job24, after the first draft of this report), and it reproduces their
  numbers exactly — see 5b.2. What I still have not done is test whether their set's rate holds at other depths.
- I did not bisect the 11 remaining S14 options in combination, nor find where the `LmpBase=8` mate delay ends.
- I did not write a patch for the repetition door (S-F13 only shows seat 01's patch is insufficient).
- I did not test the Windows build, or any GUI behaviour after `bestmove 0000`.
- I did not resolve what `hashfull` is *meant* to report, only what it does.

## 7. Times
Every time in my files is `date -u` output; see each `jobN/stamps.txt` and `honesty/out/stamps.txt`. (The container
clock advanced abnormally slowly during this session — several jobs reported the same wall-clock minute — so I
pushed at every job boundary rather than trusting the clock.)

## 8. Where everything is
`FINDINGS.md` (41 lines: 26 findings, 15 checks), `HONESTY.txt`, `STATUS.md`, `AUDIT/` (3 audits + `hardened.py`),
`job1`–`job21` (scripts, raw output, predictions, stamps), `REPORT_job{2,3,4,5,6,7,9,10,11,12}.md`, and the check
write-ups `jobN/CHECK_*.md` / `jobN/FINDING_*.md`.
