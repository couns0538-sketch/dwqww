# R3-1 self-play matrix, git head 330237f3

Generated 2026-10-27 22:55:10 by run_matrix.py from F:/opus_scratch/r3/R3-1L/smoke/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure_nnue | opus_r3sp_base.exe `07eb6fdeb058` | 1 | PureNnue=1, NNUEFile=F:/opus_scratch/r3/R3-1L/smoke/nets/pure_material.fnn2 | 10/10 | 1098 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 450072 | 10.0 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pure_nnue | 1156 | 1074 | 45571 | 1176 | 53 | 34 | 654/87/97/90/56/54/60 | 0 | 0 | 0 (0.0 ms) | checkmate 9, insufficient_material 1 |
