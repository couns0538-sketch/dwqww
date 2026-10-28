# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:23:27 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on_v1net | opus_r3sp_allsw.exe `51e46d533c37` | 2 | SyzygyPath=/home/runner/syzygy345, CorrHistPlus=7, CorrMargins=1, CorrExt=1, CuckooRep=true, MaterialKeyTable=true, NetScale=99, HistRework=2, IntendedThreefold=true, HardDeadline=10, LocklessTT=true, SmpExactNodes=true, SmpBestThread=true, TtChildPrefetch=true, NnueLazyAcc=true, Profile=true, NnueInt16=true | 100/100 | 11049 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 518 | 332408 | 247.1 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on_v1net | 11581 | 11060 | 237227 | 11781 | 531 | 330 | 6526/896/1051/884/635/514/543 | 518 | 11063 | 1 (0.1 ms) | checkmate 86, threefold 6, ply_cap 4, insufficient_material 4 |
