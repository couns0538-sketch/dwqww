# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:33:17 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on | opus_r3sp_allsw.exe `fef5e70d73b9` | 2 | SyzygyPath=/home/runner/syzygy345, CorrHistPlus=7, CorrMargins=1, CorrExt=1, CuckooRep=true, MaterialKeyTable=true, NetScale=99, HistRework=2, IntendedThreefold=true, HardDeadline=10, LocklessTT=true, SmpExactNodes=true, SmpBestThread=true, TtChildPrefetch=true, NnueLazyAcc=true, Profile=true, NnueInt16=true, NNUEKingBuckets=8, NNUEOutputBuckets=8, NNUEThreats=1, NNUEPawnPairs=1, NNUEFile=/home/runner/work/dwqww/dwqww/sp_out/nets/replica_rm8_ob8_thr0_pp0.fnn2 | 250/250 | 29111 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 654 | 362031 | 452.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on | 30519 | 29249 | 752057 | 31019 | 1445 | 858 | 16980/2257/2922/2400/1681/1433/1438 | 654 | 29865 | 0 (0.0 ms) | checkmate 199, ply_cap 21, threefold 19, insufficient_material 10, fifty_moves 1 |
