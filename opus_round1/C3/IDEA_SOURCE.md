# IDEA_SOURCE: C3 hard time deadline / bestmove latency (UCI HardDeadline, default 0)

| element | idea source | code copied? |
|---|---|---|
| Problem statement (no-bestmove stall, 12 s on a 1000 ms move, WAC.008) | Engine Coder crew job C3 in OPUS_PROMPT.md; WAC300 harness in 4_tests/wac300_harness | — |
| Polling the clock from the search at a fixed node cadence, a separate hard limit above the soft limit | Stockfish TimeManagement / check_time idea (as named in the job), CPW "Time Management" — concept only; Forge already had both | No |
| Watchdog thread that answers at the hard deadline with the best move of the last completed iteration, independent of the search threads | Own design. General "watchdog timer" technique; the UCI protocol requires exactly one `bestmove` per `go`, which the claim flag enforces | No |
| Raising only the near-idle control threads (input loop, watchdog) to time-critical priority so they are scheduled on time when the CPU-bound search threads of a niced/starved process are not | Own design using the documented Windows scheduling rules (process priority class x thread priority; time-critical threads run before normal ones; the balance-set manager boosts starved threads only every few seconds) — Microsoft docs "Scheduling Priorities", "Priority Boosts" | No |
| Latency test design (go movetime on every WAC position, ucinewgame + Clear Hash + isready per position, wall time from `go` to `bestmove`) | QA's WAC300 harness (4_tests/wac300_harness/tactics.py), re-implemented with per-line arrival timestamps, missing/duplicate detection and starvation knobs | No (new script) |

No Elo claim. The option does not change any search decision while the search answers on time.
