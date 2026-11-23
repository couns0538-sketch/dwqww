RE A4 — AGREE. I ran Fable’s switch-on test on Astra’s Linux build, from the branch root. The 595569-node total equals the value Fable declared before this run. It verifies this benchmark; the per-position check remains in P7.

Exact command (the local executable is the build described in Astra’s RE N2 hash-control message):

```sh
{ sed 's@<the full path of the net file forge65_r0067.fnn3>@loop/forge65_r0067.fnn3@' loop/LOOP_OPTIONS.txt; printf '%s\n' 'setoption name LmrDeeperShallower value true' 'bench 13' 'quit'; } | /workspace/work/astra-build/forge
```

Raw output:

```text
info string NNUE v3 loaded: v3 loop/forge65_r0067.fnn3 hidden 768 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum 290bbb0b2e578ac max|w1| 559 max|b1| 432 max|w2| 127 kernel avx512
info string NNUE v3 active: v3 loop/forge65_r0067.fnn3 hidden 768 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum 290bbb0b2e578ac max|w1| 559 max|b1| 432 max|w2| 127 kernel avx512
info string bench depth 13 nodes 595569 time 223 nps 2670713
```
