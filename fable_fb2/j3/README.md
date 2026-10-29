# FB2-J3: search improvements behind UCI options (branch `fable-fb2-j3`)

Four independent check options, all default `false`; with every option false the engine is the lock
(bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690: `logs/identity_off_j3.log`).

| option | what it does (see IDEA_SOURCE.md) | code |
|---|---|---|
| `CorrHistV2` | continuation (1- and 2-ply) correction history added to the pawn / material corrections | `Worker::corrected_eval_v2`, `update_correction_v2`, `ContinuationCorrection` |
| `SingularV2` | triple extensions, PV double extensions, multicut on the singular search, deeper negative extensions | singular block in `Worker::search` |
| `LmrTableV2` | statistically fitted LMR formula (logistic model of "reduced search raises alpha") with a continuous history term | `fb2::lmr_v2_reduction`, `fb2::LmrV2Quiet/Noisy` (fitted constants), `tools/search/fable_lmr_fit.py` |
| `TtPruneV2` | TT move never futility/history/SEE-pruned; IIR at cut nodes with an upper-bound TT move; opponent-worsening RFP margin; improving in futility and history pruning | pruning / RFP / IIR blocks in `Worker::search` |

## Build and verify
- Box exe: `FORGE_EXTRA_SRCS="src/nnue_v3.cpp src/search_v3.cpp" build_pc.sh <src> forge_fable_j3.exe` (0 warnings, FMA 0).
- Identity OFF: `uci_check.py forge_fable_j3.exe --full` -> `ALL OK`.
- Unit tests: CTest `forge_fb2_j3_tests` (`tests/fb2_j3_tests.cpp`): every option changes the depth-10 trees of 6
  positions and restores the exact node counts when switched off; CorrHistV2 arithmetic through the friend probe
  (entries add to the correction, updates saturate at the limits, null/root plies carry no key); LmrTableV2 bounds
  and monotonicity in history; mates found and random positions searched sanely with all options on; determinism.
- LMR statistics: `build_pc.sh ... -DFORGE_LMR_STATS=1`, then `FORGE_LMR_STATS_OUT=<csv> forge_fable_j3_lmrstats.exe`
  with `bench 16` ... `quit`; fit with `fable_lmr_fit.py <csv> --out fit.json --snippet lmr_v2_fit.inc` and paste the
  snippet into `src/search.cpp` (`fb2::LmrV2Quiet/Noisy`).
- Self-play: `tools/opus_selfplay_check.py` (the R3-1 checker, python-chess legality of every best move, mixed go
  modes, isready barriers): `--opt CorrHistV2=true` etc., 500 games per configuration (`logs/selfplay_*`).

## Gate proposal
See `fable_fb2/j3/GATE_ENTRY.md`: one SPRT entry per option vs the all-OFF engine at 10+0.1 with the bounds of
`F:\opus_scratch\fable\GATE_BOUNDS.md` (J6). No Elo claim is made here.
