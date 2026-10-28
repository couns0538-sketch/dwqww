# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:15:38 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on_pure | opus_r3sp_allsw.exe `51e46d533c37` | 2 | SyzygyPath=/home/runner/syzygy345, CorrHistPlus=7, CorrMargins=1, CorrExt=1, CuckooRep=true, MaterialKeyTable=true, NetScale=99, HistRework=2, IntendedThreefold=true, HardDeadline=10, LocklessTT=true, SmpExactNodes=true, SmpBestThread=true, TtChildPrefetch=true, NnueLazyAcc=true, Profile=true, NnueInt16=true, NNUEKingBuckets=8, NNUEOutputBuckets=8, NNUEThreats=1, NNUEPawnPairs=1, PureNnue=1, NNUEFile=/home/runner/work/dwqww/dwqww/sp_out/nets/pure_material_rm8_ob8_thr0_pp0.fnn2 | 100/100 | 12860 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 644 | 368464 | 345.1 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on_pure | 13484 | 12827 | 216797 | 13684 | 634 | 388 | 7523/1030/1260/1031/740/638/638 | 644 | 12840 | 0 (0.0 ms) | checkmate 79, ply_cap 15, threefold 5, insufficient_material 1 |
