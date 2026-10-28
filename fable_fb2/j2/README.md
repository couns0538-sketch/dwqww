# FB2-J2: self-play datagen v2 (branch `fable-fb2-j2`)

In-engine self-play behind the UCI command `datagen` (the engine's normal paths are untouched: OFF identity pins hold).

## Generate
```
printf 'datagen --out F:/opus_scratch/fable/datagen/run1 --max-minutes 10 --nodes 5000 --hash 16 \
  --random-plies 8 --random-plies-jitter 4 --temp-plies 2 --temperature 100 --temp-depth 3 --opening-eval-cap 300 \
  --min-ply 16 --skip-prob 0.25 --draw-cp 8 --draw-plies 10 --draw-min-ply 80 --seed 20261028 --pos\nquit\n' | forge_fable_j2.exe
```
Limits: `--games N`, `--records N`, `--max-minutes M` (any combination; the first reached stops). Search: `--nodes N` or
`--depth D`, `--hash MB`. Openings: `--book FILE` (FEN/EPD lines, one random line per game), `--random-plies N`,
`--random-plies-jitter J`, `--temp-plies M --temperature T --temp-depth D` (softmax over per-move shallow searches),
`--opening-eval-cap C --opening-attempts A` (redraw lopsided openings). Rules: `--max-ply`, `--win-cp --win-plies`,
`--draw-cp --draw-plies --draw-min-ply`. Filters: `--max-score`, `--min-ply`, `--pv-capture-plies K`, `--skip-prob p`,
`--keep-in-check`, `--filter-gives-check`. Outputs: `<out>.fgb` (always), `<out>.info.json` (config + statistics),
`--pos` (also `<out>.pos/.hce` written directly), `--text` (`fen | score | result` lines). Same seed = same bytes.
To generate with the v3 net: `setoption name NNUEArch value true` / `NNUEArchFile` before `datagen`.

## Convert (compact -> trainer format)
```
datagen convert <in.fgb> <out prefix> [text]      ->  <out>.pos, <out>.hce (+ .txt)
```
The converter replays every game with the engine's Board and recomputes the HCE labels; its output is byte-identical
to the direct `--pos` files (tests below).

## Independent decoder (python-chess)
`tools/nnue/fable_datagen_decode.py info|decode|compare|test` — replays the games without the engine, checks every
move's legality, the termination/result consistency and the in-check / noisy flags, rebuilds the FPOS rows and
compares them byte for byte with the engine's output (`compare`), or runs a whole tiny generation + conversion
against an engine exe (`test <forge.exe> <scratch>`).

## Tests
- `forge_datagen2_tests <scratch>` (CTest `forge_datagen2_tests`): move encoding over 153 legal moves (castling,
  promotions, en passant), serialisation round trip + corruption detection (flipped byte, truncation, bad counts),
  4 played games (flags vs rules, kept records obey every filter, checkmate/stalemate/adjudication results), same
  seed = byte-identical games and files, direct `.pos/.hce/.txt` == converter output, argument parsing.
- `fable_datagen_decode.py test <forge.exe> <scratch>`: 6 games, python-chess rows == engine rows, converter files ==
  direct files, text == text.

## Build
Box recipe: `FORGE_EXTRA_SRCS="src/nnue_v3.cpp src/search_v3.cpp src/datagen2.cpp" build_pc.sh <src> <out.exe>`;
CMake adds `src/datagen2.cpp` to `forge_core` and the test target. Evidence in `logs/`.
