# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:31:05 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on_v1net | opus_r3sp_allsw.exe `baa4d9a65513` | 2 | SyzygyPath=/home/runner/syzygy345, CorrHistPlus=7, CorrMargins=1, CorrExt=1, CuckooRep=true, MaterialKeyTable=true, NetScale=99, HistRework=2, IntendedThreefold=true, HardDeadline=10, LocklessTT=true, SmpExactNodes=true, SmpBestThread=true, TtChildPrefetch=true, NnueLazyAcc=true, Profile=true, NnueInt16=true | 500/500 | 56027 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 332408 | 579.4 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on_v1net | 58783 | 57264 | 2499920 | 59783 | 2638 | 1658 | 32501/4530/5667/4411/3361/2731/2826 | 0 | 58783 | 0 (0.0 ms) | checkmate 424, threefold 46, ply_cap 20, insufficient_material 7, fifty_moves 3 |
