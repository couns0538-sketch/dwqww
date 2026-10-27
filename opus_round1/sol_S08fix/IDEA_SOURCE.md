# IDEA_SOURCE — S08fix

- Engine change ported unchanged first: Sol's S08 profile counters, `forge_sol_S08_profcounters_TLS_v2_20261026.patch`
  (sha256 `91c28d9f3b70af08885d50239141890813722cf00114bda8a2d12b71eb5e476c`, branch `forge/sol-pack31-20261025`
  @ 17aa0cae): `FORGE_PROF` (default OFF), 55 fixed counters, `Profile` UCI option (default false), `bench_prof`.
  Sol's idea sources: the user's S08 request (profiling + feature-frequency audit); his documentation patches
  (L/Lprime/B) are not ported because the AL1 README/IDEA_SOURCE differ; this file replaces them.
- Fix-up items: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3, S08-2 (per-worker counter banks + merge()), S08-3 (OFF
  proof, same-machine NPS, ON overhead %), S08-4 (dead-feature table corpus, drop capture_futility_prunes).
- Per-worker banks: the common per-thread-statistics pattern (each search thread owns its counters, the controller
  sums them after the threads are joined), as used for node counts in Forge itself (`Worker::nodes_`,
  `Worker::total_nodes()`); original code. Cache-line alignment (`alignas(64)`) to avoid false sharing: standard
  practice (C++17 `std::hardware_destructive_interference_size` rationale, P0154R1).
- NPS tools: `nps_prof_ab.py` extends opus-O3 / sol_S29 `nps_ab.py` (ABBA order, fresh processes, CPU-time NPS)
  to several arms and the `bench_prof` command; `prof_threads_nps.py` is original.
- Profile collector v2: Sol's `forge_sol_S08_collect_profiles_substitute_20261026.py` with configurable bench pins
  (AL1 defaults) and the S08-4 table rules.

## Corpus limit (S08-4)

The specified 2,000-position WAC/STS set is not available: no STS (Strategic Test Suite) file exists on the PC
(searched `C:\Users\Administrator\grok-pc`, `D:\grok-pc-data`, `F:\opus_scratch`, the lock archive), and Sol's
handoff had none either. The dead-feature table is therefore re-run on Sol's sealed substitute corpus (300 WAC
+ 7 bench + 1,693 synthetic quiet opening positions = 2,000 distinct, manifest sha256 in `corpus/`), now on the AL1
lock with the per-worker-bank build. It is NOT the specified WAC/STS set; frequencies on tactical/strategic test
positions may differ, and no feature is removed on this evidence.

`capture_futility_prunes` is dropped from the dead-feature rows: its count is 0 because the lock defaults disable the
prune (`tune::CaptureFutilityBase = 0`, src/search.cpp; the prune requires `CaptureFutilityBase > 0` and the
opportunity counter runs before that guard). It is listed separately as "disabled by default", not as a dead feature.
