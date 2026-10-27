# S13 [Sol leftover] TT prefetch at every key change + 64-byte bucket — DONE

Branch `opus-sol-S13` = `d4f4312` + `0d99f02` cherry-picked (`479e83ab`) + [S13] commits:
- `8557326e`: Sol's patch cc3efc96, 4 production files, verbatim.
- `cb6f8789`: probe test.
- `4b8b99cf`: tools and CI.
- `170dabf1`: evidence ([skip ci]).

Every file and archive size: `FILES.md`. No Elo or speed claim.

## 1. What was done
- AL1 already prefetches the TT bucket after the main-search make and the quiescence make, and has
  `static_assert(sizeof(TTCluster) == 64)` with `struct alignas(64) TTCluster`.
- Sol's `forge_sol_S13_ttprefetch_20261026.patch` (sha256 cc3efc96…; prepared, source-checked, never compiled)
  adds the two remaining key changes: after `make_null_move` and after the ProbCut `make_move`. With the option
  on, every make in the search prefetches the child's bucket.
- The port is verbatim: `git apply` (core.autocrlf=false) and, independently, GNU `patch -F0` reproduce the four
  files of `8557326e` byte for byte. Sol's root README/IDEA_SOURCE notes moved to `IDEA_SOURCE.md` here.
- Design kept from Sol:
  - The build switch `FORGE_S13_TT_CHILD_PREFETCH` (CMake option, default OFF) contains UCI `TtChildPrefetch`
    (check, default false).
  - The option is snapshotted into SearchLimits once per search, before helpers start; each worker reads its own
    copy.
  - ON prints `info string TtChildPrefetch active` once per Searcher, and `bench` inherits the option.
  - Without the switch the build is the lock binary. With it, OFF vs ON are timed in one binary. Sol's checker
    applies unchanged.
- New test `tests/tt_prefetch_probe_tests.cpp` (CTest `forge_tt_prefetch_probe`, written after Sol's probe design):
  - It includes the real `src/search.cpp` with `__builtin_prefetch` redirected to a counter.
  - The link map shows the archive's `search.cpp.obj` is not linked.
  - Every build: `sizeof`/`alignof(TTCluster) == 64`, and every prefetched bucket address is a multiple of 64.
  - Switch on: OFF/ON parity, plus coverage of the null-move and ProbCut child sites.

## 2. Acceptance (fix-up S13-1 + A)

| # | line | result | command → raw output |
|---|---|---|---|
| 1 | checker-fix re-review | PASS | Sol's `forge_sol_S13_source_contract_20261026.py` (47938e15…) and tests (49d24d01…) are unchanged; their hashes match his SHA256SUMS and root review. `python -B -m unittest` with base = 294dbed and candidate = 8557326e: 10/10 OK. `validate_source` → PASS_SOURCE_ONLY. Review of the fix: `#else`/`#elif` anywhere inside a feature guard is rejected, which closes the hidden OFF-branch gap. `checker_rereview_controls.py` (8 controls), all as expected: accept the real candidate; reject a nested `#if/#else`, `#if defined(FLAG)`, an `#ifndef FLAG` block, an unguarded extra prefetch, `#ifdef FLAG // comment`, a forced `#define FLAG`, and a CMake default ON. Known limit: it reads only 4 files. On this branch that is covered: the full diff vs the lock is those 4 files plus the probe test and 9 CMake test lines, and the compiled OFF build is the lock binary |
| 2 | full Release + ASan (CI) | PASS | **Default build** (opus-ci 40481055829): release identity ALL OK, Linux forge sha256 6635d4d1 = lock build; asan and tsan known-only; probe passes. **Switch on** (opus-sol-s13-ci 40481055934): release ctest known-only and probe 8/8; asan ctest known-only, probe 8/8, identity d11/13/16 + perft OFF/ON ALL OK, 0 ASan/UBSan reports; tsan ctest known-only, probe 8/8, Threads 2 and 4 UCI sessions with TtChildPrefetch on OK, 0 TSan reports |
| 3 | ON node counts == OFF exactly | PASS | **PC** switch-on exe, `uci_check_opt.py --full [--set TtChildPrefetch=true]`: 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, ALL OK both. **Linux** release same. **Probe** (4 positions, d10): same move, ponder, score, depth, seldepth, nodes, PV and null-move attempts |
| 4 | bench NPS OFF vs ON, same binary, 5 runs each | DONE, no measurable effect | `nps_onoff.py s13_on.exe 5 TtChildPrefetch 16 20`, PC, nice 19, machine exclusive: no. Medians ON/OFF: d16 +0.88% wall / −2.86% CPU; d20 +0.79% / +2.22%; all 95% CIs contain 0. Quiet runner, 10 runs: d16 +0.00% (CI −0.89..+2.58), d20 −0.11% (CI −1.00..+1.86). Nodes identical on every run |
| A1 | builds on the lock tree | PASS | PC recipe (default, and `-DFORGE_S13_TT_CHILD_PREFETCH=1`), CMake both configurations, Linux |
| A2 | OFF bench-exact, perft5, FMA 0 | PASS | Default exe vs lock exe: `cmp -l` shows 5 bytes (offsets 137-139 PE timestamp, 217-218 PE checksum); whole-binary `objdump -d` identical; `uci_check.py --full` ALL OK. Linux default binary IDENTICAL to the lock build (sha256 and disassembly). FMA 0 in all builds |
| A3 | CTest + ASan/UBSan (CI) | PASS | Local ctest 14/15 known-only in both configurations; CI as line 2 |
| A4 | UCI option default OFF | PASS | Switch-on build: `option name TtChildPrefetch type check default false`; invalid value → `info string invalid value for option TtChildPrefetch`. Default build: no option |
| A5 | IDEA_SOURCE; ON node/NPS numbers; no Elo claim | PASS | `IDEA_SOURCE.md`; above |
| S | every key change prefetched; bucket = one 64-byte line | PASS | Switch-on exe `Worker::search` has 3 `prefetch` instructions (lock 1); qsearch unchanged. Probe ON: 640 null-move and 217 ProbCut child requests. With the option off: 87,171 requests, 0 misaligned bucket addresses; static_assert alignof 64. Negative diagnostic (both new statements removed, option kept): probe fails exactly the 2 coverage checks (ProbCut children 0) |

- **Codegen of the switch-on build vs lock:** `Worker::search` 2413 -> 2417 instructions, same 32 mod 64; the
  iterative driver +7 (the snapshot); every other hot function identical.
- **Lock vs switch-on binary, option OFF (runner):** d16 +0.66% (CI −0.19..+1.50), d20 +0.03% (CI −1.04..+1.09).
- **CI runs:** opus-ci 40481055829 (release, asan, tsan: all success) and opus-sol-s13-ci 40481055934 (release,
  asan, tsan: all success).

## 3. Left / UNVERIFIED
- Speed gain: UNVERIFIED. No measurable effect, so no claim; the ≥ +2% rule is not met.
- Hardware prefetch completion and cache effects are not measured: the probe counts requests only.
- No prefetch after unmake, by Sol's design: the parent's bucket was already probed in this frame.
- Gate: if QA wants one, use S29's single speed-stack gate. QA picks the srand.
- The probe's `-Wl,-Map` link option is GNU-only (guarded with `NOT MSVC`). MSVC is untested.
- The PC clock is about 9 h ahead of UTC.
