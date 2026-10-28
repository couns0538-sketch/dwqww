# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:12:29 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on | opus_r3sp_allsw.exe `baa4d9a65513` | 2 | SyzygyPath=/home/runner/syzygy345, CorrHistPlus=7, CorrMargins=1, CorrExt=1, CuckooRep=true, MaterialKeyTable=true, NetScale=99, HistRework=2, IntendedThreefold=true, HardDeadline=10, LocklessTT=true, SmpExactNodes=true, SmpBestThread=true, TtChildPrefetch=true, NnueLazyAcc=true, Profile=true, NnueInt16=true, NNUEKingBuckets=8, NNUEOutputBuckets=8, NNUEThreats=1, NNUEPawnPairs=1, NNUEFile=/home/runner/work/dwqww/dwqww/sp_out/nets/replica_rm8_ob8_thr0_pp0.fnn2 | 500/500 | 55287 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 362031 | 564.3 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on | 58072 | 56692 | 2396803 | 59072 | 2641 | 1605 | 32141/4400/5563/4362/3214/2744/2863 | 0 | 58072 | 0 (0.0 ms) | checkmate 415, threefold 51, ply_cap 21, insufficient_material 10, fifty_moves 2, stalemate 1 |
