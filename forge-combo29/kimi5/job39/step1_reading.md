# job 39 step 1: reading — DeadMaterial's three replacement sites, the option, every
# static-eval path, every clamp a 2,000–13,000 value could cross.
Chain: 6b98f217 + pc_r15.patch (sha256 d6bd72c5…), `-DFORGE_MATE_ALPHA_GUARD=1`. File:line are
of THAT tree (file 39's "ours" numbers are r15d's = pc_r15 + a_speed + e1; eval.cpp's region is
identical line-for-line, uci.cpp/search.cpp shifted by pc_r15's/other patches' sizes).

## The three places DeadMaterial's value replaces the evaluation
1. `src/eval.cpp:587-592` in `Evaluator::static_eval_components` (starts 582): `if
   (dead_material_enabled) { int fixed = 0; if (dead_material_score(board, fixed)) {
   parts.total = fixed; return parts; } }` — this is what the `eval` command prints
   (`src/uci.cpp:742-746`: `parts.total` after "total"; theirs 833-835).
2. `src/search.cpp:1178-1181` at the top of `Worker::static_evaluate` (starts 1176), BEFORE the
   net branch at 1182 (`if (!nnue::enabled || !nnue::available()) return
   evaluator_.evaluate(board);`) and before the v3 branch 1183-1185 (`#if FORGE_NNUE_V3`,
   compiled out on this chain) (theirs 1280-1283 before net at 1284-1287).
3. `src/search.cpp:1292-1295` at the top of `Worker::corrected_eval` (starts 1290), before the
   correction-history term at 1296ff, so correction history cannot tilt a fixed value (theirs
   1414-1417).
The function itself: `src/eval.cpp:514` (`bool dead_material_enabled = false;`), `516-565`
(`dead_material_score`), declared `include/forge/eval.hpp:46-53`.

## The option
- `uci` line: `src/uci.cpp:345` (`option name DeadMaterial type check default false`) (theirs 449).
- Parsing: `src/uci.cpp:538-542`: any value but `true`/`false` → `note_invalid()` (prints
  `info string invalid value for option DeadMaterial`, 403-405); a value that CHANGES the flag
  sets it and calls `searcher.clear_hash()` (542); re-sending the current value does not clear
  (theirs 646-651).
- Unknown option names fall to the final else at `src/uci.cpp:624-627`: prints `info string
  unknown option <name>` and nothing is set (the C-ARRIVE refusal line).

## Every other place in the search that computes a static evaluation
All go through `Worker::static_evaluate` and/or `Worker::corrected_eval`:
- Quiescence stand-pat: `src/search.cpp:1668-1669` in `Worker::qsearch` (starts 1623): raw =
  static_evaluate, eval = corrected_eval(raw). MaxPly cap of qsearch: 1628 → static_evaluate.
- Main node: `src/search.cpp:1871-1872` in `Worker::search` (starts 1765): same pair; every
  consumer below (null move 1957-1967, the razoring block 1931ff, LMR, futility) reads this
  `eval` / `ss->static_eval`, never a fresh computation. MaxPly cap of search: 1779 →
  static_evaluate.
- ProbCut: `src/search.cpp:1827-1832`: `raw = hashed_eval ? tte.eval : static_evaluate(...)` then
  `corrected_eval(board, raw, ss)`. The TT-stored eval (`tte.eval`) is one written from
  static_evaluate's result through the store clamp (below), so a guard value reaches ProbCut on
  both paths.
- Null move / razoring: no new static evaluation; they read the node's `eval` from 1871-1872
  (null's reduction uses `(eval - beta)` at 1958; razoring's gate is 1931-1933).
So the three insertion points cover every static evaluation the search prints, stores, or
prunes on, as long as the guard sits at the TOP of both functions (as DeadMaterial does).

## Clamps and fixed bounds a value of 2,000–13,000 could cross
- `src/search.cpp:553-555` and `634-636`: TT store clamps `score` and `eval` to int16
  (±32,767) (theirs 573/666). Guard values ≤ 13,000 fit: stored undistorted.
- `src/search.cpp:1231`: static_evaluate's residual-net return clamps to ±(MateInMaxPly−1) =
  ±31,871; `src/search.cpp:1323`: corrected_eval's return clamps raw+correction to the same
  (theirs 1333/1472). Both sit AFTER the guard's early return: unreachable for a guarded
  position, and a guard value would pass unclamped anyway.
- `include/forge/search.hpp:74-79`: MateValue 32,000, MateInMaxPly = 31,872 (MaxPly 128),
  `is_mate_score` at ±31,872: a guard value never reads as mate.
- Others (named as the job asks):
  - `src/search.cpp:2445-2453`: AspDecisiveScore 640 — a guard value (≥ 2,000) crosses it, so
    the next root search opens with an infinite window (by design for a decisive score).
  - `src/search.cpp:1894`: the eval swing (child vs parent static eval) is clamped to
    ±EvalSwingMax 200 — a guard value's swing is clamped (by design).
  - `include/forge/search.hpp:362-367` `rule50_damped_static`: scales any non-mate score by
    (100−clock)/100, but only when `tune::EvalRule50Damp` is true; default false and PC20 does
    not set it (pc20.opt has no such line), so identity on every run of this job. If it were
    ever on, it would scale the guard's value too.
  - `src/search.cpp:328-329`: history-bonus clamp to ±HistoryMax — not a static evaluation.

## The PC line (v3 net)
`src/uci.cpp:729-746`: the `eval` command first checks `#if FORGE_NNUE_V3` +
`nnue::v3::active()` (730-740): with a v3 net loaded it prints the net's own value
(`evaluate_reference`) and `continue`s — `Evaluator::static_eval_components` (742) is never
reached, so on the PC the guard's value can be seen in a SEARCH, not in `eval` (theirs
822-831). Confirmed on this chain: FORGE_NNUE_V3 is NOT defined here (CMakeLists.txt defines
only FORGE_NNUE_HIDDEN/WEIGHTS/EXPOSE_TUNABLES/SPD_*; no v3), so the block is compiled out and
`eval` always reaches static_eval_components — which is why K2's ON column is checkable here.
