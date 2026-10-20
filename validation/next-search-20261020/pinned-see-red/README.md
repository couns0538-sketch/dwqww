# Actual frozen-core SEE diagnostic

Frozen 6.4.12 source `8865666cc0ab4961cd507bae40ff6ce44e9319df` headers and
the existing actual gated Release core were used without rebuilding or editing
production code. `actual-core-commands.json` records every compile/run argument,
deadline, exit code and source/header/core/driver hash. Inputs stayed unchanged.

The diagnostic completed all12 cases. All initial-capture legality results and
all10 legal-position recapture sets match the independent python-chess oracle.
Two mirrored absolute-pin cases reproduce **RED**: Qxd5 (or mirrored Qxd4)
legally wins100 with no legal recapture; real `see_ge(move,0)` returns false
and `static_exchange` returns−800. The unpinned controls correctly lose−800.
This demonstrates a SEE approximation/pruning false-negative risk; no full
search failure, emitted illegal move, NPS or Elo improvement is established.

Eight legal controls agree at threshold0. Along-ray pinned rook captures remain
legal and report−300. Both-color king-recapture controls already work: legal
unprotected recapture loses−800; a defended target makes the king recapture
illegal and reports+100 (threshold100 true,101 false). Preserve that behavior.

Two intentionally illegal initial-capture controls produce positive SEE; initial
legality is not checked by SEE. Main/qsearch verify legality before pruning.
MovePicker can call SEE earlier to order pseudo-legal moves, then search filters
them. Do not turn SEE into a complete legality checker or infer illegal engine
output from this diagnostic.

`assert_pinned_see.py` intentionally fails against the saved actual-core output;
its stdout/stderr/exit1 are retained separately. `analysis.json` classifies the
two RED cases and all controls. Runtime was bounded to5seconds and completed
in milliseconds; the complete diagnostic compile/run used less than1minute.
