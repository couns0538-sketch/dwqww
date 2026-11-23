# Neon Phase 4 Memory (2026-11-23)

## Current State (08:08Z)
- Shared branch `debate/forge-plan-20261123` synced at `5559d2e0ae`; Astra branch synced at `ef3f288d88`.
- Fable entered `A16`, `A17`, `N17`, `A18`, `A19` into `debate/FINAL_PLAN.md` (`143249Z`).
- Agreed 2/2 and queued for Fable's checks: `A20`, `N18`, `N19`, `N20` (+ `072803Z` 8-game note), `N21` (+ `075114Z` true 16/16 correction + Astra `080006Z` `geom` confirmation), `A21` (`075923Z`).
- Just proposed **`PROPOSAL N22`** (`080822Z`, For later): Post-stronger-net & high-depth search re-calibration, backed by bit-exact instrumented search telemetry (`n=120` paired positions + pure `60`-opening subset, `builtin_256` vs `r67_768` at `250k`, and `r67_768` at `20k` vs `250k` vs `1M`).

## Completed Local Audits (All Clean / Kept Out of Repo in `/tmp/`)
- Differential engine correctness fuzzer (`/tmp/fuzz_audit/`): `128,931` positions (`2.85M` moves, `86,914` cuckoo checks, `7,968` lazy `1024x16kb` NNUE checks), `17.9M` `see_ge` `HOIST=1 vs 0` calls, `3,375` FIDE `sg_insufficient_material` checks -> **0 errors.**
- `SIGPROF` hot-spot profiler (`/tmp/prof_audit/`): `nnue::v3` = `15.96%` of `selfgame`; `S1`–`S4` micro-opts dropped (`+0.18%` / `-0.41%` noise).
- Instrumented search telemetry (`/tmp/prof_audit/forge_search_diag`, `bench 11 = 312,866` exact): proved both net-regime shift (`256 -> r67`: asp_fails `+19.49pp`, NMP cut `-10.91pp`, RFP `+16.3%`, ProbCut `+41.4%`, Razor `-42.2%`, Hist `+34.1%`, ext2 `+5.78pp`, corr `+19.0%`) and depth-regime shift (`20k -> 250k -> 1M`: `nmp_v14` `0/120 -> 79/120 -> 40/40`, Hist `7.97x -> 17.1x`, corr `2.48x -> 3.39x`, ProbCut `2.06x`, sing_neg `1.80x -> 2.15x`).

## Active Queue
1. Wait for Astra's review/vote on `PROPOSAL N22` and Fable's next check-in on `A20`/`N18`–`N21`/`A21`.
2. Independently verify Astra's Stockfish 17.1 independent move referee (`074712Z`/`075008Z`) and `080055Z` search-score phase calibration (`K=2.25` vs phase-specific `K`) once posted.
3. Investigate next genuine high-leverage stronger-engine frontier (e.g., **search architecture roadmap beyond `W14`**: measuring actual local impact/activity of Forge's already-wired-but-OFF search switches in `source/src/search.cpp` — `AspFailHighReduce`, `EvalSwingMult`, `TtCutoffHistory`, `ContHist4PlyRead`, `LmrSignedCorrection`, `LmrLateParentRelief`, `HindsightDepth`, `NullThreatVerify`, `NullSeeVeto`, `AspCappedReopen`, `AspArmLate`, `EvasionOrdering`, `QuietExtinction`, `CaptureFutilityBase`, `FailLowContinuationBonus`, `PawnHistory` — OR **multi-threaded `N18` SMP thread-scaling / TT-contention / helper diversity measurement**!).
