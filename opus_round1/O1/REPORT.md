# O1 [Engine QA] Lazy SMP: robustness audit, fixes and scaling suite — DONE

Branch `opus-O1` = `opus-O3` (`0d99f02`) + [O1] commits:
- `c994f6e`: bug 2
- `44b2db1`: bug 1, option `SmpExactNodes`
- `0abed6a`: option `SmpBestThread`
- `c695680`: stress/TSan/self-play/scaling tooling + CI
- `efc570c`: merge of opus-O3's MovePicker pin and CI timeouts
- `33b0790`: TSan CI fix after run 40367007552

Engine code is final at `efc570c`; `33b0790` changes only CI and tools. `patch.diff` = `git diff 0d99f02 HEAD`
(engine tree and tests). Lazy SMP was audited and hardened, not reimplemented. Behaviour changes for
Threads > 1 sit behind two new UCI options, both default false. No Elo claims.

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | Threads=1: bench all 5 depths exact | **PASS**: PC recipe build of `33b0790` (sha256 `98351ec9…`): d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, FMA 0 (`logs/identity_pc_recipe.log`); Linux CI g++-14 identical |
| 2 | TSan: 0 reports on 200 positions x `go depth 12` at Threads 2/4/8 and on a 500x stop/ponderhit/isready/setoption-Threads stress script (deliver the script) | **PASS**: CI run 40381524268, 4 shards, **0 TSan reports**. Depth 12: Threads 2 200/200 (593 s), Threads 4 200/200 (587 s), Threads 8 200/200 (1165 s), all bestmoves legal. Stress 500/500 (40 s). Script: `uci_stress.py` |
| 3 | 2000 fast self-play games at Threads 4: no illegal move, no crash, no hang, 0 missing bestmoves (PGN + legality check) | **PASS**: CI run 40381524051, 4 x 500 games at tc 1+0.01, Threads 4: **0 illegal, 0 crashes, 0 stalls / missing bestmoves, 0 time forfeits**, 500/500 normal terminations per shard. A fifth shard of 500 games with both new options on (engine A) is also clean. Checker `pgn_legality.py` (python-chess); PGNs in `logs/ci/selfplay-*/games.pgn.xz` |
| 4 | scaling table: time-to-depth and NPS for Threads 1/2/4/8, ~30 bench positions, 5 runs each, analysis | **done** on the CI runner (2 cores / 4 hardware threads; analysis below). The PC could not be used: the session is limited to 3 threads and the PC is busy with gate jobs |
| 5 | bug list with repro + fix commit per bug | 2 bugs, below |
| 6 | gate specs only for behaviour-changing options | `SmpExactNodes`, `SmpBestThread` (SMP-only gates), below |
| §3 | ctest only known failures; ASan+UBSan; TSan | **PASS**: ctest 17/18 with only the 4 known `forge_tests` lines (release, ASan+UBSan, TSan); new `forge_smp_tests` passes in all three (2.3 s / 11 s / 196 s); TSan 0 reports, including the short per-push TSan hook (CI run 40381524034) |
| §3 | default hot code / layout | `codegen_compare.sh` lock vs O1 (`logs/codegen_lock_vs_o1.log`), details below |

## Audit (lock code; O3 module names)

