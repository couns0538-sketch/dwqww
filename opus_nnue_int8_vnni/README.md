# NnueInt8Vnni pack (int8 VNNI NNUE inference) - UNPROVEN, not bit-exact, default OFF

- **Branch:** `opus-nnue-int8-vnni-20261106`, cut from the opus-speed tip after the runner audit (e5412ac5).
- **Engine parent:** the live lock trial_w6 source, `F:\ospd\src\trial_w6`, sha256 4181A589...6FB0 when its six lock
  switches are flipped.
- **Builds and outputs:** `D:\opus_5h\int8_vnni\`.
- **Macro:** `FORGE_NNUE_INT8_VNNI`, one `#define FORGE_NNUE_INT8_VNNI 0` line in `include/forge/nnue.hpp`.
- **Gate build only:** UCI `option name NnueInt8Vnni type spin default 0 min 0 max 1`.
  - Runtime 0 is the lock's float path.
  - Runtime 1 is the int8 path in QUANT_SCHEME.md.
- **Gate line (QA, after Code Review):** gate exe with `setoption name NnueInt8Vnni value 1` vs trial_w6. This needs an
  SPRT, because nodes and eval change. No Elo or speed claim is made here.

| file | content |
|---|---|
| QUANT_SCHEME.md | scales, clips, SCReLU, converter (2a) |
| BOUNDS.md | int16 FT and int32 vpdpbusd overflow bounds (2c) |
| BENCH.md | identity / gate pins, ON nodes (2e) |
| int8_vnni_after_w6.patch | the source change vs trial_w6 (all switches at their source default 0) |
| tools/ | int8_convert.py, harness, bounds tool, port_controls.sh |
| STATUS.md | done / in progress / next step / resume commands / unproven claims |
