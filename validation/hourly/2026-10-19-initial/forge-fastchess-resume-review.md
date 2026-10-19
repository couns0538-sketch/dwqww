# fastchess recovery review for Forge 6.4

Reviewed source: official `Disservin/fastchess`, commit `ebfd64cb7fac80d4822c50b07dca4fe934779d21`, binary `fastchess alpha 1.8.2 20261011-ebfd64c`.
This was a read-only source/manual review. No matches, tests, or benchmarks were run by this reviewer.

## Decision

**Use naturally completed cumulative-round tranches: 100 rounds, then resume to a total of 200, then 300, up to the separately predeclared ceiling of 10,000 pairs. Do not use scheduled SIGINT as a normal checkpoint boundary.** Keep one unchanged SPRT: logistic `[0,5]`, the predeclared alpha/beta, engines/networks/options, 10+0.1 clock, Hash 64, Threads 1, six active lanes, opening suite/seed and adjudication.

Natural completion gives a complete prefix of opening/color pairs. An SPRT boundary is terminal, even when it occurs before the current tranche's pair cap. Finishing a tranche, or exiting with code 0, is not itself an SPRT pass.

## Why cumulative resume works

- `cli.cpp:485-507` loads tournament settings, both engines and stats. `stats=true` retains the loaded stats; only `stats=false`, `discard=true`, or more than two engines causes the loader to clear them (`510-537`).
- CLI switches execute in argument order (`cli.hpp:215-250`). `parseRounds` merely replaces `tournament_config.rounds` (`cli.cpp:590-591`). **Put `-rounds 200` after `-config ...`; rounds means cumulative total, not additional rounds.**
- Loaded `wins + losses + draws` becomes `initial_matchcount_` (`base/tournament.cpp:29-39,331-344`). For two games per round, the scheduler starts at `completed_games / 2 + 1`; its game IDs start at `completed_games + 1` and its pair ID at `completed_games / 2` (`schedule/base_scheduler.hpp:16-28,43-53`).
- With two engines, the total is `rounds * games` (`roundrobin/scheduler.hpp:19-21`). A fully completed 100-round state has 200 games. Resuming it with `-rounds 200` schedules another 200 games, for 400 cumulative games and 200 complete pairs.
- At natural exhaustion the main loop waits until all scheduled games finish (`roundrobin/roundrobin.cpp:43-51`). The destructor joins worker activity and then saves the final JSON (`base/tournament.cpp:61-87`).

## Concrete commands

Use absolute paths. The following continuation assumes the first 100-round checkpoint was validated and the SPRT remains undecided. `/ABS_RUN` and `ALLOCATED_CPU_LIST` are placeholders for the parent task's actual paths/allocation:

```sh
/tmp/forge64-fastchess/fastchess \
  -config file=/ABS_RUN/checkpoint-0100.json stats=true outname=/ABS_RUN/checkpoint-0200.json \
  -rounds 200 \
  -use-affinity ALLOCATED_CPU_LIST \
  -log file=/ABS_RUN/tranche-0200-engine.log level=trace engine=true append=false \
  > /ABS_RUN/tranche-0200-runner.log 2>&1
```

For the following tranche, load `checkpoint-0200.json`, set `outname=...checkpoint-0300.json`, and put `-rounds 300` afterwards. Do not re-add `-engine` entries or use `stats=false`. No other SPRT or engine settings need to be reapplied because they are loaded from the checkpoint. Reapply any explicitly chosen options omitted from serialization, as listed below.

For the initial tranche, add `-games 2 -rounds 100 -report penta=true -config outname=/ABS_RUN/checkpoint-0100.json` to the full predeclared match command. Store the overall 10,000-pair ceiling in the external protocol: the native config records only that tranche's cumulative cap. Use a distinct new config output for every tranche so the prior completed checkpoint stays immutable.

## Opening continuity and PGNs

`TournamentManager` seeds the PRNG from saved `seed` before constructing the book (`tournament_manager.cpp:43`). The book reloads the same file, runs the same Fisher-Yates shuffle when random order is selected, then rotates it by `opening.start - 1 + completed_games / games` (`opening_book.cpp:15-24,40-50`; `opening_book.hpp:19-40`). It does not save a PRNG cursor, because it reconstructs the sequence from the seed and completed-game count. With a complete prefix and unchanged source book/order/seed, this continues at the next opening. Changing the cumulative `rounds` cap does not skip extra openings; it only changes how much of the rotated list is retained.

The same `Round` header is assigned to both games of a pair (`base/tournament.cpp:266`; `pgn_builder.cpp:31`). PGN records arrive in completion order, not numerical round order. Validate by `(Round, White, Black)` and starting FEN, rather than by raw file order or timestamps.

When loaded stats contain any games, PGN and EPD writers force append mode, even if the saved flag says `append=false` (`base/tournament.cpp:41-55`). A cumulative PGN therefore continues safely provided its existing contents match the checkpoint. **Engine trace logs do not receive this override:** saved `log.append_file=false` truncates an old log when reopened (`logger.cpp:26-42`). Use distinct per-tranche trace and stdout files, as above, or deliberately append.