| area | finding |
|---|---|
| **TT entries / torn reads** (`tt.hpp`, `tt.inc`) | No torn reads possible. `probe` and `store` hold one of 1024 striped mutexes (one per cluster index mod 1024) while they copy or write a 16-byte entry. A probe returns a copy (`TTProbe`), never a pointer into the table. `hashfull` locks too. `prefetch` only issues `__builtin_prefetch`, which is not a memory access. A single-threaded search takes an exclusive lease, so no locking happens. The lock-free variant is O1-LTT (separate option, separate job). |
| **TT lifecycle** | `generation_` and `epoch_` are plain members. They are written by `new_search` / `clear` / `resize` only. `new_search` runs in `Searcher::search` before the helper threads are created; thread creation gives the happens-before. `clear` / `resize` run from the UCI thread only after `stop_search()` has joined the search thread. A `store` with a stale probe (epoch changed) is rejected. OK. |
| **Shared counters** | Each worker publishes `nodes_` (atomic, relaxed) from `should_stop()`. `total_nodes()` sums the other workers' published counts. No race, but **the counts are stale between searches: bug 1.** |
| **`all_workers_` lifetime** | Points to a `std::vector<Worker*>` local to `Searcher::search`. It is valid during the search and **dangles afterwards: bug 2** (latent). |
| **Stop hand-over** (`searcher.inc`) | The main worker returns, then the Searcher reads the external stop flag, sets `stop`, joins the helpers and restores the flag. A `stop` arriving between the read and the store is overwritten. This is harmless: the result is already final, and the next `go` resets the flag (`reset_stop`). The helpers poll `stop` in `should_stop`, which is atomic and sufficient. |
| **Best move across workers** | AL1 always reports thread 0's result (move, PV, score, depth). The helpers' results are discarded. Correct, but it can report a shallower line than a helper finished. The OFF-default option `SmpBestThread` addresses this. |
| **`setoption Threads` while idle / right after `stop`** (`uci.cpp`) | Every `setoption`, `ucinewgame`, `position`, `go` and `stop` first calls `stop_search()`. That sets the flag, wakes a waiting infinite/ponder search and joins the search thread before anything is changed. `set_threads` runs only when no worker thread exists. Stressed by `uci_stress.py` (`stop_threads`, `go_stop_race` scenarios); TSan clean. |
| **`ucinewgame`** | Stops and joins first, then clears the TT and every worker's histories and caches. OK. |
| **`go infinite` / `ponderhit` / `isready` during search** | `isready` is answered at once by the UCI thread. Output is serialised by `uci_output_mutex`. An infinite or ponder search that finishes early waits on a condition variable for `stop`, or for `ponderhit` in the ponder case, before printing `bestmove`. `ponderhit` sets `ponder_hit_ns` atomically, which starts the clock. 500/500 stress iterations: 1 bestmove per go; max stop latency 68 ms and max isready latency 53 ms under TSan, 2 ms and 1 ms in a normal build. |
| **Bench** | `bench` uses its own single-thread `Searcher`, so the `Threads` option never changes bench. |

## Bugs

### Bug 1: stale helper node counters make `go nodes N` at Threads > 1 play an unsearched move
- **Cause.** A helper publishes its node count only from inside its own search. Until it starts, the count of
  the previous search stays published. At the next `go nodes N`, the main thread checks the node budget at
  every node, sums those stale counts and stops before depth 1 completes. The engine then plays the first
  legal move with no completed iteration and no info line. The same effect inflates nodes/nps in the first
  info lines of any multi-thread search.
- **Repro.** `repro_stale_nodes.py`: Threads 3, kiwipete, `go depth 13` then `go nodes 20000`, 5 rounds
  (`logs/repro_stale_nodes.log`). `tests/smp_tests.cpp` fails 10/10 without the fix.
  - AL1 s198 lock exe: **4 of 5** rounds returned `bestmove a2a3` with no completed iteration. The failure
    depends on how fast the helpers start; earlier runs gave 5/5.
  - O1 exe with the option off: 5 of 5.
- **Fix, `44b2db1`.** UCI `SmpExactNodes`, default false. It changes Threads > 1 node accounting, so it is an
  option and not a silent fix. Every worker's published count is reset before the helpers start, and the
  exact total is reported after they stop.
  - With the option on: **0 of 5**. Every round completed depth 9-12 and played `e2a6`.
  - Threads=1 is unaffected: bench is identical, and the option is inert at Threads=1 (tested).

### Bug 2: `Worker::all_workers_` dangles after every search (latent use-after-scope)
- **Cause.** The pointer to the Searcher's local worker list survived the call. Nothing reads it between
  searches today, but any later use would read freed stack memory.
- **Repro.** `tests/smp_tests.cpp` "worker list pointer cleared" fails 2/2 (Threads 1 and 3) on the unfixed
  tree.
- **Fix, `c994f6e`.** `Searcher::search` calls `Worker::end_search()` for every worker after the join. No
  behaviour change (bench identical), so no option.

### Improvement (not a bug): `SmpBestThread`, `0abed6a` + review fix
UCI `SmpBestThread`, default false, acts only with Threads > 1.
- **What it reports.** The best move, ponder move, PV and score of the best worker instead of always thread
  0's. One extra info line with that PV is printed so that GUIs see a consistent line.
