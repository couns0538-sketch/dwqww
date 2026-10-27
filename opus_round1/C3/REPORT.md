# C3 [Engine Coder] Hard time deadline / bestmove latency fix (UCI HardDeadline, default 0) — DONE

Branch `opus-C3` = `opus-O3` (`0d99f02`) + [C3] commits:
- `dd15d85`: `tools/latency_test.py`
- `1de9871`: the HardDeadline option
- `9ae572a`: CI latency matrix, Linux starvation run, short TSan hook
- `0410aec`: evidence
- follow-up (2026-10-27, the commit that adds this line): the watchdog's answer obeys `go searchmoves`, and
  `DebugSearchDelayMs` is compiled only in debug builds (section "Follow-up" below)

`patch.diff` = `git diff 0d99f02` of the follow-up commit (engine, tools, tests). Ideas: `IDEA_SOURCE.md`.
UNPROVEN until gated; no Elo claim.

## Cause of the WAC stall (12 s on a 1000 ms move, WAC.008)
**Process starvation, not the search.** The WAC300 harness ran the engine at nice 19 / idle priority on a
busy machine. A CPU-bound search thread at the lowest priority gets almost no CPU while normal-priority work
runs on the same core. The clock is polled correctly, but the process does not run. On Windows the
balance-set manager boosts a starved thread only every few seconds.

**Reproduced** with `latency_test.py --affinity --idle`: the engine is pinned to one CPU at the lowest
priority, with a CPU hog at BelowNormal on the same CPU.
- AL1 behaviour (HardDeadline 0): answers 3.7-4.7 s late on every position (`logs/starvation_demo_windows.log`).

**The other suspects were cleared by measurement.** The prompt listed node-poll frequency, long
quiescence/extension chains, stop propagation to the helpers, and the uci.cpp hand-off. Under normal load,
with HardDeadline 0 (AL1 behaviour), 3 full WAC300 passes at 100 ms and at 1000 ms at Threads 1 and 4 (3,600
searches) never answered late: the latest bestmove arrived 7.6 ms *before* the movetime. So none of these
causes a stall without starvation.

## Fix: UCI `HardDeadline` (spin 0-1000 ms, default 0 = off)
**Watchdog.** With N > 0, a persistent watchdog thread, created when the option is set, sleeps until the
hard time limit + N ms of every clocked `go` (from `ponderhit` when pondering). If no bestmove is out by then,
it stops the search and sends the move of the main worker's last completed iteration. That move was
published through one atomic (`options::published_moves`, packed best and ponder move) and is checked against
the root candidates: the legal moves, restricted to `go searchmoves` when given. Otherwise it sends the first
candidate, and `0000` when there is none, exactly the search's own fallbacks.

**Exactly one bestmove.** An atomic claim ensures one `bestmove` per `go` (watchdog vs normal path). The run
counts as done only after the bestmove line is written.

**Priorities (Windows).**
- The watchdog runs at time-critical thread priority.
- The UCI input loop also waits at time-critical priority, dropping to normal for heavy commands. A starved
  process therefore still reads `go` and answers on time.
- The search threads keep their priority.

**Testing hook.** The hidden option `DebugSearchDelayMs` holds the search thread back for the regression
test. It is not advertised and is inert at 0. It is compiled only in debug builds (no `NDEBUG`) and in the
test-only CMake target `forge_debughooks` (`FORGE_DEBUG_HOOKS=1`), which CTest's `hard_deadline_regression`
uses. Release builds (CMake Release, the box recipe `build_pc.sh`) contain no trace of it.

**Off = AL1.** With HardDeadline 0, no thread is created and no node path changes.
- **Layout:** publishing the move is a `[[gnu::cold]]` call per completed iteration; the slot is a
  constant-initialised global.
