# R8: fast self-play data generation (`forge_selfplay_fast`)

A native (C++) replacement for the Python orchestration of `forge-nnue-tools/forge_selfplay.py`. It drives the
**unchanged engine binary** over UCI exactly like the live script (same commands, same rules, same output lines),
so the data are the same by construction; the line-by-line equivalence test proves it. Nothing here replaces the
live workers: switching is the owner's decision.

## Build (MSYS2 ucrt64 g++, Git Bash, from the branch root)
```
python -I -B r8/tools/run_pinned.py --mask 0x00FF -- r8/tools/build_driver.py <repo root> <out.exe>
```
(`run_pinned.py` keeps the compiler on CPUs 0-7 at BelowNormal.) The driver links Forge's own Board
(`src/board.cpp`, `src/bitboard.cpp` of this tree, Forge 6.2.0 release source) for the chess rules only; the
engine that searches is whatever `--engine` names.

## Run (the live configuration, written to a NEW folder)
```
forge_selfplay_fast.exe --engine C:\Users\Administrator\grok-pc\nnue\forge.exe --out D:\grok-pc-data\selfplay_out_fast ^
    --workers 2 --cpus 12-15 --nodes 5000 --hash 16 --pos --progress-seconds 60
```
- Engines start at Idle priority (`--priority belownormal` to change), pinned to `--cpus` (one CPU each when there
  are at least as many CPUs as workers and more than one worker, else all of them, like the live script).
- Output: `<prefix>_NNN.txt` (default prefix `forge_selfplay_fast`), "FEN | cp | result" lines identical to the live
  files, 10,000,000 lines per file; with `--pos` also `<prefix>_NNN.pos` (FPOS v1, the format of `nnue_data\pos`) and
  `.pos.info`. Existing files are never overwritten (the number skips to the next free one).
- De-duplication is in memory for the run (first four FEN fields): by default a bounded table of 64-bit
  fingerprints (`--dedup-mb 512` = 67M slots, the newest key wins a slot collision, like the Stockfish generator;
  memory does not grow), `--dedup exact` = an exact set (memory grows ~64 bytes per kept position; for tests).
  To also drop positions already in the live database, run
  `r8/tools/dedup_against_db.py <live forge_seen_hashes.sqlite3> <out.txt> <in.txt>` (read only).
- A worker whose engine stops answering ends with an error message (the others go on).
- With `--pos` a file's records are held in memory until the file is complete (35 bytes each, 350 MB for 10M lines)
  and written at rotation or at a normal stop; if the process is killed, the last file has text only.
- Stops after `--max-minutes` or `--games-per-worker`; otherwise runs until the process is ended.
- `--openings FILE` plays fixed openings (one game per line, UCI moves) instead of random ones (used by the test).

## Options that change the data (all OFF / at the live values by default)
`--own-book true` (the live script leaves the engine default `OwnBook=true`; the driver sets false, see the report),
`--hash` (live 16), `--nodes` (live 5000), `--opening-plies` (8), `--max-ply` (300), `--adjudicate-cp` (2000),
`--adjudicate-plies` (4), `--max-score` (3000), `--no-dedup`, `--check-nodes N` (in-check positions, which are never
recorded, searched with N nodes instead of `--nodes`: same labels, a different game path after them).

## Tests
- `r8/tools/equivalence_ref.py gen 60 <seed> openings.txt`, then `ref <engine> openings.txt ref.txt` (the live
  `play_game()` itself) and `forge_selfplay_fast --openings openings.txt --no-dedup ...`: the two text files must be
  byte-identical.
- `r8/tools/check_pos_vs_text.py <file.pos> <file.txt>`: the `.pos` holds exactly the text file's records.
- `r8/tools/quality_check.py base=<baseline.txt> fast=<driver.txt>`: score / result / ply spread, duplicates.