- **Ranking** (`better_thread_result`, src/search/searcher.inc), after the code review:
  - **As soon as either result carries a mate score, the higher score wins.** A found mate is never
    replaced by a deeper line without one, a shorter mate beats a longer one, and any line that is not
    mated beats a mated one.
  - **Without mate scores,** the deeper completed iteration wins, then the higher score.
  - **The old rule** (`0abed6a`: deepest iteration first, always) let a deeper helper override a found mate.
    That was the review finding.
- **Test.** `tests/smp_tests.cpp` `test_best_thread_ranking` has 13 cases: deeper non-mate vs found mate,
  deeper longer mate vs shorter mate, shallower found mate vs deeper non-mate, mated vs not mated, two mated
  lines. With the old rule planted back, 8 of the 13 cases FAIL (`logs/review_fix_mutation.log`); with the
  fix, all 70 checks of `forge_smp_tests` pass (`logs/review_fix_smp_tests.log`).
- **CI after the fix** (`85c15e3`):
  - opus-ci 40467016547: release, ASan+UBSan and TSan pass, with only the 4 known lines;
  - opus-o1-smp 40467016636: all 5 self-play shards pass. The options-on shard (SmpExactNodes +
    SmpBestThread, i.e. the new ranking) played 500 games: 0 illegal moves, 0 crashes, 0 stalls or missing
    bestmoves, 0 time forfeits (`logs/ci/selfplay-options-on-85c15e3/pgn_legality.log`).
- **How results are collected.** Helper results go into one slot per helper and are read after the join.
- **Layout.** `select_best_thread` and `better_thread_result` are `[[gnu::cold]]`, and `format_score` is
  always inlined, so the default build's hot code is unchanged. Re-checked after the fix: the default build
  is identical at all 5 depths, and the codegen has the same two differences as before
  (`logs/review_fix_identity.log`, `logs/review_fix_codegen.log`).

## Default build: hot code and speed
- **Codegen** (`codegen_compare.sh`, lock exe vs O1 exe, PC recipe; `logs/codegen_lock_vs_o1.log`):
  - Alpha-beta, qsearch, static_evaluate, TT probe/store, should_stop, is_draw, the correction and history
    functions, record_move, the NNUE functions, make/unmake and see_ge are instruction-identical at the same
    address mod 64.
  - `MovePicker::next` reports 32 "differing" lines. An objdump diff shows they are 32 trailing nop padding
    lines and 12 RIP-relative displacements to moved data; the instructions are identical.
  - The per-iteration driver `Worker::search(Board, ...)` differs, because `format_score` is now inlined
    there. It runs once per iteration, not per node.
- **NPS** (`nps_ab.py`, lock exe vs O1 exe, PC recipe, 10 ABBA runs, node counts equal in every run, busy
  PC at BelowNormal priority; `logs/nps_ab_lock_vs_o1.log`). No measurable change:
  - d16: CPU +0.00% (95% CI −4.01 .. +4.01), wall +1.92% (−1.39 .. +5.24);
  - d20: CPU +0.65% (−1.59 .. +2.90), wall +0.62% (−0.79 .. +2.04).

## Scaling (Threads 1/2/4/8; CI run 40381524051, `logs/ci/scaling/`)

**Setup:** `scaling.py`, 36 positions (the 8 bench positions + 14 ECM + 14 Forge openings), `go depth 20`, 5
runs per thread count, Hash 16, a fresh `ucinewgame` per position. The machine is a GitHub runner: AMD EPYC
7763, **4 vCPUs = 2 cores x 2 SMT threads**.

| Threads | time-to-depth mean (sd) | speedup | nodes mean | node overhead | NPS mean | NPS scaling |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 41.42 s (0.09) | 1.00x | 54,933,743 | 1.00x | 1,326,254 | 1.00x |
| 2 | 36.86 s (2.43) | 1.12x | 88,900,038 | 1.62x | 2,415,477 | 1.82x |
| 4 | 42.13 s (1.68) | 0.98x | 131,590,722 | 2.40x | 3,123,938 | 2.36x |
| 8 | 61.82 s (5.60) | 0.67x | 196,123,055 | 3.57x | 3,172,082 | 2.39x |

**Analysis.**
- **NPS** scales 1.82x with 2 threads on 2 physical cores. That is a good ratio: the TT is shared through
  striped locks, and the gap reflects memory and lock traffic.
- **Threads 4** only adds SMT siblings: +30% NPS over 2.
- **Threads 8** is oversubscribed (8 engine threads on 4 hardware threads) and adds no NPS.
- **Time-to-depth** is the Lazy SMP weak point: each extra thread searches many duplicate or speculative
  nodes. The node overhead (1.62x at 2 threads) eats most of the NPS gain, so depth 20 is reached only 1.12x
  sooner.
