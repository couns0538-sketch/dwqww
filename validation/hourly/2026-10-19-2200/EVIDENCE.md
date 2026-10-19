# Forge 6.4 22:00 standalone policy regression evidence

This is a **policy model only**. Do not interpret it as a full Forge search result.

Accepted engine ref: `forge/6.4-hourly-20261019` at `9108d012526be80c6d163f7cab684e6acd9abf8d`.
Audit branch: `forge/audit-rule50-reverse-contamination-20261019-2200`.

Source: `rule50_producer_consumer_repro.cpp`, SHA256 `5279c3f1a8f6a777caf99a778513efcc81dcbf6ea90d7cc8b40be2528c9599ce`, Git blob `1c8a81a1a44166ef36d3c3da8573398eb84bb2c3`.

GCC 14.2.0, Clang 17.0.0 (Linux). Exact commands executed in a writable directory with the source file:

```sh
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Wshadow rule50_producer_consumer_repro.cpp -o repro-gcc
./repro-gcc
clang++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wconversion -Wshadow rule50_producer_consumer_repro.cpp -o repro-clang
./repro-clang
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer rule50_producer_consumer_repro.cpp -o repro-san
ASAN_OPTIONS=detect_leaks=0 ./repro-san
```

All three independently exited 0; logs contain exactly:

```
MODEL PASS 33 cases, 12 source-high/probe-low paths
```

Original logs: `gcc-raw.log`, `clang-raw.log`, `sanitizer-raw.log`, each SHA256 `1bc7deb6c1271abc7c84f0ef4a432432370fba8444be9f5f2b0968f4d2d51292`.

No Forge compilation, perft, UCI, bench or match was performed. No PGNs, no Elo estimate.

**Next independent reproduction:** log TT score stores at halfmove 90-99 and probes at halfmove 0-89 for the identical position key, establish an actual legal-position score oracle, then evaluate storage provenance and speed impact. Keep baseline unchanged.
