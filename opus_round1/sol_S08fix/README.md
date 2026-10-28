# S08fix — profile counters on AL1: per-worker banks + merge (S08-2), OFF proof and overhead (S08-3), dead-feature table (S08-4)

Branch `opus-sol-S08fix` = AL1 lock tree `d4f4312` + CI baseline `0d99f02` + `990cbb18` (Sol's S08 TLS v2 patch,
verbatim) + the fix-ups. `FORGE_PROF` stays default OFF (CMake option; box recipe `-DFORGE_PROF=1` plus
`FORGE_EXTRA_SRCS=src/profile.cpp`); ON builds advertise `Profile` (default false) and the `bench_prof` command.

## S08-2 per-worker counter banks

Sol's version kept one `prof::Bank` of 55 `std::atomic<uint64_t>` in `SharedSearchState`; every worker thread's
TLS pointer aimed at it, so at Threads>1 every node wrote the same cache lines from all threads. Now:
- `prof::Bank` is a cache-line-aligned array of plain `uint64_t` (sticky overflow flag kept);
- every `Worker` owns one bank (`profile_bank_`); `Worker::search` binds its own bank in its own thread;
- `Searcher::search` resets all worker banks before the helpers start; `Searcher::profile_snapshot()` merges them
  with `prof::merge()` after the helpers are joined; `profile_worker_snapshots()` / `profile_worker_nodes()` expose
  the per-worker view (tests);
- `bench_prof`, the `go` counter packet and the packet format (schema 1, 55 lines) are unchanged.
`tests/prof_tests.cpp` replaces the shared-bank thread test: per-thread banks + merge, and real searches at
Threads 1/2/4 where each worker's bank must hold exactly that worker's node count and every worker must count.

## Run (PC)

```sh
nice -n 19 bash $T/build_pc.sh "$PWD" .../forge_s08fix_OFF.exe                                   # OFF = lock
FORGE_EXTRA_SRCS=src/profile.cpp nice -n 19 bash $T/build_pc.sh "$PWD" .../forge_s08fix_ON.exe -DFORGE_PROF=1
JOBS=1 nice -n 19 bash $T/cmake_build.sh "$PWD" .../cmake_on -DFORGE_PROF=ON && (cd .../cmake_on && ctest)
python -B nps_prof_ab.py --runs 7 --depth 16 --depth 20 --arm lock=LOCK.exe --arm off=OFF.exe \
   --arm on_inactive=ON.exe --arm on_counting=ON.exe@bench_prof                                  # S08-3 (advisory)
python -B forge_sol_S08_collect_profiles_v2.py --engine ON.exe --suite corpus/...WAC... --suite corpus/...BENCH... \
   --suite corpus/...OPENING... --corpus-manifest corpus/forge_sol_S08_authorized_corpus_manifest_20261026.json \
   --nodes 10000 --output NEW_DIR                                                                # S08-4
python -B test_forge_sol_S08_collect_v2.py -v
```

Linux CI: `.github/workflows/opus-sol-s08fix-ci.yml` -> `ci_s08fix.sh release|asan|tsan` (OFF vs lock, ON identity,
bench_prof pins, ctest incl. `forge_prof_tests`, NPS overhead on the runner, Threads 4/1 profile on/off NPS of Sol's
shared bank vs per-worker banks, ASan/UBSan and TSan with profiled Threads 2/4 searches).

## Files

- `nps_prof_ab.py` (multi-arm ABBA NPS incl. `bench_prof`), `prof_threads_nps.py` (Threads>1 skew check),
  `make_prof_mutant.py` (planted bugs for the S08-2 tests), `ci_s08fix.sh`.
- `forge_sol_S08_collect_profiles_v2.py` + `test_forge_sol_S08_collect_v2.py` (Sol's collector with AL1 pins, the
  S08-4 table rules and Windows pipe reading via reader threads -- v1 used select() on pipes, which Windows does not
  support; Sol's 6 delivery checks + 4 new), `forge_sol_S08_deadfeature_table_v2.py` (writes the low-frequency table
  from a collector report), `sol_v1_unchanged/` (Sol's v1 collector, for the CI RED run), `corpus/` (Sol's sealed
  substitute corpus, unchanged), `forge_sol_S08_profile_packet_reference_20261026.stdout` (Sol's fixture, unchanged).
- `forge_sol_S08_v3.patch` — whole engine diff vs the AL1 base.
- `logs/` — PC builds, identity, ctest, mutants, NPS, collector run + v2 dead-feature table, CI artifacts.