- **On this machine** 4 and 8 threads reach depth more slowly than 1. The NPS added by SMT and
  oversubscription does not cover the 2.4-3.6x node overhead, and the extra threads also slow each other
  down.
- **This is not a defect,** for three reasons:
  - Lazy SMP trades time-to-depth for a wider, deeper-checked tree, so strength at equal time is what
    matters, and that is QA's Threads 4 vs Threads 1 gate.
  - Depth-20 time-to-depth is noisy (sd 2-6 s with helpers).
  - No hang or crash occurred in 40 x 36 searches.
- **QA should repeat** `scaling.py` on a machine with at least 8 idle cores to get 4- and 8-core numbers.
  The command is in "How to reproduce".

## Proposed gates (SMP-only; one option per gate; QA sets srand and ID)
1. **`SmpExactNodes=true`**:
   - candidate: O1 exe with the option; opponent: the same O1 exe without it. Both Threads 4, Hash 16
     (or 64 at 40+0.4), OwnBook false.
   - SPRT [0,10] at 10+0.1 per `GATE_RULES.md`.
   - Expected effect at time controls: small (it only removes inflated early node counts). The point is
     correctness of `go nodes` at Threads > 1: a functional fix that matters for node-limited matches.
2. **`SmpBestThread=true`**: same setup, candidate with `SmpBestThread=true`. SPRT [0,10] at 10+0.1, then a
   confirm at 40+0.4 if H1.

The lock does not count these toward the single-thread gate: both options are inert at Threads 1. Self-play
seeds 9901-9905 were used only for the robustness games above, not for any gate.

## Files
- **Engine:** `include/forge/search_options.hpp`, `src/search/options.inc` (option storage),
  `src/search/searcher.inc`, `include/forge/search.hpp`, `src/search/uci_info.inc`, `src/uci.cpp`.
- **Tests:** `tests/smp_tests.cpp` (CTest `forge_smp_tests`).
- **Tools** (`opus_round1/O1/`): `ucilib.py`, `uci_stress.py`, `smp_depth.py`, `selfplay.sh`,
  `pgn_legality.py`, `scaling.py`, `repro_stale_nodes.py`, `tsan_extra.sh` (short per-push TSan hook),
  `tsan_full.trigger`.
- **CI:** `.github/workflows/opus-o1-smp.yml` (self-play, scaling) and `opus-o1-tsan-full.yml` (the
  full-size TSan acceptance, sharded).
- **Report folder:** `REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `logs/`, `SHA256SUMS`.

## TSan CI timeout (run 40367007552)
- **What happened:** the first O1 TSan job ran 52 min. It ended with "The hosted runner lost communication
  with the server" and no log.
- **Diagnosis:** a starved runner, not a hang.
  - The old hook ran the full acceptance load (200 x depth 12 at Threads 2/4/8 + 700 stress iterations)
    under TSan on 4 vCPUs, with 8 engine threads and all output redirected to files.
  - The same loads finish locally (stress 500/500, depth 12 at Threads 2/3).
  - They finish on CI when sharded (run 40381524268, the longest shard 19.4 min, each with a per-minute
    memory/CPU monitor).
- **Fix, `33b0790`:**
  - the per-push hook is short: 40 positions x depth 8 at Threads 2/4, 120 stress iterations, option-on runs;
  - each test runs under its own timeout and prints its name at start, end and timeout;
  - the engine runs under `nice`.
- **Result:** the next opus-ci TSan job took 5.5 min (run 40381524034). The full load runs in the separate
  sharded workflow.

## How to reproduce
```
python3 opus_round1/O1/uci_stress.py <forge> --iterations 500 --seed <s> --positions <epd>
python3 opus_round1/O1/smp_depth.py <forge> --positions tools/openings/forge-10000.epd --count 200 --depth 12 --threads 2,4,8
bash opus_round1/O1/selfplay.sh <forge> 500 out <srand>      # then pgn_legality.py out/games.pgn
python3 opus_round1/O1/scaling.py <forge> --positions <file> --threads 1,2,4,8 --runs 5 --depth 20
python3 opus_round1/O1/repro_stale_nodes.py <forge> --threads 3 --rounds 5 [--option SmpExactNodes=true]
```
