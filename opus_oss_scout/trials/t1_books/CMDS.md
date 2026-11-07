# T1 book resolution - exact commands

Base folder: `C:\opus_5h\oss_scout` (SHA256SUMS paths are relative to it). Every process ran at Idle priority on CPUs 2-3
(inherited from the session process, pid 4532, mask 0xC).

## Inputs
- fastchess 1.8.2-alpha: downloaded with
  `curl -sSfL -o dl/fastchess-1.8.2-alpha/fastchess-windows-x86-64.zip https://github.com/Disservin/fastchess/releases/download/v1.8.2-alpha/fastchess-windows-x86-64.zip`,
  unpacked with `Expand-Archive` to `dl/fastchess-1.8.2-alpha/x/`.
  `fastchess.exe --version` = "fastchess alpha 1.8.2 compiled for windows-latest 20260726-f618e34 (CI)". This is our own
  copy; the gates' fastchess was not run.
- Engine: a copy of `C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe` made to
  `build/lock/forge_trial_w6.exe`.
  - sha256 4181a589... = the live lock trial_w6.
  - forge-uci `pin_check` PASS at 19:27: bench d11 312866, d13 862329, d16 3024920; perft5 startpos 4865609, kiwipete
    193690690.
- Books (copies from `C:\Users\Administrator\grok-pc\coder-fuzz\`):
  - `8moves_v3.pgn`: sha256 5835239f..., the gates' book (RUN_INFO.json of gate_tm_scoreloss1_vs_AL1).
  - `UHO_Lichess_4852_v1.epd`: sha256 7a7f6470..., 174,889,110 bytes. This is the CC0 suite of
    https://github.com/official-stockfish/books.

## Match (tools/t1_run.sh)
```
fastchess.exe \
  -engine cmd=C:/opus_5h/oss_scout/build/lock/forge_trial_w6.exe name=n20k nodes=20000 \
  -engine cmd=C:/opus_5h/oss_scout/build/lock/forge_trial_w6.exe name=n10k nodes=10000 \
  -each proto=uci option.OwnBook=false option.Hash=16 option.Threads=1 \
  -openings file=<book> format=<epd|pgn> order=random \
  -srand 20261106 -games 2 -repeat -rounds 600 -concurrency 2 \
  -ratinginterval 50 -report penta=true -recover -event oss_scout_t1_<tag> \
  -pgnout file=build/t1_books/<tag>/games.pgn -log file=build/t1_books/<tag>/fastchess.log level=warn engine=false
```
- Runs: `bash tools/t1_run.sh uho 600 uho600`, then `bash tools/t1_run.sh 8moves 600 8moves600` (one chain, started
  19:28, log `logs/t1_chain.log`). Smoke first: `bash tools/t1_run.sh uho 2 smoke_uho2` (4 games, 6 s).
- Why fixed nodes: with nodes limits and Threads 1 every move is the same however busy the CPU is, so the crew load on
  CPUs 0-3 cannot change the result, only the wall time.
- Why 2:1 node odds: a clear signal (nElo near 300). Its SE is (800/ln10)/sqrt(2 N) = 10.0 nElo at N = 600 pairs, so
  the ratio between the books is known to about +-10 %.
- OwnBook=false: the lock defaults to OwnBook true, and the gates set it false too.

## T1b (1.33:1 node odds)
`T1_NODES_A=20000 T1_NODES_B=15000 bash tools/t1_run.sh uho 1500 uho1500_n15k`, then the same for `8moves 1500 8moves1500_n15k`.
- One background chain, started 20:13 (log `logs/t1b_chain.log`). The runner now reads the node limits from the
  environment (sha256 in SHA256SUMS); with the defaults it behaves exactly like the T1a version.
- Analysis: `python -I -B tools/t1_analyze.py --engine n20k 8moves=build/t1_books/8moves1500_n15k/games.pgn,build/t1_books/8moves1500_n15k/stdout.txt uho=build/t1_books/uho1500_n15k/games.pgn,build/t1_books/uho1500_n15k/stdout.txt --json repo/opus_oss_scout/trials/t1_books/t1b_result.json`.

## Analysis (T1a)
```
python -I -B tools/t1_analyze.py --engine n20k \
  8moves=build/t1_books/8moves600/games.pgn,build/t1_books/8moves600/stdout.txt \
  uho=build/t1_books/uho600/games.pgn,build/t1_books/uho600/stdout.txt --json repo/opus_oss_scout/trials/t1_books/t1_result.json
```