## Checkpoint fields and acceptance checks

The native config includes `stats`, `engines`, `sprt`, `games`, `rounds`, `seed`, `opening`, `pgn`, `log`, `concurrency`, `report_penta`, color/variant flags and adjudication settings. It does **not** contain the live game counter, completed pair IDs, partial-pair cache, LLR/terminal SPRT state, engine hashes, book hash, or runner identity.

For the one `stats["CANDIDATE vs BASELINE"]` entry, inspect these exact fields: `wins`, `losses`, `draws`, `penta_WW`, `penta_WD`, `penta_WL`, `penta_DD`, `penta_LD`, `penta_LL` (`scoreboard.hpp:45-63`; `stats.hpp:86-98`). Let `P` be the sum of the six penta fields. Require:

```text
wins + losses + draws = 2*P
wins   = 2*penta_WW + penta_WD + penta_WL
losses = 2*penta_LL + penta_LD + penta_WL
draws  = 2*penta_DD + penta_LD + penta_WD
```

For a resumable natural 100-round checkpoint, require `P=100`, 200 counted games and 200 cumulative PGNs, with rounds 1 through 100 each containing exactly two games, swapped colors and identical starting positions. The next 200-round checkpoint must extend the prefix through round 200 and have `P=200`. Verify stats against PGN outcomes. Retain every crash, illegal move or timeout in the evidence and result.

Before each continuation, verify runner/engine/network/opening SHA-256 hashes against the external protocol. Check `engines[].name`, `cmd`, `dir`, `args`, `restart`, `options`, and `limit`; expected 10+0.1 has `limit.tc.time=10000`, `increment=100`, `fixed_time=0`, `moves=0`, the chosen `timemargin`, and no node/depth restriction. Verify Hash 64, Threads 1, NNUE/book/ponder options, both engine order/identity, the original SPRT bounds/model/alpha/beta, `games=2`, `report_penta=true`, `noswap=false`, and unchanged opening/adjudication/resource policy.

**Serialization omissions:** `affinity_cpus`, `startup_time`, `ucinewgame_time`, `ping_time`, `strict` and `test_env` are absent from the `Tournament` JSON macro (`types/tournament.hpp:85-88`). Reapply explicit `-use-affinity` CPU lists and any nondefault initialization/timeouts/strictness/environment options each time. `concurrency` and the `affinity` boolean do persist, but an affinity boolean alone does not preserve a particular CPU list.

Require a new valid JSON file after process exit; the native config writer uses a truncating `ofstream` with no atomic replacement or checked write result (`base/tournament.cpp:164-169`). Do not promote an autosave or interrupted write to a completed checkpoint merely because it parses. Snapshot the verified final config, cumulative PGN and raw logs before launching the next tranche. A saved config has no terminal SPRT marker, so check the runner's actual stopping result/LLR and do not resume a test already accepted or rejected.

## Why SIGINT is unsuitable for routine tranches

On Linux only SIGINT is registered for graceful runner cleanup; SIGTERM is not handled here (`globals.cpp:94-112`). SIGINT sets `stop=true` and `abnormal_termination=true` immediately (`63-68`). Games detect interruption at turn boundaries, blocked reads are awakened, queued work is discarded and active workers are joined rather than allowed to finish their games (`match.cpp:393-420`; `base/tournament.cpp:61-68`; `threadpool.hpp:51-64`). Interrupted games are not added to PGNs/stats (`base/tournament.cpp:263-279`). The runner writes its final config and exits with failure code 1, normally with a resume message (`main.cpp:33-39,68`).

Only complete pairs reach cumulative stats; a completed first game is held in an in-memory pair cache until its counterpart finishes (`scoreboard.hpp:118-144`). The cache is not saved. PGN writing happens per completed game, so an orphan completed game can be in the PGN but absent from stats.

More seriously, concurrent complete pairs need not form a prefix. If pair 3 has completed while pairs 1 and 2 are unfinished, a saved one-pair count causes native resume to skip opening 1 and restart at opening 2, eventually repeating already-counted opening 3. Pair IDs are not available in native JSON to resolve this. Therefore arbitrary SIGINT checkpoints cannot be assumed to preserve a unique opening sequence, even if their aggregate penta/WDL equations are consistent.

If emergency SIGINT is unavoidable, preserve the checkpoint, all raw logs and PGNs, mark the tranche interrupted and do not automatically resume it as an ordinary completed checkpoint. It needs explicit recovery of pair identities from evidence. Do not silently erase or relabel existing outcomes.

## Minimal infrastructure check for the parent

Run two naturally completed A/A rounds, then native resume to four cumulative rounds, and compare with a fresh uninterrupted four-round control using identical runner/book/seed/options. Confirm checkpoint counters 4 -> 8 games, Round/FEN/color identities 1-2 -> 1-4, no duplicate/omitted pairs, unchanged SPRT settings and preserved logs. Compare structural recovery behavior; wall-clock engine matches need not reproduce identical moves or results. No such test was executed in this review.
