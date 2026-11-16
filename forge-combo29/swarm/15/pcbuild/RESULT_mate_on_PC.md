# Mate distance on the PC build (r15) under PC20 — my 15-F1 / 15-F9 faults are GONE

All **Threads 1**, Hash 16, fresh process per search, base tree under **S14** and PC build under
**PC20** (S14 + CuckooRep/HistRework 2/TtPruneV2/CorrHistV2/MateAlphaGuard/OwnBook false).

## 1. The two positions that carried my findings: correct on the PC build

`mate_pc.txt`, from `matecheck/pc_regimes.py`:

| position | depth | base tree / S14 | PC r15 / PC20 | verdict |
|---|---|---|---|---|
| `8/8/1p6/8/p3p3/8/2Kpk3/8 w` (**15-F1**) | 12 | `mate -12`, 18-ply PV, does **not** end in mate | **`mate -4`, 8-ply PV, ends in CHECKMATE** | **REPAIRED** |
| same | 14 | `mate -9`, 15-ply PV, no mate | `mate -4`, 8-ply, checkmate | repaired |
| same | 16 | `mate -6`, 12-ply, checkmate | `mate -4`, 8-ply, checkmate | repaired (base needs d16 to agree) |
| `k7/6R1/5N2/p4K1P/P7/8/8/8 b` (**15-F9**) | 14 | `mate -9`, 15-ply PV, no mate | **`mate -3`, 6-ply PV, ends in CHECKMATE** | **REPAIRED** |
| same | 16 | `mate -3`, 6-ply, checkmate | `mate -3`, 6-ply, checkmate | agree |

The truth values (mate in 8 plies for 15-F1, mate in 6 plies for 15-F9) were established earlier by
two independent python-chess solvers in `job4/evidence_mate_g14.txt`. On the PC build both positions
report **exactly the true distance at depth 12 and 14**, where the base tree is wrong by 5-6 moves.

## 2. The whole G set at depth 12: no mate-rule violation at all

`g14pc/analyze_pc20.txt`, 353 G positions, depth 12, PC20, same analyser that found the faults:

```
records        353
accepted       353
refused        0
A illegal_pv_moves      0
B bestmove_not_pv_first 0
C mate_len_mismatch     0          <-- base tree at depth 12 had 1 (15-F1), at depth 14 had 2 (15-F9)
   positions_with_mate_score 12
D no_info_pv_line       0
E cp_on_terminal_root   0
CONTROL planted_illegal_last_move tried 5 caught 5
```

So **12 mate scores, 0 violations** on the PC build under PC20, against the base tree's 1-in-10 at
depth 12 and 2-in-14 at depth 14. The control caught 5 of 5 planted illegal moves, so the detector
was able to fire; this zero is "shown", not assumed.

Node total for the run: 17,611,204 over 353 positions (the brief's 18,466,239 is a **base-tree / S14**
number, so it is not expected to match the PC build and does not; I state this so nobody reads the
difference as a failure).

## 3. What this means, and what it does not

- **15-F1 and 15-F9 are base-tree findings.** Both are gone on the PC build under PC20. The owner's
  PC does not have this defect in either position.
- I cannot attribute the repair to `MateAlphaGuard` specifically: PC20 sets five options at once
  (CuckooRep, HistRework 2, TtPruneV2, CorrHistV2, MateAlphaGuard). Another seat reports that
  MateAlphaGuard alone fixes one case, which is consistent with what I see, but I have **not**
  isolated it here and do not claim it. Isolating it is a clean one-option-at-a-time job.
- The finding still matters for the base tree, which is what every seat that has not rebuilt sits on.

## 4. Method notes

- Every row above came from a harness that reads stdout until `bestmove`, keeps stdin open, sets
  **Threads 1**, and treats a missing token as `PARSE_FAIL` rather than 0.
- One harness bug caught and fixed while doing this: `rep_pvloop.py` first reported numbers for a
  position the engine had **REFUSED** (`7k/8/6K1/8/8/8/8/Q7 w` — python-chess also calls it invalid,
  `side that moved left its king in check`), because it did not check the answer lines and so measured
  the stale previous board. It now detects `invalid FEN` / `invalid value` / `illegal move` / `unknown
  option` and reports `REFUSED_FEN`, and carries a startpos positive control that must search. The
  numbers from the broken version were discarded; the table above does not use them.
