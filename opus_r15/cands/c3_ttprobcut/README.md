# C3 TtProbcut - cut from a slightly too shallow TT lower bound far above beta (UNPROVEN)

Gate line: engine A = `D:\o15\cands\c3_ttprobcut\forge_ltopgo_c3tpc.exe` + `setoption name TtProbcut value 360`,
engine B = the lock. Exe sha256, ON bench and check results: `D:\o15\cands\INDEX.md` and `logs/RESULT.json`.
Patch: `c3_ttprobcut.patch` (src/search.cpp only, +11), applies with `patch -p1` to git d4f4312.

## What it changes
Right after the lock's TT cutoff (which needs `tt_depth >= depth`): at a non-PV, non-root node without an excluded
move, a TT entry with a usable non-mate score, a lower (or exact) bound, `tt_depth >= depth - 3`, halfmove clock < 90
and `tt_score >= beta + margin` (beta not a mate score) returns `beta + margin` without searching. Also in check (no
static evaluation is needed). Option `TtProbcut` = the margin in cp (spin 0..1000, default 0 = off; ON line 360 =
twice the lock's ProbcutMargin 180).

## Why it should gain
When an earlier search at most three plies shallower already proved this position to be at least beta + 360 - more
than twice the lock's own ProbCut margin above beta - the full-depth search will almost surely fail high again, yet
the lock's TT cutoff needs a stored depth of at least the current depth and so searches these nodes again from the
start. Taking the stored bound as the cut saves those re-searches (ON bench d22 20,921,486 vs 34,048,354 nodes), the
margin covers the depth deficit the same way the lock's ProbCut margin covers its reduced verification search, and
the value returned (beta + margin) is a lower bound below the stored one, so it never claims more than the table
knows.

## OFF identity
`TtProbcut 0` fails the first test: the lock's search. Kit OFF node identity ALL OK, bench d11-d22 + perft = pins.

## Own review (structured self-review, NOT independent)
- Overflow: `!is_mate_score(tt_score)` gives tt_score < MateInMaxPly, and the cut needs beta + margin <= tt_score, so
  the returned value is a normal score below MateInMaxPly; `beta` is not a mate score either.
- Graph history: the same `halfmove_clock() < 90` guard as the lock's TT cutoff; `score_usable` already excludes
  entries stored with a different 50-move context.
- PV nodes, the root and singular verification searches (excluded move) are never cut; the PV stays exact.
- Bound test `(tt_bound & BoundLower) != 0` accepts lower and exact bounds (BoundExact = 3 has the lower bit).
- In check: allowed - the stored bound belongs to the same position; nothing else of the node is read.
- Risk: positions where three more plies would find a refutation of a large fail-high (zugzwang-like, deep tactics);
  the margin and the 3-ply limit bound it. NMP verification and ProbCut keep their own guards.
- PGO cold-path note as for every option line.

## Check results (generated)

- exe `D:\o15\cands\c3_ttprobcut\forge_ltopgo_c3tpc.exe` sha256 `4c48a25bdc051659795b653e3b30bf5a6063bf84813c9f0e8ab1bbb733a87723` md5 `92b69c3f81cb1b9a86e5106527674df8`; kit pc1 = pc2 `4c48a25bdc051659795b653e3b30bf5a6063bf84813c9f0e8ab1bbb733a87723`
- ON bench d11 / d13 / d16 / d20 / d22: 322040 / 845712 / 2757689 / 9154533 / 20921486; OFF = the lock pins; perft 4865609 / 193690690 both ways
- cand_pack checks: patch_applies PASS, cleanroom_lint PASS, kit_build PASS, pc1_equals_pc2 PASS, kit_identity PASS, kit_vfmadd0 PASS, kit_missing_profile0 PASS, kit_on_live PASS, exe_copy_sha256 PASS, pin_off PASS, pin_on_live PASS, smoke PASS
- smoke with the fixed clock (12:37 fix): PASS - 21 games, 2574 plies, illegal 0, crashes 0, hangs 0, time losses 0
- R13 cand_checks (T1 / T4 movetime smoke with perft-1 legality, mate probe 22 positions at 3M nodes): FAIL; mates OFF 19 / ON 21; strict-rule flips: mate lost: TtProbcut=360 3k4/8/8/8/7r/8/8/6K1 b - - 0 1 OFF mate 15 ON cp 549
  - 30M re-probe (lost) `3k4/8/8/8/7r/8/8/6K1 b - - 0 1`: 3M OFF mate 15 / ON cp 549; 30M OFF mate 11 / ON mate 11 -> horizon flip (both find it at N)
  - 30M re-probe (gained) `8/1r6/8/8/8/4K2k/8/8 b - - 0 1`: 3M OFF cp 474 / ON mate 17; 30M OFF mate 14 / ON mate 13 -> horizon flip (both find it at N)
  - 30M re-probe (gained) `8/8/5K2/7r/8/8/k7/8 b - - 0 1`: 3M OFF cp 503 / ON mate 15; 30M OFF mate 14 / ON mate 14 -> horizon flip (both find it at N)
  - 30M re-probe (gained) `8/3k4/5R2/8/8/8/8/2K5 w - - 0 1`: 3M OFF cp 544 / ON mate 25; 30M OFF mate 14 / ON mate 13 -> horizon flip (both find it at N)
- CI ASan+UBSan self-play: run 41628366851 success on 9fc59ea3c497 (patch sha256 = the built one)
