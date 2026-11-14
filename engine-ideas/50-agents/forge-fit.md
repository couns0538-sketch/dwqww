# Forge module map

Read-only. Nothing in the engine was changed. The maintained split is the tree on `origin/astra-r14-20261103`. The same module set is on `origin/forge-bundle-int`. `main` at `5176ddf` does not check these files out. It has `chess-engine-forge-5.31.0(2).zip`, whose engine is one `search.cpp` with eval, reductions, aspiration, history, and a clock check inside it, and no network, book, datagen, threads, probcut, singular search, or Syzygy. An idea written only against that zip will add a module the later trees already have.

## Where ideas land

- Search selectivity, pruning, reductions, aspiration, probcut, null-move verification, singular extensions, history, and threads: `src/search/`, mainly `alphabeta.inc`, `movepicker.hpp`, `history.hpp`, `searcher.inc`. Null-move verification at depth 14 or more, ProbCut, late-move reduction and pruning, aspiration, singular extensions, and butterfly, capture, and continuation history are already there. There is no policy head, no visit tree, no contempt, no MultiPV, and no fortress test.
- Hand-crafted eval, taper, pawn structure, mobility, passers, king safety, and material-draw scaling: `src/eval.cpp`. Phase taper and `scale_factor` are already there. `tools/tune/texel.cpp` traces the same terms.
- Network, incremental updates, a future policy or WDL output, and eval scaling of the net: `src/nnue.cpp`. The shipped net is a residual on the hand-crafted eval. Incremental refresh and update exist. `NetScale` defaults to 100. No policy head and no WDL head. A v4 net on `origin/opus-r5c-netv4` rebuilds both accumulators every eval, so the incremental-update ideas (U1–U3) do not apply to that net.
- Clock: `src/search/timeman.hpp`. Soft and hard budgets, increment, moves-to-go, and a stable-move adjustment are already there. No separate bullet profile. B3’s node estimate belongs here plus the reduction in `alphabeta.inc`.
- Opening variety: `src/book.cpp`. `Book Variety` already picks inside a weight band before search. A second variety mechanism in search will not see book moves.
- Training labels: `src/datagen.cpp` and `tools/nnue/train_resid_v3b.py`. Records are `.pos` and `.hce`. A different label format breaks that trainer. Search-constant tuning is `tools/spsa/`.
- A style or must-win switch: a default-off UCI option. Every added search option already defaults off. There is no contempt, Elo limit, or MultiPV option.

## Do not stack these

`NetScale`, the phase taper, and `scale_factor` already rescale one score. B4, E3, and a new taper move the pruning margins that were tuned for the compiled-in residual net.

Draw handling is already three mechanisms: terminal draws, `scale_factor`, and Syzygy. V1, a fortress score, and a must-win term will each pull the same positions toward a draw.

Singular extension options that are marked exclusive should not be stacked. Helpers share one transposition table.

## Sources

Paths on `origin/astra-r14-20261103` named by the read-only pass: `src/search/alphabeta.inc`, `src/search/iterative.inc`, `src/search/timeman.hpp`, `src/search/evaluation.inc`, `src/eval.cpp`, `src/nnue.cpp`, `src/book.cpp`, `src/datagen.cpp`, `src/uci.cpp`, `include/forge/nnue.hpp`, `include/forge/eval.hpp`, `include/forge/net_scale.hpp`, `tools/nnue/train_resid_v3b.py`, `tools/tune/texel.cpp`. The zip on `main` is `chess-engine-forge-5.31.0(2).zip`.
