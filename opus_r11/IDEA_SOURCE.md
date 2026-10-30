# R11 idea sources

- Own project only: Forge FPOS/FHCE formats (src/datagen.cpp, forge_push/nnue_data), the R7 J2 converter rule
  (fpos2sf_mt: FPOS -> binpack, castling/ep "-", constant ply, king-square null move), the R8 v5 self-play post-step
  (`.dedup.json` = shard done), Astra A1's filtered set and transport tools, R6 AMD trainer port, R10 HalfKA tools
  (halfka_tool, parity_nnue_pytorch.py, halfka_uci_check.py, wac_tactics.py, build_r10.py / build_tool.py).
- nnue-pytorch (GPL-3.0, pinned b2614500 in the R6 clone) is used as a library: its binpack writer (`lib/binpack.h`)
  and its trainer modules are included / imported from the clone at run time, never copied. Everything that links or
  imports it lives in `tools/nnue_pytorch_amd/r11/` (GPL tool tree) and never in Forge `src/`, `include/`, `tests/`.
- Generic techniques (no code copied from any engine): external-memory dedup by hash-range passes with a stable sort
  (first occurrence in a fixed priority order wins), atomic writes (temp + rename) with per-unit done markers,
  checkpoint rotation (newest N + best by validation loss), resource governors (free RAM, system CPU, production
  process detection).
