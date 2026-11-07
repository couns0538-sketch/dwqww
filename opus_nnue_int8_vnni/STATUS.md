# NnueInt8Vnni - STATUS

**Last update:** step 2a, 2026-11-06 PC clock (see the commit time).

**Done:**
- 2a: QUANT_SCHEME.md and the converter `tools/int8_convert.py`.
  - The generated `nnue_int8_weights.inc` (md5 25982cc2) is in `D:\opus_5h\int8_vnni\src\int8\src\`.
  - It will ship inside the after_w6 patch from 2b on.

**In progress:** 2b, the scalar int8 path in nnue.cpp/hpp, the uci.cpp option and the eval-diff harness.

**Exact next step:**
1. Edit `D:\opus_5h\int8_vnni\src\int8`. Every new line must sit inside `#if FORGE_NNUE_INT8_VNNI`.
2. Run a `g++ -E` identity check at macro 0.
3. Build the harness and write the eval-diff statistics.

**Resume commands:**
```
cd /f/ospd/wt && git checkout opus-nnue-int8-vnni-20261106
C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B opus_nnue_int8_vnni/tools/int8_convert.py \
  /f/ospd/src/trial_w6/src/nnue_weights.inc <new path>/nnue_int8_weights.inc     # expect md5 25982cc2
```

**Unproven / not claimed:** everything about strength and speed. Eval-diff statistics do not exist yet (2b), and neither
do the bounds (2c). There is no SIMD yet.

**Disk:** D: had 47.8 GiB free at the start, below the 50 GB floor of earlier jobs. This brief names D: for builds. The
own footprint is under 0.3 GB, and D: is checked before every build.
