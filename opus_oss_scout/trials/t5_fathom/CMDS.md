# T5 Fathom as an oracle for Forge's own Syzygy reader - exact commands

Base folder: `C:\opus_5h\oss_scout`. Idle priority, CPUs 2-3 (inherited).

## Inputs
- Tables: the PC's 3-4-5 piece set, read in place (read-only):
  `D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345`, 291 files, 938 MB (145 WDL + 145 DTZ; R3-1L list
  `opus_r3/R3-1L/syzygy345.sha256`).
- Fathom (MIT): `git clone --depth 1 https://github.com/jdart1/Fathom.git dl/fathom` at
  c9c6fef0dddc05d2e242c183acf5833149ab676d (2025-12-23).
- Forge's reader: the R13 P6 port.
  - Source: lock source d4f4312 (src, include; LF) + `opus_r13/p6/syzygy_port.patch` from opus-r13-p6-syzygy tip
    4bf626eb (md5 4342d24f, the md5 named in the P6 RESULTS.md), applied with `patch -p1 -F0` (6 files).
  - Probe tool: `opus_r13/p6/tb_probe.cpp` from the same tip.
- Positions: `python -I -B tools/t5_gen_fens.py D:/grok-pc-data/dwqww/.claude/worktrees/syzygy345 build/t5/data/t5_50k.fens --n 50000 --seed 20261106 --max-pieces 5`.
  - 50,000 random legal positions from the 145 materials.
  - Rules: no castling, no ep, halfmove 0; side to move random; the side not to move is not in check.
  - Own stdlib code; no python-chess.

## Builds
- Fathom batch prober (own `tools/t5_fathom_batch.c` + Fathom `src/tbprobe.c`), MSYS2 ucrt64 gcc 15.2:
  `gcc -O2 -std=c11 -march=x86-64-v3 -I dl/fathom/src tools/t5_fathom_batch.c dl/fathom/src/tbprobe.c -static -o build/t5/fathom/t5_fathom_batch.exe`
- Forge tb_probe (the build line from the tb_probe.cpp header), g++ 15.2:
  `g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -march=x86-64-v3 -static -Iinclude tb_probe.cpp src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp -o tb_probe.exe`

## Runs
- `build/t5/fathom/t5_fathom_batch.exe <tables> build/t5/data/t5_50k.fens 3 > fathom_50k.out 2> fathom_50k.err`
  (stderr: WDL-only timing passes over all parsed positions).
- `build/t5/forge/tb_probe.exe <tables> build/t5/data/t5_50k.fens > forge_50k.out 2> forge_50k.err`
- `python -I -B tools/t5_compare.py build/t5/data/t5_50k.fens forge_50k.out fathom_50k.out --json trials/t5_fathom/t5_result.json`
