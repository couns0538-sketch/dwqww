# fpos2sf_mt: multi-threaded, streaming Forge .pos -> .binpack / .bin (R7 J2)

GPL-3.0 (built against nnue-pytorch's `data_loader/cpp/lib` headers; derived from Grok Bot's
`F:\nnue_pytorch\forge_tools\fpos2sf.cpp`). Tool tree only; never copy into Forge sources.

Same command line and **byte-identical output** as `fpos2sf.exe`, plus `--threads T` (default 3, the PC's cap;
the main thread is one of them) and a `--verify` mode.

## Build (MSYS2 ucrt64 g++ 15.2, Git Bash)
```
export PATH=/c/msys64/ucrt64/bin:$PATH
g++ -std=c++20 -O3 -DNDEBUG -march=native -DHAS_BMI2 -I<nnue-pytorch>/data_loader/cpp -static -pthread \
    tools/nnue_pytorch_amd/fpos2sf_mt/fpos2sf_mt.cpp -o fpos2sf_mt.exe
```
(`-march=native` = this PC; the output bytes do not depend on it.)

## Use
```
fpos2sf_mt <in.pos> <out.binpack|out.bin> [--max N] [--skip N] [--stride K] [--ply P] [--score-mult M] [--threads T] [--fen-out f.txt]
fpos2sf_mt --verify <in.pos> <file.binpack|file.bin> [same selection options] [--threads T] [--reader-check 0|1]
```
`--verify` decodes every output record with the loader's decoder (`unpackEntry` / `packedSfenValueToTrainingDataEntry`)
and compares it with the FPOS record square by square (not via a FEN): pieces, side to move, score (after
`--score-mult` and the +-32000 clip), result, ply, move; it also counts bad source records, format errors and
missing/extra records, and (binpack) streams the file through the training loader's own sequential
`CompressedTrainingDataEntryReader`. Exit 0 only on `VERIFY OK`.

## Why the parallel output is identical
FPOS has no move or ply, so every entry gets the same `--ply`; binpack chains entries only when `ply + 1` matches
(`isContinuation`), so it never chains: each entry is 32 packed bytes + a 2-byte zero move count, and the sequential
writer flushes a chunk after exactly ceil(1 MiB / 34) = 30,841 entries. Workers convert whole 30,841-record units;
the main thread emits them in order and flushes exactly where the sequential writer would (bad records skipped the
same way, `--max` counted on written records).

## Tests
- `j2_check.sh <fpos2sf_mt.exe> <old fpos2sf.exe> <shard.pos> <work dir>`: full shard old vs new (1 and 3 threads),
  `.bin`, skip/stride/ply/score-mult/max + `--fen-out`, a 200k copy with 6 planted bad records (`make_bad_pos.py`),
  verify of each output, and a planted 1-byte corruption that verify must reject. Prints `J2 CHECK PASS`.
- `movecheck.cpp`: shows that binpack stores the from == to dummy move as `Move::null()` (square 64).
