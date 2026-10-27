# S43 S26 add-on: absolute paths, `--base`, bench-ref file (PC-native net-batch v5)

Sol's S26 v4 kit already took `--base`, a bench-ref FILE and absolute paths, but only on Linux (flock lock file, nice,
CPU affinity, `setsid`, GCC 14 box recipe), and its native qualification was outstanding. `forge_sol_S43_netbatch_v5_20261027.py`
is a new, small, PC-native successor for the S43 requirements. Sol's files are not edited; his `forge-s26-bench-refs-v1`
and `forge-s26-allowlist-v1` files are read unchanged.

## What it guarantees
- `--base <dir>`: any Forge tree. Command-line paths may be relative or absolute; all of them are resolved ONCE at start
  (against the cwd at that moment) to absolute real paths, and only absolute paths are used afterwards. Applying the tool
  to a new base therefore needs no edit, only arguments (and, for a different net, a reference file).
- `--bench-ref <FILE>`: bench nodes at d11/13/16/20/22, keyed by the net's sha256 (Sol's schema). A missing net is
  `NO_REFERENCE` and a differing depth is `PIN_MISMATCH`. Both exit 1.
- Absolute paths everywhere: outputs, logs, the private source copy, build products, the CTest build dir and the junit
  file. Every subprocess gets an explicit absolute cwd. CTest is called with `--test-dir <abs>` and `--output-junit <abs>`
  (CTest resolves a relative junit path against the test dir, not the caller's cwd: the class of failure that once
  aborted ctest with exit 2).
- Per net: a private copy of the base under the NEW `--out` (the base is hashed before and after and never modified; the
  copy filter uses exact, case-sensitive names, because `shutil.ignore_patterns` is case-insensitive on Windows and a
  pattern like `cmake*` would drop `CMakeLists.txt`); the net copied into `src/nnue_weights.inc` (sha256 checked); the PC
  lock recipe build (MSYS2 ucrt64 g++ 15.2: `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off
  -fno-fast-math -march=znver5 -static -pthread`); the FMA count over the whole binary (`objdump -d`); bench at five
  depths in one UCI process (Threads=1, Hash=16, OwnBook=false); optional `--perft` (startpos and kiwipete perft 5);
  optional `--ctest` (CMake + Ninja `-j 1`, CTest with a Sol-format allowlist: only the allowed test may fail, and each
  FAIL/KNOWN_FAILURE line must match a rule within its max_count and the max_total).
- Idle priority, one process at a time, single-threaded builds, free RAM checked before every step (default 6 GiB).

## Usage
```
nice -n 19 <python> -I -B forge_sol_S43_netbatch_v5_20261027.py --base <tree> --net <a.inc> [--net <b.inc> ...] \
   --bench-ref <refs.json> --out <NEW dir> [--perft] [--ctest --allowlist <allow.json>] \
   [--gpp ...] [--objdump ...] [--cmake ...] [--ctest-exe ...] [--python3 C:/Python314/python.exe]
```
Outputs: `<out>/netbatch_result.json` (inputs as given and as resolved, cwd at start, tool sha256, per-net rows, every
step's argv/cwd/exit code/log paths), `<out>/netbatch_table.md`, `<out>/logs/*`, `<out>/net_NN_<sha12>/` (private tree,
`forge.exe`, `uci_transcript.txt`, CTest build and junit). Exit 0 only if every net passes.

Data files for the AL1 tree (a new base; no tool edit): `forge_sol_S43_bench_refs_AL1_20261027.json` (AL1 pins
312866 / 862329 / 3024920 / 12389307 / 34048354, net a7ebcf3a…) and `forge_sol_S43_allowlist_AL1_20261027.json` (the 4
known AL1 lines; WAC 001 score 623 with the AL1 net, 661 with h256_e12).

## Tests
`test_forge_sol_S43_netbatch_v5_20261027.py` (7 tests) uses `fake_toolchain_s43.py`: a SYNTHETIC g++ that refuses
sources it cannot find relative to its cwd, a fake engine whose bench depends on the embedded net, a fake objdump, and
a fake cmake/ctest that exit 2 on any relative `-S/-B/--test-dir/--output-junit`. The tests cover: relative paths from
one cwd equal absolute paths from another; a new base with the tool unchanged; a PIN_MISMATCH at d22; NO_REFERENCE;
FMA detection; refusals; the allowlist classifier; and the CTest path from a foreign cwd (with `CMakeLists.txt` kept and
build products dropped). `mutation_check_s43.py` runs an unmutated control and 9 planted bugs.
