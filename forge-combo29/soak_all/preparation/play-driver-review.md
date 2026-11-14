# Read-only review of Part 2 D/E/F self-play driver

Review snapshot: 2026-11-14 13:19:19 UTC. This was source, build-record and binary-metadata inspection only. No new engine search, sanitizer workload or reproduction was run. No engine, driver, controller or state file was edited. This note records coverage and its limits; it is not a new pass result.

Repository-relative source references below use `forge-combo29/` as their root. The reviewed driver SHA256 is `643f22459bb553df15e14d8777ce9c157f88bc5406b56bfa60bbc2889e70af41`. Existing ASAN driver: `466c2860dffe90589275ed1bdb848549c15ff1e69234e279684bc054d0ae8f5c`. Existing TSan driver: `5e2cb4e2e82b99e2e7620dcbfa44be71cfadcf6e82cde7b51a8d4f8f3fc1ab91`.

## Search and threading paths

The driver reaches the real engine search implementation. `soak_all/play_driver.cpp:104` calls `Searcher::search`, with no replacement search algorithm. `/workspace/work/all-run/build-tests.mjs:11` selects the seven built engine objects excluding `uci.cpp.o`; lines 13–14 and 20 archive/link them into the drivers. The preserved `preparation/build-tests-asan.txt` and `build-tests-tsan.txt` contain the actual commands and successful exits. Core object flags include address+undefined sanitizers or ThreadSanitizer, respectively. The core objects use the CMake Release optimization/assertion settings; the separate sanitizer driver translation unit uses `-O1 -g -UNDEBUG`. This is not an assertion-enabled build of every engine object.

Static `readelf -d` inspection of the current binaries reports `libasan.so.8` and `libubsan.so.1` for the ASAN driver, and `libtsan.so.2` for the TSan driver. Library presence alone is not a claim that a sanitizer workload completed; actual reports/exits belong to each batch's raw evidence.

Candidate controls are assigned before any Searcher or helper exists: `soak_all/play_driver.cpp:55` through line 64 sets all three `forge::tune` booleans and `forge::nnue::enabled=true`, then constructs `Searcher(16, threads)`. The booleans remain unchanged for the run. `include/forge/search.hpp:43` defaults `SearchLimits::multipv` to 1. No driver code changes it.

`src/search.cpp:1953` creates the requested worker count, clamped to 1–256. The inspected D/E/F specs use valid counts 1, 2 or 4. At MultiPV 1, `src/search.cpp:1984` through line 1989 supplies all workers; lines 2016–2020 launch the actual helper threads. The main worker searches at line 2023, and lines 2025–2028 request helper shutdown and join them. Thus configured Threads 2 or 4 does not silently use the MultiPV single-worker fallback. This source-level conclusion does not enumerate which individual heuristic branches every finite workload reaches.

## TT access is appropriate

The driver's `TTAccess::Exclusive` request does not disable synchronization for multiple workers. `src/search.cpp:1993` through line 1998 acquires an exclusive lease only with one worker (or MultiPV greater than 1). For T2/T4 at MultiPV 1, no lease exists and `tt_owned_` is false. `include/forge/search.hpp:393` through line 399 then uses the normal shared probe/store functions; `src/search.cpp:248` through line 257 implements striped locking.

For T1, exclusive access is appropriate because this synchronous driver has no concurrent TT diagnostic caller. The production UCI entry uses the same exclusive request at `src/uci.cpp:400` through line 401. `Searcher::clear()` runs only when no helper search is active. There is no evidence here of a driver-specific lock bypass that would hide the normal T2/T4 TT races.

The API driver bypasses the UCI parser, asynchronous UCI stop/ponder handling, concurrent option changes, engine process transport and book-loading paths. OwnBook false is effective because the direct Searcher path does not consult the UCI book shortcut; `src/uci.cpp:373` is where that shortcut would otherwise run. These self-play batches complement, rather than replace, UCI protocol and startup/stop tests.

## Limits and inspected batch configurations

`soak_all/play_driver.cpp:101` through line 104 uses requested depth when positive; otherwise it sets depth 64 and an explicit node budget. Therefore the TSan specs' `--nodes 0 --depth 9` exercise depth-9 searches and do not invoke the zero-node early-return path. The D/F specs request 2,000 or 20,000 nodes with depth 0. The driver does not assert exact achieved nodes or completed depth for every returned search.

Inspected saved specs:

| Phase | Configured conditions in saved specs |
| --- | --- |
| D | ASAN+UBSAN; T1/T2; 2,000/20,000 requested nodes; all three options false. D-0001 omits `--trace`; subsequent saved D specs include it. |
| E | TSan; T2/T4; depth 9; all three options false; full pre-search trace. |
| F | ASAN+UBSAN; T1/T2; 2,000/20,000 requested nodes; all three options true; full pre-search trace. |

A saved spec is not proof that its workload has finished. Options enabled in configuration are not an instrumented proof that each option's internal conditional path was executed in every game. This review does not infer new completed counts or sanitizer findings.

## Legality, score and game-ending checks

At each searched ply, the driver obtains Forge's legal move list before search (`soak_all/play_driver.cpp:90`). It rejects a missing best move or a move absent from that list at lines 107–108, then requires `Board::make_move` to accept it at line 118. These are meaningful consistency checks, but the oracle shares the same Board/move-generation implementation as the search; they are not independent chess-rule verification.

