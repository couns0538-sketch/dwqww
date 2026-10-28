# R3-1 self-play matrix, git head 6f4067c3

Generated 2026-10-27 21:44:33 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on_final | opus_r3sp_allsw.exe `33a1a1c8e2ab` | 2 | SyzygyPath=/home/runner/syzygy345, CorrHistPlus=7, CorrMargins=1, CorrExt=1, CuckooRep=true, MaterialKeyTable=true, NetScale=99, HistRework=2, IntendedThreefold=true, HardDeadline=10, LocklessTT=true, SmpExactNodes=true, SmpBestThread=true, TtChildPrefetch=true, NnueLazyAcc=true, Profile=true, NnueInt16=true, SmpHelpersPastDepth=true, NNUEKingBuckets=8, NNUEOutputBuckets=8, NNUEThreats=1, NNUEPawnPairs=1, NNUEFile=/home/runner/work/dwqww/dwqww/sp_out/nets/replica_rm8_ob8_thr0_pp0.fnn2 | 500/500 | 55037 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 362031 | 595.3 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on_final | 57753 | 56318 | 2244404 | 58753 | 2623 | 1673 | 31991/4407/5491/4353/3321/2692/2782 | 0 | 57753 | 0 (0.0 ms) | checkmate 419, threefold 48, ply_cap 17, insufficient_material 14, stalemate 1, fifty_moves 1 |
