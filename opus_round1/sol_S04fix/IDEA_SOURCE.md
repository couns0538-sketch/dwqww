# IDEA_SOURCE — S04fix

- Engine change (unchanged from Sol): Sol's S04 v2 patch `forge_sol_S04_v2_20261025.patch`
  (sha256 `b425157e6e9521a544e3612f3c32c3955bb1fd3195735692975d5a6d6d89590b`, branch `forge/sol-pack31-20261025`
  @ 17aa0cae). Sol's own idea sources: the user's S4 request, the Forge cold-first-Board race reproducer and the
  C++ `std::call_once` publication guarantee (https://en.cppreference.com/w/cpp/thread/call_once). Its IDEA_SOURCE
  paragraph is moved here because the AL1 root `IDEA_SOURCE.md` differs from Sol's base.
- Fix-up items: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3, S04-1 ("make the 1000-iteration cold-start probe a ctest
  target") and S04-2 ("give the TSan test a TIMEOUT; build ON with MinGW").
- Probe driver: Sol's `forge_sol_S04_cold_runs_20261025.py` (fresh process per iteration, stop at the first
  failure, `TSAN_OPTIONS=halt_on_error=1:exitcode=66`, no suppressions), re-implemented in CMake script mode so the
  ctest target needs no Python. Original code.
- CTest semantics used: the `TIMEOUT` test property takes precedence over `ctest --timeout`
  (CMake documentation, `TIMEOUT` test property and `ctest --timeout`).
- Native (MinGW) variant of the cold test: original; same test source, no sanitizer, because MinGW-w64 GCC
  ships no ThreadSanitizer runtime.
- No search, evaluation, NNUE, tuning constant or code from another engine is involved.
