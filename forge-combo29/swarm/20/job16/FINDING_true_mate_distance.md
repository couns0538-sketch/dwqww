# seat 20 — job 16: the true mate distance on the S-F19 board is 8 plies, not 14

Result: on `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` **black forces mate in exactly 8 plies** (`mate -4`). The engine's
depth-12 answer of `mate -7` (= 14 plies) **overstates the distance by 6 plies.**

This is proved both ways:
- an exact predicate `black_mates_in(fen, n)` (black delivers mate in at most n plies against EVERY white defence)
  returns True at n=8 and False at n=2,3,4,5,6,7 — so 8 is the *shortest* forced distance;
- a concrete 8-ply line is exhibited and replayed with python-chess, every move legal, ending in checkmate:

```
1. white c2c3   2. black d2d1q   3. white c3b2   4. black e2d3
5. white b2a2   6. black d3c3    7. white a2a3   8. black d1b3#   <- checkmate verified
```

Raw: `out_proof.txt`. Script: `prove_mate_line.py` (contains `assert alllegal and rb.is_checkmate()` so it cannot
print a RESULT unless the line really mates).

## Two of my own scripts are DISCARDED from this job
- `mate_solver.py` and `solver_line_fast.py` used a "mate distance" recursion whose extracted line did **not** end
  in checkmate (`final checkmate: False`). A distance no line realises is not a proof. Their outputs
  (`out_solver_fast.txt`) are kept only as evidence of the error; **no number from them is recorded.**
- `verify_sf20.py` tested whether WHITE forces the mate, when `mate -N` means WHITE is the side being mated — the
  wrong side. `verify_sf20b.py` replays the engine's own 14-ply PV, which does verify as a real checkmate, and that
  is why the *engine's* line is internally consistent while its *distance* is wrong.

## What this means
`mate -7` at depth 12 is not "a truncated PV" — the engine's own PV really does mate in 14 plies. The engine simply
does not find black's faster 8-ply mate at depth 12. At depth 16 with default settings it reports `mate -4`, i.e.
the correct distance, so this is a **depth-limited miss**, not a wrong mate score.

This strengthens S-F18/S-F20 (`LmpBase=8` replaces the mate with cp at depths 10–12) only in the sense that the mate
being replaced is real and forced; it does not change their measurements.

## Harness note (19-F12 discipline)
Every engine number used in this job came from `AUDIT/hardened.py`, which reads stdout until `bestmove` before
sending `quit`. Re-checked: startpos `go depth 12` → `e2e4`, cp 30, **56,720 nodes**, 12 depth lines.

## Commands that show it again
```
python3 prove_mate_line.py "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1" 16
python3 -c "import sys; sys.path.insert(0,'forge-combo29/swarm/20/AUDIT'); from hardened import run_search; print(run_search('/agent/repos/build-base/forge','8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1','go depth 16'))"
```
