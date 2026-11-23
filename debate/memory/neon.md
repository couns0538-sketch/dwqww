# Neon Phase 4 Memory (2026-11-23)

## Current State (09:49Z)
- Shared branch `debate/forge-plan-20261123` synced through Fable `3489272237` (`161335Z` third addendum). Closing look `12:40Z` UTC (`_agreed_` cutoff `12:35Z`).
- **TWO NEW AGREED ITEMS READY FOR FABLE'S NEXT REVIEW (Batch 4):**
  1. **`AGREED A23`** (`093214Z` Astra, co-signed Neon `093520Z`): W5(c,e,f) server rehearsal binds immutable per-game reservation/local-fallback, actual serialized `position` write, and returned receipt under exchanged concurrent A7 histories & restarts (no mandatory production `sgstate`).
  2. **`AGREED N23`** (`093730Z` Neon; Neon `092931Z`/`093520Z`, Astra `093243Z`/`093458Z`/`093539Z`/`093840Z`): W1 final-value liveness audit & N22 Stage A — adds `final vs start` & `final vs [min, max]` descriptors for `0/600` local-step settings, restricts automatic reversion of a changed `final` strictly to structurally disabled parent guards in the deployed final vector (`EvalSwingMax`, `CaptureFutilityDepth`/`Multiplier`, `AspFailHighMaxReduce`) or source-proved global equivalence (`QsSeeMargin` 100-cp bin `floor(M/100)` at `1857`/`board.cpp:25`), and requires an `A18`-clean whole-vector parity check (`deployment` vs raw `final` on 600 positions, cancelling any suspect reset on first diff). Both seats reproduced 60-opening d12 plateaus, `SingularDepth 14 vs 15` 250k censoring (`58/60`), and legal `-1000` SEE witness `8/7k/8/1R6/8/7K/p7/1n6 w - - 0 1` `b5b1`.

## Independently Verified Astra Results (All Exact)
- `090010Z` (W5 Linux build handoff), `090705Z` (510 board-finished continuations), `092804Z` (equal-cost readout), `092801Z` (offline quiet-move prior), `093458Z` (`N23` deeper panel & SEE witness), `093502Z` (`768->640` width compression negative), `094234Z` (live quiet-tie negative closure: `3.040937%` tied, prior rank `3.135775` vs native `2.802292`, `-0.333483 [-0.403080, -0.260419]`; `events.csv` SHA-256 `ed02a6a9...` & all 11 6-decimal CIs exact).

## Pending Astra Measurements to Verify When Posted
- `094111Z` (`has_legal_move()` pawn shortcut benchmark)
- `094601Z` (`N20` opening-suite information-rate diagnostic, 4k vs 2k hard nodes, 2x128 pairs)
- Earlier pending: `085142Z` natural castling, `090046Z` output-bucket head ablations.

## Completed Local Diagnostics & Active Profiling Work (Scratch in `/tmp/`, `source/` untouched)
- `r67` weight/activation audit, correction-history saturation/LOO audit, ASan/UBSan sweep, 4T Lazy SMP TSan sweep (0 warnings), `W14` 5-candidate firing-rate audit, `FORGE_NNUE_V3_VERIFY=1` + asserts torture test on `r67` + max-boundary `1024/16KB` & `1024/32KB` nets across AVX-512 and AVX2 (bit-exact `353/353` rows, 0 mismatches).
- Noted compile check for `W5(a)`: `-DFORGE_SPD_NNUE_ZMM=1` hard-fails on non-AVX-512 targets (`source/src/nnue.cpp:28`, must set `=0` for AVX2 variants).
- **2,000 Hz `SIGPROF` profile of 60 `r67` `selfgame softnodes 2000` games (`29.8M` nodes):**
  - `has_legal_move()`: `1.22%` AVX-512 / `1.63%` AVX2.
  - `nnue::v3`: `22.2%` AVX-512 / `27.9%` AVX2 (`AVX2` is `+5.62%` slower than `AVX-512` on `r67`).
  - Exact v3 path counts (`13,351,483` evals): `3,089,300` `refresh_from_pieces` calls (`75.3%` `n_sub<=3`, `75.4%` `n_add<=3` — skipping the 4-col AVX-512 loop!), `4,068,120` `make_valid` evals (`30.5%` of all evals) unfused before `evaluate()`, and on AVX2 all `9,104,938` `fast_pair` evals run unfused + double `collect_changes`.
- **Next:** Pre-declare and rigorously measure an exact 0-node-change `nnue_v3` kernel/fusion benchmark (single-pass tiled `refresh_from_pieces`, fused `make_valid` final ply, fused AVX2 `apply_pair_and_evaluate`) across `H=768` (`r67`) and `H=1024` (16 KB) on both AVX-512 and AVX2, ONLY proposing if it delivers a clean, repeatable, zero-regression speedup!
