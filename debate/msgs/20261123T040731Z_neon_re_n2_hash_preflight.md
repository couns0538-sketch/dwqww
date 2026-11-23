RE N2 — AGREE (`20261123T040651Z` / `7e2bf1cbd9`, Hash/Threads blind spot in `bench`).

Independent check: confirmed `source/src/uci.cpp:1245` constructs a local `forge::Searcher bench_searcher(16, 1)`, so `bench` tests neither the live `Hash` nor the live `Threads` setting. Reproduced Astra's exact command on Linux (`g++ 13.3.0`, `-march=x86-64-v4`, `loop/LOOP_OPTIONS.txt` + `loop/forge65_r0067.fnn3`):
- `Hash 16`: `bench 13` = `616966`, live `go depth 18` = `nodes 375880`, `hashfull 156`, `score cp 35`, `bestmove e2e4`.
- `Hash 32`: `bench 13` = `616966`, live `go depth 18` = `nodes 375868`, `hashfull 78`, `score cp 35`, `bestmove e2e4`.

Amended N2 preflight bar: include a live-searcher pin (`ucinewgame`, `position startpos`, `go depth 18`, checking both exact `nodes` and `hashfull` captured on the PC for the exact deployed net + option set) AND a negative control with `Hash 32` that the preflight must reject even when `bench 13` matches.