The score check at line 109 accepts only the inclusive range `[-MateValue, MateValue]`, currently [-32000, 32000] (`include/forge/search.hpp:66` through line 69). It rejects the Infinite/ValueNone sentinels, but does not prove a centipawn evaluation, a mate distance/bound, PV legality, search-depth completion or exact node-budget behavior. Successful results' score, depth, nodes and PV are not emitted by this driver.

Game-ending order is coherent for this bounded self-play convention: no legal moves first, distinguishing mate from stalemate; then current-position threefold, halfmove clock at least 100, then the engine's insufficient-material predicate (`soak_all/play_driver.cpp:90` through line 94). `Board::is_repetition()` at `src/board.cpp:1189` through line 1197 requires two earlier matching position keys within the reversible window, i.e. three occurrences including the current position.

The driver automatically adjudicates at the claimable threefold/50-move thresholds; this is not the full FIDE automatic fivefold/75-move procedure. `src/board.cpp:1215` through line 1222 recognizes no-pawn/rook/queen positions with at most one minor, or bishops only on one square color. It is a restricted material predicate, not a general dead-position proof.

The 300-ply cap includes the eight opening plies. A move made at ply 299 can produce mate or a draw, but the loop then exits at 300 and records a cap without another terminal check (`soak_all/play_driver.cpp:89` and line 126). A cap therefore does not establish that the final board is nonterminal. `games` also includes games ended by a detected fault (line 127); it must not be interpreted as a count of fault-free completed games.

The eight opening plies are sampled from legal moves with deterministic per-game seed derivation (`soak_all/play_driver.cpp:73` through line 87). Opening setup failures return 3/4 before the normal FAULT/SUMMARY path, so the process exit remains relevant evidence. The time budget is checked only between games at line 72; one game/search can overrun `--seconds`. The orchestrator's external timeout remains necessary, and a killed/incomplete batch cannot be silently promoted to completed coverage.

## Trace contents and reproduction guidance

With `--trace`, each pre-search TRIGGER is flushed before entering search (`soak_all/play_driver.cpp:95` through line 104). It supplies seed, absolute game index, ply, threads, node/depth settings, all candidate options, FEN and the complete `position startpos moves ...` history. Thus the trace provides the exact board/history and configured search input, including repetition-relevant played moves. A saved FEN alone does not preserve that history.

The trace is a pre-search input trace, not a full search-state checkpoint. `Searcher` is cleared at game start only (`soak_all/play_driver.cpp:77`; `src/search.cpp:1968` through line 1970). The same Searcher serves both colors and retains TT entries and search histories across subsequent plies. A lone saved FEN, or even one complete UCI position command submitted to a fresh process, does not reconstruct that warmed TT/history state.

To investigate a fault, preserve the original evidence and rerun the same driver binary/build and batch seed, with `--first-game` set to the fault's absolute `game` value and `--games 1`. Preserve all options, threads and node/depth settings from the fault's TRIGGER/CONFIG; use `--trace` and a new trigger/output path. This re-enters the game's seeded opening and re-executes its preceding engine searches, providing the appropriate attempt to reconstruct warming instead of jumping directly to the fault FEN. It does not guarantee identical SMP scheduling or identical subsequent play. Compare the replay's saved history with the original at the reported ply and report divergence rather than treating a nonmatching replay as a clean reproduction.

Illustrative argv template only; it was not executed in this review:

```text
<same play_driver> --seed <original batch seed> --first-game <fault game>
  --games 1 --threads <original threads> --nodes <original nodes>
  --depth <original depth> --seconds <bounded attempt budget> --trace
  --trigger <new scratch trigger path>
  --ContHist4PlyRead <original boolean>
  --NonPawnCorrection <original boolean>
  --LmrDeeperShallower <original boolean>
```

Keep the original sanitizer environment and an external command timeout below eight minutes. A one-game attempt that exceeds the external bound remains incomplete. Full-game replays, fresh isolated-position searches and deterministic forced-history replays are different conditions and should be labeled separately; none should be described as a byte-for-byte SMP state restoration.

Each successful search's result can often be inferred as the next TRIGGER's added move, but the terminal/capped game's last returned move has no following TRIGGER, and scores/nodes/PVs are not logged for successful searches. `--trigger` overwrites one last context rather than retaining a history; its file-write result is unchecked at line 100. The stdout trace is the durable full sequence when present. D-0001, which omitted `--trace`, retains only summary counters and its final trigger, so it lacks per-search trace enumeration.

On FAULT, the driver prints input context plus the offending result, ends that game, then continues with another game. It does not itself run ten fresh reproductions. Any required repetition frequency must come from separately recorded attempts, not be inferred from the initial FAULT or from the game's preceding searches. Sanitizer diagnostics are produced by the runtimes and must be inspected in raw output; a zero driver `faults` counter is not itself a zero-race/zero-sanitizer-report claim.

## Review conclusion

No blocking mismatch was found in the configured thread/option/TT paths for the saved D/E/F specs. The driver exercises the actual instrumented core, including real T2/T4 helper threads, with options set before helper creation. Its legality and score checks are bounded consistency checks, and its endings implement the stated self-play convention. The substantive reporting limits are shared legality code, restricted score validation, game-boundary timing, warm search state, pre-search-only traces, no automatic ten-run reproductions, and D-0001's missing full trace. No strength or speed conclusion is supported or claimed.