- **Codegen** (`logs/codegen_identity.log`): alpha-beta, qsearch and every other listed hot function are
  instruction-identical to the lock at the same address mod 64. `MovePicker::next`'s 32 lines are padding and
  data displacements only. The per-iteration driver differs, because it publishes once per iteration.

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | OFF -> bench exact | **PASS**: d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, FMA 0 (PC recipe `logs/identity_pc_recipe.log`; Linux CI) |
| 2 | deliver `tools/latency_test.py` running all 300 WAC positions at 100 ms and 1000 ms | **done** (WAC suite copied from the archive's `4_tests/suites/wac300.epd`) |
| 3 | with the fix: max overshoot < 50 ms over 3 full passes at both movetimes, 0 missing bestmoves, also at Threads 4 | **PASS** (CI run 40379626553, quiet Linux runner): Threads 1 and 4, with HardDeadline 10 and with 0. Each configuration: 3 passes x 300 positions x {100, 1000} ms, 0 missing, 0 duplicates, 0 over 50 ms. Max overshoot: T1 HD10 −8.6 ms; T4 HD10 −6.4 ms; T1 HD0 −8.4 ms; T4 HD0 −7.6 ms (negative = before the movetime). Locally on the busy PC, 1 pass each: lock −9.0 ms, HD10 −9.0 ms |
| 4 | ctest only known failures | **PASS**: 17/18, only `forge_tests` with its 4 known lines (Windows and Linux CI). New CTest `hard_deadline_regression` (`tools/hard_deadline_regression.py`) passes, and a planted "ignore the claim" bug fails it with a duplicate bestmove |
| §3 | ASan+UBSan, TSan | **PASS** (CI run 40379626358): 0 reports. The short TSan hook runs HardDeadline=1 at Threads 2 with 20 and 100 ms movetimes, so the watchdog races the search on almost every move |

### Follow-up (2026-10-27): searchmoves and a debug-only hook
| check | result | evidence |
|---|---|---|
| watchdog answer obeys `searchmoves` | **PASS**. New starved scenarios: `go movetime 20 searchmoves <1-3 legal moves>`, leaving out the engine's first legal move (from its own `go perft 1` order, which is what an unrestricted fallback plays), must be answered from that list. `searchmoves a1a1` (no legal move) must be answered `0000`, like the search. Local runs: 300 searches each at Threads 1 and 2, PASS (58 + 72 searchmoves scenarios, 117 + 140 watchdog answers) | `logs/followup_regression_hooks.log` |
| the test catches the old behaviour | **PASS**. A planted mutant whose fallback ignores `searchmoves` fails: `SEARCHMOVES ignored: bestmove a2a3 (starved_badsearchmoves) ... allowed []` | `logs/followup_regression_mutant.log` |
| hook only in debug builds | **PASS**. The box-recipe release exe has no `DebugSearchDelayMs` string (0 matches), the `FORGE_DEBUG_HOOKS=1` exe has it (1). The test refuses an engine without the hook: "engine has no DebugSearchDelayMs hook: use a debug build or the forge_debughooks target" | `logs/followup_hook_strings.log`, `logs/followup_regression_release_refused.log` |
| OFF = AL1 | **PASS**. Box recipe (`build_pc.sh`), release: bench 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, ALL OK; FMA 0 | `logs/followup_identity_release.log` |
| CMake + CTest | **PASS**. Local Release build (`cmake_build.sh`, JOBS=1) builds `forge`, `forge_debughooks` and `forge_tests`; `hard_deadline_regression` (on `forge_debughooks`) and `uci_regression` pass | `logs/followup_ctest_subset.log` |
| CI on `f07630e` | opus-ci 40498064402: release **PASS**, ASan **PASS**, TSan ctest **PASS** (known-only, 0 reports), but the C3 TSan hook **FAILED**. It ran the regression on the TSan `forge`, which no longer has the hook (RelWithDebInfo defines `NDEBUG`), and the hook probe could pass by the watchdog winning a race against the slow search ("starved search (starved_badsearchmoves) was not answered"). opus-c3-latency 40498064363: **PASS** (starvation + 4 latency jobs) | CI logs |
| fix (`581ad5d`) | `tsan_extra.sh` runs the regression on `forge_debughooks` from the same build (with `forge` as the perft reference). The probe now uses `go movetime 20 searchmoves a1a1`, where a hook-less engine answers `0000` at once, so it cannot pass by a race. Locally the release exe is refused 3/3, and the hooks exe passes 150 searches at Threads 3 | `logs/followup_regression_hooks_t3_probe2.log` |
| CI on `581ad5d` | **PASS**. opus-ci 40503292559: release, ASan, TSan all status 0, known-only; the C3 TSan hook `hard_deadline_regression_t3` PASS (150 searches, exactly one legal bestmove each), TSan 0 reports. opus-c3-latency 40503292638: starvation + latency (1,0) (1,10) (4,0) (4,10) all PASS | CI logs |

### Starvation (the actual failure mode)

| where | HardDeadline 0 (AL1 behaviour) | HardDeadline 10 |
|---|---|---|
| Windows PC: engine at idle priority pinned to CPU 11, hog on the same CPU (12 WAC positions per movetime) | **3,750-4,651 ms late**, 24/24 over 50 ms | max **+23.0 ms** (100 ms) / **+28.8 ms** (1000 ms); 0/24 over 50 ms; all forced by the watchdog |
| Linux CI: engine at nice 19 pinned to CPU 1, hog on the same CPU (30 positions per movetime) | max **+224 / +228 ms**, 52/60 over 50 ms | max **+90.2 / +63.2 ms**, **3/60 over 50 ms** (52 of 60 forced) |

On Windows the fix holds. On Linux an unprivileged process cannot raise a thread above its nice level, so
the watchdog competes with the hog at nice 19. HardDeadline cuts the lateness about 3x there, but cannot
guarantee 50 ms. Linux boxes should not run the engine at nice 19 next to CPU hogs, or should grant the
engine `CAP_SYS_NICE`; this is documented, not changed.

## Proposed gate
HardDeadline does not change any search decision while the engine answers on time. Under normal conditions
the watchdog never fired: 0 forced answers in the 3,600 normal-load searches with HardDeadline 10. A
standard gate of
`HardDeadline=10` vs AL1 (SPRT [0,10], 10+0.1, Threads 1, Hash 16, OwnBook false, new srand from QA) is
therefore expected to measure only noise.

What decides the option is the harness condition: QA's WAC300 run at nice 19 on the busy PC, repeated with
`setoption name HardDeadline value 10`. The expected result is 0 stalls over 50 ms on Windows.

No Elo claim.

## Files
- **Engine:** `src/uci.cpp` (watchdog, claim, priorities, options), `src/search/iterative.inc` (publish per
  iteration), `include/forge/search_options.hpp` / `src/search/options.inc` (published moves),
  `include/forge/search.hpp`, `include/forge/thread_data.hpp`, `src/search.cpp`.
- **Tests:** `tools/latency_test.py`, `tools/hard_deadline_regression.py`, `tools/wac300.epd`, `CMakeLists.txt`
  (the CTest entry and the test-only `forge_debughooks` target).
- **CI:** `.github/workflows/opus-c3-latency.yml`.
- **`opus_round1/C3`:** `REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `starvation_demo.py`, `tsan_extra.sh`,
  `logs/` (identity, codegen, ctest, local latency, the Windows starvation demo, and the CI latency and
  starvation logs in `logs/ci/`), `SHA256SUMS`.
