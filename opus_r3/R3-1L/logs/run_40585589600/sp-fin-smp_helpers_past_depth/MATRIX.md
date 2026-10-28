# R3-1 self-play matrix, git head 6f4067c3

Generated 2026-10-27 21:41:36 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_helpers_past_depth | opus_r3sp_base.exe `d6190041a757` | 2 | SmpHelpersPastDepth=true | 500/500 | 48500 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 442.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_helpers_past_depth | 50915 | 46326 | 2315776 | 51915 | 2275 | 1416 | 28192/3892/4855/3877/2859/2350/2475 | 0 | 0 | 0 (0.0 ms) | checkmate 444, insufficient_material 24, threefold 19, ply_cap 8, stalemate 5 |
