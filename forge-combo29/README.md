# Forge combo29 (current speed lock)

Standalone Linux build of the Forge lock source. GCC 12+ or Clang 15+, CMake 3.16+, an x86-64 CPU.

```bash
cd forge-combo29
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j
scripts/check_pins.sh build/forge          # bench 11/13/16/20/22 net-on + net-off, then perft 5; must print "PINS MATCH combo29"
```

Manual commands (UCI on stdin): `bench 13` → `info string bench depth 13 nodes 862329 ...`;
`setoption name UseNNUE value false` then `bench 13` → `nodes 907205`; `position startpos` then `go perft 5` → `nodes 4865609`.
`eval` prints `info string eval hce <a> nnue <b> total <c>` for the current position (append ` incheck 1` when the side to move is in check). `ctest --test-dir build` runs that check.

No AVX-512/BMI2 on the host? Configure with `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` (drops the PEXT and ZMM speed switches; on the box this still gave the same pins).

Rules: keep strict FP order (`-ffp-contract=off -fno-fast-math`); every engine change goes in as a default-0 switch with the lock code under `#else`; prove pins/bit-exactness first. NPS from a Linux container is not a speed result, and Elo comes only from SPRT gates on Couns's PC. See LOCK.md for hashes and where everything came from.
