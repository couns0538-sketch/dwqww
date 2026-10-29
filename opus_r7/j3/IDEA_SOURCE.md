# IDEA_SOURCE (R7 J3, engine NPS)

| change | idea source | notes |
|---|---|---|
| hotspot list | own profiles: callgrind bench 13 + perf bench 16 on a quiet GitHub runner (`.github/workflows/opus-r7-prof.yml`), FORGE_PROF counters | `logs/ci_prof1_base/` |
| R7TtExclusive (TT probe/store without `lock_stripe()` for the lease holder) | own reading of the PC build's disassembly: every probe/store calls `__emutls_get_address` (MinGW emulated TLS) through `has_exclusive_access()`, then defers the lock anyway | the ExclusiveLease design is Forge's (src/search/tt.inc); no external code |
| R7QuietGen (quiet-only generation in the quiet stage) | common engine practice (separate quiet / capture generators, e.g. Stockfish's `generate<QUIETS>`), as an idea only; the code is Forge's own `generate_pseudo_legal` with the capture/promotion parts left out | must keep the exact order: `tests/r7_quiet_gen_tests.cpp` |
| R7EvalPrefetch (prefetch the child's pawn-cache entry) | the TT-child prefetch already in Forge (S13 / main search), applied to the HCE pawn cache | hint only |
| no GPL code | nnue-pytorch / Stockfish code was not copied; nothing from `tools/nnue_pytorch_amd/` is in src/include/tests | |
